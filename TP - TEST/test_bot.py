"""
test_bot.py - Unit and Integration Tests for RPA Intelligence Bot components.
Validates config loading, salary parsing, matching scores, and Excel generation.
"""

from pathlib import Path
import unittest
import pandas as pd

from bot.config import get_config
from bot.data_processor import DataProcessor
from bot.excel_reporter import ExcelReporter
from bot.notifier import Notifier


class TestRPABot(unittest.TestCase):
    def setUp(self):
        self.config = get_config("config.json")
        self.processor = DataProcessor(self.config)
        self.reporter = ExcelReporter(self.config)
        self.notifier = Notifier(self.config)

    def test_config_loaded(self):
        self.assertIsNotNone(self.config.project_name)
        self.assertGreater(len(self.config.keywords), 0)
        self.assertGreater(self.config.min_salary_usd, 0)

    def test_salary_parsing(self):
        min_s, max_s, est = self.processor._parse_salary("$120,000 - $160,000")
        self.assertEqual(min_s, 120000.0)
        self.assertEqual(max_s, 160000.0)
        self.assertEqual(est, 140000.0)

        min_s2, max_s2, est2 = self.processor._parse_salary("85k")
        self.assertEqual(est2, 85000.0)

    def test_data_processing_and_scoring(self):
        dummy_records = [
            {
                "source": "UnitTest",
                "title": "Senior AI Agent Developer",
                "company": "Tech Corp",
                "location": "Remote",
                "salary_raw": "$130k - $150k",
                "tags": ["AI Agent", "Python", "RPA"],
                "description": "Building automated intelligent workflows.",
                "url": "https://example.com/job1",
                "date_posted": "2026-10-13",
                "harvest_method": "TEST",
            }
        ]
        df = self.processor.process(dummy_records)
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 1)
        self.assertGreaterEqual(df.iloc[0]["match_score"], 70)
        self.assertTrue(df.iloc[0]["is_alert"])

    def test_excel_generation(self):
        dummy_records = [
            {
                "source": "UnitTest",
                "title": "Lead RPA Engineer",
                "company": "AutoCo",
                "location": "Remote",
                "salary_raw": "$100,000",
                "tags": ["RPA", "UiPath"],
                "description": "RPA enterprise systems.",
                "url": "https://example.com/job2",
                "date_posted": "2026-10-13",
                "harvest_method": "TEST",
            }
        ]
        df = self.processor.process(dummy_records)
        kpis = self.processor.compute_summary_kpis(df)
        excel_path = self.reporter.generate_report(df, kpis)
        self.assertTrue(excel_path.exists())
        self.assertTrue(excel_path.stat().st_size > 0)


if __name__ == "__main__":
    unittest.main()
