"""
speed.py — Internet speed measurement using Cloudflare CDN.

Uses Cloudflare's speed test endpoints with multiple parallel streams.
No external CLI dependency — works reliably inside the compiled EXE.
"""

import time
import threading
import socket
import psutil
import requests


DOWNLOAD_URLS = [
    "https://speed.cloudflare.com/__down?bytes=10000000",   # 10 MB
    "https://speed.cloudflare.com/__down?bytes=5000000",    # 5 MB fallback
]

UPLOAD_URL  = "https://speed.cloudflare.com/__up"
TIMEOUT     = 45


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


def _measure_download_mbps(streams: int = 3) -> float:
    """Download from Cloudflare using parallel streams. Returns total Mbps."""
    results = []
    lock    = threading.Lock()

    def _worker():
        for url in DOWNLOAD_URLS:
            try:
                start = time.perf_counter()
                resp  = requests.get(url, timeout=TIMEOUT, stream=True)
                resp.raise_for_status()
                received = sum(len(chunk) for chunk in resp.iter_content(chunk_size=131072))
                elapsed  = time.perf_counter() - start
                if elapsed > 0 and received > 0:
                    with lock:
                        results.append((received * 8) / (elapsed * 1_000_000))
                return
            except Exception:
                continue

    threads = [threading.Thread(target=_worker, daemon=True) for _ in range(streams)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=TIMEOUT + 5)

    return sum(results) if results else 0.0


def _measure_upload_mbps(streams: int = 2) -> float:
    """Upload data to Cloudflare using parallel streams. Returns total Mbps."""
    results = []
    lock    = threading.Lock()
    data    = b"0" * 2_000_000  # 2 MB per stream

    def _worker():
        try:
            start = time.perf_counter()
            requests.post(UPLOAD_URL, data=data, timeout=TIMEOUT,
                          headers={"Content-Type": "application/octet-stream"})
            elapsed = time.perf_counter() - start
            if elapsed > 0:
                with lock:
                    results.append((len(data) * 8) / (elapsed * 1_000_000))
        except Exception:
            pass

    threads = [threading.Thread(target=_worker, daemon=True) for _ in range(streams)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=TIMEOUT + 5)

    return sum(results) if results else 0.0


def _measure_latency_ms() -> float:
    """Measure latency to Cloudflare."""
    try:
        times = []
        for _ in range(3):
            start = time.perf_counter()
            requests.get("https://speed.cloudflare.com/__down?bytes=0", timeout=5)
            times.append((time.perf_counter() - start) * 1000)
        return round(min(times), 1)
    except Exception:
        return 0.0


def run_speedtest(callback=None) -> dict:
    """Measure internet speed using Cloudflare CDN."""
    connection_type = get_connection_type()

    try:
        if callback:
            callback("Step 1/3: Measuring latency...")
        latency_ms = _measure_latency_ms()

        if callback:
            callback("Step 2/3: Testing download speed...")
        download_mbps = _measure_download_mbps(streams=3)

        if callback:
            callback("Step 3/3: Testing upload speed...")
        upload_mbps = _measure_upload_mbps(streams=2)

        if download_mbps == 0.0:
            return _error_result(connection_type, "No internet connection or server unavailable.")

        if callback:
            callback("Done!")

        return {
            "download":        f"{download_mbps:.1f} Mbps",
            "upload":          f"{upload_mbps:.1f} Mbps",
            "latency":         f"{latency_ms:.0f} ms",
            "jitter":          "—",
            "server":          "Cloudflare CDN",
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
