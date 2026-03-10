# Changelog

All notable changes to this project will be documented in this file.

## v1.0.3 – 2026-03-10

### Polish

- Added `-> None` return annotations to all void methods across `main_window`, `skin_list_widget`, `backup_manager`, and `skin_validator`
- Defined `APP_VERSION` constant in `main.py` and imported it into `main_window.py` — version string is no longer duplicated/hardcoded
- Removed unused `QLabel#sectionLabel` and `QLabel#dropZoneLabel` CSS rules from both light and dark themes in `styles.py`
- Fixed `_rebuild_validation_index()` in `skin_list_widget.py` — previously dropped validation entries for rows below a deleted row; now correctly remaps all surviving entries to their new indices

## v1.0.2 – 2026-03-10

### Robustness

- Added `CANCEL` to `ConflictAction` enum; injection loop now aborts immediately when the user cancels a rename dialog instead of silently skipping
- `ConflictDialog` defaults to `CANCEL` on window close (X button) rather than leaving action undefined
- Rename-cancel in `main_window` returns `CANCEL` instead of `SKIP`
- Expired-backup cleanup moved to a single startup call (`_cleanup_all_backups`) across all cars — no longer runs on every car dropdown change
- Batched multiple unsupported-file warnings into one dialog instead of one per file
- Backup retention label reads the value from config rather than hardcoding "30 days"
- `get_available_backups` now returns `List[BackupInfo]`; `restore_backup` accepts `BackupInfo`
- `car_scanner.get_car_list` now returns `List[CarEntry]`
- `ValidationResult.is_valid` defaults to `False`; `skin_validator` explicitly sets it to `True` once `livery.png` is confirmed
- Config property fallbacks now reference `DEFAULT_CONFIG` instead of duplicate literals
- New `src/models/types.py` module defining `CarEntry` and `BackupInfo` shared types

## v1.0.1 – 2026-03-10

### Bug fixes

- `get_base_dir()` consolidated into `utils/logger.py` as the single source of truth — removed duplicate definitions from `utils/config.py` and `core/zip_handler.py`
- Skin injection RENAME branch now uses a local `resolved_name` variable instead of mutating `skin.name`, preventing the name change from persisting if injection fails
- Backup `datetime.now()` captured once per backup operation so the folder name and both metadata timestamps (`created`, `expires`) are always in sync
- `car_scanner` now imports `BACKUP_FOLDER_NAME` from `backup_manager` instead of hardcoding the string `".ac_skin_backups"`

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
