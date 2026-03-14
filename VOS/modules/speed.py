"""
speed.py — Fast, accurate internet speed measurement using direct HTTP downloads.

Uses Cloudflare's speed test CDN endpoints — no CLI binary required.
Downloads and uploads actual data to accurately measure bandwidth.
Much faster and more reliable than the Ookla CLI approach.
"""

import time
import threading
import socket
import psutil
import requests


# ── CDN test files for download speed measurement ────────────────────────────
# Using Cloudflare's speed.cloudflare.com which is fast, reliable, unrestricted
DOWNLOAD_URLS = [
    "https://speed.cloudflare.com/__down?bytes=5000000",    # 5 MB
    "https://speed.cloudflare.com/__down?bytes=2000000",    # 2 MB fallback
]

UPLOAD_URL = "https://speed.cloudflare.com/__up"

TIMEOUT = 45  # Increased timeout for slower connections


def get_network_name() -> str:
    """
    Get the SSID/Profile name of the connected network on Windows.
    Handles both Wi-Fi and Ethernet with high reliability.
    Removes trailing Windows numbers (e.g. "Home 3" -> "Home").
    """
    try:
        import subprocess
        import re

        # Source 1: PowerShell Connection Profile (Primary for both Wi-Fi and Ethernet)
        # We query all names and pick the first one that has internet connectivity or is not "Unidentified"
        ps_cmd = (
            "Get-NetConnectionProfile | "
            "Sort-Object IPv4Connectivity -Descending | "
            "Select-Object -ExpandProperty Name"
        )
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
        
        profile_names = []
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
            if output:
                profile_names = [line.strip() for line in output.split("\n") if line.strip() and "unidentified" not in line.lower()]
        except Exception:
            pass

        # Source 2: Netsh fallback (Specific to Wi-Fi SSID if profile is generic/empty)
        ssid = ""
        try:
            cmd_wifi = ["netsh", "wlan", "show", "interfaces"]
            output = subprocess.check_output(cmd_wifi, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW).decode()
            for line in output.split("\n"):
                if " SSID" in line and ":" in line:
                    ssid = line.split(":")[1].strip()
                    break
        except Exception:
            pass

        # Decision Logic
        final_name = ""
        if profile_names:
            final_name = profile_names[0]
            # If the profile name is generic "Network" and we have a specific SSID, prefer the SSID
            if final_name.lower() == "network" and ssid:
                final_name = ssid
        elif ssid:
            final_name = ssid
        
        # Cleanup: Remove Windows auto-increment numbers (e.g. "Home 2", "Home 3")
        if final_name:
            # Matches any space followed by one or more digits at the end of the string
            final_name = re.sub(r'\s+\d+$', '', final_name)
            return final_name
            
        return "Unknown"
    except Exception:
        return "Unknown"


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


def _measure_download_mbps(streams: int = 8) -> float:
    """Download from Cloudflare CDN using multiple parallel streams."""
    results = []
    threads = []
    
    def _worker():
        for url in DOWNLOAD_URLS:
            try:
                # Track starting time and downloaded bytes within the stream
                start = time.perf_counter()
                resp = requests.get(url, timeout=TIMEOUT, stream=True)
                resp.raise_for_status()
                bytes_received = 0
                for chunk in resp.iter_content(chunk_size=131072):
                    bytes_received += len(chunk)
                
                elapsed = time.perf_counter() - start
                if elapsed > 0:
                    results.append((bytes_received * 8) / (elapsed * 1_000_000))
                return
            except Exception:
                continue

    for _ in range(streams):
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join(timeout=TIMEOUT + 5)
        
    return sum(results) if results else 0.0


def _measure_upload_mbps(streams: int = 5) -> float:
    """Upload data to Cloudflare CDN using multiple parallel streams."""
    results = []
    threads = []
    data = b"0" * 2_000_000 # 2 MB per stream (easier to finish within timeout)
    
    def _worker():
        try:
            start = time.perf_counter()
            requests.post(UPLOAD_URL, data=data, timeout=TIMEOUT,
                         headers={"Content-Type": "application/octet-stream"})
            elapsed = time.perf_counter() - start
            if elapsed > 0:
                results.append((len(data) * 8) / (elapsed * 1_000_000))
        except Exception:
            pass

    for _ in range(streams):
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join(timeout=TIMEOUT + 5)
        
    return sum(results) if results else 0.0


def _measure_latency_ms() -> float:
    """Measure latency to Cloudflare by timing a small HTTP request."""
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
    """
    Measure internet speed using Cloudflare CDN.
    Runs tests SEQUENTIALLY with multi-threaded streams for accuracy.
    """
    connection_type = get_connection_type()

    try:
        if callback:
            callback("Step 1/3: Measuring latency...")
        latency_ms = _measure_latency_ms()

        if callback:
            callback("Step 2/3: Testing download speed (multi-stream)...")
        download_mbps = _measure_download_mbps(streams=6)

        if callback:
            callback("Step 3/3: Testing upload speed (multi-stream)...")
        upload_mbps = _measure_upload_mbps(streams=4)

        if download_mbps == 0.0:
            return _error_result(connection_type, "No internet connection or server unavailable.")

        if callback:
            callback("Done!")

        return {
            "download":        f"{download_mbps:.1f} Mbps",
            "upload":          f"{upload_mbps:.1f} Mbps",
            "latency":         f"{latency_ms:.0f} ms",
            "jitter":          "—",
            "server":          "Cloudflare CDN (Multi-Stream)",
            "connection_type": connection_type,
            "network_name":    get_network_name(),
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