"""
types.py
--------
Shared type aliases and TypedDicts used across multiple modules.

Keeping these here avoids circular imports and gives all string-keyed
dictionaries a single, authoritative schema.
"""

from pathlib import Path
from typing import Tuple
from typing_extensions import TypedDict


# A (folder_name, display_name) pair representing a car in the dropdown.
# folder_name : the actual directory name on disk (e.g. 'ks_ferrari_458')
# display_name: the human-readable name from ui_car.json (e.g. 'Ferrari 458 Italia')
CarEntry = Tuple[str, str]


class BackupInfo(TypedDict):
    """
    Describes a single backup entry returned by backup_manager.get_available_backups().

    Keys:
        backup_name  : The timestamped folder name inside .ac_skin_backups/.
        original_name: The skin folder name the backup was taken from.
        created      : ISO 8601 datetime string of when the backup was made.
        expires      : ISO 8601 datetime string of when the backup will be auto-deleted.
        path         : Absolute Path to the backup folder on disk.
    """
    backup_name: str
    original_name: str
    created: str
    expires: str
    path: Path
