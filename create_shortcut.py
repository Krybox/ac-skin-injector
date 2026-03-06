# create_shortcut.py
# ------------------
# One-time helper script: creates "Assetto Corsa Skin Injector.lnk" on the
# Windows Desktop pointing to dist\AC_Skin_Injector.exe.
#
# Uses only Python stdlib (ctypes + comtypes-free IShellLink via COM).
# Run once after building the .exe:
#   python create_shortcut.py

import os
import sys
import ctypes
import ctypes.wintypes

# ── Resolve paths ────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
EXE_PATH    = os.path.join(SCRIPT_DIR, "dist", "AC_Skin_Injector.exe")
WORK_DIR    = os.path.join(SCRIPT_DIR, "dist")
ICON_PATH   = os.path.join(SCRIPT_DIR, "resources", "icons", "app_icon.ico")
SHORTCUT_NAME = "Assetto Corsa Skin Injector.lnk"

# Desktop path via Windows API (works for all locales / custom desktop locations)
CSIDL_DESKTOP = 0
buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, 0, buf)
DESKTOP = buf.value
SHORTCUT_PATH = os.path.join(DESKTOP, SHORTCUT_NAME)

# ── Validation ────────────────────────────────────────────────────────────────
if not os.path.isfile(EXE_PATH):
    print(f"ERROR: Executable not found: {EXE_PATH}")
    print("Build the project first with:  pyinstaller build.spec")
    sys.exit(1)

# ── COM / IShellLink shortcut creation ────────────────────────────────────────
# We use Windows Script Host via the shell32 COM object through ctypes,
# accessed via the 'comtypes'-free approach: PowerShell as a subprocess.
# This avoids needing pywin32 or comtypes installed.

import subprocess

# Build a small PowerShell one-liner that creates the shortcut
ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('{SHORTCUT_PATH.replace("'", "''")}')
$sc.TargetPath    = '{EXE_PATH.replace("'", "''")}'
$sc.WorkingDirectory = '{WORK_DIR.replace("'", "''")}'
$sc.IconLocation  = '{ICON_PATH.replace("'", "''")}',0
$sc.Description   = 'Assetto Corsa Skin Injector'
$sc.Save()
Write-Host 'OK'
""".strip()

result = subprocess.run(
    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
    capture_output=True,
    text=True,
)

if result.returncode == 0 and "OK" in result.stdout:
    print(f"Shortcut created: {SHORTCUT_PATH}")
else:
    print("ERROR: PowerShell shortcut creation failed.")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    sys.exit(1)
