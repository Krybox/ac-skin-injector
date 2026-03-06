"""
ac_detector.py
--------------
Responsible for finding the Assetto Corsa installation on the user's machine.

Detection strategy (in order):
1. Parse Steam's libraryfolders.vdf to find all Steam library locations.
2. Check the Windows registry for the Steam install path as a fallback.
3. Check a hardcoded default path as a last resort.
4. Return None if AC cannot be found (user will be prompted to browse manually).
"""

import winreg
from pathlib import Path
from typing import Optional, List

from utils.logger import log

# The sub-path inside any Steam library that leads to the AC installation
AC_RELATIVE_PATH = Path("steamapps") / "common" / "assettocorsa"

# Common locations where Steam's main folder might live
DEFAULT_STEAM_PATHS = [
    Path("C:/Program Files (x86)/Steam"),
    Path("C:/Program Files/Steam"),
]


def find_ac_installation() -> Optional[Path]:
    """
    Tries to automatically locate the Assetto Corsa installation folder.
    Returns the Path to the AC root folder, or None if not found.
    """
    log.info("Starting Assetto Corsa installation detection...")

    # Collect all Steam library root paths to search
    steam_libraries = _get_all_steam_libraries()

    for library in steam_libraries:
        candidate = library / AC_RELATIVE_PATH
        if _is_valid_ac_path(candidate):
            log.info("Found AC installation at: %s", candidate)
            return candidate

    log.warning("Could not auto-detect AC installation.")
    return None


def _get_all_steam_libraries() -> List[Path]:
    """
    Returns a list of all Steam library root folders found on this machine.
    Combines results from the registry, default paths, and libraryfolders.vdf.
    """
    libraries: List[Path] = []

    # First try to get Steam's main install path from the Windows registry
    steam_root = _get_steam_path_from_registry()

    if steam_root:
        libraries.append(steam_root)
    else:
        # Fall back to checking well-known default install locations
        for default in DEFAULT_STEAM_PATHS:
            if default.exists():
                libraries.append(default)

    # Parse libraryfolders.vdf to find any additional Steam library drives
    for base in list(libraries):
        extra = _parse_library_folders_vdf(base)
        for lib in extra:
            if lib not in libraries:
                libraries.append(lib)

    log.debug("Steam libraries found: %s", libraries)
    return libraries


def _get_steam_path_from_registry() -> Optional[Path]:
    """
    Reads the Steam installation path from the Windows registry.
    Returns the Path if found, otherwise None.
    """
    registry_keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam"),
    ]

    for hive, key_path in registry_keys:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                value, _ = winreg.QueryValueEx(key, "InstallPath")
                path = Path(value)
                if path.exists():
                    log.debug("Steam path from registry: %s", path)
                    return path
        except (FileNotFoundError, OSError):
            # Key doesn't exist or can't be read — try the next one
            continue

    return None


def _parse_library_folders_vdf(steam_root: Path) -> List[Path]:
    """
    Parses Steam's libraryfolders.vdf file to find all configured Steam library paths.
    The VDF file lists every drive/folder where the user has installed Steam games.
    Returns a list of additional library root Paths.
    """
    vdf_path = steam_root / "steamapps" / "libraryfolders.vdf"

    if not vdf_path.exists():
        log.debug("libraryfolders.vdf not found at: %s", vdf_path)
        return []

    try:
        import vdf as vdf_parser
        with open(vdf_path, "r", encoding="utf-8") as f:
            data = vdf_parser.load(f)

        libraries: List[Path] = []

        # The VDF structure has a top-level "libraryfolders" key containing
        # numbered entries ("0", "1", ...) each with a "path" field
        folders = data.get("libraryfolders", {})
        for entry in folders.values():
            if isinstance(entry, dict):
                raw_path = entry.get("path", "")
                if raw_path:
                    lib_path = Path(raw_path)
                    if lib_path.exists():
                        libraries.append(lib_path)

        log.debug("Library paths from VDF: %s", libraries)
        return libraries

    except Exception as e:
        log.warning("Failed to parse libraryfolders.vdf: %s", e)
        return []


def _is_valid_ac_path(path: Path) -> bool:
    """
    Checks whether the given path looks like a valid Assetto Corsa installation.
    We verify the 'content/cars' folder exists as a basic sanity check.
    """
    return (path / "content" / "cars").is_dir()


def get_cars_path(ac_root: Path) -> Path:
    """
    Returns the path to the 'content/cars' folder inside the AC installation.
    This is where all car folders (and their skins subfolders) live.
    """
    return ac_root / "content" / "cars"
