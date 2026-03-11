"""Tests for modules/specs.py — CPU scoring and specs retrieval."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.specs import get_cpu_performance, get_system_specs


def test_i5_6th_gen_is_baseline():
    score, label = get_cpu_performance("Intel Core i5-6500")
    assert score == 100
    assert "Similar" in label or "Baseline" in label


def test_celeron_is_weak():
    score, _ = get_cpu_performance("Intel Celeron N4020")
    assert score < 100


def test_i7_12th_gen_is_strong():
    score, _ = get_cpu_performance("Intel Core i7-12700H")
    assert score > 100


def test_ryzen_7_is_strong():
    score, _ = get_cpu_performance("AMD Ryzen 7 5800X")
    assert score > 100


def test_apple_m3_is_strong():
    score, _ = get_cpu_performance("Apple M3 Pro")
    assert score > 200


def test_get_system_specs_returns_expected_keys():
    specs = get_system_specs()
    expected = ["cpu_model", "perf_score", "perf_label", "total_ram",
                "available_ram", "ram_usage", "gpu_name"]
    for key in expected:
        assert key in specs, f"Missing key: {key}"


def test_total_ram_is_string_with_gb():
    specs = get_system_specs()
    assert "GB" in specs["total_ram"]


def test_gpu_name_is_string():
    specs = get_system_specs()
    assert isinstance(specs["gpu_name"], str)
    assert len(specs["gpu_name"]) > 0
