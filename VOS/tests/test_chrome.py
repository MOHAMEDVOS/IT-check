"""Tests for modules/chrome.py — milestone parsing and comparison logic."""
import sys
import os
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.chrome import _get_milestone, ChromeResult, check_chrome


def test_get_milestone_valid():
    assert _get_milestone("134.0.6998.89") == 134


def test_get_milestone_simple():
    assert _get_milestone("145.0.0.0") == 145


def test_get_milestone_invalid():
    assert _get_milestone("") == 0
    assert _get_milestone(None) == 0
    assert _get_milestone("not-a-version") == 0


def test_chrome_result_defaults():
    r = ChromeResult()
    assert r.installed_version == "Not found"
    assert r.latest_version == "Unknown"
    assert r.installed_milestone == 0
    assert r.milestones_behind == 0
    assert r.status == ""
    assert r.error is None


def test_up_to_date_status():
    r = ChromeResult()
    r.installed_milestone = 134
    r.latest_milestone = 134
    r.milestones_behind = 0
    r.status = "UP_TO_DATE"
    assert r.milestones_behind == 0
    assert r.status == "UP_TO_DATE"


def test_outdated_status():
    r = ChromeResult()
    r.installed_milestone = 132
    r.latest_milestone = 135
    r.milestones_behind = 3
    r.status = "OUTDATED"
    assert r.milestones_behind >= 2
    assert r.status == "OUTDATED"


def test_staged_rollout():
    r = ChromeResult()
    r.installed_milestone = 134
    r.latest_milestone = 135
    r.milestones_behind = 1
    r.status = "STAGED_ROLLOUT"
    assert r.milestones_behind == 1


# ── check_chrome() logic tests (mock network + registry calls) ───────────────

def _run_check(installed_ver, latest_ver):
    """Helper: run check_chrome() with mocked installed + latest versions."""
    with patch("modules.chrome._get_installed_version", return_value=installed_ver), \
         patch("modules.chrome._get_latest_version", return_value=latest_ver):
        return check_chrome()


def test_check_exact_match_is_up_to_date():
    """Same version string → UP_TO_DATE."""
    r = _run_check("134.0.6998.177", "134.0.6998.177")
    assert r.status == "UP_TO_DATE"


def test_check_same_milestone_diff_patch_is_up_to_date():
    """Same major milestone, different patch → UP_TO_DATE (not a false alarm)."""
    r = _run_check("134.0.6998.177", "134.0.6998.178")
    assert r.status == "UP_TO_DATE"


def test_check_one_milestone_behind_is_staged_rollout():
    """1 milestone behind → STAGED_ROLLOUT, shown as Up to Date (Google rollout window)."""
    r = _run_check("134.0.6998.177", "135.0.7049.42")
    assert r.status == "STAGED_ROLLOUT"
    assert r.status_label == "Up to Date"


def test_check_two_milestones_behind_is_outdated():
    """2+ milestones behind → genuinely OUTDATED."""
    r = _run_check("133.0.6943.200", "135.0.7049.42")
    assert r.status == "OUTDATED"


def test_check_not_installed():
    """No Chrome registry entry → NOT_INSTALLED."""
    r = _run_check(None, "135.0.7049.42")
    assert r.status == "NOT_INSTALLED"


def test_check_api_failure():
    """Latest version unreachable → ERROR."""
    r = _run_check("134.0.6998.177", None)
    assert r.status == "ERROR"
