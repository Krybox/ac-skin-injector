# -*- mode: python ; coding: utf-8 -*-
# build.spec
# ----------
# PyInstaller configuration for the AC Skin Injector.
# Produces a single portable .exe with no console window.
#
# To build: pyinstaller build.spec
# Output:   dist/AC_Skin_Injector.exe

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],                     # Tell PyInstaller where to find our modules
    binaries=[],
    datas=[
        # Bundle the resources folder into the executable
        ('resources/default_preview.png', 'resources'),
        ('resources/icons',               'resources/icons'),
    ],
    hiddenimports=[
        'vdf',
        'PIL',
        'PIL.Image',
        'winreg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AC_Skin_Injector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No black console window — GUI only
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/app_icon.ico',    # App icon shown in File Explorer and taskbar
)
