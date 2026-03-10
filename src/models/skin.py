"""
skin.py
-------
Data model representing a single skin that is staged for injection.
Holds all the information about a skin: where it came from, its name,
its validation result, and its preview image path.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Skin:
    """
    Represents a single skin ready to be injected into a car's skins folder.

    Attributes:
        source_path : The folder on disk containing the skin's files (livery.png etc.)
        name        : The folder name that will be used inside the car's skins directory.
                      Defaults to the source folder's name but the user can rename it.
        preview_path: Path to preview.jpg inside the skin folder, if it exists.
        enabled     : Whether this skin is checked/selected for injection by the user.
        from_zip    : True if this skin was extracted from a ZIP file.
    """

    source_path: Path                    # Absolute path to the extracted/selected skin folder
    name: str = ""                       # Target folder name (editable by user before injection)
    preview_path: Optional[Path] = None  # Path to preview.jpg (None if not present)
    enabled: bool = True                 # Whether the user wants to inject this skin
    from_zip: bool = False               # True when the skin came from a ZIP archive

    def __post_init__(self) -> None:
        """
        If no name was provided, use the source folder's name as the default.
        """
        if not self.name:
            self.name = self.source_path.name

        # Automatically set preview_path if preview.jpg exists in the skin folder
        candidate = self.source_path / "preview.jpg"
        if candidate.exists() and self.preview_path is None:
            self.preview_path = candidate
