<h1 align="center">
  💻 IT-check (Vital Operations Scanner)
</h1>

<p align="center">
  <strong>A Python app that audits agent connection stability to prevent call delays, replacing manual AnyDesk checks.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/CustomTkinter-000000?style=for-the-badge" alt="CustomTkinter">
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/In_Production_at-RES--VA-06B6D4?style=for-the-badge" alt="RES-VA">
</p>

---

## 📋 What is this project?

The `IT-check` repo holds **two separate parts**:
1. **The VOS Desktop App** (`/VOS`) — A Python/Windows app that tests agents' PCs (hardware, mic, ping) to make sure their connection is good enough for ReadyMode calls.
2. **The VOS Landing Page** (root) — A React/Vite site built so users can download the tool.

> **Note**: Both are actively used by **RES-VA**.

---

Inside the `VOS/` directory, this app runs background checks using Python and CustomTkinter, then posts the results to a Flask web dashboard.

### ✨ Key Features
| Diagnostic | What It Measures |
|---|---|
| 💻 **Hardware Profiling** | Detects CPU model, total/available RAM, and GPU capabilities |
| 🌐 **Browser Health** | Verifies Chrome installation vs. latest stable version (staged rollout aware) |
| 📡 **VoIP Connection** | Runs 40 pings with jitter, packet loss, and spike analysis (scored 0–100) |
| 📶 **Bandwidth** | Automated Download/Upload speed tests via Cloudflare CDN |
| 🎙 **Audio Hardware** | Scans Windows Core Audio for microphone presence and volume level |
| 💾 **Storage** | Monitors free space on the system drive |

### 🚀 Features
- **Dashboard Sync:** Posts test results quietly to the Flask admin dashboard.
- **Background Checks:** Runs tests every hour from the system tray.
- **Auto-Updater:** Downloads and applies new versions automatically.
- **Quick Drill:** A one-click button that clears Chrome data and flushes DNS to fix common agent issues.

### ⚙️ Desktop App Setup
```bash
cd VOS

# Install dependencies
pip install -r requirements.txt

# Run the desktop client
python main.py

# Run the admin dashboard server (runs on localhost:5000)
python dashboard_server.py
```

---

## 🌐 2. The VOS Landing Page (React)

This is the code in the root directory. It's just a fast React page to show off the app and provide the `.exe` download.

- **Live Demo:** [https://vos-landing.vercel.app](https://vos-landing.vercel.app)
- **Stack:** React 18, TypeScript, Vite, TailwindCSS

### ⚙️ Landing Page Setup
```bash
# From the root directory
npm install
npm run dev
```

---

## 🏗️ Repository Structure

```
IT-check/
├── VOS/                         # 🐍 Python Desktop App & Dashboard
│   ├── main.py                  # Desktop app entry point (CustomTkinter GUI)
│   ├── dashboard_server.py      # Flask admin dashboard server
│   ├── modules/                 # Hardware & network diagnostic modules
│   ├── gui/                     # UI components and theme system
│   ├── templates/               # Flask HTML templates for the dashboard
│   ├── build.bat                # PyInstaller build script -> .exe
│   └── requirements.txt         # Python dependencies
│
├── src/                         # ⚛️ React Landing Page Source
│   ├── components/              # React UI components
│   └── ...
├── index.html                   # Vite entry HTML
├── tailwind.config.js           # Tailwind configuration
└── package.json                 # Node dependencies
```

---

## 📄 License
This is a proprietary software project built for enterprise use.
