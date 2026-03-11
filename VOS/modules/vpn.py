"""
vpn.py — Detect active VPN connections and provide disable functionality.

Scans network adapters and running processes to detect VPN usage.
Designed to warn agents that VPN may interfere with VoIP quality.
"""

import subprocess
import psutil
from logger import get_logger

log = get_logger("vpn")

# Known VPN-related keywords in network adapter names
VPN_ADAPTER_KEYWORDS = [
    "vpn", "tap-", "tun", "wireguard", "warp", "cloudflare",
    "openvpn", "nordlynx", "proton", "mullvad", "cyberghost",
    "surfshark", "expressvpn", "pia", "windscribe", "tunnelbear",
    "hotspot shield", "fortinet", "cisco anyconnect", "globalprotect",
    "pulse secure", "juniper", "softether", "zerotier", "tailscale",
]

# Known VPN process names (lowercase, without .exe)
VPN_PROCESSES = [
    "warp-svc", "warp-taskbar", "cloudflared",
    "openvpn", "openvpn-gui", "openvpnserv",
    "nordvpn", "nordlynx", "nordvpn-service",
    "protonvpn", "protonvpnservice",
    "mullvad-daemon", "mullvad-vpn",
    "cyberghostvpn", "cyberghost",
    "surfshark", "surfsharkservice",
    "expressvpnd", "expressvpn",
    "pia-service", "pia-client",
    "windscribe", "windscribeservice",
    "tunnelbear",
    "hotspotshield", "hsssrv",
    "forticlient", "fortisslvpn",
    "vpnagent", "vpnui",  # Cisco AnyConnect
    "pangpa", "pangps",   # GlobalProtect
    "dsaccessservice",    # Pulse Secure
    "softether",
    "zerotier-one", "zerotier_desktop_ui",
    "tailscaled",
]


def check_vpn() -> dict:
    """
    Detect active VPN connections.

    Returns dict with:
        active (bool): Whether a VPN is detected
        vpn_name (str): Display name of the detected VPN
        adapter (str|None): Name of the VPN network adapter
        process (str|None): Name of the VPN process found
    """
    result = {
        "active": False,
        "vpn_name": "",
        "adapter": None,
        "process": None,
    }

    # 1. Check network adapters
    try:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        for iface_name in addrs:
            name_lower = iface_name.lower()
            # Check if adapter name matches VPN keywords AND is up
            is_up = stats.get(iface_name, None)
            if is_up and is_up.isup:
                for keyword in VPN_ADAPTER_KEYWORDS:
                    if keyword in name_lower:
                        result["active"] = True
                        result["adapter"] = iface_name
                        result["vpn_name"] = iface_name
                        log.info(f"VPN adapter detected: {iface_name}")
                        break
            if result["active"]:
                break
    except Exception as e:
        log.warning(f"VPN adapter check failed: {e}")

    # 2. Check running processes
    try:
        for proc in psutil.process_iter(["name"]):
            try:
                proc_name = proc.info["name"].lower().replace(".exe", "")
                for vpn_proc in VPN_PROCESSES:
                    if vpn_proc in proc_name:
                        result["active"] = True
                        result["process"] = proc.info["name"]
                        if not result["vpn_name"]:
                            result["vpn_name"] = proc.info["name"]
                        log.info(f"VPN process detected: {proc.info['name']}")
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            if result["process"]:
                break
    except Exception as e:
        log.warning(f"VPN process check failed: {e}")

    if not result["active"]:
        log.info("No VPN detected")

    return result


if __name__ == "__main__":
    print("\nChecking for VPN...\n")
    info = check_vpn()
    if info["active"]:
        print(f"  VPN Active: {info['vpn_name']}")
        print(f"  Adapter   : {info['adapter'] or '—'}")
        print(f"  Process   : {info['process'] or '—'}")
    else:
        print("  No VPN detected.")
