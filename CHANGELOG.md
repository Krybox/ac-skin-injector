# Changelog

All notable changes to this project will be documented in this file.

## v1.0.0 – 2026-03-06

### Initial release

- Auto-detects Assetto Corsa installation via Steam
- Supports skin folders and ZIP files as input
- Drag and drop ZIP files and folders onto the skin list
- Automatically scans ZIPs for skins by detecting `livery.png`
- Validates skins — rejects missing `livery.png`, warns on missing `preview.jpg` or `ui_skin.json`
- Conflict handling — when a skin already exists, choose to Overwrite, Rename, or Skip
- Timestamped backups before overwriting, auto-deleted after 30 days
- Restore any backup via the Manage Backups dialog
- Preview thumbnails (128×128) shown in the skin list
- Light and dark mode, persisted across sessions
- Portable — config and logs stored next to the `.exe`, no installation required
