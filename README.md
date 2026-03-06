# Assetto Corsa Skin Injector

A portable Windows tool for installing car skins into Assetto Corsa.
No Python, no installation, no setup — just download and run.

## Download

Go to the [Releases page](../../releases) and download `AC_Skin_Injector_vX.X.X.zip` from the latest release.

Extract the zip to any folder on your PC — for example `C:\Tools\AC_Skin_Injector\` or your Desktop.

> **Do not extract into `C:\Program Files\`** — Windows blocks apps in that folder from writing their config and log files next to the `.exe`.

Double-click `AC_Skin_Injector.exe` to launch. Config and logs are created automatically next to the `.exe` on first run (fully portable — move the folder anywhere you like).

### Optional: create a Desktop shortcut

Run `create_shortcut.py` once (Python required) to create a shortcut on your Desktop:
```
python create_shortcut.py
```

Or just right-click `AC_Skin_Injector.exe` → **Send to → Desktop (create shortcut)**.

## Features

- Auto-detects your Assetto Corsa installation via Steam
- Accepts skin **folders** and **ZIP files** (drag & drop supported)
- Scans ZIPs automatically — finds every skin inside by looking for `livery.png`
- Conflict handling — when a skin already exists, choose to **Overwrite**, **Rename**, or **Skip**
- Timestamped **backups** before overwriting, auto-deleted after 30 days
- **Restore** any backup via the Manage Backups dialog
- Validation warnings for missing `preview.jpg` or `ui_skin.json`
- Preview thumbnails in the skin list
- Light and dark mode

## How to use

1. Launch `AC_Skin_Injector.exe`
2. Select a car from the dropdown
3. Add skins by:
   - Clicking **Add ZIP / Folder...**, or
   - Dragging and dropping a folder or ZIP onto the skin list
4. Check the skins you want to inject
5. Click **Inject Skins**

### ZIP files

The app scans ZIPs for `livery.png` to find skin folders automatically.
Each folder containing a `livery.png` is treated as one skin.

### Conflicts

If a skin with the same name already exists you will be asked to choose:
- **Overwrite** — replace the existing skin (a backup is created first if backups are enabled)
- **Rename** — install it under a different name
- **Skip** — leave the existing skin untouched

### Backups

Before overwriting, the original skin is backed up to `skins\.ac_skin_backups\`.
Backups older than 30 days are removed automatically on launch.
Use **Manage Backups** to browse and restore any backup.

## Building from source

**Requirements:** Python 3.14, and the packages in `requirements.txt`.

```
pip install -r requirements.txt
```

Generate the icon (only needed once):
```
python generate_icon.py
```

Build the executable:
```
pyinstaller build.spec
```

Assemble the release zip:
```
python build_release.py
```

Output: `release\AC_Skin_Injector_vX.X.X.zip` — contains the `.exe` and `create_shortcut.py`, ready to upload to GitHub Releases.

## Running tests

```
python -m unittest test_core -v
python test_gui.py
```
