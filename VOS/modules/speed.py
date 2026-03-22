"""
speed.py — Real internet speed measurement using Ookla's speedtest-cli.

Uses the same backend as speedtest.net — finds the closest real internet
server (not a CDN edge node), giving results that match what agents see
when they run speedtest.net themselves.
"""

import socket
import psutil
import speedtest


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


def run_speedtest(callback=None) -> dict:
    """
    Measure real internet speed using Ookla's speedtest-cli.
    Results match speedtest.net — what agents see is what the app shows.
    """
    connection_type = get_connection_type()

    try:
        if callback:
            callback("Step 1/3: Finding best server...")
        st = speedtest.Speedtest()
        st.get_best_server()
        server_name = f"{st.results.server['name']}, {st.results.server['country']}"
        latency_ms = round(st.results.ping, 1)

        if callback:
            callback("Step 2/3: Testing download speed...")
        download_mbps = st.download() / 1_000_000

        if callback:
            callback("Step 3/3: Testing upload speed...")
        upload_mbps = st.upload() / 1_000_000

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
