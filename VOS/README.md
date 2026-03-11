# VOS — Vital Operations Scanner for Call Centers

**VOS** (Vital Operations Scanner) is an internal IT health-check tool built for call center operations. It diagnoses whether agent workstations meet the minimum requirements for reliable VoIP calls (specifically tuned for **Readymode**).

## Features

| Check | What It Measures |
|---|---|
| 💻 **PC Specs** | CPU model, RAM, GPU |
| 🌐 **Chrome** | Installed vs. latest stable version (staged rollout aware) |
| 📡 **Connection** | 40 pings with jitter/loss/spike analysis, scored 0–100 |
| 📶 **Speed** | Download/Upload via Cloudflare CDN |
| 🎙 **Microphone** | Windows mic volume level (0–100) |
| 💾 **Disk Space** | Free space on system drive |

After checks, the app generates **actionable feedback** with step-by-step fix instructions.

Results are **silently posted** to a **team dashboard** so IT supervisors can monitor all agents from one web page.

---

## Quick Start

### 1. Install Dependencies

```bash
cd VOS
pip install -r requirements.txt
```

### 2. Run the Desktop App

```bash
python main.py
```

### 3. Run the Dashboard Server

```bash
python dashboard_server.py
```

Then open `http://localhost:5000`. Default password: `vos2024`.

---

## Configuration

### Agent Config (`config.json`)

```json
{
    "employee_name": "Mohamed Ibrahim Abdo",
    "anydesk_id": "1 585 322 949",
    "dashboard_url": "http://localhost:5000",
    "api_key": "sysprobe-default-key",
    "theme": "dark",
    "update_check_url": ""
}
```

### Dashboard Config (`dashboard_config.json`)

```json
{
    "admin_password": "sysprobe2024",
    "api_key": "sysprobe-default-key",
    "secret_key": "change-me-in-production",
    "smtp_host": "",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_password": "",
    "alert_recipients": [],
    "alert_from": ""
}
```

---

## Building the Executable

```bash
build.bat
```

This creates `dist/VOS.exe` using PyInstaller.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Project Structure

```
VOS/
├── main.py                  # App entry point + VOSApp class
├── thresholds.py            # All configurable threshold constants
├── logger.py                # Rotating file logger
├── config.json              # Agent configuration
├── dashboard_server.py      # Flask dashboard server (SQLite, auth)
├── dashboard_config.json    # Dashboard server configuration
├── requirements.txt         # Python dependencies
├── build.bat                # PyInstaller build script
├── gui/                     # GUI components
│   ├── cards.py             # All diagnostic card widgets
│   ├── dialogs.py           # Setup dialog
│   └── theme.py             # Dark/Light theme system
├── modules/                 # Diagnostic modules
│   ├── specs.py             # CPU + RAM + GPU detection
│   ├── chrome.py            # Chrome version check
│   ├── ping.py              # VoIP-tuned ping diagnostics
│   ├── speed.py             # Internet speed via Cloudflare
│   ├── mic.py               # Microphone level (Windows Core Audio)
│   ├── disk.py              # Disk space check
│   ├── updater.py           # Auto-update version checker
│   ├── pdf_export.py        # PDF report generation
│   └── email_alerts.py      # SMTP email alerts for critical issues
├── templates/
│   ├── dashboard.html       # Web dashboard UI
│   └── login.html           # Dashboard login page
├── tests/                   # Unit tests
└── assets/
    ├── IT.ico               # App icon
    └── fonts/               # Custom fonts
```

---

## Deploying the Dashboard Online

1. Deploy `dashboard_server.py` to a cloud platform (Railway, Render, or VPS)
2. Set `dashboard_url` in each agent's `config.json` to the server's public URL
3. Set a strong `api_key` and `admin_password` in `dashboard_config.json`
4. Configure SMTP in `dashboard_config.json` for email alerts (optional)

---

**Developer:** Mohamed Abdo  
**Version:** 2.1.0
