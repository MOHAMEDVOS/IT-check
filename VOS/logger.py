"""
logger.py — Centralized rotating-file logger for VOS.

Replaces all raw open('debug.log', 'a') calls.
Keeps max 1 MB per file, 3 backup files (debug.log, debug.log.1, etc.)

The log is written to a per-user AppData folder (NOT next to VOS.exe) so
agents don't see — and can't tamper with — it in their download folder.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

_LOG_FORMAT = "[%(asctime)s] %(name)-14s %(levelname)-7s  %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 1_048_576   # 1 MB
_BACKUP_COUNT = 3


def _hide(path: str) -> None:
    """Set the Windows 'hidden' attribute on a file or folder (best-effort)."""
    if os.name == "nt":
        try:
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_HIDDEN)
        except Exception:
            pass


def _resolve_log_dir() -> str:
    """
    Frozen (shipped) build -> %LOCALAPPDATA%\\VOS (hidden), away from the EXE.
    Dev run -> next to this file, so developers can find the log easily.
    """
    if getattr(sys, "frozen", False):
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if not base:
            import tempfile
            base = tempfile.gettempdir()
        log_dir = os.path.join(base, "VOS")
        try:
            os.makedirs(log_dir, exist_ok=True)
            _hide(log_dir)
        except Exception:
            log_dir = os.path.dirname(sys.executable)  # last-resort fallback
    else:
        log_dir = os.path.dirname(os.path.abspath(__file__))
    return log_dir


def _cleanup_legacy_logs() -> None:
    """Remove old visible debug.log* left next to the EXE by pre-3.7 builds."""
    if not getattr(sys, "frozen", False):
        return
    exe_dir = os.path.dirname(sys.executable)
    if exe_dir == _LOG_DIR:
        return
    try:
        for fn in os.listdir(exe_dir):
            if fn.startswith("debug.log"):
                try:
                    os.remove(os.path.join(exe_dir, fn))
                except Exception:
                    pass
    except Exception:
        pass


_LOG_DIR = _resolve_log_dir()
_LOG_FILE = os.path.join(_LOG_DIR, "debug.log")
_cleanup_legacy_logs()

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
        _hide(_LOG_FILE)

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
