"""
dialogs.py
----------
Contains all the small dialog windows used throughout the application:

- ConflictDialog   : Shown when a skin name already exists in the target folder.
                     User can choose to Overwrite, Rename, or Skip.
- RenameDialog     : Shown when the user chooses 'Rename' in the conflict dialog,
                     or double-clicks a skin name in the list.
- BackupDialog     : Shows all available backups for the selected car and
                     lets the user restore one.
"""

from pathlib import Path
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QDialogButtonBox,
    QMessageBox, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.skin_injector import ConflictAction
from utils.logger import log


# ---------------------------------------------------------------------------
# Conflict Dialog
# ---------------------------------------------------------------------------

class ConflictDialog(QDialog):
    """
    Displayed when a skin with the same name already exists in the target folder.
    The user must choose one of three actions:
      - Overwrite : Replace the existing skin (a backup will be created if enabled).
      - Rename    : Open the RenameDialog to choose a new name.
      - Skip      : Leave the existing skin untouched and skip this injection.
    """

    def __init__(self, skin_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Skin Already Exists")
        self.setMinimumWidth(380)
        self.setModal(True)

        self._action = ConflictAction.SKIP  # Default if dialog is closed without choosing

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Informational message
        icon_label = QLabel("⚠️")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(24)
        icon_label.setFont(font)
        layout.addWidget(icon_label)

        msg = QLabel(
            f"A skin named <b>{skin_name}</b> already exists\n"
            "in the target car's skins folder.\n\n"
            "What would you like to do?"
        )
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        layout.addWidget(msg)

        # Action buttons arranged horizontally
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._overwrite_btn = QPushButton("Overwrite")
        self._rename_btn = QPushButton("Rename")
        self._skip_btn = QPushButton("Skip")

        self._overwrite_btn.setObjectName("dangerButton")
        self._overwrite_btn.setToolTip("Replace the existing skin (backup created if enabled)")
        self._rename_btn.setToolTip("Choose a new name for the incoming skin")
        self._skip_btn.setToolTip("Leave the existing skin as-is and skip this injection")

        btn_layout.addWidget(self._overwrite_btn)
        btn_layout.addWidget(self._rename_btn)
        btn_layout.addWidget(self._skip_btn)
        layout.addLayout(btn_layout)

        # Wire up button signals
        self._overwrite_btn.clicked.connect(self._choose_overwrite)
        self._rename_btn.clicked.connect(self._choose_rename)
        self._skip_btn.clicked.connect(self._choose_skip)

    def _choose_overwrite(self):
        self._action = ConflictAction.OVERWRITE
        self.accept()

    def _choose_rename(self):
        self._action = ConflictAction.RENAME
        self.accept()

    def _choose_skip(self):
        self._action = ConflictAction.SKIP
        self.accept()

    def get_action(self) -> ConflictAction:
        """Returns the action the user selected."""
        return self._action


# ---------------------------------------------------------------------------
# Rename Dialog
# ---------------------------------------------------------------------------

class RenameDialog(QDialog):
    """
    A simple dialog that lets the user type a new name for a skin folder.
    Used both after choosing 'Rename' in the conflict dialog and when
    double-clicking a skin name in the main list.
    """

    def __init__(self, current_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rename Skin")
        self.setMinimumWidth(340)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel(f"Current name:  <b>{current_name}</b>"))
        layout.addWidget(QLabel("New name:"))

        self._name_input = QLineEdit(current_name)
        self._name_input.selectAll()
        layout.addWidget(self._name_input)

        # Standard OK / Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        """Validates the name is non-empty before accepting."""
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "The skin name cannot be empty.")
            return
        self.accept()

    def get_new_name(self) -> Optional[str]:
        """
        Returns the new name entered by the user,
        or None if the dialog was cancelled.
        """
        if self.result() == QDialog.DialogCode.Accepted:
            return self._name_input.text().strip()
        return None


# ---------------------------------------------------------------------------
# Backup / Restore Dialog
# ---------------------------------------------------------------------------

class BackupDialog(QDialog):
    """
    Lists all available backups for the currently selected car and
    lets the user restore one. Opened by clicking 'Manage Backups'.
    """

    def __init__(self, car_name: str, backups: List[Dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Backups")
        self.setMinimumSize(500, 380)
        self.setModal(True)

        self._backups = backups         # List of backup dicts from backup_manager
        self._selected_backup: Optional[Dict] = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel(f"Backups for: <b>{car_name}</b>")
        layout.addWidget(header)

        if not backups:
            # Show a friendly message when there are no backups yet
            no_backups = QLabel("No backups found for this car.")
            no_backups.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_backups.setStyleSheet("color: grey; font-style: italic; padding: 40px;")
            layout.addWidget(no_backups)
        else:
            info = QLabel("Select a backup below and click Restore to bring it back.")
            info.setWordWrap(True)
            layout.addWidget(info)

            # List widget showing all backups
            self._list = QListWidget()
            self._list.setAlternatingRowColors(True)
            for backup in backups:
                # Format the creation date nicely for display
                created_str = self._format_date(backup.get("created", ""))
                expires_str = self._format_date(backup.get("expires", ""))
                label = (
                    f"{backup['original_name']}  —  "
                    f"Created: {created_str}  |  Expires: {expires_str}"
                )
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, backup)  # Store full dict on item
                self._list.addItem(item)

            self._list.currentItemChanged.connect(self._on_selection_changed)
            layout.addWidget(self._list)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self._restore_btn = QPushButton("Restore Selected")
        self._restore_btn.setObjectName("primaryButton")
        self._restore_btn.setEnabled(False)
        close_btn = QPushButton("Close")

        self._restore_btn.clicked.connect(self._on_restore)
        close_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addWidget(self._restore_btn)
        layout.addLayout(btn_layout)

    def _on_selection_changed(self, current: QListWidgetItem, _previous):
        """Enable the Restore button only when a backup is selected."""
        self._restore_btn.setEnabled(current is not None)
        if current:
            self._selected_backup = current.data(Qt.ItemDataRole.UserRole)

    def _on_restore(self):
        """Confirm and trigger the restore action."""
        if not self._selected_backup:
            return
        name = self._selected_backup["original_name"]
        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Restore backup of '<b>{name}</b>'?<br>"
            "This will overwrite the currently installed version.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.accept()

    def get_selected_backup(self) -> Optional[Dict]:
        """
        Returns the backup dict chosen by the user,
        or None if the dialog was cancelled.
        """
        if self.result() == QDialog.DialogCode.Accepted:
            return self._selected_backup
        return None

    @staticmethod
    def _format_date(iso_string: str) -> str:
        """Converts an ISO datetime string to a readable 'YYYY-MM-DD HH:MM' format."""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso_string)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return iso_string or "Unknown"
