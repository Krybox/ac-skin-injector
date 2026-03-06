"""
validation_result.py
--------------------
Data model for the result of validating a single skin folder.
Stores whether the skin is valid, any warnings, and any blocking errors.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationResult:
    """
    Holds the outcome of validating a skin folder's contents.

    Attributes:
        is_valid     : False if any blocking errors were found (e.g. missing livery.png).
        has_livery   : True if livery.png was found in the skin folder.
        has_preview  : True if preview.jpg was found.
        has_ui_json  : True if ui_skin.json was found.
        warnings     : Non-blocking issues (e.g. missing preview, invalid JSON).
        errors       : Blocking issues that prevent injection (e.g. no livery.png).
    """

    is_valid: bool = True
    has_livery: bool = False
    has_preview: bool = False
    has_ui_json: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_warning(self, message: str):
        """Adds a non-blocking warning message."""
        self.warnings.append(message)

    def add_error(self, message: str):
        """Adds a blocking error message and marks the result as invalid."""
        self.errors.append(message)
        self.is_valid = False

    @property
    def status_text(self) -> str:
        """
        Returns a short human-readable status string for display in the skin list.
        """
        if not self.is_valid:
            return "Invalid"
        if self.warnings:
            return f"{len(self.warnings)} warning(s)"
        return "Valid"

    @property
    def tooltip_text(self) -> str:
        """
        Returns a multi-line tooltip showing all warnings and errors.
        Used to give the user details when hovering over a status icon.
        """
        lines = []
        for e in self.errors:
            lines.append(f"Error: {e}")
        for w in self.warnings:
            lines.append(f"Warning: {w}")
        return "\n".join(lines) if lines else "No issues found."
