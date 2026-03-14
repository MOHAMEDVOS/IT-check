
import subprocess
import re

def original_logic():
    ps_cmd = (
        "Get-NetConnectionProfile | "
        "Sort-Object IPv4Connectivity -Descending | "
        "Select-Object -ExpandProperty Name"
    )
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
    try:
        # Original: output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
        raw = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, creationflags=0x08000000) # CREATE_NO_WINDOW
        print(f"Raw bytes: {raw}")
        output = raw.decode().strip()
        print(f"Decoded: {output}")
        return output
    except Exception as e:
        print(f"Error in original logic: {e}")
        return "Unknown"

def fixed_logic():
    ps_cmd = (
        "Get-NetConnectionProfile | "
        "Sort-Object IPv4Connectivity -Descending | "
        "Select-Object -ExpandProperty Name"
    )
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
    try:
        raw = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, creationflags=0x08000000)
        # Try multiple decodings
        output = ""
        for enc in ['utf-8', 'cp1252', 'cp1256', 'latin-1']:
            try:
                output = raw.decode(enc).strip()
                if output: break
            except:
                continue
        if not output:
            output = raw.decode(errors='replace').strip()
        print(f"Fixed Decode: {output}")
        return output
    except Exception as e:
        print(f"Error in fixed logic: {e}")
        return "Unknown"

print("--- Original ---")
original_logic()
print("\n--- Fixed ---")
fixed_logic()
