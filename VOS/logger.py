"""
logger.py — Centralized rotating-file logger for VOS.

Replaces all raw open('debug.log', 'a') calls.
Keeps max 1 MB per file, 3 backup files (debug.log, debug.log.1, etc.)
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

_LOG_FORMAT = "[%(asctime)s] %(name)-14s %(levelname)-7s  %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 1_048_576   # 1 MB
_BACKUP_COUNT = 3

# Resolve log directory (works in both dev and PyInstaller bundle)
if getattr(sys, 'frozen', False):
    _LOG_DIR = os.path.dirname(sys.executable)
else:
    _LOG_DIR = os.path.dirname(os.path.abspath(__file__))

_LOG_FILE = os.path.join(_LOG_DIR, "debug.log")

# Shared handler — all loggers write to the same file
_file_handler = None
_console_handler = None


def _ensure_handlers():
    """Lazy-init the shared file and console handlers."""
    global _file_handler, _console_handler

    if _file_handler is None:
        _file_handler = RotatingFileHandler(
            _LOG_FILE,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        _file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
        _file_handler.setLevel(logging.DEBUG)

    if _console_handler is None:
        _console_handler = logging.StreamHandler(sys.stdout)
        _console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
        _console_handler.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger that writes to the rotating debug.log.

    Usage:
        from logger import get_logger
        log = get_logger("speed")
        log.info("Starting speed test")
        log.error("Something failed", exc_info=True)
    """
    _ensure_handlers()
    logger = logging.getLogger(f"vos.{name}")
    if not logger.handlers:
        logger.addHandler(_file_handler)
        logger.addHandler(_console_handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    return logger
