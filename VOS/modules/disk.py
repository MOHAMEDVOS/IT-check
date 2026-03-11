"""
disk.py — Check free disk space on the system drive.

Returns drive letter, total size, free space, and used percentage.
"""

import os
import psutil
from logger import get_logger

log = get_logger("disk")


def check_disk_space(drive: str = None) -> dict:
    """
    Check free disk space on the system drive (or a specified drive).

    Returns:
        dict with keys: drive, total_gb, free_gb, used_gb, used_pct, error
    """
    try:
        if drive is None:
            # Get the system drive (where Windows is installed)
            drive = os.environ.get("SystemDrive", "C:")

        usage = psutil.disk_usage(drive + "\\")

        total_gb = usage.total / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        used_gb = usage.used / (1024 ** 3)
        used_pct = usage.percent

        log.info(f"Disk check: {drive} — {free_gb:.1f}GB free / {total_gb:.0f}GB total ({used_pct}% used)")

        return {
            "drive":    drive,
            "total_gb": round(total_gb, 1),
            "free_gb":  round(free_gb, 1),
            "used_gb":  round(used_gb, 1),
            "used_pct": used_pct,
            "error":    None,
        }

    except Exception as e:
        log.error(f"Disk check failed: {e}", exc_info=True)
        return {
            "drive":    drive or "C:",
            "total_gb": 0,
            "free_gb":  0,
            "used_gb":  0,
            "used_pct": 0,
            "error":    str(e),
        }


if __name__ == "__main__":
    r = check_disk_space()
    if r["error"]:
        print(f"Error: {r['error']}")
    else:
        print(f"Drive    : {r['drive']}")
        print(f"Total    : {r['total_gb']} GB")
        print(f"Free     : {r['free_gb']} GB")
        print(f"Used     : {r['used_gb']} GB ({r['used_pct']}%)")
