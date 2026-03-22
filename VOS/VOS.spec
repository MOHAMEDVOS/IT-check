# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('assets', 'assets'), ('gui', 'gui'), ('thresholds.py', '.'), ('logger.py', '.')]
binaries = []
hiddenimports = ['pycaw.pycaw', 'pycaw.constants', 'pycaw.magic', 'comtypes.stream', 'comtypes._cominterface_items', 'comtypes.server.localserver', 'cpuinfo', 'pkg_resources.py2_warn', 'winreg', 'psutil._pswindows', 'GPUtil', 'gui', 'gui.cards', 'gui.dialogs', 'gui.theme']
tmp_ret = collect_all('pycaw')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('comtypes')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\IT.ico'],
)
