# create_shortcut.py
# ------------------
# One-time helper script: creates "Assetto Corsa Skin Injector.lnk" on the
# Windows Desktop pointing to AC_Skin_Injector.exe in the same folder.
#
# Extract the release zip anywhere (except Program Files), then run:
#   python create_shortcut.py
#
# No extra dependencies needed — uses only Python stdlib.

import os
import sys
import subprocess
import ctypes
import ctypes.wintypes

# ── Resolve paths ─────────────────────────────────────────────────────────────
# All paths are relative to wherever this script lives, so the zip can be
# extracted anywhere and it will still work correctly.
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
EXE_PATH      = os.path.join(SCRIPT_DIR, "AC_Skin_Injector.exe")
WORK_DIR      = SCRIPT_DIR
# Use the icon embedded inside the .exe itself — no separate .ico file needed
ICON_LOCATION = EXE_PATH + ",0"
SHORTCUT_NAME = "Assetto Corsa Skin Injector.lnk"

# Resolve the Desktop path via the Windows API so it works for all locales
# and for users who have moved their Desktop to a custom location.
CSIDL_DESKTOP = 0
buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, 0, buf)
DESKTOP       = buf.value
SHORTCUT_PATH = os.path.join(DESKTOP, SHORTCUT_NAME)

# ── Validate ──────────────────────────────────────────────────────────────────
if not os.path.isfile(EXE_PATH):
    print(f"ERROR: Could not find AC_Skin_Injector.exe in:\n  {SCRIPT_DIR}")
    print("Make sure create_shortcut.py is in the same folder as the .exe.")
    sys.exit(1)

# ── Create the shortcut via PowerShell WScript.Shell ─────────────────────────
# PowerShell's WScript.Shell COM object is available on every modern Windows
# install and requires no extra dependencies.
ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('{SHORTCUT_PATH.replace("'", "''")}')
$sc.TargetPath       = '{EXE_PATH.replace("'", "''")}'
$sc.WorkingDirectory = '{WORK_DIR.replace("'", "''")}'
$sc.IconLocation     = '{ICON_LOCATION.replace("'", "''")}'
$sc.Description      = 'Assetto Corsa Skin Injector'
$sc.Save()
Write-Host 'OK'
""".strip()

result = subprocess.run(
    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
    capture_output=True,
    text=True,
)

if result.returncode == 0 and "OK" in result.stdout:
    print(f"Shortcut created on Desktop: {SHORTCUT_PATH}")
else:
    print("ERROR: Could not create the shortcut.")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    sys.exit(1)
