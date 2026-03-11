"""
email_alerts.py — Send email alerts when SysProbe detects critical issues (Improvement #15).

Server-side module: called after each POST to /api/results.
If any result is critical, sends an email via SMTP.
Silently skips if SMTP is not configured.

Configuration (in dashboard_config.json):
{
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "alerts@yourcompany.com",
    "smtp_password": "app-password",
    "alert_recipients": ["it-lead@yourcompany.com"],
    "alert_from": "SysProbe Alerts <alerts@yourcompany.com>"
}
"""

import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def _load_dashboard_config() -> dict:
    """Load dashboard config from dashboard_config.json."""
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dashboard_config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _detect_critical_issues(record: dict) -> list:
    """Detect critical issues from a results record. Returns list of issue strings."""
    issues = []

    # Connection stability
    conn = record.get("connection_stability", "—")
    if conn != "—":
        try:
            import re
            match = re.search(r'(\d+)\s*/\s*100', conn)
            if match and int(match.group(1)) < 60:
                issues.append(f"🔴 Connection stability critically low: {conn}")
        except Exception:
            pass

    # Internet speed
    speed = record.get("internet_speed", "—")
    if speed != "—":
        try:
            import re
            match = re.search(r'([\d.]+)↓', speed)
            if match and float(match.group(1)) < 5:
                issues.append(f"🔴 Download speed critically low: {speed}")
        except Exception:
            pass

    # Mic level
    mic = record.get("mic_level", "—")
    if mic != "—":
        try:
            import re
            match = re.search(r'(\d+)', mic)
            if match and int(match.group(1)) < 30:
                issues.append(f"🔴 Microphone level critically low: {mic}")
        except Exception:
            pass

    # Chrome
    chrome = record.get("chrome_version", "—")
    if "outdated" in chrome.lower():
        issues.append(f"⚠️ Chrome browser outdated: {chrome}")

    # Disk space
    disk = record.get("disk_space", "—")
    if disk != "—":
        try:
            import re
            match = re.search(r'([\d.]+)GB', disk)
            if match and float(match.group(1)) < 5:
                issues.append(f"🔴 Disk space critically low: {disk}")
        except Exception:
            pass

    return issues


def send_alert_if_critical(record: dict):
    """
    Check a results record for critical issues and send email alert if found.
    Silently returns if SMTP is not configured.
    """
    cfg = _load_dashboard_config()

    smtp_host = cfg.get("smtp_host", "")
    smtp_port = cfg.get("smtp_port", 587)
    smtp_user = cfg.get("smtp_user", "")
    smtp_password = cfg.get("smtp_password", "")
    recipients = cfg.get("alert_recipients", [])
    from_addr = cfg.get("alert_from", smtp_user)

    # If SMTP is not configured, silently skip
    if not smtp_host or not smtp_user or not smtp_password or not recipients:
        return

    issues = _detect_critical_issues(record)
    if not issues:
        return

    agent_name = record.get("agent_name", "Unknown")
    anydesk_id = record.get("anydesk_id", "—")

    # Build email
    subject = f"⚠️ SysProbe Alert: {agent_name} has critical issues"


    html_body = f"""
    <html>
    <body style="font-family: -apple-system, sans-serif; background: #f5f5f5; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h2 style="color: #EF4444; margin-top: 0;">⚠️ SysProbe Critical Alert</h2>
        <p><strong>Agent:</strong> {agent_name}</p>
        <p><strong>AnyDesk ID:</strong> {anydesk_id}</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr style="border: 1px solid #eee;">
        <h3 style="color: #333;">Issues Detected:</h3>
        <ul>
            {''.join(f'<li style="margin: 8px 0; color: #333;">{issue}</li>' for issue in issues)}
        </ul>
        <hr style="border: 1px solid #eee;">
        <p style="color: #999; font-size: 12px;">
            Sent by SysProbe Team Dashboard
        </p>
    </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_addr, recipients, msg.as_string())
    except Exception:
        pass  # Silent — don't crash the dashboard
