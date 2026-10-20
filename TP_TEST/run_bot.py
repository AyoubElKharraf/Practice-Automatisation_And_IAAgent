"""
run_bot.py - Master Orchestrator for the RPA Intelligence Bot.
Master M2I - Automatisation IA & Agent (TP3).

Executes the complete robotic lifecycle:
1. Initialization & Configuration Loading
2. Robotic Web & API Harvesting (Playwright + Requests)
3. ETL Processing & Profile Scoring (Pandas)
4. Enterprise Excel Dashboard Generation (OpenPyXL)
5. Multi-channel Notification & HTML Alert Dispatch
"""

import sys
import time
from pathlib import Path

from bot.config import get_config
from bot.data_processor import DataProcessor
from bot.excel_reporter import ExcelReporter
from bot.harvester import DataHarvester
from bot.logger import BotLogger
from bot.notifier import Notifier


def main():
    start_time = time.time()
    logger = BotLogger.get_logger()

    logger.info("================================================================")
    logger.info("   [RPA BOT] STARTING INTELLIGENCE BOT ORCHESTRATION PIPELINE   ")
    logger.info("================================================================")

    try:
        # Step 1: Load Configuration
        logger.info("[Step 1/5] Loading and validating bot configuration...")
        config = get_config("config.json")
        logger.info(f"Target Keywords: {config.keywords}")
        logger.info(f"Priority Alert Threshold: >= {config.min_match_score}% or >= ${config.min_salary_usd:,.0f}")

        # Step 2: Robotic Harvesting
        logger.info("[Step 2/5] Initiating Robotic Data Harvester...")
        harvester = DataHarvester(config)
        raw_records = harvester.harvest_all()
        logger.info(f"Harvester successfully collected {len(raw_records)} raw records.")

        if not raw_records:
            logger.error("No data collected across all channels. Aborting workflow.")
            sys.exit(1)

        # Step 3: ETL Transformation, Cleaning & Scoring
        logger.info("[Step 3/5] Starting ETL & Match Scoring pipeline...")
        processor = DataProcessor(config)
        df_processed = processor.process(raw_records)
        kpis = processor.compute_summary_kpis(df_processed)
        logger.info(f"ETL completed: {len(df_processed)} unique roles, {kpis['alert_count']} alert matches.")

        # Step 4: Enterprise Excel Reporting
        logger.info("[Step 4/5] Generating Styled Multi-Sheet Excel Dashboard...")
        reporter = ExcelReporter(config)
        excel_path = reporter.generate_report(df_processed, kpis)

        # Step 5: Alerting & Stakeholder Digest
        logger.info("[Step 5/5] Dispatching Alerts & Building HTML Digest...")
        notifier = Notifier(config)
        html_path = notifier.send_notifications(df_processed, kpis, excel_path)

        # Completion telemetry
        elapsed = round(time.time() - start_time, 2)
        logger.info("================================================================")
        logger.info(f"   [SUCCESS] RPA BOT WORKFLOW COMPLETED IN {elapsed}s")
        logger.info(f"   [REPORT] Excel Dashboard: {excel_path.resolve()}")
        logger.info(f"   [DIGEST] HTML Digest    : {html_path.resolve()}")
        logger.info("================================================================")

    except KeyboardInterrupt:
        logger.warning("Bot execution interrupted by user.")
    except Exception as e:
        logger.error(f"Critical unhandled exception in RPA Bot: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
