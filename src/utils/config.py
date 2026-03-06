"""
config.py
---------
Manages loading and saving the application's configuration as a JSON file.
The config file is stored in a 'config' folder next to the executable,
making the app fully portable (no registry or AppData writes).
"""

import json
import sys
from pathlib import Path
from utils.logger import log


def get_base_dir() -> Path:
    """
    Returns the directory where the executable (or main script) lives.
    Ensures the config folder is always created next to the .exe.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent.parent


# Default values used when no config file exists yet
DEFAULT_CONFIG = {
    "ac_installation_path": "",        # Path to the AC installation root
    "last_selected_car": "",           # Last car the user selected
    "dark_mode_enabled": False,        # UI theme preference
    "auto_detect_on_startup": True,    # Try to find AC automatically on launch
    "create_backups": True,            # Whether to back up skins before overwriting
    "backup_retention_days": 30,       # How many days to keep backups
    "window_geometry": {               # Remember window size and position
        "width": 900,
        "height": 650,
        "x": 100,
        "y": 100,
    },
}


class Config:
    """
    Handles reading and writing app settings to/from a JSON config file.
    Automatically creates the file with defaults if it doesn't exist.
    """

    def __init__(self):
        config_dir = get_base_dir() / "config"
        config_dir.mkdir(exist_ok=True)
        self._path = config_dir / "app_config.json"
        self._data = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        """
        Reads the config file from disk.
        If the file is missing or corrupted, falls back to defaults.
        """
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # Merge saved values into defaults so new keys are always present
                self._data.update(saved)
                log.info("Config loaded from %s", self._path)
            except Exception as e:
                log.warning("Failed to load config, using defaults: %s", e)
                self._data = dict(DEFAULT_CONFIG)
        else:
            log.info("No config file found, using defaults.")

    def save(self):
        """
        Writes the current config values to disk as JSON.
        """
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4)
            log.info("Config saved to %s", self._path)
        except Exception as e:
            log.error("Failed to save config: %s", e)

    def get(self, key: str, default=None):
        """Returns the value for the given config key, or a default if not found."""
        return self._data.get(key, default)

    def set(self, key: str, value):
        """Updates a config value in memory (call save() to persist it)."""
        self._data[key] = value

    # Convenience properties for the most commonly used settings

    @property
    def ac_path(self) -> str:
        return self._data.get("ac_installation_path", "")

    @ac_path.setter
    def ac_path(self, value: str):
        self._data["ac_installation_path"] = value

    @property
    def dark_mode(self) -> bool:
        return self._data.get("dark_mode_enabled", False)

    @dark_mode.setter
    def dark_mode(self, value: bool):
        self._data["dark_mode_enabled"] = value

    @property
    def create_backups(self) -> bool:
        return self._data.get("create_backups", True)

    @create_backups.setter
    def create_backups(self, value: bool):
        self._data["create_backups"] = value

    @property
    def backup_retention_days(self) -> int:
        return self._data.get("backup_retention_days", 30)

    @backup_retention_days.setter
    def backup_retention_days(self, value: int):
        self._data["backup_retention_days"] = value

    @property
    def last_selected_car(self) -> str:
        return self._data.get("last_selected_car", "")

    @last_selected_car.setter
    def last_selected_car(self, value: str):
        self._data["last_selected_car"] = value
