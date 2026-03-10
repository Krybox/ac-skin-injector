# build_release.py
# ----------------
# Assembles a release ZIP ready for upload to GitHub Releases.
#
# What it does:
#   1. Checks that dist/AC_Skin_Injector.exe exists (build first if not)
#   2. Wipes and recreates the release/ staging folder
#   3. Copies AC_Skin_Injector.exe and create_shortcut.py into it
#   4. Zips the staging folder into release/AC_Skin_Injector_vX.X.X.zip
#   5. Prints the output path and file size
#
# Usage:
#   python build_release.py
#
# Build the .exe first if needed:
#   pyinstaller build.spec

import os
import sys
import shutil
import zipfile

# ── Version ───────────────────────────────────────────────────────────────────
# Bump this before each release.
VERSION = "1.0.3"

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT          = os.path.dirname(os.path.abspath(__file__))
EXE_SRC       = os.path.join(ROOT, "dist", "AC_Skin_Injector.exe")
SHORTCUT_SRC  = os.path.join(ROOT, "create_shortcut.py")
RELEASE_DIR   = os.path.join(ROOT, "release")
STAGING_DIR   = os.path.join(RELEASE_DIR, "staging")
ZIP_NAME      = f"AC_Skin_Injector_v{VERSION}.zip"
ZIP_PATH      = os.path.join(RELEASE_DIR, ZIP_NAME)

# ── Step 1: Verify the .exe exists ────────────────────────────────────────────
print(f"Building release v{VERSION}...")
print()

if not os.path.isfile(EXE_SRC):
    print("ERROR: dist\\AC_Skin_Injector.exe not found.")
    print("Run this first:  pyinstaller build.spec")
    sys.exit(1)

print(f"  Found:  {EXE_SRC}")

# ── Step 2: Clean and recreate the staging folder ─────────────────────────────
if os.path.exists(STAGING_DIR):
    shutil.rmtree(STAGING_DIR)
os.makedirs(STAGING_DIR)

# Also remove any previous zip for this version so we don't get stale files
if os.path.exists(ZIP_PATH):
    os.remove(ZIP_PATH)

# ── Step 3: Copy files into staging ───────────────────────────────────────────
shutil.copy2(EXE_SRC,      os.path.join(STAGING_DIR, "AC_Skin_Injector.exe"))
shutil.copy2(SHORTCUT_SRC, os.path.join(STAGING_DIR, "create_shortcut.py"))

print(f"  Staged: AC_Skin_Injector.exe")
print(f"  Staged: create_shortcut.py")

# ── Step 4: Zip the staging folder ────────────────────────────────────────────
os.makedirs(RELEASE_DIR, exist_ok=True)

with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for filename in os.listdir(STAGING_DIR):
        filepath = os.path.join(STAGING_DIR, filename)
        # Store files at the root of the zip (no subfolder inside the zip)
        zf.write(filepath, arcname=filename)

# Clean up the staging folder — only the zip is needed
shutil.rmtree(STAGING_DIR)

# ── Step 5: Report ────────────────────────────────────────────────────────────
size_mb = os.path.getsize(ZIP_PATH) / (1024 * 1024)
print()
print(f"Release zip created:")
print(f"  {ZIP_PATH}")
print(f"  Size: {size_mb:.1f} MB")
print()
print("Upload this file to GitHub Releases as a release asset.")
