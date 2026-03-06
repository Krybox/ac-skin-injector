"""
skin_validator.py
-----------------
Validates a skin folder before injection.

Rules:
- REQUIRED : livery.png must be present. Without it the skin is invalid.
- WARNING  : preview.jpg is missing (skin won't show a thumbnail in-game).
- WARNING  : ui_skin.json is missing (skin won't have metadata in-game).
- WARNING  : ui_skin.json exists but contains invalid JSON.

Everything else in the skin folder (custom .dds textures, subfolders, etc.)
is completely ignored — we never inspect or restrict those files.
"""

import json
from pathlib import Path

from models.validation_result import ValidationResult
from utils.logger import log


def validate_skin(skin_path: Path) -> ValidationResult:
    """
    Checks a skin folder and returns a ValidationResult describing any issues.

    Parameters:
        skin_path: The folder containing the skin's files (livery.png, preview.jpg, etc.)

    Returns:
        A ValidationResult with is_valid=True if livery.png exists,
        False otherwise. Warnings are added for missing optional files.
    """
    result = ValidationResult()

    if not skin_path.is_dir():
        result.add_error(f"Skin folder does not exist: {skin_path}")
        return result

    # --- Required: livery.png ---
    livery = skin_path / "livery.png"
    if livery.exists():
        result.has_livery = True
        log.debug("livery.png found for skin: %s", skin_path.name)
    else:
        result.add_error(
            "Missing 'livery.png'. This file is required for the skin to work in-game."
        )
        log.warning("No livery.png in skin: %s", skin_path.name)
        # No point checking further if the skin is already invalid
        return result

    # --- Optional: preview.jpg ---
    preview = skin_path / "preview.jpg"
    if preview.exists():
        result.has_preview = True
    else:
        result.add_warning(
            "Missing 'preview.jpg'. The skin will have no thumbnail in the car selection menu."
        )
        log.debug("No preview.jpg in skin: %s", skin_path.name)

    # --- Optional: ui_skin.json ---
    ui_json = skin_path / "ui_skin.json"
    if ui_json.exists():
        result.has_ui_json = True
        # Validate that the JSON is parseable
        _validate_ui_skin_json(ui_json, result)
    else:
        result.add_warning(
            "Missing 'ui_skin.json'. The skin won't have a name, author, or number in-game."
        )
        log.debug("No ui_skin.json in skin: %s", skin_path.name)

    return result


def _validate_ui_skin_json(json_path: Path, result: ValidationResult):
    """
    Attempts to parse ui_skin.json and adds a warning if it's not valid JSON.
    We only check that the file is parseable — we don't enforce which fields exist.
    """
    try:
        with open(json_path, "r", encoding="utf-8", errors="replace") as f:
            json.load(f)
    except json.JSONDecodeError as e:
        result.add_warning(f"'ui_skin.json' contains invalid JSON: {e}")
        log.debug("Invalid ui_skin.json in %s: %s", json_path.parent.name, e)
