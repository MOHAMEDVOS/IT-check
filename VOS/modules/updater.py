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
        # Strip 'v', whitespace, and handle common delimiters
        v = version_str.strip().lower().lstrip('v').replace('-', '.').replace('_', '.')
        parts = v.split(".")
        return tuple(int(p) for p in parts if p.isdigit())
    except (ValueError, AttributeError):
        return (0, 0, 0)


def check_for_update(update_url: str = None) -> dict:
    """
    Check for a newer version of VOS from GitHub.
    """
    if not update_url:
        update_url = DEFAULT_UPDATE_URL

    try:
        url_with_timestamp = f"{update_url}?t={int(time.time())}"
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        resp = requests.get(url_with_timestamp, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        latest = data.get("latest_version", APP_VERSION)
        current_tuple = _parse_version(APP_VERSION)
        latest_tuple = _parse_version(latest)

        update_available = latest_tuple > current_tuple
        
        log.info(f"Version comparison: local={APP_VERSION} ({current_tuple}), remote={latest} ({latest_tuple}) -> Update={update_available}")

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
        
        # 1. Download the file with cache busting
        url_with_timestamp = f"{download_url}?t={int(time.time())}"
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        resp = requests.get(url_with_timestamp, headers=headers, stream=True, timeout=30)
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
        vbs_path = os.path.join(app_dir, "update.vbs")

        bat_content = f"""@echo off
set "EXE_PATH={current_exe}"
set "NEW_EXE={new_exe_path}"
set "EXE_NAME={os.path.basename(current_exe)}"
set "VBS_PATH={vbs_path}"

:: Wait for app to close
ping 127.0.0.1 -n 3 > nul 2>&1

:: Hard kill just in case
taskkill /f /im "%EXE_NAME%" > nul 2>&1
ping 127.0.0.1 -n 2 > nul 2>&1

:: Swap
if exist "%EXE_PATH%" del /f /q "%EXE_PATH%" > nul 2>&1
if exist "%NEW_EXE%" move /y "%NEW_EXE%" "%EXE_PATH%" > nul 2>&1

:: Restart (use cmd /c start with minimized flag to avoid flash)
if exist "%EXE_PATH%" start "" /b "%EXE_PATH%"

:: Cleanup VBS launcher and this script
if exist "%VBS_PATH%" del /f /q "%VBS_PATH%" > nul 2>&1
del "%~f0" > nul 2>&1
"""
        with open(bat_path, "w") as f:
            f.write(bat_content)

        # 3. Create a VBScript wrapper to launch the batch file completely hidden
        vbs_content = f'CreateObject("Wscript.Shell").Run """{bat_path}""", 0, False\n'
        with open(vbs_path, "w") as f:
            f.write(vbs_content)

        log.info("Update scripts created. Launching hidden update and exiting...")

        # 4. Launch the VBScript (which runs the bat hidden) — no window at all
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            subprocess.Popen(
                ["wscript.exe", vbs_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                startupinfo=startupinfo,
            )
        
        # 5. Terminate immediately so the batch script can delete this file
        os._exit(0)

    except Exception as e:
        log.error(f"Failed to apply update: {e}", exc_info=True)
        return False
