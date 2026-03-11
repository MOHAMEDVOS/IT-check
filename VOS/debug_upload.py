import requests
import time
import threading

UPLOAD_URL = "https://speed.cloudflare.com/__up"
TIMEOUT = 30

def test_upload():
    data = b"0" * 5_000_000 # 5 MB
    try:
        print("Starting upload...")
        start = time.perf_counter()
        resp = requests.post(
            UPLOAD_URL, 
            data=data, 
            timeout=TIMEOUT,
            headers={"Content-Type": "application/octet-stream"}
        )
        elapsed = time.perf_counter() - start
        print(f"Status Code: {resp.status_code}")
        if elapsed > 0:
            speed = (len(data) * 8) / (elapsed * 1_000_000)
            print(f"Upload Speed: {speed:.2f} Mbps")
        else:
            print("Elapsed time is zero.")
    except Exception as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    test_upload()
