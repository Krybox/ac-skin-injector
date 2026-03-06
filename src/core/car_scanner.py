"""
car_scanner.py
--------------
Scans the Assetto Corsa 'content/cars' directory and builds a list of
all available cars. Each car is represented by its folder name and,
if available, its human-readable display name from ui_car.json.
"""

from pathlib import Path
from typing import List, Tuple
import json

from utils.logger import log


def get_car_list(cars_path: Path) -> List[Tuple[str, str]]:
    """
    Scans the given cars directory and returns a list of (folder_name, display_name) tuples.

    - folder_name : The actual folder name used in the file system (e.g. 'ks_ferrari_458').
    - display_name: A friendly name read from ui_car.json, or the folder name if unavailable.

    The list is sorted alphabetically by display name for easy browsing.
    """
    if not cars_path.is_dir():
        log.error("Cars path does not exist or is not a directory: %s", cars_path)
        return []

    cars: List[Tuple[str, str]] = []

    for car_dir in cars_path.iterdir():
        # Only process actual directories (skip files)
        if not car_dir.is_dir():
            continue

        folder_name = car_dir.name
        display_name = _read_display_name(car_dir) or folder_name
        cars.append((folder_name, display_name))

    # Sort by display name so the dropdown is alphabetically ordered
    cars.sort(key=lambda x: x[1].lower())

    log.info("Found %d cars in %s", len(cars), cars_path)
    return cars


def _read_display_name(car_dir: Path) -> str:
    """
    Attempts to read the car's human-readable name from its ui_car.json file.
    Returns an empty string if the file doesn't exist or can't be parsed.

    The ui_car.json file lives at: content/cars/{car_name}/ui/ui_car.json
    """
    ui_json_path = car_dir / "ui" / "ui_car.json"

    if not ui_json_path.exists():
        return ""

    try:
        with open(ui_json_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        # The 'name' field holds the display name shown in-game
        return data.get("name", "").strip()
    except Exception as e:
        log.debug("Could not read ui_car.json for %s: %s", car_dir.name, e)
        return ""


def get_installed_skin_names(car_path: Path) -> List[str]:
    """
    Returns a list of skin folder names already installed for the given car.
    Used to check for naming conflicts before injecting a new skin.

    Ignores the hidden '.ac_skin_backups' folder used for backup storage.
    """
    skins_path = car_path / "skins"

    if not skins_path.is_dir():
        return []

    return [
        d.name
        for d in skins_path.iterdir()
        if d.is_dir() and d.name != ".ac_skin_backups"
    ]
