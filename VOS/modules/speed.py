"""
speed.py — Internet speed measurement.

Primary  : Ookla/speedtest.net protocol via direct HTTP requests.
           Same servers and test files as speedtest.net — results match.
Fallback : Cloudflare CDN if Ookla servers are unreachable.

No external library needed — only uses 'requests' which is already bundled.
"""

import time
import threading
import socket
import psutil
import requests


TIMEOUT = 30

# Ookla server list (JSON API — same source as speedtest-cli)
_OOKLA_SERVERS_URL = "https://www.speedtest.net/api/js/servers"

# Cloudflare fallback
_CF_DOWNLOAD_URL = "https://speed.cloudflare.com/__down?bytes=10000000"
_CF_UPLOAD_URL   = "https://speed.cloudflare.com/__up"


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


# ── Ookla protocol ────────────────────────────────────────────────────────────

def _get_best_ookla_server() -> dict | None:
    """
    Fetch Ookla server list and return the lowest-latency server.
    Returns None if the API is unreachable.
    """
    try:
        resp = requests.get(
            _OOKLA_SERVERS_URL,
            params={"engine": "js", "https_functional": "true", "limit": "10"},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=10
        )
        resp.raise_for_status()
        servers = resp.json()
    except Exception:
        return None

    best, best_ping = None, float("inf")
    for server in servers[:6]:
        url = server.get("url", "")
        if not url:
            continue
        # Server URLs end with /upload.php — strip to get the base path
        base = url.rsplit("/", 1)[0]
        try:
            start = time.perf_counter()
            requests.get(f"{base}/latency.txt", timeout=5)
            ping = (time.perf_counter() - start) * 1000
            if ping < best_ping:
                best_ping = ping
                best = {**server, "ping": round(ping, 1)}
        except Exception:
            continue

    return best


def _ookla_download(server_url: str) -> float:
    """
    Download Ookla test images in parallel (3 streams). Returns Mbps.
    Uses same random*.jpg format as speedtest.net.
    Parallel streams are required to saturate the TCP connection.
    """
    sizes       = [2000, 2500, 3000]   # one per thread
    total_bytes = 0
    lock        = threading.Lock()
    start       = time.perf_counter()

    base = server_url.rsplit("/", 1)[0]   # strip upload.php

    def _fetch(size):
        nonlocal total_bytes
        received = 0
        try:
            url  = f"{base}/random{size}x{size}.jpg"
            resp = requests.get(url, stream=True, timeout=TIMEOUT)
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=65536):
                received += len(chunk)
        except Exception:
            pass
        finally:
            if received > 0:
                with lock:
                    total_bytes += received

    threads = [threading.Thread(target=_fetch, args=(s,)) for s in sizes]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    elapsed = time.perf_counter() - start
    if elapsed > 0 and total_bytes > 0:
        return (total_bytes * 8) / (elapsed * 1_000_000)
    return 0.0


def _ookla_upload(server_url: str) -> float:
    """Upload data to Ookla server. Returns Mbps."""
    sizes       = [1_000_000, 2_000_000]  # 1 MB + 2 MB
    total_bytes = 0
    start       = time.perf_counter()

    for size in sizes:
        try:
            data = b"x" * size
            requests.post(
                server_url,
                data=data,
                headers={"Content-Type": "application/octet-stream"},
                timeout=TIMEOUT
            )
            total_bytes += size
        except Exception:
            continue

    elapsed = time.perf_counter() - start
    if elapsed > 0 and total_bytes > 0:
        return (total_bytes * 8) / (elapsed * 1_000_000)
    return 0.0


def _ookla_latency(server_url: str) -> float:
    """Ping Ookla server. Returns ms."""
    try:
        base  = server_url.rsplit("/", 1)[0]   # strip upload.php
        times = []
        for _ in range(3):
            start = time.perf_counter()
            requests.get(f"{base}/latency.txt", timeout=5)
            times.append((time.perf_counter() - start) * 1000)
        return round(min(times), 1)
    except Exception:
        return 0.0


# ── Cloudflare fallback ───────────────────────────────────────────────────────

def _cf_download() -> float:
    try:
        start = time.perf_counter()
        resp  = requests.get(_CF_DOWNLOAD_URL, stream=True, timeout=TIMEOUT)
        resp.raise_for_status()
        received = sum(len(c) for c in resp.iter_content(chunk_size=131072))
        elapsed  = time.perf_counter() - start
        return (received * 8) / (elapsed * 1_000_000) if elapsed > 0 else 0.0
    except Exception:
        return 0.0


def _cf_upload() -> float:
    try:
        data  = b"0" * 2_000_000
        start = time.perf_counter()
        requests.post(_CF_UPLOAD_URL, data=data, timeout=TIMEOUT,
                      headers={"Content-Type": "application/octet-stream"})
        elapsed = time.perf_counter() - start
        return (len(data) * 8) / (elapsed * 1_000_000) if elapsed > 0 else 0.0
    except Exception:
        return 0.0


def _cf_latency() -> float:
    try:
        times = []
        for _ in range(3):
            start = time.perf_counter()
            requests.get("https://speed.cloudflare.com/__down?bytes=0", timeout=5)
            times.append((time.perf_counter() - start) * 1000)
        return round(min(times), 1)
    except Exception:
        return 0.0


# ── Main entry point ──────────────────────────────────────────────────────────

def run_speedtest(callback=None) -> dict:
    connection_type = get_connection_type()

    try:
        # ── Try Ookla first ───────────────────────────────────────────────────
        if callback:
            callback("Step 1/3: Finding best server...")
        server = _get_best_ookla_server()

        if server:
            server_url  = server.get("url", "")
            server_name = f"{server.get('name', '')}, {server.get('country', '')}"

            if callback:
                callback(f"Step 2/3: Testing download speed ({server.get('sponsor', 'Ookla')})...")
            download_mbps = _ookla_download(server_url)

            if callback:
                callback("Step 3/3: Testing upload speed...")
            upload_mbps = _ookla_upload(server_url)
            latency_ms  = server.get("ping", _ookla_latency(server_url))

            if download_mbps > 0:
                if callback:
                    callback("Done!")
                return {
                    "download":        f"{download_mbps:.1f} Mbps",
                    "upload":          f"{upload_mbps:.1f} Mbps",
                    "latency":         f"{latency_ms:.0f} ms",
                    "jitter":          "—",
                    "server":          server_name,
                    "connection_type": connection_type,
                    "error":           None
                }

        # ── Cloudflare fallback ───────────────────────────────────────────────
        if callback:
            callback("Step 2/3: Testing download speed (fallback)...")
        download_mbps = _cf_download()

        if callback:
            callback("Step 3/3: Testing upload speed (fallback)...")
        upload_mbps = _cf_upload()
        latency_ms  = _cf_latency()

        if download_mbps == 0.0:
            return _error_result(connection_type, "No internet connection or server unavailable.")

        if callback:
            callback("Done!")

        return {
            "download":        f"{download_mbps:.1f} Mbps",
            "upload":          f"{upload_mbps:.1f} Mbps",
            "latency":         f"{latency_ms:.0f} ms",
            "jitter":          "—",
            "server":          "Cloudflare CDN (fallback)",
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
