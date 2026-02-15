"""Logging and observability setup."""

import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logging(name: str, level=logging.INFO) -> logging.Logger:
    \"\"\"Setup logging with file and console handlers.\"\"\"
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # File handler
    fh = logging.handlers.RotatingFileHandler(
        LOG_DIR / f"{name}.log",
        maxBytes=10485760,  # 10MB
        backupCount=5,
    )
    fh.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


# Module-level loggers
logger = setup_logging("neuro_triage")
