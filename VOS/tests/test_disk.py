"""Tests for modules/disk.py — disk space check."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.disk import check_disk_space


def test_disk_returns_expected_keys():
    result = check_disk_space()
    expected = ["drive", "total_gb", "free_gb", "used_gb", "used_pct", "error"]
    for key in expected:
        assert key in result, f"Missing key: {key}"


def test_disk_values_are_numeric():
    result = check_disk_space()
    assert isinstance(result["total_gb"], (int, float))
    assert isinstance(result["free_gb"], (int, float))
    assert isinstance(result["used_pct"], (int, float))


def test_disk_total_greater_than_free():
    result = check_disk_space()
    if result["error"] is None:
        assert result["total_gb"] >= result["free_gb"]


def test_disk_no_error_on_system_drive():
    result = check_disk_space()
    assert result["error"] is None


def test_disk_used_pct_in_range():
    result = check_disk_space()
    if result["error"] is None:
        assert 0 <= result["used_pct"] <= 100
