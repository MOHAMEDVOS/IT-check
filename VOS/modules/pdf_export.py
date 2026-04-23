"""
pdf_export.py — Export VOS check results to a PDF report (Improvement #14).

Uses reportlab to generate a professional system diagnostics report.
"""

import os
import sys
from datetime import datetime
from logger import get_logger
from thresholds import APP_NAME, APP_VERSION

log = get_logger("pdf_export")


def export_results_to_pdf(results: dict, agent_name: str = "Unknown",
                          anydesk_id: str = "—", team_name: str = "—", output_dir: str = None) -> str:
    """
    Generate a PDF report of VOS check results.

    Args:
        results: The results dict from VOSApp.
        agent_name: Employee name for the report header.
        anydesk_id: AnyDesk ID for the report header.
        team_name: Team name for the report header.
        output_dir: Where to save the PDF. Defaults to Desktop.

    Returns:
        Absolute path to the generated PDF file.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    if output_dir is None:
        output_dir = os.path.join(os.path.expanduser("~"), "Desktop")

    safe_name = agent_name.strip()[:40]
    filename = f"{safe_name}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            leftMargin=25 * mm, rightMargin=25 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm)

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=22, spaceAfter=6,
        textColor=HexColor("#0A1118"),
    )
    heading_style = ParagraphStyle(
        'CustomHeading', parent=styles['Heading2'],
        fontSize=14, spaceBefore=16, spaceAfter=8,
        textColor=HexColor("#00D2FF"),
    )
    normal_style = ParagraphStyle(
        'CustomNormal', parent=styles['Normal'],
        fontSize=11, spaceAfter=4,
    )
    small_style = ParagraphStyle(
        'CustomSmall', parent=styles['Normal'],
        fontSize=9, textColor=HexColor("#666666"),
    )

    elements = []

    # Title
    elements.append(Paragraph(f"{APP_NAME} — System Report", title_style))

    # Header Table (12hr format)
    header_data = [
        ["Agent:", agent_name, "Date:", datetime.now().strftime('%Y-%m-%d %I:%M %p')],
        ["AnyDesk:", anydesk_id, "Team:", team_name]
    ]

    ht = Table(header_data, colWidths=[25 * mm, 60 * mm, 20 * mm, 55 * mm], hAlign='LEFT')
    ht.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (0, -1), HexColor("#E8EDF2")),
        ('BACKGROUND', (2, 0), (2, -1), HexColor("#E8EDF2")),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor("#666666")),  # Labels
        ('TEXTCOLOR', (2, 0), (2, -1), HexColor("#666666")),  # Labels
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor("#0A1118")),  # Values
        ('TEXTCOLOR', (3, 0), (3, -1), HexColor("#0A1118")),  # Values
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('VITALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(ht)
    elements.append(Spacer(1, 6 * mm))

    # ── Overall Assessment ──
    from thresholds import CPU_PERF_SCORE_MIN

    specs = results.get("specs", {})
    speed = results.get("speed", {})
    mic = results.get("mic", {})

    reasons = []

    # 1. Specs
    cpu_label = specs.get("cpu_label", specs.get("perf_label", "")).lower()
    if cpu_label != "approved":
        reasons.append("PC Specs do not meet the minimum requirements (Intel Core i5 6th Gen or higher)")

    # 1b. RAM
    import re
    ram_str = str(specs.get("total_ram", ""))
    ram_match = re.search(r'([\d.]+)', ram_str)
    if ram_match:
        try:
            ram_val = float(ram_match.group(1))
            if ram_val < 7.0:  # Allow 7.x since 8GB sometimes reads as 7.8GB usable
                reasons.append(f"RAM does not meet minimum requirement (8GB) — Detected: {ram_str}")
        except ValueError:
            pass

    # 2. Connection type — Ethernet required
    conn_type = str(speed.get("connection_type", "")).lower()
    if "ethernet" not in conn_type and "eth" not in conn_type:
        reasons.append("Wi-Fi connection detected — Ethernet (wired) is required")

    # 3. Speed — 10 Mbps down, 2 Mbps up
    try:
        dl = float(speed.get("download", speed.get("_raw_down", 0)) or 0)
        ul = float(speed.get("upload", speed.get("_raw_up", 0)) or 0)
    except (ValueError, TypeError):
        dl, ul = 0.0, 0.0
    if dl < 10.0 or ul < 2.0:
        reasons.append(f"Internet speed below requirement — Need: 10 Mbps down / 2 Mbps up, Got: {dl} / {ul}")

    # 4. Mic — USB or AUX/jack required
    mic_type = str(mic.get("type", "")).lower()
    mic_device = str(mic.get("device", "")).lower()
    mic_ok = (
        "usb" in mic_type or "usb" in mic_device or
        "aux" in mic_type or "aux" in mic_device or
        "jack" in mic_device or "3.5" in mic_device
    )
    if not mic_ok:
        mic_label = mic.get("type", mic.get("device", "Unknown"))
        reasons.append(f"Headset is not USB or AUX type — Detected: {mic_label}")

    def _display_mic_type(mic_data: dict) -> str:
        raw_type = str(mic_data.get("type", "") or "").strip()
        raw_device = str(mic_data.get("device", "") or "").lower()
        raw_type_l = raw_type.lower()
        if "usb" in raw_type_l or "usb" in raw_device:
            return "USB"
        if "aux" in raw_type_l or "aux" in raw_device or "jack" in raw_device or "3.5" in raw_device:
            return "AUX"
        if raw_type and raw_type != "—":
            return raw_type
        return "—"

    is_approved = len(reasons) == 0

    verdict_style = ParagraphStyle(
        'Verdict', parent=styles['Normal'],
        fontSize=16, fontName='Helvetica-Bold',
        textColor=HexColor("#15803d") if is_approved else HexColor("#dc2626"),
        spaceBefore=4, spaceAfter=4,
    )
    reason_style = ParagraphStyle(
        'Reason', parent=styles['Normal'],
        fontSize=10, textColor=HexColor("#991b1b"),
        leftIndent=10, spaceAfter=2,
    )

    elements.append(Paragraph("Overall Assessment", heading_style))

    # Verdict box
    verdict_text = "APPROVED" if is_approved else "NOT APPROVED"
    verdict_bg = HexColor("#dcfce7") if is_approved else HexColor("#fee2e2")
    verdict_border = HexColor("#16a34a") if is_approved else HexColor("#dc2626")

    verdict_data = [[Paragraph(verdict_text, verdict_style)]]
    vt = Table(verdict_data, colWidths=[160 * mm])
    vt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), verdict_bg),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1.5, verdict_border),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    elements.append(vt)

    if reasons:
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph("Reasons:", ParagraphStyle(
            'ReasonsHeader', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica-Bold',
            textColor=HexColor("#450a0a"), spaceAfter=4,
        )))
        for r in reasons:
            elements.append(Paragraph(f"- {r}", reason_style))

    elements.append(Spacer(1, 6 * mm))
    if specs:
        elements.append(Paragraph("💻 System Specs", heading_style))
        data = [
            ["CPU", specs.get("cpu_model", "—")],
            ["RAM", specs.get("total_ram", "—")],
            ["GPU", specs.get("gpu_name", "—")],
            ["Performance", specs.get("cpu_label", specs.get("perf_label", "—"))],
        ]
        t = Table(data, colWidths=[40 * mm, 120 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor("#E8EDF2")),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
        ]))
        elements.append(t)

    # Internet Speed
    speed = results.get("speed", {})
    if speed:
        elements.append(Paragraph("📶 Internet Speed", heading_style))
        data = [
            ["Download", str(speed.get("download", speed.get("_raw_down", "—")))],
            ["Upload", str(speed.get("upload", speed.get("_raw_up", "—")))],
            ["Connection", str(speed.get("connection_type", "—"))],
        ]
        t = Table(data, colWidths=[40 * mm, 120 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor("#E8EDF2")),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
        ]))
        elements.append(t)

    # Connection Stability
    ping = results.get("ping", None)
    if ping and hasattr(ping, "stability_score"):
        elements.append(Paragraph("📡 Connection Stability", heading_style))
        data = [
            ["Score", f"{ping.stability_score}/100"],
            ["Verdict", ping.verdict],
            ["Jitter", f"{ping.jitter} ms"],
            ["Avg RTT", f"{ping.avg_rtt:.0f} ms"],
            ["Packet Loss", f"{ping.packet_loss_pct}%"],
            ["Spikes", str(ping.spike_count)],
        ]
        t = Table(data, colWidths=[40 * mm, 120 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor("#E8EDF2")),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
        ]))
        elements.append(t)

    # Chrome
    chrome = results.get("chrome", None)
    if chrome and hasattr(chrome, "installed_version"):
        elements.append(Paragraph("🌐 Chrome Browser", heading_style))
        data = [
            ["Installed", f"{chrome.installed_version} (v{chrome.installed_milestone})"],
            ["Latest", f"{chrome.latest_version} (v{chrome.latest_milestone})"],
            ["Status", chrome.status_label],
        ]
        t = Table(data, colWidths=[40 * mm, 120 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor("#E8EDF2")),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
        ]))
        elements.append(t)

    # Microphone
    mic = results.get("mic", {})
    if mic:
        mic_type_display = _display_mic_type(mic)
        elements.append(Paragraph("🎙 Microphone", heading_style))
        data = [
            ["Device", str(mic.get("device", "—"))],
            ["Type", mic_type_display],
            ["Level", f"{mic.get('level', 0)}/100"],
            ["Notes", str(mic.get("notes", "—"))],
        ]
        t = Table(data, colWidths=[40 * mm, 120 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor("#E8EDF2")),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
        ]))
        elements.append(t)

    # Disk
    disk = results.get("disk", {})
    if disk and disk.get("free_gb"):
        elements.append(Paragraph("💾 Disk Space", heading_style))
        data = [
            ["Drive", str(disk.get("drive", "—"))],
            ["Free Space", f"{disk.get('free_gb', 0):.1f} GB"],
            ["Total", f"{disk.get('total_gb', 0):.0f} GB"],
            ["Used", f"{disk.get('used_pct', 0)}%"],
        ]
        t = Table(data, colWidths=[40 * mm, 120 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor("#E8EDF2")),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
        ]))
        elements.append(t)

    # Footer
    elements.append(Spacer(1, 15 * mm))
    elements.append(Paragraph(
        f"Generated by {APP_NAME} v{APP_VERSION} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        small_style,
    ))

    doc.build(elements)
    log.info(f"PDF report generated: {filepath}")
    return filepath
