import requests
import json

API_TOKEN = "7e56f3e0dc4e4ccef07fefca25d85138a73e2771"
USERNAME = "mohamed404"
DOMAIN = f"{USERNAME}.pythonanywhere.com"

# API URL for access log
log_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/var/log/{DOMAIN}.access.log"

headers = {"Authorization": f"Token {API_TOKEN}"}
resp = requests.get(log_url, headers=headers)

if resp.status_code == 200:
    lines = resp.text.splitlines()
    print("----- ALL POST REQUESTS -----")
    for line in lines:
        if '"POST ' in line:
            print(line)
else:
    print(f"Failed to fetch logs: {resp.status_code} - {resp.text}")
