"""Tests for modules/speed.py — connection type detection, error handling, and result structure."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from modules.speed import get_connection_type, _error_result, run_speedtest


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


def test_run_speedtest_returns_all_keys():
    """run_speedtest always returns a dict with all expected keys, even on failure."""
    # Mock both Ookla and Cloudflare failing
    with patch("modules.speed._run_ookla_speedtest", side_effect=Exception("no network")):
        with patch("modules.speed._run_cloudflare_fallback", side_effect=Exception("no network")):
            result = run_speedtest()
    expected_keys = ["download", "upload", "latency", "jitter", "server",
                     "connection_type", "error"]
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"


def test_run_speedtest_uses_ookla_when_available():
    """When speedtest-cli works, result shows Ookla server label."""
    mock_result = {
        "download": "50.0 Mbps",
        "upload": "10.0 Mbps",
        "latency": "15 ms",
        "jitter": "—",
        "server": "Ookla — Test Server, ZA",
        "connection_type": "⦿ Ethernet",
        "error": None,
        "_method": "ookla",
    }
    with patch("modules.speed._run_ookla_speedtest", return_value=mock_result):
        result = run_speedtest()
    assert result["error"] is None
    assert "Ookla" in result["server"]


def test_run_speedtest_falls_back_to_cloudflare_on_ookla_failure():
    """When Ookla fails, falls back to Cloudflare (single stream)."""
    mock_cf_result = {
        "download": "30.0 Mbps",
        "upload": "5.0 Mbps",
        "latency": "20 ms",
        "jitter": "—",
        "server": "Cloudflare CDN (fallback)",
        "connection_type": "⦿ Wi-Fi",
        "error": None,
        "_method": "cloudflare",
    }
    with patch("modules.speed._run_ookla_speedtest", side_effect=Exception("server unreachable")):
        with patch("modules.speed._run_cloudflare_fallback", return_value=mock_cf_result):
            result = run_speedtest()
    assert result["error"] is None
    assert "Cloudflare" in result["server"]
