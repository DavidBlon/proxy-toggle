# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Python 3.14 on Windows may not expose its bundled Tcl/Tk paths to
# PyInstaller automatically. Set them before Analysis so the tkinter hook can
# collect both the Python module and the Tcl/Tk runtime files.
_tcl_root = os.path.join(sys.base_prefix, 'tcl')
_tcl_library = os.path.join(_tcl_root, 'tcl8.6')
_tk_library = os.path.join(_tcl_root, 'tk8.6')
if os.path.isfile(os.path.join(_tcl_library, 'init.tcl')):
    os.environ['TCL_LIBRARY'] = _tcl_library
if os.path.isfile(os.path.join(_tk_library, 'tk.tcl')):
    os.environ['TK_LIBRARY'] = _tk_library

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/proxy_toggle.ico', 'assets')],
    hiddenimports=[],
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
    name='ProxyToggle',
    icon='assets/proxy_toggle.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
