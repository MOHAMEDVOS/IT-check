import subprocess
import time
import sys
import os

def test_background_flag():
    print("Testing VOS with --background flag...")
    
    # Path to the script we want to test
    script_path = os.path.join(os.getcwd(), "main.py")
    
    # 1. Start the first instance in background mode
    print("Launching first instance with --background...")
    proc1 = subprocess.Popen([sys.executable, script_path, "--background"], 
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    
    time.sleep(5) # Wait for it to initialize and grab the mutex
    
    # 2. Try to launch a second instance with --background
    print("Launching second instance with --background (should exit immediately without restoring proc1)...")
    start_time = time.time()
    proc2 = subprocess.run([sys.executable, script_path, "--background"], timeout=10)
    end_time = time.time()
    
    print(f"Second instance exited with code: {proc2.returncode}")
    print(f"Time taken for second instance: {end_time - start_time:.2f}s")
    
    if proc2.returncode == 0:
        print("SUCCESS: Second instance exited quietly.")
    else:
        print(f"FAILURE: Second instance exited with code {proc2.returncode}")

    # Cleanup
    print("Cleaning up...")
    proc1.terminate()

if __name__ == "__main__":
    test_background_flag()
