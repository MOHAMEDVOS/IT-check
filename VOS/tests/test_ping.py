"""Tests for modules/ping.py — jitter, spikes, distribution, and scoring."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.ping import (
    _calc_jitter, _detect_spikes, _build_latency_distribution,
    _score_and_verdict, PingResult,
)


def test_calc_jitter_constant():
    """If all pings are the same, jitter should be 0."""
    assert _calc_jitter([40, 40, 40, 40]) == 0.0


def test_calc_jitter_varying():
    result = _calc_jitter([40, 50, 40, 50])
    assert result == 10.0


def test_calc_jitter_empty():
    assert _calc_jitter([]) == 0.0
    assert _calc_jitter([42]) == 0.0


def test_detect_spikes_none():
    spikes, indices = _detect_spikes([40, 41, 39, 42], avg=40.5)
    assert len(spikes) == 0


def test_detect_spikes_found():
    samples = [40, 40, 40, 120, 40]
    spikes, indices = _detect_spikes(samples, avg=40.0)
    assert 120 in spikes
    assert 4 in indices  # ping #4 (1-based)


def test_build_latency_distribution():
    result = _build_latency_distribution([40, 41, 42, 80])
    assert "40ms" in result
    assert "80ms" in result


def test_build_latency_distribution_empty():
    assert _build_latency_distribution([]) == ""


def test_score_perfect_connection():
    r = PingResult(host="test.com")
    r.samples = [20] * 20
    r.avg_rtt = 20.0
    r.jitter = 0.0
    r.packet_loss_pct = 0.0
    r.spike_count = 0
    r.spikes = []

    score, verdict, color, notes = _score_and_verdict(r)
    assert score >= 90
    assert verdict in ("EXCELLENT", "GOOD")


def test_score_bad_connection():
    r = PingResult(host="test.com")
    r.samples = [40, 200, 40, 300, 40, 500] * 3
    r.avg_rtt = 200.0
    r.jitter = 80.0
    r.packet_loss_pct = 5.0
    r.spike_count = 6
    r.spikes = [200, 300, 500, 200, 300, 500]

    score, verdict, color, notes = _score_and_verdict(r)
    assert score < 50
    assert verdict in ("POOR", "CRITICAL")
