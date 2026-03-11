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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = agent_name.replace(" ", "_")[:20]
    filename = f"VOS_Report_{safe_name}_{timestamp}.pdf"
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
    elements.append(Spacer(1, 10 * mm))

    # System Specs
    specs = results.get("specs", {})
    if specs:
        elements.append(Paragraph("💻 System Specs", heading_style))
        data = [
            ["CPU", specs.get("cpu_model", "—")],
            ["RAM", specs.get("total_ram", "—")],
            ["GPU", specs.get("gpu_name", "—")],
            ["Performance", specs.get("perf_label", "—")],
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
        elements.append(Paragraph("🎙 Microphone", heading_style))
        data = [
            ["Device", str(mic.get("device", "—"))],
            ["Type", str(mic.get("type", "—"))],
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
