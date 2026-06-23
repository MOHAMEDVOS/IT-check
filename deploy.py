import requests

TOKEN = "7e56f3e0dc4e4ccef07fefca25d85138a73e2771"
USER = "mohamed404"
HEADERS = {"Authorization": f"Token {TOKEN}"}

FILES_TO_UPLOAD = [
    (
        r"C:\Users\vos\Desktop\IT check\VOS\templates\dashboard.html",
        "/home/mohamed404/SysProbe/templates/dashboard.html",
        "dashboard.html",
    ),
    (
        r"C:\Users\vos\Desktop\IT check\VOS\modules\pdf_export.py",
        "/home/mohamed404/SysProbe/modules/pdf_export.py",
        "pdf_export.py",
    ),
]

print("========================================")
print("  VOS Dashboard Deploy to PythonAnywhere")
print("========================================\n")

# Step 1: Upload required files
print("[1/3] Uploading files...")
for local_path, remote_path, label in FILES_TO_UPLOAD:
    print(f"  Uploading {label}...")
    with open(local_path, "rb") as f:
        r = requests.post(
            f"https://www.pythonanywhere.com/api/v0/user/{USER}/files/path{remote_path}",
            headers=HEADERS,
            files={"content": f}
        )
    if r.status_code in (200, 201):
        print(f"    Upload OK ({r.status_code})")
    else:
        print(f"    Upload FAILED ({r.status_code}): {r.text}")
        input("\nPress Enter to close...")
        exit(1)

# Step 2: Reload web app
print("\n[2/3] Reloading web app...")
r = requests.post(
    f"https://www.pythonanywhere.com/api/v0/user/{USER}/webapps/{USER}.pythonanywhere.com/reload/",
    headers=HEADERS
)
if r.status_code == 200:
    print("  Reload OK")
else:
    print(f"  Reload status: {r.status_code} — {r.text}")

print("\n[3/3] Deploy complete")
print("========================================")
print("  Done! https://mohamed404.pythonanywhere.com")
print("========================================\n")
input("Press Enter to close...")
