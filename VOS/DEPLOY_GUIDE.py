# ╔══════════════════════════════════════════════════════════════╗
# ║  SysProbe Dashboard — PythonAnywhere Deployment Guide       ║
# ╚══════════════════════════════════════════════════════════════╝
#
# Total time: ~10 minutes
# Cost: FREE (PythonAnywhere free tier)
# Result: https://yourusername.pythonanywhere.com
#
# ──────────────────────────────────────────────────────────────
# STEP 1: Create a PythonAnywhere Account
# ──────────────────────────────────────────────────────────────
#
#   1. Go to https://www.pythonanywhere.com
#   2. Click "Start running Python online in less than a minute!"
#   3. Sign up (free "Beginner" plan is fine)
#   4. Remember your username (it becomes your URL)
#
# ──────────────────────────────────────────────────────────────
# STEP 2: Upload Your Files
# ──────────────────────────────────────────────────────────────
#
#   1. Go to the "Files" tab
#   2. Create a folder: /home/yourusername/SysProbe
#   3. Upload these files into that folder:
#      - dashboard_server.py
#      - dashboard_config.json
#      - wsgi.py
#   4. Create a subfolder: /home/yourusername/SysProbe/templates
#   5. Upload into templates/:
#      - dashboard.html
#      - login.html
#   6. Create a subfolder: /home/yourusername/SysProbe/modules
#   7. Upload into modules/:
#      - email_alerts.py
#      - __init__.py   (create empty file if not present)
#
# ──────────────────────────────────────────────────────────────
# STEP 3: Install Dependencies
# ──────────────────────────────────────────────────────────────
#
#   1. Go to the "Consoles" tab
#   2. Start a "Bash" console
#   3. Run:
#
#      pip install --user flask flask-cors
#
# ──────────────────────────────────────────────────────────────
# STEP 4: Create the Web App
# ──────────────────────────────────────────────────────────────
#
#   1. Go to the "Web" tab
#   2. Click "Add a new web app"
#   3. Choose "Manual configuration"
#   4. Select Python 3.10 (or latest available)
#   5. In the "Code" section:
#      - Source code: /home/yourusername/SysProbe
#   6. Click on the "WSGI configuration file" link
#   7. DELETE all existing content, replace with:
#
#      import sys
#      sys.path.insert(0, '/home/yourusername/SysProbe')
#      from dashboard_server import app as application
#
#   8. Click "Save"
#   9. Go back to the Web tab, click "Reload"
#
# ──────────────────────────────────────────────────────────────
# STEP 5: Configure Security
# ──────────────────────────────────────────────────────────────
#
#   1. Go to Files → /home/yourusername/SysProbe/dashboard_config.json
#   2. Change these values:
#
#      {
#          "admin_password": "YOUR_STRONG_PASSWORD",
#          "api_key": "YOUR_SECRET_API_KEY",
#          "secret_key": "RANDOM_STRING_FOR_SESSIONS"
#      }
#
#   3. Reload the web app
#
# ──────────────────────────────────────────────────────────────
# STEP 6: Update Agent PCs
# ──────────────────────────────────────────────────────────────
#
#   On each agent PC, edit config.json:
#
#   {
#       "dashboard_url": "https://yourusername.pythonanywhere.com",
#       "api_key": "YOUR_SECRET_API_KEY"
#   }
#
# ──────────────────────────────────────────────────────────────
# DONE! Visit https://yourusername.pythonanywhere.com
# Login with your admin password to see all agent results.
# ──────────────────────────────────────────────────────────────
#
# NOTES:
# - Free tier allows 1 web app
# - SQLite database is stored at /home/yourusername/SysProbe/team_results.db
# - To update: upload new files via Files tab, then Reload
# - Free tier has outbound HTTP restrictions (whitelist needed for SMTP)
