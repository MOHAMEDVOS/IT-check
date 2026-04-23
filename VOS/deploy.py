import requests, os

API_TOKEN = "7e56f3e0dc4e4ccef07fefca25d85138a73e2771"
USERNAME = "mohamed404"
BASE = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
PROJECT = r"c:\Users\vos\Desktop\IT check\VOS"

files = {
    "dashboard_server.py": "SysProbe/dashboard_server.py",
    "logger.py": "SysProbe/logger.py",
    "thresholds.py": "SysProbe/thresholds.py",
    os.path.join("templates", "dashboard.html"): "SysProbe/templates/dashboard.html",
    os.path.join("templates", "login.html"): "SysProbe/templates/login.html",
    os.path.join("modules", "__init__.py"): "SysProbe/modules/__init__.py",
    os.path.join("modules", "pdf_export.py"): "SysProbe/modules/pdf_export.py",
    os.path.join("modules", "email_alerts.py"): "SysProbe/modules/email_alerts.py",
}

for local, remote in files.items():
    path = os.path.join(PROJECT, local)
    if not os.path.exists(path):
        print(f"Skipping {path} - does not exist locally.")
        continue
    with open(path, "rb") as f:
        content = f.read()
    url = f"{BASE}/{remote}"
    r = requests.post(url, headers=HEADERS, files={"content": (os.path.basename(remote), content)})
    ok = "OK" if r.status_code in (200, 201) else f"FAIL({r.status_code})"
    print(f"  {ok}  {remote}")

# Reload
reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME}.pythonanywhere.com/reload/"
r = requests.post(reload_url, headers=HEADERS)
print(f"  Reload: {r.status_code}")
