"""
zip_handler.py
--------------
Handles extracting skin folders from ZIP files.

The core rule is simple: scan the ZIP for every occurrence of 'livery.png'.
Each 'livery.png' found means its parent folder is a skin. Copy that entire
parent folder (recursively) to a temporary directory for further processing.

If no 'livery.png' is found at all, the ZIP is considered invalid and an
InvalidSkinZipError is raised with a descriptive message for the user.
"""

import zipfile
import shutil
import sys
from pathlib import Path, PurePosixPath
from typing import List

from utils.logger import log


class InvalidSkinZipError(Exception):
    """Raised when a ZIP file does not contain any valid skin (no livery.png found)."""
    pass


def get_temp_dir() -> Path:
    """
    Returns the path to the temporary extraction folder next to the .exe.
    Creates it if it doesn't exist yet.
    """
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent.parent.parent

    temp_dir = base / "temp"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir


def extract_skins_from_zip(zip_path: Path) -> List[Path]:
    """
    Extracts all skin folders found inside a ZIP file to the temp directory.

    Returns a list of Paths, each pointing to an extracted skin folder in temp.
    Raises InvalidSkinZipError if no 'livery.png' is found anywhere in the ZIP.

    How it works:
    1. Scan all files in the ZIP for 'livery.png' (case-insensitive).
    2. Each livery.png's parent path = one skin.
    3. Extract all files whose path starts with that parent to temp/{skin_name}/.
    4. If livery.png is at the root (no parent folder), use the ZIP filename as the skin name.
    """
    log.info("Extracting skins from ZIP: %s", zip_path)

    if not zipfile.is_zipfile(zip_path):
        raise InvalidSkinZipError(f"'{zip_path.name}' is not a valid ZIP file.")

    with zipfile.ZipFile(zip_path, "r") as zf:
        all_names = zf.namelist()

        # Find every entry that is (or ends with) livery.png, ignoring case
        livery_entries = [
            name for name in all_names
            if PurePosixPath(name).name.lower() == "livery.png"
        ]

        if not livery_entries:
            raise InvalidSkinZipError(
                f"No 'livery.png' was found in '{zip_path.name}'.\n"
                "Please check that you have selected the correct ZIP file."
            )

        log.debug("Found %d livery.png(s) in ZIP: %s", len(livery_entries), livery_entries)

        extracted_paths: List[Path] = []

        for livery_entry in livery_entries:
            # Determine the skin folder name:
            # - If livery.png is at the root (no subdirectory), use the ZIP filename.
            # - Otherwise, use the name of the immediate parent folder.
            posix_path = PurePosixPath(livery_entry)
            parts = posix_path.parts  # e.g. ('my_skin', 'livery.png') or ('livery.png',)

            if len(parts) == 1:
                # livery.png is at the root of the ZIP
                skin_folder_name = zip_path.stem  # e.g. 'my_skin' from 'my_skin.zip'
                skin_prefix = ""                  # No prefix to strip from member paths
            else:
                # livery.png is inside a subfolder (possibly deeply nested).
                # The parent folder of livery.png becomes the skin folder name,
                # regardless of how deeply nested it is.
                skin_folder_name = parts[-2]       # The direct parent of livery.png
                # The prefix is everything above the skin folder in the ZIP path
                # e.g. for 'content/cars/car/skins/my_skin/livery.png', prefix = 'content/cars/car/skins/my_skin'
                skin_prefix = str(posix_path.parent)  # 'my_skin' or 'content/.../my_skin'

            # Create the destination folder: temp/{skin_name}/
            dest_dir = get_temp_dir() / skin_folder_name
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            dest_dir.mkdir(parents=True)

            # Extract all files that belong to this skin (share the same prefix)
            _extract_skin_members(zf, all_names, skin_prefix, dest_dir)

            log.info("Extracted skin '%s' to: %s", skin_folder_name, dest_dir)
            extracted_paths.append(dest_dir)

    return extracted_paths


def _extract_skin_members(
    zf: zipfile.ZipFile,
    all_names: List[str],
    skin_prefix: str,
    dest_dir: Path,
):
    """
    Extracts all ZIP members that belong to the skin identified by skin_prefix
    into dest_dir, preserving subfolder structure within the skin.

    For root-level skins (skin_prefix == ""), all members are extracted directly.
    For nested skins, only members under the prefix are extracted, and the
    prefix is stripped from their paths so the skin folder stays clean.
    """
    for member in all_names:
        posix_member = PurePosixPath(member)

        if skin_prefix == "":
            # Root-level skin: extract everything, skip directory entries
            if member.endswith("/"):
                continue
            relative_path = posix_member
        else:
            # Nested skin: only extract files that live under our prefix
            try:
                relative_path = posix_member.relative_to(skin_prefix)
            except ValueError:
                # This member is not under our skin prefix, skip it
                continue

            # Skip bare directory entries (they have no filename part)
            if str(relative_path) == "." or member.endswith("/"):
                continue

        # Build the final destination path and create any needed subdirectories
        target_file = dest_dir / Path(str(relative_path))
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Write the file content from the ZIP to disk
        with zf.open(member) as src, open(target_file, "wb") as dst:
            shutil.copyfileobj(src, dst)


def cleanup_temp_dir():
    """
    Deletes all files and folders inside the temp directory.
    Called when the application exits or the user clicks 'Clear All'.
    """
    temp_dir = get_temp_dir()
    if temp_dir.exists():
        for item in temp_dir.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except Exception as e:
                log.warning("Could not clean up temp item %s: %s", item, e)
    log.info("Temp directory cleaned up.")
