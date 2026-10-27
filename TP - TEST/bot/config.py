"""
bot/config.py - Configuration loader and validator for the RPA Bot.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


class BotConfig:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.raw_data: Dict[str, Any] = self._load_config()

        # General
        self.project_name: str = self.raw_data.get("project_name", "RPA Bot")
        self.version: str = self.raw_data.get("version", "1.0.0")

        # Search Settings
        search = self.raw_data.get("search_settings", {})
        self.keywords: List[str] = search.get("keywords", ["RPA", "AI Agent", "Python"])
        self.location: str = search.get("location", "Remote")
        self.sources: List[Dict[str, Any]] = search.get("sources", [])
        self.max_results: int = search.get("max_results_per_source", 25)

        # Alert Rules
        alerts = self.raw_data.get("alert_rules", {})
        self.min_salary_usd: float = float(alerts.get("min_salary_usd", 60000))
        self.priority_keywords: List[str] = alerts.get("priority_keywords", ["AI Agent", "RPA"])
        self.min_match_score: int = int(alerts.get("min_match_score", 70))

        # Reporting & Paths
        reporting = self.raw_data.get("reporting", {})
        self.output_dir: Path = Path(reporting.get("output_dir", "reports"))
        self.excel_prefix: str = reporting.get("excel_filename_prefix", "Job_Market_Report")
        self.html_alert_filename: str = reporting.get("html_alert_filename", "alert_notification.html")

        # Browser Settings
        browser = self.raw_data.get("browser_settings", {})
        self.headless: bool = browser.get("headless", True)
        self.timeout_ms: int = int(browser.get("timeout_ms", 15000))
        self.slow_mo_ms: int = int(browser.get("slow_mo_ms", 50))

        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(parents=True, exist_ok=True)
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        Path("data/processed").mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found at: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)


# Singleton instance helper
def get_config(config_path: str = "config.json") -> BotConfig:
    return BotConfig(config_path)
