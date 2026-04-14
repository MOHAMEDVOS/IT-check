import requests

TOKEN = "7e56f3e0dc4e4ccef07fefca25d85138a73e2771"
USER = "mohamed404"
HEADERS = {"Authorization": f"Token {TOKEN}"}
REMOTE_PATH = "/home/mohamed404/SysProbe/VOS/templates/dashboard.html"
LOCAL_PATH = r"C:\Users\vos\Desktop\IT check\VOS\templates\dashboard.html"

print("========================================")
print("  VOS Dashboard Deploy to PythonAnywhere")
print("========================================\n")

# Step 1: Upload dashboard.html
print("[1/2] Uploading dashboard.html...")
with open(LOCAL_PATH, "rb") as f:
    r = requests.post(
        f"https://www.pythonanywhere.com/api/v0/user/{USER}/files/path{REMOTE_PATH}",
        headers=HEADERS,
        files={"content": f}
    )
if r.status_code in (200, 201):
    print(f"  Upload OK ({r.status_code})")
else:
    print(f"  Upload FAILED ({r.status_code}): {r.text}")
    input("\nPress Enter to close...")
    exit(1)

# Step 2: Reload web app
print("\n[2/2] Reloading web app...")
r = requests.post(
    f"https://www.pythonanywhere.com/api/v0/user/{USER}/webapps/{USER}.pythonanywhere.com/reload/",
    headers=HEADERS
)
if r.status_code == 200:
    print("  Reload OK")
else:
    print(f"  Reload status: {r.status_code} — {r.text}")

print("\n========================================")
print("  Done! https://mohamed404.pythonanywhere.com")
print("========================================\n")
input("Press Enter to close...")
