"""
speed.py — Internet speed measurement via Cloudflare Speed Test.
Uses only 'requests' which is already bundled.
"""

import time
import socket
import psutil
import requests


TIMEOUT = 30

_CF_DOWNLOAD_URL = "https://speed.cloudflare.com/__down?bytes=10000000"
_CF_UPLOAD_URL   = "https://speed.cloudflare.com/__up"
_CF_UPLOAD_SIZE  = 5_000_000


# ── Connection type detection ─────────────────────────────────────────────────

def get_connection_type() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        for iface_name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address == local_ip:
                    name_lower = iface_name.lower()
                    if any(k in name_lower for k in ("wi-fi", "wifi", "wireless", "wlan", "802.11")):
                        return "⦿ Wi-Fi"
                    elif any(k in name_lower for k in ("ethernet", "eth", "lan", "local area")):
                        return "⦿ Ethernet"
                    else:
                        return f"⦿ {iface_name}"
        return "Unknown"
    except Exception:
        return "Unknown"


# ── Cloudflare speed test ─────────────────────────────────────────────────────

def _cf_download() -> float:
    samples = []
    for _ in range(3):
        try:
            with requests.get(_CF_DOWNLOAD_URL, stream=True, timeout=TIMEOUT) as resp:
                resp.raise_for_status()
                start = time.perf_counter()
                received = sum(len(c) for c in resp.iter_content(chunk_size=131072))
                elapsed = time.perf_counter() - start
                if elapsed > 0:
                    samples.append((received * 8) / (elapsed * 1_000_000))
        except Exception:
            pass
    return round(sum(samples) / len(samples), 1) if samples else 0.0


def _cf_upload() -> float:
    data = b"0" * _CF_UPLOAD_SIZE
    samples = []
    for _ in range(3):
        try:
            start = time.perf_counter()
            with requests.post(_CF_UPLOAD_URL, data=data, timeout=TIMEOUT,
                               headers={"Content-Type": "application/octet-stream"}):
                pass
            elapsed = time.perf_counter() - start
            if elapsed > 0:
                samples.append((len(data) * 8) / (elapsed * 1_000_000))
        except Exception:
            pass
    return round(sum(samples) / len(samples), 1) if samples else 0.0


def _cf_latency() -> tuple:
    try:
        times = []
        for _ in range(3):
            start = time.perf_counter()
            with requests.get("https://speed.cloudflare.com/__down?bytes=0", timeout=5):
                pass
            times.append((time.perf_counter() - start) * 1000)
        latency = round(min(times), 1)
        jitter = round(max(times) - min(times), 1) if len(times) > 1 else 0.0
        return latency, jitter
    except Exception:
        return 0.0, 0.0


# ── Main entry point ──────────────────────────────────────────────────────────

def run_speedtest(callback=None) -> dict:
    connection_type = get_connection_type()

    try:
        if callback:
            callback("Step 1/3: Measuring latency...")
        latency_ms, jitter_ms = _cf_latency()

        if callback:
            callback("Step 2/3: Testing download speed...")
        download_mbps = _cf_download()

        if callback:
            callback("Step 3/3: Testing upload speed...")
        upload_mbps = _cf_upload()

        if download_mbps == 0.0:
            return _error_result(connection_type, "No internet connection or server unavailable.")

        if callback:
            callback("Done!")

        return {
            "download":        f"{download_mbps:.1f} Mbps",
            "upload":          f"{upload_mbps:.1f} Mbps",
            "latency":         f"{latency_ms:.0f} ms",
            "jitter":          f"{jitter_ms:.0f} ms" if jitter_ms > 0 else "—",
            "server":          "Cloudflare Speed Test",
            "connection_type": connection_type,
            "error":           None
        }

    except Exception as e:
        return _error_result(connection_type, str(e))


def _error_result(connection_type: str, error: str) -> dict:
    return {
        "download":        "—",
        "upload":          "—",
        "latency":         "—",
        "jitter":          "—",
        "server":          "—",
        "connection_type": connection_type,
        "error":           error
    }


if __name__ == "__main__":
    print("\nRunning speed test...\n")
    r = run_speedtest(callback=print)
    if r["error"]:
        print(f"\n  Error      : {r['error']}")
    else:
        print(f"\n  Connection : {r['connection_type']}")
        print(f"  Download   : {r['download']}")
        print(f"  Upload     : {r['upload']}")
        print(f"  Latency    : {r['latency']}")
        print(f"  Server     : {r['server']}")
