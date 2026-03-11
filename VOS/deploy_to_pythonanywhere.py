"""
Upload all SysProbe dashboard files to PythonAnywhere via their API.
Run once to deploy, then delete this script.
"""
import requests
import os

API_TOKEN = "7e56f3e0dc4e4ccef07fefca25d85138a73e2771"
USERNAME = "mohamed404"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Files to upload with their remote paths
FILES = {
    "dashboard_server.py": "SysProbe/dashboard_server.py",
    "wsgi.py": "SysProbe/wsgi.py",
    os.path.join("templates", "dashboard.html"): "SysProbe/templates/dashboard.html",
    os.path.join("templates", "login.html"): "SysProbe/templates/login.html",
    os.path.join("modules", "email_alerts.py"): "SysProbe/modules/email_alerts.py",
    os.path.join("modules", "__init__.py"): "SysProbe/modules/__init__.py",
}


def upload_file(local_rel_path, remote_rel_path):
    local_path = os.path.join(PROJECT_DIR, local_rel_path)
    url = f"{BASE_URL}/{remote_rel_path}"

    with open(local_path, "rb") as f:
        content = f.read()

    resp = requests.post(url, headers=HEADERS, files={"content": (os.path.basename(remote_rel_path), content)})
    status = "✓" if resp.status_code in (200, 201) else f"✗ ({resp.status_code})"
    print(f"  {status}  {remote_rel_path}")
    if resp.status_code not in (200, 201):
        print(f"       {resp.text[:200]}")
    return resp.status_code in (200, 201)


def upload_content(content, remote_rel_path):
    url = f"{BASE_URL}/{remote_rel_path}"
    resp = requests.post(url, headers=HEADERS, files={"content": (os.path.basename(remote_rel_path), content.encode("utf-8"))})
    status = "✓" if resp.status_code in (200, 201) else f"✗ ({resp.status_code})"
    print(f"  {status}  {remote_rel_path}")
    if resp.status_code not in (200, 201):
        print(f"       {resp.text[:200]}")
    return resp.status_code in (200, 201)


def reload_webapp():
    print(f"\n  Reloading web app...")
    domain = f"{USERNAME}.pythonanywhere.com"
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{domain}/reload/"
    resp = requests.post(url, headers=HEADERS)
    if resp.status_code == 200:
        print("  ✓  Web app reloaded successfully.")
    else:
        print(f"  ✗  Reload failed: {resp.status_code} {resp.text}")


if __name__ == "__main__":
    import json

    print("\n  ╔══════════════════════════════════════════════╗")
    print("  ║  Deploying SysProbe to PythonAnywhere...     ║")
    print("  ╚══════════════════════════════════════════════╝\n")

    # Upload all files
    ok = 0
    total = len(FILES)
    for local, remote in FILES.items():
        if upload_file(local, remote):
            ok += 1

    # Upload dashboard_config.json with strong defaults
    config = {
        "admin_password": "sysprobe2024",
        "api_key": "vos-default-key",
        "secret_key": "pythonanywhere-session-secret-change-me",
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "alert_recipients": [],
        "alert_from": "",
    }
    if upload_content(json.dumps(config, indent=2), "SysProbe/dashboard_config.json"):
        ok += 1
    total += 1

    print(f"\n  Uploaded {ok}/{total} files successfully.")

    if ok == total:
        reload_webapp()
        print("\n  All files uploaded and app reloaded! Visit:")
        print(f"  https://{USERNAME}.pythonanywhere.com")
