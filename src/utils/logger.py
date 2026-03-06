"""
logger.py
---------
Sets up a rotating file logger for the application.
Logs are stored in a 'logs' folder next to the executable.
Max size per log file: 10MB, keeps last 5 files.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_base_dir() -> Path:
    """
    Returns the directory where the executable (or main script) lives.
    This ensures log files are stored next to the .exe when packaged.
    """
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundled .exe
        return Path(sys.executable).parent
    else:
        # Running as a normal Python script
        return Path(__file__).parent.parent.parent


def setup_logger() -> logging.Logger:
    """
    Creates and configures the application logger.
    Returns a logger named 'ac_skin_injector'.
    """
    log_dir = get_base_dir() / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "app.log"

    logger = logging.getLogger("ac_skin_injector")
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if setup_logger is called more than once
    if logger.handlers:
        return logger

    # Rotating file handler: 10MB max, keep last 5 log files
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler for development (only shows warnings and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Module-level logger instance, importable directly
log = setup_logger()
