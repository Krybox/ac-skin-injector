"""
skin_injector.py
----------------
Handles the actual injection (copying) of validated skin folders
into the target car's skins directory.

For each skin, the injector:
1. Checks if a skin with the same name already exists.
2. If a conflict exists, asks the caller how to handle it (overwrite/rename/skip).
3. Optionally creates a backup of the existing skin before overwriting.
4. Copies the entire skin folder (recursively) to the destination.
"""

import shutil
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Callable, Optional, Tuple

from models.skin import Skin
from utils.logger import log


class ConflictAction(Enum):
    """The action chosen by the user when a skin name already exists."""
    OVERWRITE = auto()
    RENAME = auto()
    SKIP = auto()


@dataclass
class InjectionRecord:
    """
    Records the outcome of attempting to inject a single skin.

    Attributes:
        skin_name : The name of the skin that was processed.
        success   : True if the skin was injected successfully.
        skipped   : True if the user chose to skip this skin.
        error     : An error message if injection failed, otherwise empty.
        final_name: The name the skin was actually saved as (may differ after rename).
    """
    skin_name: str
    success: bool = False
    skipped: bool = False
    error: str = ""
    final_name: str = ""


@dataclass
class InjectionResult:
    """Summary of an entire injection batch."""
    records: List[InjectionRecord] = field(default_factory=list)

    @property
    def succeeded(self) -> List[InjectionRecord]:
        return [r for r in self.records if r.success]

    @property
    def skipped(self) -> List[InjectionRecord]:
        return [r for r in self.records if r.skipped]

    @property
    def failed(self) -> List[InjectionRecord]:
        return [r for r in self.records if not r.success and not r.skipped]

    def summary_text(self) -> str:
        """Returns a short human-readable summary string for display in the status bar."""
        parts = []
        if self.succeeded:
            parts.append(f"{len(self.succeeded)} injected")
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped")
        if self.failed:
            parts.append(f"{len(self.failed)} failed")
        return ", ".join(parts) if parts else "Nothing to inject."


def inject_skins(
    skins: List[Skin],
    car_path: Path,
    create_backups: bool,
    retention_days: int,
    on_conflict: Callable[[str], Tuple[ConflictAction, Optional[str]]],
) -> InjectionResult:
    """
    Injects a list of skins into the given car's skins folder.

    Parameters:
        skins          : List of Skin objects to inject (only enabled ones are processed).
        car_path       : Path to the target car folder (parent of 'skins/').
        create_backups : Whether to back up existing skins before overwriting.
        retention_days : How many days to keep backups before auto-deleting.
        on_conflict    : A callback invoked when a skin name already exists.
                         Receives the skin name, returns (ConflictAction, new_name_or_None).

    Returns an InjectionResult summarising what happened to each skin.
    """
    from core.backup_manager import create_backup  # avoid circular import at module level

    skins_dir = car_path / "skins"
    skins_dir.mkdir(exist_ok=True)

    result = InjectionResult()

    for skin in skins:
        # Skip skins the user has unchecked in the list
        if not skin.enabled:
            log.debug("Skipping disabled skin: %s", skin.name)
            continue

        record = InjectionRecord(skin_name=skin.name, final_name=skin.name)
        target_path = skins_dir / skin.name

        # --- Handle naming conflict ---
        if target_path.exists():
            action, new_name = on_conflict(skin.name)

            if action == ConflictAction.SKIP:
                record.skipped = True
                log.info("User skipped skin: %s", skin.name)
                result.records.append(record)
                continue

            elif action == ConflictAction.RENAME and new_name:
                # Use a local resolved_name so we never mutate the Skin object
                # (the GUI list still holds the original name if injection fails)
                resolved_name = new_name
                record.final_name = resolved_name
                target_path = skins_dir / resolved_name
                log.info("Skin '%s' will be saved as '%s'", record.skin_name, resolved_name)
            else:
                resolved_name = skin.name

            # Back up the *existing* folder under its current on-disk name,
            # not the new name the user just chose.
            if target_path.exists() and create_backups:
                create_backup(car_path, resolved_name, retention_days)

        # --- Copy the skin folder to the destination ---
        try:
            if target_path.exists():
                shutil.rmtree(target_path)

            # Copy the entire source folder recursively including all subfolders
            shutil.copytree(skin.source_path, target_path)

            record.success = True
            log.info("Injected skin '%s' into '%s'", record.final_name or skin.name, car_path.name)

        except Exception as e:
            record.error = str(e)
            log.error("Failed to inject skin '%s': %s", skin.name, e)

        result.records.append(record)

    return result
