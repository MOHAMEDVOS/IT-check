"""
logger.py — No-op logger for VOS.

VOS no longer writes a debug.log file. get_logger() still returns a working
logger so every existing log.debug()/log.error() call keeps functioning, but
nothing is written to disk. In dev runs (not frozen) messages still go to the
console for the developer's convenience; the shipped app writes nothing.

On import, any leftover debug.log* from older builds is deleted — both next
to the EXE and in the %LOCALAPPDATA%\\VOS\\ folder used by 3.7.0.
"""

import os
import sys
import logging

_LOG_FORMAT = "[%(asctime)s] %(name)-14s %(levelname)-7s  %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _cleanup_old_logs() -> None:
    """Delete debug.log* written by older builds (best-effort)."""
    if not getattr(sys, "frozen", False):
        return
    dirs = [os.path.dirname(sys.executable)]
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base:
        dirs.append(os.path.join(base, "VOS"))
    for d in dirs:
        try:
            for fn in os.listdir(d):
                if fn.startswith("debug.log"):
                    try:
                        os.remove(os.path.join(d, fn))
                    except Exception:
                        pass
        except Exception:
            pass


_cleanup_old_logs()

_console_handler = None


def _ensure_handlers():
    """Dev-only console handler. Frozen builds get no handler (silent)."""
    global _console_handler
    if (
        _console_handler is None
        and not getattr(sys, "frozen", False)
        and sys.stdout is not None
    ):
        _console_handler = logging.StreamHandler(sys.stdout)
        _console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
        _console_handler.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger. Writes nothing to disk. Usage is unchanged:
        from logger import get_logger
        log = get_logger("speed")
        log.info("Starting speed test")
    """
    _ensure_handlers()
    logger = logging.getLogger(f"vos.{name}")
    if not logger.handlers:
        if _console_handler is not None:
            logger.addHandler(_console_handler)
        logger.addHandler(logging.NullHandler())  # no file, no crash
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    return logger
