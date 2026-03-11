"""Tests for thresholds.py — validate constants exist and have sane values."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from thresholds import *


def test_speed_thresholds_exist():
    assert SPEED_DOWNLOAD_MIN > 0
    assert SPEED_UPLOAD_MIN > 0
    assert SPEED_DOWNLOAD_WARN < SPEED_DOWNLOAD_MIN
    assert SPEED_UPLOAD_WARN < SPEED_UPLOAD_MIN


def test_ping_thresholds():
    assert PING_STABILITY_MIN > 0
    assert PING_STABILITY_MIN <= 100
    assert PING_JITTER_GOOD_MS < PING_JITTER_OK_MS
    assert PING_AVG_GOOD_MS < PING_AVG_OK_MS
    assert PING_COUNT > 0
    assert PING_ROUNDS > 0


def test_mic_thresholds():
    assert MIC_LEVEL_MIN > MIC_LEVEL_WARN
    assert MIC_LEVEL_MIN <= 100


def test_disk_thresholds():
    assert DISK_FREE_MIN_GB > DISK_FREE_WARN_GB


def test_app_version():
    assert APP_VERSION
    assert APP_NAME
    parts = APP_VERSION.split(".")
    assert len(parts) == 3
