"""
bot/harvester.py - Robotic Data Harvester engine.
Integrates Playwright browser automation and HTTP REST collectors with resilient fallbacks.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from bot.config import BotConfig
from bot.logger import BotLogger

logger = BotLogger.get_logger()


class DataHarvester:
    """
    RPA Data Harvester responsible for collecting job postings across sources.
    Uses Playwright for dynamic JavaScript-rendered pages and Requests for fast APIs.
    """

    def __init__(self, config: BotConfig):
        self.config = config
        self.raw_data_dir = Path("data/raw")
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36 RPA-Bot/1.0"
            )
        })

    def harvest_all(self) -> List[Dict[str, Any]]:
        """
        Executes harvesting across all configured sources.
        """
        all_records: List[Dict[str, Any]] = []
        logger.info(f"Starting RPA Data Harvesting across {len(self.config.sources)} configured sources...")

        for source in self.config.sources:
            if not source.get("enabled", True):
                logger.info(f"Source '{source.get('name')}' is disabled. Skipping.")
                continue

            source_type = source.get("type", "api_web")
            source_name = source.get("name", "Unknown Source")
            url = source.get("url", "")

            try:
                if source_type == "api_web":
                    records = self._harvest_api(source_name, url)
                elif source_type == "playwright_web":
                    records = self._harvest_playwright(source_name, url)
                else:
                    logger.warning(f"Unknown source type '{source_type}'. Falling back to HTTP.")
                    records = self._harvest_api(source_name, url)

                logger.info(f"Source '{source_name}' yielded {len(records)} records.")
                all_records.extend(records)
            except Exception as e:
                logger.error(f"Error harvesting from '{source_name}': {e}", exc_info=True)
                # Fallback to realistic synthetic benchmark records if network or blocked
                fallback_records = self._get_resilient_fallback_data(source_name)
                logger.info(f"Loaded {len(fallback_records)} resilient fallback records for '{source_name}'.")
                all_records.extend(fallback_records)

        # If zero records gathered from live network, use robust benchmark data
        if not all_records:
            logger.warning("No records harvested from live endpoints. Activating fallback benchmark dataset.")
            all_records = self._get_resilient_fallback_data("Resilient RPA Benchmark Feed")

        # Save raw extraction snapshot
        self._save_raw_snapshot(all_records)
        return all_records

    def _harvest_api(self, source_name: str, url: str) -> List[Dict[str, Any]]:
        """
        Fetches structured listings from RemoteOK public JSON endpoint or similar tech portals.
        """
        logger.info(f"[HTTP Harvester] Fetching data from: {url}")
        records: List[Dict[str, Any]] = []

        try:
            response = self.session.get(url, timeout=12)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # RemoteOK returns a list where the first item is a legal note
                    items = [item for item in data if isinstance(item, dict) and "position" in item]
                    for item in items[: self.config.max_results]:
                        records.append({
                            "source": source_name,
                            "title": item.get("position", "").strip(),
                            "company": item.get("company", "").strip(),
                            "location": item.get("location", "Remote"),
                            "salary_raw": self._format_salary_text(
                                item.get("salary_min"), item.get("salary_max")
                            ),
                            "tags": item.get("tags", []),
                            "description": item.get("description", "")[:400].strip(),
                            "url": item.get("url") or f"https://remoteok.com/l/{item.get('id', '')}",
                            "date_posted": item.get("date", datetime.now().isoformat()),
                            "harvest_method": "REST_API",
                        })
            else:
                logger.warning(f"HTTP Status {response.status_code} received from {url}")
        except Exception as ex:
            logger.warning(f"API request failed ({ex}). Proceeding with Playwright/fallback.")

        return records

    def _harvest_playwright(self, source_name: str, url: str) -> List[Dict[str, Any]]:
        """
        Launches Playwright headless browser to automate navigation, DOM querying, and extraction.
        Demonstrates industrial Web Automation (page loading, selector queries, attribute extraction).
        """
        logger.info(f"[Playwright RPA] Launching Chromium browser (headless={self.config.headless})...")
        records: List[Dict[str, Any]] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.config.headless,
                slow_mo=self.config.slow_mo_ms,
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()

            try:
                logger.info(f"[Playwright RPA] Navigating to: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=self.config.timeout_ms)
                page.wait_for_timeout(2000)  # Brief wait for client-side rendering

                # Query job cards using CSS selectors
                rows = page.query_selector_all("tr.job")
                logger.info(f"[Playwright RPA] Found {len(rows)} job table rows on page.")

                count = 0
                for row in rows:
                    if count >= self.config.max_results:
                        break

                    title_el = row.query_selector("h2[itemprop='title'], td.position h2")
                    company_el = row.query_selector("h3[itemprop='name'], td.company h3")
                    location_el = row.query_selector("div.location, td.location")
                    salary_el = row.query_selector("div.salary")
                    tags_els = row.query_selector_all("div.tag h3, h3.tag")

                    title = title_el.inner_text().strip() if title_el else ""
                    company = company_el.inner_text().strip() if company_el else ""

                    if not title:
                        continue

                    location = location_el.inner_text().strip() if location_el else "Remote"
                    salary_raw = salary_el.inner_text().strip() if salary_el else "Not Disclosed"
                    tags = [t.inner_text().strip() for t in tags_els if t.inner_text()]

                    # Extract job post link
                    link_el = row.query_selector("a[itemprop='url'], a.preventLink")
                    job_link = ""
                    if link_el:
                        href = link_el.get_attribute("href")
                        job_link = f"https://remoteok.com{href}" if href and href.startswith("/") else (href or "")

                    records.append({
                        "source": source_name,
                        "title": title,
                        "company": company,
                        "location": location,
                        "salary_raw": salary_raw,
                        "tags": tags,
                        "description": f"Role for {title} at {company} specializing in modern software & automation.",
                        "url": job_link or url,
                        "date_posted": datetime.now().strftime("%Y-%m-%d"),
                        "harvest_method": "PLAYWRIGHT_DOM",
                    })
                    count += 1

            except Exception as e:
                logger.warning(f"[Playwright RPA] Execution encountered an issue: {e}")
                # Save screenshot for RPA error audit
                screenshot_path = Path("logs/playwright_error_snapshot.png")
                try:
                    page.screenshot(path=str(screenshot_path))
                    logger.info(f"[Playwright RPA] Error diagnostic screenshot saved to: {screenshot_path}")
                except Exception:
                    pass
            finally:
                browser.close()
                logger.info("[Playwright RPA] Browser session closed cleanly.")

        return records

    def _format_salary_text(self, min_s: Any, max_s: Any) -> str:
        if min_s and max_s:
            return f"${min_s:,} - ${max_s:,}"
        elif min_s:
            return f"${min_s:,}+"
        elif max_s:
            return f"Up to ${max_s:,}"
        return "Not Disclosed"

    def _save_raw_snapshot(self, records: List[Dict[str, Any]]) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.raw_data_dir / f"raw_harvest_{timestamp}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        logger.info(f"Raw harvest payload snapshot saved ({len(records)} records) -> {filepath}")

    def _get_resilient_fallback_data(self, source_name: str) -> List[Dict[str, Any]]:
        """
        Guarantees that the student can execute and inspect the full pipeline
        even in offline, firewall-protected, or sandbox lab environments.
        """
        now = datetime.now().strftime("%Y-%m-%d")
        return [
            {
                "source": source_name,
                "title": "Senior AI Agent & RPA Architect",
                "company": "CognitiveAuto Labs",
                "location": "Remote / Worldwide",
                "salary_raw": "$135,000 - $165,000",
                "tags": ["AI Agent", "RPA", "LangChain", "Python", "UiPath"],
                "description": "Design autonomous multi-agent pipelines with Playwright web harvesting and LLM workflow reasoning.",
                "url": "https://careers.example.com/jobs/ai-agent-rpa-architect",
                "date_posted": now,
                "harvest_method": "RESILIENT_BENCHMARK",
            },
            {
                "source": source_name,
                "title": "Robotic Process Automation Engineer (UiPath / Python)",
                "company": "Enterprise Flow Solutions",
                "location": "Paris / Hybrid",
                "salary_raw": "€65,000 - €80,000",
                "tags": ["RPA", "UiPath", "Python", "Power Automate", "Excel"],
                "description": "Develop enterprise unattended RPA bots for financial back-office reconciliation and SAP data entry.",
                "url": "https://careers.example.com/jobs/rpa-engineer-paris",
                "date_posted": now,
                "harvest_method": "RESILIENT_BENCHMARK",
            },
            {
                "source": source_name,
                "title": "Lead Automation Engineer (Playwright & API Bot)",
                "company": "FinTech Scaler Inc",
                "location": "Remote",
                "salary_raw": "$110,000 - $140,000",
                "tags": ["Playwright", "Automation", "Python", "Selenium", "Docker"],
                "description": "Build high-throughput web automation scrapers, synthetic testing bots, and resilient crawler frameworks.",
                "url": "https://careers.example.com/jobs/lead-automation-engineer",
                "date_posted": now,
                "harvest_method": "RESILIENT_BENCHMARK",
            },
            {
                "source": source_name,
                "title": "AI & LLM Solutions Engineer",
                "company": "Agentic Dynamics",
                "location": "London / Remote",
                "salary_raw": "£85,000 - £105,000",
                "tags": ["AI Agent", "LLM", "Python", "CrewAI", "FastAPI"],
                "description": "Integrate agentic tool-calling workflows connecting CRM databases with autonomous customer-facing bots.",
                "url": "https://careers.example.com/jobs/ai-solutions-engineer",
                "date_posted": now,
                "harvest_method": "RESILIENT_BENCHMARK",
            },
            {
                "source": source_name,
                "title": "Data Scientist & Intelligent Automation Lead",
                "company": "Global Logistics AI",
                "location": "Remote",
                "salary_raw": "$125,000 - $150,000",
                "tags": ["Data Scientist", "Python", "Machine Learning", "Automation", "SQL"],
                "description": "Predictive supply chain modeling paired with automated dispatch triggers and executive reporting.",
                "url": "https://careers.example.com/jobs/data-scientist-automation",
                "date_posted": now,
                "harvest_method": "RESILIENT_BENCHMARK",
            },
            {
                "source": source_name,
                "title": "Junior RPA & Python Developer",
                "company": "NextGen Automation Group",
                "location": "Casablanca / Remote",
                "salary_raw": "$45,000 - $60,000",
                "tags": ["RPA", "Python", "OpenPyXL", "BeautifulSoup"],
                "description": "Assist in building scheduled data scraping scripts, automated Excel workbooks, and system integration bots.",
                "url": "https://careers.example.com/jobs/junior-rpa-developer",
                "date_posted": now,
                "harvest_method": "RESILIENT_BENCHMARK",
            },
            {
                "source": source_name,
                "title": "Staff AI Workflow Architect",
                "company": "NeuroSync Systems",
                "location": "Remote / USA",
                "salary_raw": "$175,000 - $210,000",
                "tags": ["AI Agent", "Python", "RPA", "LangGraph", "Kubernetes"],
                "description": "Oversee enterprise autonomous operations combining deterministic RPA with probabilistic LLM agents.",
                "url": "https://careers.example.com/jobs/staff-ai-workflow-architect",
                "date_posted": now,
                "harvest_method": "RESILIENT_BENCHMARK",
            },
        ]
