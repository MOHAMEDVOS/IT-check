
import sys
import os

# Add the current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from modules.speed import get_network_name, get_connection_type
    
    print("Testing Network Detection Fix...")
    print("-" * 30)
    
    conn_type = get_connection_type()
    net_name = get_network_name()
    
    print(f"Detected Connection Type : {conn_type}")
    print(f"Detected Network Name    : {net_name}")
    print("-" * 30)
    
    if net_name != "Unknown":
        print("RESULT: SUCCESS - Network name identified.")
    else:
        print("RESULT: FAILED - Network name is still 'Unknown'.")

except Exception as e:
    print(f"Test crashed: {e}")
