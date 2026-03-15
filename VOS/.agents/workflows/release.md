---
description: How to push a new VOS update correctly
---

# 🚀 VOS Release Workflow

Follow these steps to release a new version of VOS and ensure all users get the update notification.

### 1. Update Version Code
Open `thresholds.py` and update the `APP_VERSION` string.
> [!IMPORTANT]
> Use a standard format like `2.7.0`. Avoid "v" prefixes in this file.

### 2. Build the Executable
Run the `build.bat` file.
```powershell
.\build.bat
```
This script will:
- Compile the code into `Release\VOS.exe`.
- Automatically copy it to `..\public\downloads\vos.exe`.

### 3. Update Version Manifest
Open `..\public\downloads\version.json` and update:
- `latest_version`: Must match the version in `thresholds.py`.
- `release_notes`: Brief description of what's new.
- `_timestamp`: Set to current date/time to force GitHub to refresh its cache.

### 4. Stage and Push to GitHub
Run these commands in your terminal from the `VOS` folder:

// turbo
```powershell
# 1. Stage everything (Code, Version files, and the new EXE)
git add . ..\public\downloads\

# 2. Commit the changes
git commit -m "v2.x.x: Your release summary"

# 3. Push to main
git push origin main
```

### 5. Verify
Wait 1-2 minutes and check the raw URL in your browser:  
`https://raw.githubusercontent.com/MOHAMEDVOS/IT-check/main/public/downloads/version.json`

If it shows your new version, all users will get the update notification!
