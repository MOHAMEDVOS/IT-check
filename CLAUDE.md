# VOS — Vital Operations Scanner
## Project Guide for Claude

This file is read automatically at the start of every conversation.
It explains the project structure, release process, and critical gotchas.

---

## What This Project Is

A two-part tool for **RES-VA** (a VoIP call center) to check agent workstation readiness:

1. **VOS Desktop App** (`/VOS/`) — Python/Windows `.exe` that runs diagnostics on agent PCs (Chrome version, internet speed, ping, mic, disk, specs)
2. **Landing Page** (`/src/`) — React/Vite website where agents download the app

---

## Project Structure

```
IT check/
├── CLAUDE.md                        ← you are here
├── .gitignore
├── public/
│   └── downloads/
│       ├── VOS.exe                  ← ⚠️ THE FILE AGENTS DOWNLOAD (from website + auto-updater)
│       └── version.json             ← ⚠️ THE FILE THE AUTO-UPDATER CHECKS (NOT VOS/version.json)
├── src/                             ← React landing page source
└── VOS/
    ├── main.py                      ← Desktop app entry point
    ├── thresholds.py                ← APP_VERSION lives here
    ├── version.json                 ← Informational only — NOT checked by auto-updater
    ├── requirements.txt
    ├── build.bat                    ← PyInstaller build script
    ├── modules/
    │   ├── chrome.py                ← Chrome version check
    │   ├── speed.py                 ← Speed test (Ookla/speedtest-cli)
    │   ├── ping.py                  ← VoIP ping diagnostics
    │   ├── updater.py               ← Auto-update logic
    │   ├── mic.py, disk.py, specs.py, auth.py, vpn.py, email_alerts.py, pdf_export.py
    ├── gui/
    │   ├── cards.py, dialogs.py, theme.py, loading_screen.py
    ├── templates/
    │   ├── dashboard.html           ← Admin web dashboard
    │   └── login.html
    ├── dashboard_server.py          ← Flask server (port 5000) for admin dashboard
    ├── tests/                       ← pytest unit tests
    └── Release/
        └── VOS.exe                  ← Build output (not committed to git)
```

---

## ⚠️ Critical: How the Auto-Updater Works

The auto-updater in `VOS/modules/updater.py` checks this URL:
```
https://raw.githubusercontent.com/MOHAMEDVOS/IT-check/main/public/downloads/version.json
```

**This means:**
- `public/downloads/version.json` is the REAL manifest agents check — always update this when releasing
- `VOS/version.json` is NOT checked by the updater — it is informational only
- `public/downloads/VOS.exe` is what agents download when they update

**Auto-update flow:**
1. Agent's app starts → checks `public/downloads/version.json` for `latest_version`
2. If `latest_version` > installed version → prompts agent to update
3. Downloads `public/downloads/VOS.exe` from raw.githubusercontent.com
4. Replaces itself silently via a VBScript + batch file swap

---

## Release Process (Step by Step)

### 1. Make your code changes and test them
```bash
cd VOS
.venv_stable/Scripts/pytest tests/ -v
```

### 2. Bump the version in TWO places
- `VOS/thresholds.py` → `APP_VERSION = "X.X.X"`
- `VOS/version.json` → `"latest_version": "X.X.X"` (informational)

### 3. Update the auto-updater manifest
- `public/downloads/version.json` → bump `latest_version` and update `release_notes` and `_timestamp`

### 4. Build the EXE
```bash
cd VOS
build.bat
# Output: VOS/Release/VOS.exe
# build.bat also auto-copies to public/downloads/VOS.exe
```
If `build.bat` does NOT copy automatically, copy manually:
```bash
cp VOS/Release/VOS.exe public/downloads/VOS.exe
```

### 5. Commit everything
```bash
git add VOS/thresholds.py VOS/version.json public/downloads/version.json public/downloads/VOS.exe
# Also add any changed source files
git commit -m "vX.X.X: Short description of changes"
```

### 6. Push to GitHub
```bash
git push origin main
```

### 7. Create GitHub Release (manual — no gh CLI installed)
- Go to: github.com/MOHAMEDVOS/IT-check/releases/new
- Tag: `vX.X.X`, Target: `main`
- Attach: `VOS/Release/VOS.exe`
- Publish

**That's it.** Agents auto-update on next app restart.

---

## Tech Stack

### Desktop App
- Python 3.11+, CustomTkinter (GUI), Flask (admin dashboard), SQLite
- PyInstaller → single `.exe`, UPX disabled (caused DLL corruption)
- Key packages: `psutil`, `pycaw`, `comtypes`, `requests`, `reportlab`, `GPUtil`, `pystray`

### Landing Page
- React 18, TypeScript, Vite, TailwindCSS
- Hosted on Vercel

---

## Key Design Decisions

| Decision | Reason |
|----------|--------|
| UPX disabled in build | UPX corrupted python310.dll — caused crash on update |
| `_MEIPASS` env vars stripped on update | PyInstaller child process inherited parent's temp path — caused DLL crash |
| Staged rollout tolerance (1 milestone) for Chrome | Google rolls out Chrome gradually — 1 milestone behind is normal |
| Ookla HTTP protocol (no library) for speed test | Cloudflare CDN is peered inside ISPs — gives inflated results. `speedtest-cli` library caused "No module" errors inside PyInstaller EXE. Direct HTTP to Ookla servers (`/random{N}x{N}.jpg`) with 3 parallel streams gives accurate results matching speedtest.net. Server URLs end with `/upload.php` — strip it with `rsplit('/', 1)[0]` before constructing download/latency URLs. |
| VBS wrapper for update swap | Hides the cmd window during self-update |

---

## Admin Dashboard

- Runs locally on the **dashboard machine** (not on agent machines)
- Start: `python dashboard_server.py`
- Access: `http://localhost:5000`
- Login: see `dashboard_config.json`
- Agents POST their results to the dashboard via API key

---

## Git Rules

These are excluded from git (see `.gitignore`):
- `VOS/build/` — PyInstaller build artifacts
- `VOS/Release/` — compiled EXE output
- `VOS/.venv_stable/` — Python virtual environment
- `*.log`, `*.db`

**Never commit** the venv or build folders — they are large and regeneratable.
