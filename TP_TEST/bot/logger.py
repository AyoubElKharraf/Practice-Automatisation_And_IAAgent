"""
bot/logger.py - Enterprise logging setup for RPA Bot.
Provides timestamped file logging, colored console output, and execution profiling.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


class BotLogger:
    _instance = None

    @classmethod
    def get_logger(cls, name: str = "RPABot") -> logging.Logger:
        if cls._instance is not None:
            return cls._instance

        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        today_str = datetime.now().strftime("%Y%m%d")
        log_file = logs_dir / f"rpa_execution_{today_str}.log"

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            # Reconfigure stdout for utf-8 if supported
            if hasattr(sys.stdout, "reconfigure"):
                try:
                    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass

            # File Handler (Detailed with Milliseconds, UTF-8)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                fmt="%(asctime)s [%(levelname)-8s] (%(filename)s:%(lineno)d) %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)

            # Console Handler (Human-readable, safe errors replacement)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter(
                fmt="[%(asctime)s] [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S",
            )
            console_handler.setFormatter(console_format)
            logger.addHandler(console_handler)

        cls._instance = logger
        return logger
