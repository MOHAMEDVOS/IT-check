"""
speed.py — Accurate internet speed measurement using Ookla's server network.

PRIMARY:  speedtest-cli library → connects to Ookla/Speedtest.net servers.
          Results match speedtest.net by Ookla — the company standard.
FALLBACK: Cloudflare CDN single-stream (if Ookla servers are unreachable).

Why did the old code give inflated results?
  1. Cloudflare CDN has dedicated peering — bypasses real-world congestion.
  2. The old code summed parallel stream speeds instead of measuring real throughput.
     (6 streams × 10 Mbps = reported 60 Mbps, actual bandwidth = 10 Mbps)
"""

import time
import socket
import psutil
import requests
import logging

logger = logging.getLogger(__name__)


# ── Cloudflare fallback endpoints ────────────────────────────────────────────
_CF_DOWNLOAD_URL = "https://speed.cloudflare.com/__down?bytes=10000000"  # 10 MB, single stream
_CF_UPLOAD_URL   = "https://speed.cloudflare.com/__up"
_CF_LATENCY_URL  = "https://speed.cloudflare.com/__down?bytes=0"
_TIMEOUT = 45


# ── Connection type detection ─────────────────────────────────────────────────

def get_connection_type() -> str:
    """Detect whether active connection is Wi-Fi or Ethernet."""
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


# ── Primary: Ookla / speedtest-cli ───────────────────────────────────────────

def _calculate_jitter_ms(latency_url: str, samples: int = 10) -> float:
    """
    Jitter = mean absolute deviation between consecutive latency samples.
    This is the same method Ookla uses on speedtest.net.
    Pings `latency_url` via a small HTTP request `samples` times.
    """
    try:
        times = []
        for _ in range(samples):
            start = time.perf_counter()
            requests.get(latency_url, timeout=5)
            times.append((time.perf_counter() - start) * 1000)
        if len(times) < 2:
            return 0.0
        # Mean absolute deviation between consecutive samples
        deltas = [abs(times[i] - times[i - 1]) for i in range(1, len(times))]
        return round(sum(deltas) / len(deltas), 1)
    except Exception as e:
        logger.debug(f"Jitter calculation failed: {e}")
        return 0.0


def _run_ookla_speedtest() -> dict:
    """
    Use speedtest-cli to test via Ookla's server network.
    Results match speedtest.net — the company standard tool.
    """
    import speedtest  # imported here so fallback still works if not installed

    st = speedtest.Speedtest(secure=True)

    # Pick the best server (closest, lowest latency)
    best = st.get_best_server()
    
    # Construct latency.txt URL from the base URL
    server_base_url = best.get("url", "").rsplit("/", 1)[0]
    latency_url = f"{server_base_url}/latency.txt" if server_base_url else ""

    # Run tests with the same thread count speedtest.net web app uses (8 down / 6 up).
    # Default speedtest-cli uses too few threads and under-reports vs the browser.
    download_bps = st.download(threads=8)
    upload_bps   = st.upload(threads=6)

    results = st.results.dict()

    download_mbps  = download_bps / 1_000_000
    upload_mbps    = upload_bps   / 1_000_000
    latency_ms     = results.get("ping", 0.0)
    server_name    = results.get("server", {}).get("name", "Ookla server")
    server_country = results.get("server", {}).get("country", "")
    server_label   = f"Ookla — {server_name}, {server_country}".strip(", ")

    # Measure jitter against the selected Ookla server
    jitter_ms = _calculate_jitter_ms(latency_url) if latency_url else 0.0
    jitter_str = f"{jitter_ms:.1f} ms" if jitter_ms > 0 else "—"

    return {
        "download":        f"{download_mbps:.1f} Mbps",
        "upload":          f"{upload_mbps:.1f} Mbps",
        "latency":         f"{latency_ms:.0f} ms",
        "jitter":          jitter_str,
        "server":          server_label,
        "connection_type": get_connection_type(),
        "error":           None,
        "_method":         "ookla",
    }


# ── Fallback: Cloudflare single-stream ───────────────────────────────────────

def _measure_download_mbps_single() -> float:
    """
    Single-stream download from Cloudflare.
    Single stream = no aggregation inflation.
    """
    try:
        start = time.perf_counter()
        resp = requests.get(_CF_DOWNLOAD_URL, timeout=_TIMEOUT, stream=True)
        resp.raise_for_status()
        bytes_received = 0
        for chunk in resp.iter_content(chunk_size=131072):
            bytes_received += len(chunk)
        elapsed = time.perf_counter() - start
        if elapsed > 0 and bytes_received > 0:
            return (bytes_received * 8) / (elapsed * 1_000_000)
    except Exception as e:
        logger.warning(f"Cloudflare download fallback failed: {e}")
    return 0.0


def _measure_upload_mbps_single() -> float:
    """Single-stream upload to Cloudflare."""
    try:
        data = b"0" * 5_000_000  # 5 MB
        start = time.perf_counter()
        requests.post(
            _CF_UPLOAD_URL, data=data, timeout=_TIMEOUT,
            headers={"Content-Type": "application/octet-stream"}
        )
        elapsed = time.perf_counter() - start
        if elapsed > 0:
            return (len(data) * 8) / (elapsed * 1_000_000)
    except Exception as e:
        logger.warning(f"Cloudflare upload fallback failed: {e}")
    return 0.0


def _measure_latency_ms() -> tuple[float, float]:
    """Measure latency + jitter to Cloudflare (10 samples)."""
    try:
        times = []
        for _ in range(10):
            start = time.perf_counter()
            requests.get(_CF_LATENCY_URL, timeout=5)
            times.append((time.perf_counter() - start) * 1000)
        min_latency = round(min(times), 1)
        deltas = [abs(times[i] - times[i - 1]) for i in range(1, len(times))]
        jitter = round(sum(deltas) / len(deltas), 1) if deltas else 0.0
        return min_latency, jitter
    except Exception:
        return 0.0, 0.0


def _run_cloudflare_fallback() -> dict:
    """Cloudflare single-stream fallback."""
    latency_ms, jitter_ms = _measure_latency_ms()
    download_mbps = _measure_download_mbps_single()
    upload_mbps   = _measure_upload_mbps_single()

    if download_mbps == 0.0:
        raise RuntimeError("Cloudflare fallback also failed — no internet connection.")

    jitter_str = f"{jitter_ms:.1f} ms" if jitter_ms > 0 else "—"

    return {
        "download":        f"{download_mbps:.1f} Mbps",
        "upload":          f"{upload_mbps:.1f} Mbps",
        "latency":         f"{latency_ms:.0f} ms",
        "jitter":          jitter_str,
        "server":          "Cloudflare CDN (fallback)",
        "connection_type": get_connection_type(),
        "error":           None,
        "_method":         "cloudflare",
    }


# ── Public API ────────────────────────────────────────────────────────────────

def run_speedtest(callback=None) -> dict:
    """
    Measure internet speed — Ookla primary, Cloudflare fallback.

    The Ookla path uses speedtest-cli which connects to the same server
    network as speedtest.net — the company standard.
    """
    connection_type = get_connection_type()

    # ── Primary: Ookla via speedtest-cli ──────────────────────────────────
    try:
        if callback:
            callback("Connecting to Ookla speed test server...")
        result = _run_ookla_speedtest()
        result["connection_type"] = connection_type
        if callback:
            callback("Done!")
        logger.info(f"Speed test (Ookla): {result['download']} down / {result['upload']} up")
        return result

    except ImportError:
        logger.warning("speedtest-cli not installed — falling back to Cloudflare.")
        if callback:
            callback("Ookla unavailable, using Cloudflare fallback...")

    except Exception as e:
        logger.warning(f"Ookla speed test failed ({e}) — falling back to Cloudflare.")
        if callback:
            callback("Ookla server unreachable, using Cloudflare fallback...")

    # ── Fallback: Cloudflare single-stream ────────────────────────────────
    try:
        if callback:
            callback("Step 1/3: Measuring latency...")
        result = _run_cloudflare_fallback()
        result["connection_type"] = connection_type
        if callback:
            callback("Done!")
        logger.info(f"Speed test (Cloudflare fallback): {result['download']} down / {result['upload']} up")
        return result

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
        "error":           error,
    }


if __name__ == "__main__":
    print("\nRunning speed test (Ookla primary)...\n")
    r = run_speedtest(callback=print)
    if r["error"]:
        print(f"\n  Error      : {r['error']}")
    else:
        print(f"\n  Connection : {r['connection_type']}")
        print(f"  Server     : {r['server']}")
        print(f"  Download   : {r['download']}")
        print(f"  Upload     : {r['upload']}")
        print(f"  Latency    : {r['latency']}")
        print(f"  Jitter     : {r['jitter']}")