"""
skin_list_widget.py
-------------------
A custom QTableWidget that displays the list of skins staged for injection.

Each row shows:
  - A checkbox to enable/disable the skin for injection
  - A 128x128 preview thumbnail (from preview.jpg, or a placeholder)
  - The skin's name (editable via double-click to trigger a rename dialog)
  - A status icon with a tooltip describing validation results

Also handles drag-and-drop of ZIP files and folders directly onto the widget.
"""

import sys
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QLabel, QCheckBox,
    QWidget, QHBoxLayout, QHeaderView, QAbstractItemView, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap

from models.skin import Skin
from models.validation_result import ValidationResult
from utils.logger import log

# Size for preview thumbnails in the list
THUMBNAIL_SIZE = 128


def get_resource_path(relative: str) -> Path:
    """Returns the absolute path to a resource file, compatible with PyInstaller."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent.parent / "resources"
    return base / relative


class SkinListWidget(QTableWidget):
    """
    Displays staged skins in a table with preview thumbnails.

    Signals:
        files_dropped(list[Path]) : Emitted when the user drops ZIP/folder paths.
        rename_requested(int, str): Emitted when user double-clicks a skin name row,
                                    carrying (row_index, current_name).
    """

    files_dropped = Signal(list)          # List[Path] of dropped ZIPs or folders
    rename_requested = Signal(int, str)   # (row_index, current_skin_name)

    # Column indices for easy reference
    COL_CHECK   = 0
    COL_PREVIEW = 1
    COL_NAME    = 2
    COL_STATUS  = 3

    def __init__(self, parent=None) -> None:
        super().__init__(0, 4, parent)  # 0 rows, 4 columns

        self._skins: List[Skin] = []
        self._validations: dict[int, ValidationResult] = {}  # row → ValidationResult

        self._setup_table()
        self.setAcceptDrops(True)

    def _setup_table(self) -> None:
        """Configures column headers, widths, and general table behaviour."""
        self.setHorizontalHeaderLabels(["", "Preview", "Skin Name", "Status"])

        header = self.horizontalHeader()
        header.setSectionResizeMode(self.COL_CHECK,   QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_PREVIEW, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_NAME,    QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_STATUS,  QHeaderView.ResizeMode.Fixed)

        self.setColumnWidth(self.COL_CHECK,   40)
        self.setColumnWidth(self.COL_PREVIEW, THUMBNAIL_SIZE + 16)
        self.setColumnWidth(self.COL_STATUS,  110)

        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setRowHeight(0, THUMBNAIL_SIZE + 12)  # Default row height

        # Double-clicking the name column triggers the rename flow
        self.cellDoubleClicked.connect(self._on_double_click)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_skin(self, skin: Skin, validation: ValidationResult) -> None:
        """
        Appends a new skin row to the table.
        Called after a skin has been extracted and validated.
        """
        row = self.rowCount()
        self.insertRow(row)
        self.setRowHeight(row, THUMBNAIL_SIZE + 12)

        self._skins.append(skin)
        self._validations[row] = validation

        # Column 0: Checkbox (enabled/disabled toggle)
        check_widget = self._make_checkbox_widget(skin)
        self.setCellWidget(row, self.COL_CHECK, check_widget)

        # Column 1: Preview thumbnail
        preview_label = self._make_preview_label(skin.preview_path)
        self.setCellWidget(row, self.COL_PREVIEW, preview_label)

        # Column 2: Skin name (plain text item)
        name_item = QTableWidgetItem(skin.name)
        name_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        # Show a tooltip hinting the user can double-click to rename
        name_item.setToolTip("Double-click to rename this skin before injection.")
        self.setItem(row, self.COL_NAME, name_item)

        # Column 3: Validation status icon + text
        status_widget = self._make_status_widget(validation)
        self.setCellWidget(row, self.COL_STATUS, status_widget)

    def get_skins(self) -> List[Skin]:
        """Returns the current list of staged skins (reflects any renames and checkbox states)."""
        return self._skins

    def rename_skin_at_row(self, row: int, new_name: str) -> None:
        """Updates the skin name for the given row after a rename dialog completes."""
        if 0 <= row < len(self._skins):
            self._skins[row].name = new_name
            item = self.item(row, self.COL_NAME)
            if item:
                item.setText(new_name)

    def remove_selected_rows(self) -> None:
        """Removes all currently selected rows from the table."""
        selected_rows = sorted(
            {idx.row() for idx in self.selectedIndexes()}, reverse=True
        )
        for row in selected_rows:
            self.removeRow(row)
            if row < len(self._skins):
                self._skins.pop(row)
            self._validations.pop(row, None)

        # Re-index the validations dict after removal
        self._rebuild_validation_index()

    def clear_all(self) -> None:
        """Clears all rows and resets internal state."""
        self.setRowCount(0)
        self._skins.clear()
        self._validations.clear()

    def has_skins(self) -> bool:
        """Returns True if there is at least one skin in the table."""
        return len(self._skins) > 0

    # ------------------------------------------------------------------
    # Widget construction helpers
    # ------------------------------------------------------------------

    def _make_checkbox_widget(self, skin: Skin) -> QWidget:
        """Creates a centred checkbox widget for the enable/disable column."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        checkbox = QCheckBox()
        checkbox.setChecked(skin.enabled)
        # Connect the checkbox directly to the skin's enabled attribute
        checkbox.toggled.connect(lambda checked: setattr(skin, "enabled", checked))
        layout.addWidget(checkbox)
        return container

    def _make_preview_label(self, preview_path: Optional[Path]) -> QLabel:
        """
        Creates a QLabel containing the skin's preview thumbnail.
        Falls back to a grey placeholder if no preview.jpg is available.
        """
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFixedSize(QSize(THUMBNAIL_SIZE + 16, THUMBNAIL_SIZE + 12))

        if preview_path and preview_path.exists():
            pixmap = QPixmap(str(preview_path))
            if not pixmap.isNull():
                label.setPixmap(
                    pixmap.scaled(
                        THUMBNAIL_SIZE,
                        THUMBNAIL_SIZE,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                return label

        # No preview — show a placeholder with text
        placeholder_path = get_resource_path("default_preview.png")
        if placeholder_path.exists():
            pixmap = QPixmap(str(placeholder_path))
            label.setPixmap(
                pixmap.scaled(
                    THUMBNAIL_SIZE,
                    THUMBNAIL_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            label.setText("No preview")
            label.setStyleSheet("color: grey; font-size: 11px;")

        return label

    def _make_status_widget(self, validation: ValidationResult) -> QWidget:
        """
        Creates a small widget showing a coloured status icon and short text.
        A tooltip shows the full list of warnings/errors on hover.
        """
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(4)

        if not validation.is_valid:
            icon, text, color = "✗", "Invalid", "#e05252"
        elif validation.warnings:
            icon, text, color = "⚠", f"{len(validation.warnings)} warning(s)", "#e0a020"
        else:
            icon, text, color = "✓", "Valid", "#4caf50"

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")

        text_label = QLabel(text)
        text_label.setStyleSheet(f"color: {color}; font-size: 11px;")

        layout.addWidget(icon_label)
        layout.addWidget(text_label)

        # Show all warnings/errors when the user hovers over the status cell
        container.setToolTip(validation.tooltip_text)
        return container

    # ------------------------------------------------------------------
    # Drag and drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event) -> None:
        """Accept drag events that carry file/folder URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        """Keep accepting the drag as long as it has URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        """
        Called when the user drops files/folders onto the table.
        Emits the files_dropped signal with a list of Path objects.
        """
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        if paths:
            log.info("Dropped %d path(s) onto skin list", len(paths))
            self.files_dropped.emit(paths)
        event.acceptProposedAction()

    # ------------------------------------------------------------------
    # Double-click to rename
    # ------------------------------------------------------------------

    def _on_double_click(self, row: int, col: int) -> None:
        """Triggers the rename flow when the Name column is double-clicked."""
        if col == self.COL_NAME and row < len(self._skins):
            self.rename_requested.emit(row, self._skins[row].name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rebuild_validation_index(self) -> None:
        """
        Rebuilds the row → ValidationResult mapping after rows are removed.
        Needed because dict keys (row indices) shift when rows are deleted.

        Strategy: collect the surviving ValidationResult values in original order
        (skipping the removed entries whose keys no longer exist), then reassign
        them to 0-based sequential keys matching the current row count.
        """
        # Gather surviving results in ascending key order
        surviving = [
            self._validations[key]
            for key in sorted(self._validations)
            if key < self.rowCount()
        ]
        self._validations = {i: v for i, v in enumerate(surviving)}
