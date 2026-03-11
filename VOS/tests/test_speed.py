"""Tests for modules/speed.py — connection type detection and error handling."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.speed import get_connection_type, _error_result


def test_get_connection_type_returns_string():
    result = get_connection_type()
    assert isinstance(result, str)
    assert len(result) > 0


def test_error_result_format():
    result = _error_result("⦿ Wi-Fi", "Test error")
    assert result["connection_type"] == "⦿ Wi-Fi"
    assert result["error"] == "Test error"
    assert result["download"] == "—"
    assert result["upload"] == "—"
    assert result["latency"] == "—"


def test_error_result_has_all_keys():
    result = _error_result("Unknown", "fail")
    expected_keys = ["download", "upload", "latency", "jitter", "server",
                     "connection_type", "error"]
    for key in expected_keys:
        assert key in result
