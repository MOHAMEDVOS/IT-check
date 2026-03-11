import requests
import sqlite3

API_TOKEN = "7e56f3e0dc4e4ccef07fefca25d85138a73e2771"
USERNAME = "mohamed404"
db_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/SysProbe/team_results.db"

headers = {"Authorization": f"Token {API_TOKEN}"}
resp = requests.get(db_url, headers=headers)

if resp.status_code == 200:
    with open("dist/downloaded_team_results.db", "wb") as f:
        f.write(resp.content)
    
    # Read DB
    conn = sqlite3.connect("dist/downloaded_team_results.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT agent_name, last_checked FROM results").fetchall()
    print("Database agents:")
    for r in rows:
        print(f" - {r['agent_name']}: {r['last_checked']}")
    conn.close()
else:
    print(f"Failed to fetch DB: {resp.status_code}")
