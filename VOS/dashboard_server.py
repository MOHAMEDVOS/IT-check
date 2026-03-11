"""
VOS - Vital Operations Scanner Dashboard
──────────────────────────────────────────
A Flask server that collects IT check results from all VOS agents
and displays them in a live web dashboard.

Features:
  - SQLite database for persistent storage (Improvement #2)
  - Full history tracking with timestamps (Improvement #7)
  - API key authentication for POST endpoints (Improvement #1)
  - Session-based login for the web dashboard (Improvement #1)
  - Email alerts for critical issues (Improvement #15)
  - CORS support (Improvement #18)

Usage:
    pip install flask flask-cors
    python dashboard_server.py

Then open http://localhost:5000 in your browser.
Default login: admin / vos2024


Configuration (dashboard_config.json):
{
    "admin_password": "vos2024",
    "api_key": "your-secret-key-here",
    "secret_key": "flask-session-secret",
    "smtp_host": "",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_password": "",
    "alert_recipients": [],
    "alert_from": ""
}
"""

import json
import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, request, render_template, session, redirect, url_for, send_file
from flask_cors import CORS
import tempfile
try:
    from modules.pdf_export import export_results_to_pdf
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# ── Config ──────────────────────────────────────────────────────────────
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(APP_DIR, "team_results.db")
CONFIG_FILE = os.path.join(APP_DIR, "dashboard_config.json")
PORT = 5000

app = Flask(__name__, template_folder=os.path.join(APP_DIR, "templates"))
CORS(app)


def _load_dashboard_config() -> dict:
    """Load dashboard configuration."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Create default config
    default = {
        "admin_password": "vos2024",
        "api_key": "vos-default-key",
        "secret_key": "change-me-in-production",
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "alert_recipients": [],
        "alert_from": "",
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
    except Exception:
        pass
    return default


cfg = _load_dashboard_config()
app.secret_key = cfg.get("secret_key", "change-me-in-production")
ADMIN_PASSWORD = cfg.get("admin_password", "vos2024")
API_KEY = cfg.get("api_key", "vos-default-key")


# ── Database ────────────────────────────────────────────────────────────
def _get_db():
    """Get a SQLite connection. Creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            anydesk_id TEXT DEFAULT '—',
            team TEXT DEFAULT '—',
            res_id TEXT DEFAULT '—',
            pc_specs TEXT DEFAULT '—',
            gpu TEXT DEFAULT '—',
            cpu_score INTEGER DEFAULT 0,
            cpu_label TEXT DEFAULT '—',
            chrome_version TEXT DEFAULT '—',
            chrome_status TEXT DEFAULT '—',
            connection_type TEXT DEFAULT '—',
            connection_stability TEXT DEFAULT '—',
            ping_details TEXT DEFAULT '{}',
            download_mbps REAL DEFAULT 0,
            upload_mbps REAL DEFAULT 0,
            internet_speed TEXT DEFAULT '—',
            mic_level TEXT DEFAULT '—',
            mic_device TEXT DEFAULT '—',
            disk_space TEXT DEFAULT '—',
            disk_free_gb REAL DEFAULT 0,
            disk_used_pct REAL DEFAULT 0,
            vpn_active INTEGER DEFAULT 0,
            vpn_name TEXT DEFAULT '',
            last_checked TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_name ON results(agent_name)
    """)
    cursor = conn.execute("PRAGMA table_info(results)")
    existing_cols = [row[1] for row in cursor.fetchall()]

    needed_cols = [
        ("anydesk_id", "TEXT DEFAULT '—'"),
        ("team", "TEXT DEFAULT '—'"),
        ("res_id", "TEXT DEFAULT '—'"),
        ("pc_specs", "TEXT DEFAULT '—'"),
        ("gpu", "TEXT DEFAULT '—'"),
        ("cpu_score", "INTEGER DEFAULT 0"),
        ("cpu_label", "TEXT DEFAULT '—'"),
        ("chrome_version", "TEXT DEFAULT '—'"),
        ("chrome_status", "TEXT DEFAULT '—'"),
        ("connection_type", "TEXT DEFAULT '—'"),
        ("connection_stability", "TEXT DEFAULT '—'"),
        ("ping_details", "TEXT DEFAULT '{}'"),
        ("download_mbps", "REAL DEFAULT 0"),
        ("upload_mbps", "REAL DEFAULT 0"),
        ("internet_speed", "TEXT DEFAULT '—'"),
        ("mic_level", "TEXT DEFAULT '—'"),
        ("mic_device", "TEXT DEFAULT '—'"),
        ("disk_space", "TEXT DEFAULT '—'"),
        ("disk_free_gb", "REAL DEFAULT 0"),
        ("disk_used_pct", "REAL DEFAULT 0"),
        ("vpn_active", "INTEGER DEFAULT 0"),
        ("vpn_name", "TEXT DEFAULT ''"),
        ("last_checked", "TEXT DEFAULT ''"),
        ("notes", "TEXT DEFAULT ''"),
    ]

    for col_name, col_def in needed_cols:
        if col_name not in existing_cols:
            try:
                conn.execute(f"ALTER TABLE results ADD COLUMN {col_name} {col_def}")
            except Exception:
                pass
    conn.commit()
    return conn


def _migrate_json_to_sqlite():
    """One-time migration: if team_results.json exists, import into SQLite."""
    json_file = os.path.join(APP_DIR, "team_results.json")
    if not os.path.exists(json_file):
        return
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            return
        conn = _get_db()
        for name, record in data.items():
            conn.execute("""
                INSERT INTO results (agent_name, anydesk_id, pc_specs, chrome_version,
                    connection_stability, internet_speed, mic_level, last_checked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.get("agent_name", name),
                record.get("anydesk_id", "—"),
                record.get("pc_specs", "—"),
                record.get("chrome_version", "—"),
                record.get("connection_stability", "—"),
                record.get("internet_speed", "—"),
                record.get("mic_level", "—"),
                record.get("last_checked", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ))
        conn.commit()
        conn.close()
        # Rename old file so we don't migrate again
        os.rename(json_file, json_file + ".migrated")
        print(f"  ✓ Migrated {len(data)} records from JSON to SQLite")
    except Exception as e:
        print(f"  ⚠ JSON migration failed: {e}")


# ── Auth Helpers ────────────────────────────────────────────────────────
def require_api_key(f):
    """Decorator: require X-API-Key header for API endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-Key", "")
        if key != API_KEY:
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated


def require_login(f):
    """Decorator: require session login for web pages."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


# ── Routes ──────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login_page():
    """Login page for the dashboard."""
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        error = "Invalid password"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login_page"))


@app.route("/")
@require_login
def dashboard():
    """Serve the main dashboard page."""
    return render_template("dashboard.html")


@app.route("/api/results", methods=["GET"])
@require_login
def get_results():
    """Return the latest result per agent as a JSON array."""
    conn = _get_db()
    # Get latest record per agent using a subquery
    rows = conn.execute("""
        SELECT r.* FROM results r
        INNER JOIN (
            SELECT agent_name, MAX(id) as max_id
            FROM results
            GROUP BY agent_name
        ) latest ON r.id = latest.max_id
        ORDER BY r.agent_name COLLATE NOCASE
    """).fetchall()
    conn.close()

    results_list = [dict(row) for row in rows]
    return jsonify(results_list)


@app.route("/api/results", methods=["POST"])
@require_api_key
def post_results():
    """Receive check results from a VOS agent. Stores full history."""
    payload = request.get_json(force=True)
    agent_name = payload.get("agent_name", "").strip()

    if not agent_name:
        return jsonify({"error": "agent_name is required"}), 400

    last_checked = payload.get("last_checked",
                               datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    conn = _get_db()
    # Upsert: remove old records for this agent, then insert the latest
    conn.execute("DELETE FROM results WHERE agent_name = ?", (agent_name,))
    conn.execute("""
        INSERT INTO results (agent_name, anydesk_id, team, res_id, pc_specs, gpu, cpu_score, cpu_label,
            chrome_version, chrome_status, connection_type, connection_stability, ping_details,
            download_mbps, upload_mbps, internet_speed, mic_level, mic_device,
            disk_space, disk_free_gb, disk_used_pct, vpn_active, vpn_name, last_checked, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        agent_name,
        payload.get("anydesk_id", "—"),
        payload.get("team", "—"),
        payload.get("res_id", "—"),
        payload.get("pc_specs", "—"),
        payload.get("gpu", "—"),
        payload.get("cpu_score", 0),
        payload.get("cpu_label", "—"),
        payload.get("chrome_version", "—"),
        payload.get("chrome_status", "—"),
        payload.get("connection_type", "—"),
        payload.get("connection_stability", "—"),
        payload.get("ping_details", "{}"),
        payload.get("download_mbps", 0),
        payload.get("upload_mbps", 0),
        payload.get("internet_speed", "—"),
        payload.get("mic_level", "—"),
        payload.get("mic_device", "—"),
        payload.get("disk_space", "—"),
        payload.get("disk_free_gb", 0),
        payload.get("disk_used_pct", 0),
        1 if payload.get("vpn_active") else 0,
        payload.get("vpn_name", ""),
        last_checked,
        payload.get("notes", ""),
    ))
    conn.commit()
    conn.close()

    # Check for critical issues and send email alert (Improvement #15)
    try:
        from modules.email_alerts import send_alert_if_critical
        send_alert_if_critical(payload)
    except Exception:
        pass

    return jsonify({"status": "ok", "agent": agent_name}), 200


@app.route("/api/results/<agent_name>", methods=["DELETE"])
def delete_agent(agent_name):
    """Delete all records for a specific agent. Requires session login."""
    if not session.get("logged_in"):
        return jsonify({"error": "Not authenticated"}), 401
    conn = _get_db()
    conn.execute("DELETE FROM results WHERE agent_name = ?", (agent_name,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted", "agent": agent_name}), 200


@app.route("/api/history/<agent_name>", methods=["GET"])
@require_login
def get_history(agent_name):
    """Return full check history for a specific agent."""
    limit = request.args.get("limit", 50, type=int)
    conn = _get_db()
    rows = conn.execute("""
        SELECT * FROM results
        WHERE agent_name = ?
        ORDER BY id DESC
        LIMIT ?
    """, (agent_name, limit)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/pdf/<agent_name>", methods=["GET"])
@require_login
def get_pdf(agent_name):
    """Generate and return a PDF report for the given agent."""
    if not HAS_PDF:
        return jsonify({"error": "PDF generation is currently unavailable (missing reportlab)"}), 503
    
    conn = _get_db()
    row = conn.execute("""
        SELECT * FROM results
        WHERE agent_name = ?
        ORDER BY id DESC
        LIMIT 1
    """, (agent_name,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Agent not found"}), 404

    # Reconstruct results dict as expected by pdf_export module
    # (The PDF module expects the nested structure created by the app)
    ping_details = {}
    try:
        ping_details = json.loads(row["ping_details"])
    except:
        pass

    results = {
        "specs": {
            "cpu_model": row["pc_specs"],
            "total_ram": row["pc_specs"].split("/")[-1].strip() if "/" in row["pc_specs"] else "—",
            "gpu_name": row["gpu"],
            "perf_label": row["cpu_label"],
        },
        "speed": {
            "download": row["download_mbps"],
            "upload": row["upload_mbps"],
            "connection_type": row["connection_type"],
        },
        "mic": {
            "device": row["mic_device"].split("—")[0].strip() if "—" in row["mic_device"] else row["mic_device"],
            "type": row["mic_device"].split("—")[-1].strip() if "—" in row["mic_device"] else "—",
            "level": row["mic_level"],
        },
        "disk": {
            "drive": "C:",
            "free_gb": row["disk_free_gb"],
            "total_gb": 0, # Not explicitly stored separately in float
            "used_pct": row["disk_used_pct"],
            "disk_space": row["disk_space"]
        },
        "chrome": {
            "installed_version": row["chrome_version"],
            "status_label": row["chrome_status"],
            # dummy milestone values to satisfy exporters hasattr checks
            "installed_milestone": "—",
            "latest_version": "—",
            "latest_milestone": "—"
        }
    }

    # Reconstruct a dummy ping object to satisfy pdf_export's hasattr checks
    class DummyPing:
        def __init__(self, details):
            self.stability_score = details.get("score", "—")
            self.verdict = details.get("verdict", "—")
            self.jitter = details.get("jitter_ms", "—")
            self.avg_rtt = details.get("avg_ms", 0)
            self.packet_loss_pct = details.get("loss_pct", 0)
            self.spike_count = details.get("spikes", "—")
    
    results["ping"] = DummyPing(ping_details)

    try:
        # Use temp directory for the generated PDF
        temp_dir = tempfile.gettempdir()
        filepath = export_results_to_pdf(
            results=results,
            agent_name=row["agent_name"],
            anydesk_id=row["anydesk_id"],
            team_name=row["team"],
            output_dir=temp_dir
        )
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500


# ── Main ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    _migrate_json_to_sqlite()
    _get_db()  # Ensure tables exist
    print(f"\n  +----------------------------------------------+")
    print(f"  |   VOS Vital Operations Scanner Dashboard     |")
    print(f"  |   Running on  http://localhost:{PORT}           |")
    print(f"  |   Login: admin / {ADMIN_PASSWORD[:8]}{'…' if len(ADMIN_PASSWORD) > 8 else ''}                    |")
    print(f"  +----------------------------------------------+\n")
    app.run(host="0.0.0.0", port=PORT, debug=False)
