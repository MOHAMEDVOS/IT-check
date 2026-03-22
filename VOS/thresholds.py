# ─── VOS — Vital Operations Scanner ─── Threshold Constants ───

APP_NAME = "VOS"
APP_VERSION = "3.6.0"
PING_DEFAULT_TARGET = "resva.readymode.com"

# ── Internet Speed (Mbps) ──
SPEED_DOWNLOAD_MIN = 10.0
SPEED_UPLOAD_MIN = 2.0
SPEED_DOWNLOAD_WARN = 5.0
SPEED_UPLOAD_WARN = 1.0

# ── Ping / Connection Stability ──
# Warning appears only when score < this (matches POOR band: score 20–35 = POOR, < 20 = CRITICAL)
PING_STABILITY_MIN = 35
PING_JITTER_GOOD_MS = 10
PING_JITTER_OK_MS = 30
PING_AVG_GOOD_MS = 50
PING_AVG_OK_MS = 100
PING_COUNT = 20
PING_ROUNDS = 3

# ── Microphone ──
MIC_LEVEL_MIN = 50
MIC_LEVEL_WARN = 20

# ── System Specs ──
RAM_MIN_GB = 8
CPU_PERF_SCORE_MIN = 80

# ── Disk Space (GB) ──
DISK_FREE_MIN_GB = 20.0
DISK_FREE_WARN_GB = 10.0

# ── Dashboard / API ──
DASHBOARD_URL = "https://mohamed404.pythonanywhere.com"
API_KEY = "vos-default-key"
