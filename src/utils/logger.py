"""
src/utils/logger.py
-------------------
Centralised logging configuration.
Call setup_logging() once at process entry point (main.py).
"""

import logging
import logging.handlers
import sys
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_dir: str = "logs",
    log_file: str = "pipeline.log",
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 3,
) -> None:
    """
    Configure root logger with:
      - StreamHandler → stdout (colourised in terminals)
      - RotatingFileHandler → logs/pipeline.log
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(numeric_level)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)

    # Silence noisy third-party libs
    for noisy in ("urllib3", "spotipy", "requests", "charset_normalizer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    root.addHandler(stdout_handler)
    root.addHandler(file_handler)
