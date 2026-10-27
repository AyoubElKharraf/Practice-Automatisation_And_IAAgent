"""
bot/data_processor.py - ETL Data transformation, cleaning, scoring & analysis pipeline.
Uses Pandas to standardize extracted records, clean salaries, and compute matching scores.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from bot.config import BotConfig
from bot.logger import BotLogger

logger = BotLogger.get_logger()

# Catalog of known market skills for detection
KNOWN_TECH_SKILLS = [
    "Python", "RPA", "UiPath", "Playwright", "Selenium", "AI Agent",
    "LLM", "LangChain", "LangGraph", "CrewAI", "Power Automate",
    "Docker", "Kubernetes", "SQL", "Pandas", "OpenPyXL", "Machine Learning",
    "FastAPI", "Flask", "BeautifulSoup", "Automation", "Git"
]


class DataProcessor:
    """
    ETL component responsible for cleaning, transforming, scoring,
    and generating analytics from harvested data.
    """

    def __init__(self, config: BotConfig):
        self.config = config
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def process(self, raw_records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Transforms raw dictionaries into a clean, scored, deduplicated DataFrame.
        """
        if not raw_records:
            logger.warning("Empty records received in DataProcessor. Returning empty DataFrame.")
            return pd.DataFrame()

        logger.info(f"Starting ETL Processing for {len(raw_records)} raw records...")
        df = pd.DataFrame(raw_records)

        # 1. Clean strings (title, company, location)
        for col in ["title", "company", "location", "description"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # 2. Extract & Normalize Salary (Numeric Min, Max, and Estimated Midpoint)
        df[["salary_min", "salary_max", "salary_estimated"]] = df["salary_raw"].apply(
            self._parse_salary
        ).tolist()

        # 3. Detect Technical Skills in text and tags
        df["skills_detected"] = df.apply(self._detect_skills, axis=1)
        df["skills_str"] = df["skills_detected"].apply(lambda s: ", ".join(s) if s else "General")

        # 4. Compute Profile Match Score (0 - 100%)
        df["match_score"] = df.apply(self._calculate_match_score, axis=1)

        # 5. Evaluate Alert Trigger
        df["is_alert"] = df.apply(self._evaluate_alert_criteria, axis=1)

        # 6. Deduplicate by title & company
        initial_len = len(df)
        df = df.drop_duplicates(subset=["title", "company"], keep="first").reset_index(drop=True)
        dropped = initial_len - len(df)
        if dropped > 0:
            logger.info(f"Deduplicated {dropped} duplicate job postings.")

        # 7. Sort by Match Score and Estimated Salary
        df = df.sort_values(by=["match_score", "salary_estimated"], ascending=[False, False]).reset_index(drop=True)

        # 8. Save Processed CSV Snapshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        processed_file = self.processed_dir / f"processed_dataset_{timestamp}.csv"
        df.to_csv(processed_file, index=False, encoding="utf-8")
        logger.info(f"Clean processed dataset saved ({len(df)} rows) -> {processed_file}")

        return df

    def _parse_salary(self, raw_val: str) -> Tuple[float, float, float]:
        """
        Extracts numeric values from messy strings like '$120,000 - $150,000', '€65k', or 'Not Disclosed'.
        Returns (min_salary, max_salary, estimated_midpoint).
        """
        if not raw_val or raw_val.lower() in ["not disclosed", "none", "nan"]:
            return (0.0, 0.0, 0.0)

        # Clean string
        text = str(raw_val).replace(",", "").replace(" ", "").lower()

        # Check for currency multipliers like 'k'
        matches = re.findall(r"(\d+(?:\.\d+)?)(k)?", text)
        if not matches:
            return (0.0, 0.0, 0.0)

        numbers = []
        for num_str, is_k in matches:
            try:
                val = float(num_str)
                if is_k or val < 1000:  # If marked with k or written as '120'
                    val *= 1000
                numbers.append(val)
            except ValueError:
                continue

        if not numbers:
            return (0.0, 0.0, 0.0)

        min_val = min(numbers)
        max_val = max(numbers)
        estimated = (min_val + max_val) / 2.0 if min_val != max_val else min_val
        return (min_val, max_val, estimated)

    def _detect_skills(self, row: pd.Series) -> List[str]:
        """
        Detects relevant technical skills from tags, title, and description.
        """
        found = set()
        raw_tags = row.get("tags", [])
        if isinstance(raw_tags, list):
            for t in raw_tags:
                found.add(str(t).strip())

        full_text = f"{row.get('title', '')} {row.get('description', '')}".lower()
        for skill in KNOWN_TECH_SKILLS:
            pattern = rf"\b{re.escape(skill.lower())}\b"
            if re.search(pattern, full_text):
                found.add(skill)

        return sorted(list(found))

    def _calculate_match_score(self, row: pd.Series) -> int:
        """
        Calculates a compatibility score (0 - 100) based on targeted keywords,
        skills, and priority roles.
        """
        score = 0
        title = row.get("title", "").lower()
        skills = [s.lower() for s in row.get("skills_detected", [])]
        desc = row.get("description", "").lower()

        # Check priority keywords (+25 each, up to 50)
        priority_hits = 0
        for kw in self.config.priority_keywords:
            kw_l = kw.lower()
            if kw_l in title or kw_l in skills:
                priority_hits += 1
        score += min(priority_hits * 25, 50)

        # Check general configured search keywords (+10 each, up to 30)
        kw_hits = 0
        for kw in self.config.keywords:
            kw_l = kw.lower()
            if kw_l in title or kw_l in skills or kw_l in desc:
                kw_hits += 1
        score += min(kw_hits * 10, 30)

        # Check salary incentive (+20 if salary is disclosed and above minimum)
        if row.get("salary_estimated", 0) >= self.config.min_salary_usd:
            score += 20
        elif row.get("salary_estimated", 0) > 0:
            score += 10

        return min(max(score, 10), 100)

    def _evaluate_alert_criteria(self, row: pd.Series) -> bool:
        """
        Triggers an Alert flag if:
        1. Match score meets threshold, OR
        2. Contains critical priority keywords AND meets salary threshold
        """
        score = row.get("match_score", 0)
        salary = row.get("salary_estimated", 0)
        skills = [s.lower() for s in row.get("skills_detected", [])]
        title = row.get("title", "").lower()

        if score >= self.config.min_match_score:
            return True

        has_priority = any(
            p.lower() in title or p.lower() in skills
            for p in self.config.priority_keywords
        )
        if has_priority and (salary >= self.config.min_salary_usd or salary == 0):
            return True

        return False

    def compute_summary_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculates executive KPIs for the dashboard.
        """
        if df.empty:
            return {
                "total_jobs": 0,
                "alert_count": 0,
                "avg_salary": 0,
                "top_skill": "N/A",
                "top_location": "N/A",
            }

        salaries_with_values = df[df["salary_estimated"] > 0]["salary_estimated"]
        avg_salary = salaries_with_values.mean() if not salaries_with_values.empty else 0

        # Skill frequency
        all_skills = [s for sublist in df["skills_detected"] for s in sublist]
        skill_counts = pd.Series(all_skills).value_counts() if all_skills else pd.Series(dtype=int)
        top_skill = skill_counts.index[0] if not skill_counts.empty else "Python"

        # Top location
        top_location = df["location"].value_counts().index[0] if not df["location"].empty else "Remote"

        return {
            "total_jobs": len(df),
            "alert_count": int(df["is_alert"].sum()),
            "avg_salary": round(avg_salary, 2),
            "top_skill": top_skill,
            "top_location": top_location,
            "skill_distribution": skill_counts.head(10).to_dict(),
        }
