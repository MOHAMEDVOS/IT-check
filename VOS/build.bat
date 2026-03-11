@echo off
echo ============================================
echo  VOS Build Script
echo ============================================

python -m PyInstaller ^
  --noconsole ^
  --onefile ^
  --name VOS ^
  --icon "assets\IT.ico" ^
  --add-data "assets;assets" ^
  --add-data "gui;gui" ^
  --add-data "thresholds.py;." ^
  --add-data "logger.py;." ^
  --distpath "Release" ^
  --hidden-import=pycaw.pycaw ^
  --hidden-import=pycaw.constants ^
  --hidden-import=pycaw.magic ^
  --hidden-import=comtypes.stream ^
  --hidden-import=comtypes._cominterface_items ^
  --hidden-import=comtypes.server.localserver ^
  --hidden-import=cpuinfo ^
  --hidden-import=pkg_resources.py2_warn ^
  --hidden-import=winreg ^
  --hidden-import=psutil._pswindows ^
  --hidden-import=GPUtil ^
  --hidden-import=gui ^
  --hidden-import=gui.cards ^
  --hidden-import=gui.dialogs ^
  --hidden-import=gui.theme ^
  --collect-all pycaw ^
  --collect-all comtypes ^
  main.py

echo.
echo ============================================
if exist dist\VOS.exe (
  echo  BUILD SUCCESSFUL — dist\VOS.exe ready
) else (
  echo  BUILD FAILED — check output above
)
echo ============================================
pause
