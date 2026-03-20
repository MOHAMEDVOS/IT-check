<h1 align="center">
  💻 IT-check (Vital Operations Scanner)
</h1>

<p align="center">
  <strong>An enterprise-grade Python desktop application for call center IT diagnostics and health monitoring</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/CustomTkinter-000000?style=for-the-badge" alt="CustomTkinter">
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/In_Production_at-RES--VA-06B6D4?style=for-the-badge" alt="RES-VA">
</p>

---

## 📋 What is this project?

The `IT-check` repository actually contains **two complete systems**:
1. **The VOS Desktop Application** (`/VOS` directory) — A Python-based Windows desktop tool that runs deep health diagnostics on call center agents' PCs to ensure they meet the rigorous requirements for VoIP calls (specifically tuned for ReadyMode).
2. **The VOS Landing Page** (root directory) — A modern React/Vite web application that serves as the download portal and marketing page for the desktop tool.

> **Note**: Both systems are currently deployed and **in active production use by RES-VA**.

---

## 🛠️ 1. The VOS Desktop App (Python)

Located in the `VOS/` directory, this robust desktop application is built with Python and CustomTkinter. It performs automated system checks and silently reports results to a centralized Flask dashboard.

### ✨ Key Features
| Diagnostic | What It Measures |
|---|---|
| 💻 **Hardware Profiling** | Detects CPU model, total/available RAM, and GPU capabilities |
| 🌐 **Browser Health** | Verifies Chrome installation vs. latest stable version (staged rollout aware) |
| 📡 **VoIP Connection** | Runs 40 pings with jitter, packet loss, and spike analysis (scored 0–100) |
| 📶 **Bandwidth** | Automated Download/Upload speed tests via Cloudflare CDN |
| 🎙 **Audio Hardware** | Scans Windows Core Audio for microphone presence and volume level |
| 💾 **Storage** | Monitors free space on the system drive |

### 🚀 Capabilities
- **Silent Dashboard Sync:** Results are silently POSTed to a centralized Flask web dashboard for IT administrators.
- **Automated Hourly Checks:** Runs diagnostics in the background while sitting quietly in the Windows system tray.
- **Auto-Updater:** Built-in mechanism to check for and apply new software updates.
- **"Quick Drill" Feature:** One-click automated fix for common issues (clears Chrome data and flushes DNS).

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

Located in the root of this repository, the landing page is a fast, responsive React application built to showcase the tool and provide a direct download link.

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
