"""
backup_manager.py
-----------------
Manages backups of existing skins before they are overwritten.

Backups are stored in a hidden '.ac_skin_backups' folder inside the car's
skins directory. Each backup is a timestamped copy of the skin folder.
A 'backup_metadata.json' file tracks creation and expiry dates.

Backups older than the configured retention period (default: 30 days)
are automatically deleted on every app launch and before new backups are made.
"""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from utils.logger import log
from models.types import BackupInfo

# Name of the hidden backup folder inside each car's skins directory
BACKUP_FOLDER_NAME = ".ac_skin_backups"
METADATA_FILE_NAME = "backup_metadata.json"


def get_backup_dir(car_path: Path) -> Path:
    """Returns the path to the backup folder for a given car's skins directory."""
    return car_path / "skins" / BACKUP_FOLDER_NAME


def get_metadata_path(car_path: Path) -> Path:
    """Returns the path to the backup metadata JSON file for a given car."""
    return get_backup_dir(car_path) / METADATA_FILE_NAME


def _load_metadata(car_path: Path) -> Dict:
    """
    Loads the backup metadata from disk.
    Returns an empty dict if the file doesn't exist or can't be parsed.
    """
    meta_path = get_metadata_path(car_path)
    if not meta_path.exists():
        return {}
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning("Could not read backup metadata for %s: %s", car_path.name, e)
        return {}


def _save_metadata(car_path: Path, metadata: Dict):
    """Writes the backup metadata dictionary to disk as JSON."""
    meta_path = get_metadata_path(car_path)
    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
    except Exception as e:
        log.error("Could not save backup metadata for %s: %s", car_path.name, e)


def create_backup(car_path: Path, skin_name: str, retention_days: int = 30) -> bool:
    """
    Creates a timestamped backup of an existing skin folder before it is overwritten.

    The backup is stored at: skins/.ac_skin_backups/{skin_name}_{timestamp}/
    Metadata records the original name, creation time, and expiry time.

    Returns True if the backup was created successfully, False otherwise.
    """
    source = car_path / "skins" / skin_name

    if not source.is_dir():
        log.debug("No existing skin to back up: %s", source)
        return False

    # Create the backup directory if it doesn't exist yet
    backup_dir = get_backup_dir(car_path)
    backup_dir.mkdir(exist_ok=True)

    # Capture the timestamp once so the folder name and metadata are always in sync
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    backup_name = f"{skin_name}_{timestamp}"
    backup_dest = backup_dir / backup_name

    try:
        shutil.copytree(source, backup_dest)
        log.info("Backup created: %s", backup_dest)
    except Exception as e:
        log.error("Failed to create backup for '%s': %s", skin_name, e)
        return False

    # Record this backup in the metadata file
    metadata = _load_metadata(car_path)
    metadata[backup_name] = {
        "original_name": skin_name,
        "created": now.isoformat(),
        "expires": (now + timedelta(days=retention_days)).isoformat(),
    }
    _save_metadata(car_path, metadata)

    return True


def cleanup_old_backups(car_path: Path) -> int:
    """
    Deletes all backups that have passed their expiry date.
    Runs automatically on app launch and before creating new backups.

    Returns the number of backups that were deleted.
    """
    metadata = _load_metadata(car_path)
    if not metadata:
        return 0

    now = datetime.now()
    deleted_count = 0
    keys_to_remove = []

    for backup_name, info in metadata.items():
        try:
            expires = datetime.fromisoformat(info.get("expires", ""))
        except (ValueError, TypeError):
            # Corrupt expiry date — mark for removal
            keys_to_remove.append(backup_name)
            continue

        if now > expires:
            backup_path = get_backup_dir(car_path) / backup_name
            if backup_path.is_dir():
                try:
                    shutil.rmtree(backup_path)
                    log.info("Deleted expired backup: %s", backup_name)
                    deleted_count += 1
                except Exception as e:
                    log.warning("Could not delete backup %s: %s", backup_name, e)
                    continue
            keys_to_remove.append(backup_name)

    # Remove expired entries from metadata and save
    for key in keys_to_remove:
        metadata.pop(key, None)

    if keys_to_remove:
        _save_metadata(car_path, metadata)

    return deleted_count


def get_available_backups(car_path: Path) -> List[BackupInfo]:
    """
    Returns a list of available backups for the given car, sorted by creation date
    (newest first). Each entry is a dict with: backup_name, original_name, created, expires.
    Used to populate the Restore from Backup dialog.
    """
    metadata = _load_metadata(car_path)
    backups = []

    for backup_name, info in metadata.items():
        backup_path = get_backup_dir(car_path) / backup_name
        # Only include backups whose folder still exists on disk
        if backup_path.is_dir():
            backups.append(BackupInfo(
                backup_name=backup_name,
                original_name=info.get("original_name", backup_name),
                created=info.get("created", ""),
                expires=info.get("expires", ""),
                path=backup_path,
            ))

    # Sort newest first
    backups.sort(key=lambda x: x["created"], reverse=True)
    return backups


def restore_backup(backup_info: BackupInfo, car_path: Path) -> bool:
    """
    Restores a backup by copying it back to the active skins folder.

    If a skin with the same name already exists, it will be overwritten.
    The backup folder itself is NOT deleted after restore (user may want to keep it).

    Parameters:
        backup_info: A dict from get_available_backups() describing the backup.
        car_path   : The path to the car folder (parent of 'skins/').

    Returns True on success, False on failure.
    """
    source = backup_info["path"]
    target_name = backup_info["original_name"]
    target = car_path / "skins" / target_name

    try:
        # Remove existing skin folder if it's already there
        if target.exists():
            shutil.rmtree(target)

        shutil.copytree(source, target)
        log.info("Restored backup '%s' to '%s'", backup_info["backup_name"], target)
        return True
    except Exception as e:
        log.error("Failed to restore backup '%s': %s", backup_info["backup_name"], e)
        return False
