"""
updater.py — Detects new versions and handles the automatic self-update.

Checks a GitHub JSON manifest for new versions.
Downloads the new .exe, creates a replacement batch script, and swaps them.
"""

import requests
import os
import sys
import time
import platform
import subprocess
from thresholds import APP_VERSION
from logger import get_logger

log = get_logger("updater")

# Point to raw GitHub content for the version file
DEFAULT_UPDATE_URL = "https://raw.githubusercontent.com/MOHAMEDVOS/IT-check/main/public/downloads/version.json"


def _parse_version(version_str: str) -> tuple:
    """Parse '2.1.0' into (2, 1, 0) for comparison."""
    try:
        parts = version_str.strip().split(".")
        return tuple(int(p) for p in parts)
    except (ValueError, AttributeError):
        return (0, 0, 0)


def check_for_update(update_url: str = None) -> dict:
    """
    Check for a newer version of VOS from GitHub.
    """
    if not update_url:
        update_url = DEFAULT_UPDATE_URL

    try:
        resp = requests.get(update_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        latest = data.get("latest_version", APP_VERSION)
        current_tuple = _parse_version(APP_VERSION)
        latest_tuple = _parse_version(latest)

        update_available = latest_tuple > current_tuple

        result = {
            "update_available": update_available,
            "latest_version":   latest,
            "download_url":     data.get("download_url", ""),
            "release_notes":    data.get("release_notes", ""),
            "error":            None,
        }

        if update_available:
            log.info(f"Update available: {APP_VERSION} → {latest}")
        else:
            log.debug(f"No update needed (current: {APP_VERSION}, remote: {latest})")

        return result

    except Exception as e:
        log.warning(f"Update check failed: {e}")
        return {
            "update_available": False,
            "latest_version":   APP_VERSION,
            "download_url":     "",
            "release_notes":    "",
            "error":            str(e),
        }


def apply_update(download_url: str) -> bool:
    """
    Background worker process to download the update and trigger the swap script.
    """
    try:
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            # We are running as a compiled PyInstaller executable
            current_exe = sys.executable
            app_dir = os.path.dirname(current_exe)
        else:
            # Running from source (mostly for dev/testing)
            current_exe = ""
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log.warning("Applying update while running from source. Only the download will be tested.")

        new_exe_path = os.path.join(app_dir, "VOS_new.exe")
        bat_path = os.path.join(app_dir, "update.bat")

        log.info(f"Downloading update from: {download_url}")
        
        # 1. Download the file
        resp = requests.get(download_url, stream=True, timeout=30)
        resp.raise_for_status()
        
        with open(new_exe_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        log.info(f"Download complete: {new_exe_path}")

        # If not frozen, don't attempt the file-swap magic as it would overwrite source code!
        if not is_frozen:
            log.info("Running from source: Skipping self-replacement script.")
            return True

        # 2. Create the batch script to swap files (Only for frozen EXE)
        bat_content = f"""@echo off
set "EXE_NAME={os.path.basename(current_exe)}"
set "NEW_EXE={os.path.basename(new_exe_path)}"

:WAIT_LOOP
taskkill /f /im "%EXE_NAME%" > NUL 2>&1
timeout /t 1 /nobreak > NUL
del /f /q "{current_exe}" > NUL 2>&1
if exist "{current_exe}" goto WAIT_LOOP

move /y "{new_exe_path}" "{current_exe}" > NUL 2>&1
start "" "{current_exe}"
del "%~f0"
"""
        with open(bat_path, "w") as f:
            f.write(bat_content)

        log.info("Update batch script created. Launching script and exiting...")

        # 3. Launch the script in the background completely detached
        if platform.system() == "Windows":
            subprocess.Popen(
                [bat_path], 
                creationflags=subprocess.CREATE_NO_WINDOW | 0x00000008,
                shell=True
            )
        
        # 4. Terminate immediately so the batch script can delete this file
        sys.exit(0)

    except Exception as e:
        log.error(f"Failed to apply update: {e}", exc_info=True)
        return False
