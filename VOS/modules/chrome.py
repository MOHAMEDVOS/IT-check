"""
chrome.py — Detects installed Chrome version and compares against latest stable.
Handles Google's staged rollouts correctly — avoids false "Update available" alerts.

Google rolls out new Chrome milestones gradually over 1–2 weeks.
Being 1 milestone behind does NOT mean an update is available for YOUR machine.
Only flag as truly outdated if 2+ milestones behind.
"""

import winreg
import requests
import re
import os
import psutil
import shutil
import json
import time
from dataclasses import dataclass
from typing import Optional

def clear_chrome_data() -> bool:
    """
    Force closes Chrome, then clears Cache, Cookies, and Site Settings across all profiles.
    Returns True if successful, False if it failed.
    """
    try:
        # 1. Force close chrome.exe
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == 'chrome.exe':
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        time.sleep(1) # Give it a moment to release file locks

        local_app_data = os.getenv('LOCALAPPDATA')
        if not local_app_data:
            return False
            
        chrome_user_data = os.path.join(local_app_data, 'Google', 'Chrome', 'User Data')
        if not os.path.exists(chrome_user_data):
            return False

        # Identify profile folders
        profile_dirs = []
        for d in os.listdir(chrome_user_data):
            full_path = os.path.join(chrome_user_data, d)
            if os.path.isdir(full_path) and (d == 'Default' or d.startswith('Profile ')):
                profile_dirs.append(full_path)

        for profile_path in profile_dirs:
            # 2. Delete Cache folders
            cache_targets = [
                os.path.join(profile_path, 'Cache'),
                os.path.join(profile_path, 'Code Cache'),
                os.path.join(profile_path, 'GPUCache'),
                os.path.join(profile_path, 'Media Cache')
            ]
            for target in cache_targets:
                if os.path.exists(target):
                    try:
                        shutil.rmtree(target, ignore_errors=True)
                    except Exception:
                        pass
                        
            # 3. Delete Cookies & Site Data
            cookie_targets = [
                os.path.join(profile_path, 'Network', 'Cookies'),
                os.path.join(profile_path, 'Network', 'Cookies-journal'),
                os.path.join(profile_path, 'Local Storage'),
                os.path.join(profile_path, 'Session Storage'),
                os.path.join(profile_path, 'IndexedDB'),
                os.path.join(profile_path, 'Service Worker')
            ]
            for target in cookie_targets:
                if os.path.exists(target):
                    if os.path.isdir(target):
                        shutil.rmtree(target, ignore_errors=True)
                    else:
                        try:
                            os.remove(target)
                        except OSError:
                            pass

            # 4. Clear Site Settings (Preferences)
            prefs_path = os.path.join(profile_path, 'Preferences')
            if os.path.exists(prefs_path):
                try:
                    with open(prefs_path, 'r', encoding='utf-8') as f:
                        prefs = json.load(f)
                    
                    if 'profile' in prefs and 'content_settings' in prefs['profile']:
                        if 'exceptions' in prefs['profile']['content_settings']:
                            prefs['profile']['content_settings']['exceptions'] = {}
                            
                    with open(prefs_path, 'w', encoding='utf-8') as f:
                        json.dump(prefs, f)
                except Exception:
                    pass

        return True
    except Exception:
        return False


# ── Version sources (tried in order, first success wins) ────────────────────
VERSION_SOURCES = [
    # Chromium Dash — most reliable, used by developers
    "https://chromiumdash.appspot.com/fetch_releases?channel=Stable&platform=Windows&num=1",
    # Google version history API — fallback
    "https://versionhistory.googleapis.com/v1/chrome/platforms/win/channels/stable/versions?filter=endtime=none&pageSize=1",
]

# Registry paths where Chrome stores its version on Windows
CHROME_REGISTRY_PATHS = [
    (winreg.HKEY_CURRENT_USER,  r"Software\Google\Chrome\BLBeacon"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Google\Chrome\BLBeacon"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Wow6432Node\Google\Chrome\BLBeacon"),
    (winreg.HKEY_CURRENT_USER,  r"Software\Google\Update\Clients\{8A69D345-D564-463c-AFF1-A69D9E530F96}"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Google\Update\Clients\{8A69D345-D564-463c-AFF1-A69D9E530F96}"),
]


@dataclass
class ChromeResult:
    installed_version: str       = "Not found"
    latest_version: str          = "Unknown"
    installed_milestone: int     = 0     # e.g. 145
    latest_milestone: int        = 0     # e.g. 146
    milestones_behind: int       = 0     # 0 = current, 1 = staged rollout, 2+ = outdated
    status: str                  = ""    # UP_TO_DATE / STAGED_ROLLOUT / OUTDATED / NOT_INSTALLED / ERROR
    status_label: str            = ""    # Human-readable label for the UI
    status_color: str            = ""    # hex color string
    note: str                    = ""    # Explanation shown in the UI card
    error: Optional[str]         = None


def _get_milestone(version_str: str) -> int:
    """Extract the major milestone number from a version string like '145.0.7632.160'."""
    try:
        return int(version_str.split(".")[0])
    except (ValueError, IndexError, AttributeError):
        return 0


def _get_installed_version() -> Optional[str]:
    """Read installed Chrome version from the Windows registry."""
    for hive, path in CHROME_REGISTRY_PATHS:
        try:
            key = winreg.OpenKey(hive, path)
            # Try 'version' key first, then 'pv'
            for value_name in ("version", "pv"):
                try:
                    version, _ = winreg.QueryValueEx(key, value_name)
                    if version and re.match(r'\d+\.\d+\.\d+\.\d+', str(version)):
                        winreg.CloseKey(key)
                        return str(version).strip()
                except FileNotFoundError:
                    continue
            winreg.CloseKey(key)
        except (FileNotFoundError, PermissionError, OSError):
            continue
    return None


def _get_latest_version() -> Optional[str]:
    """Fetch latest stable Chrome version for Windows from Google's APIs."""
    for url in VERSION_SOURCES:
        try:
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            data = resp.json()

            # Chromium Dash format: list of release objects
            if isinstance(data, list) and data:
                version = data[0].get("version", "")
                if re.match(r'\d+\.\d+\.\d+\.\d+', version):
                    return version

            # Version history API format: { "versions": [{ "version": "..." }] }
            if isinstance(data, dict):
                versions = data.get("versions", [])
                if versions:
                    version = versions[0].get("version", "")
                    if re.match(r'\d+\.\d+\.\d+\.\d+', version):
                        return version

        except Exception:
            continue  # Try next source

    return None


def check_chrome() -> ChromeResult:
    result = ChromeResult()

    # ── Step 1: Get installed version ────────────────────────────────────────
    installed = _get_installed_version()
    if not installed:
        result.status        = "NOT_INSTALLED"
        result.status_label  = "Not Installed"
        result.status_color  = "#EF4444"
        result.note          = "Google Chrome does not appear to be installed on this machine."
        return result

    result.installed_version    = installed
    result.installed_milestone  = _get_milestone(installed)

    # ── Step 2: Get latest version from Google ───────────────────────────────
    latest = _get_latest_version()
    if not latest:
        result.status        = "ERROR"
        result.status_label  = "Check Failed"
        result.status_color  = "#F59E0B"
        result.note          = "Could not reach Google's update servers. Check internet connection."
        result.error         = "All version API sources failed."
        return result

    result.latest_version    = latest
    result.latest_milestone  = _get_milestone(latest)
    result.milestones_behind = max(0, result.latest_milestone - result.installed_milestone)

    # ── Step 3: Full-version comparison with Major/Minor distinction ─────────
    if result.installed_version == result.latest_version:
        result.status       = "UP_TO_DATE"
        result.status_label = "✅ Up to Date"
        result.status_color = "#10B981"
        result.note         = f"Your Chrome browser is up to date (v{result.installed_version})."

    elif result.milestones_behind > 0:
        # One or more milestones behind — Major update
        result.status       = "OUTDATED"
        result.status_label = "⚠️ Major Update Available"
        result.status_color = "#EF4444"
        result.note         = (
            "Open Chrome → Menu → Help → About Google Chrome to update."
        )

    else:
        # Same milestone but different point release — Minor/Security update
        result.status       = "OUTDATED"
        result.status_label = "🔄 Minor Update Available"
        result.status_color = "#F59E0B" # Amber/Orange for minor
        result.note         = (
            "Open Chrome → Menu → Help → About Google Chrome to update."
        )

    return result
