"""
main_window.py
--------------
The main application window. Ties together all core modules and GUI widgets.

Responsibilities:
- Show the AC installation path and allow changing it
- Populate the car dropdown from the detected AC installation
- Handle adding skins via file browser or drag-and-drop
- Run extraction + validation on added ZIP files / folders
- Manage the inject workflow (conflicts, backups, progress)
- Provide access to the Backup/Restore dialog
- Toggle dark/light mode and persist user preferences
"""

from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QCheckBox, QFileDialog, QStatusBar, QMessageBox,
    QMenuBar, QMenu, QGroupBox, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent

from core.ac_detector import find_ac_installation, get_cars_path
from core.car_scanner import get_car_list, get_installed_skin_names
from core.zip_handler import extract_skins_from_zip, cleanup_temp_dir, InvalidSkinZipError
from core.skin_validator import validate_skin
from core.skin_injector import inject_skins, ConflictAction, InjectionResult
from core.backup_manager import (
    cleanup_old_backups, get_available_backups, restore_backup
)
from models.skin import Skin
from models.types import CarEntry, BackupInfo
from gui.skin_list_widget import SkinListWidget
from gui.dialogs import ConflictDialog, RenameDialog, BackupDialog
from gui.styles import apply_stylesheet
from utils.config import Config
from utils.logger import log
from main import APP_VERSION


class MainWindow(QMainWindow):
    """
    The application's single main window.
    All user interaction flows through this class.
    """

    def __init__(self, config: Config, app):
        super().__init__()

        self._config = config
        self._app = app          # Reference to QApplication for stylesheet switching
        self._cars: List[CarEntry] = []  # (folder_name, display_name)
        self._ac_root: Optional[Path] = None

        self.setWindowTitle("Assetto Corsa Skin Injector")
        self.setMinimumSize(900, 650)

        # Restore previous window geometry if available
        # Cast to dict explicitly so the type checker knows .get() is valid
        geo: dict = config.get("window_geometry") or {}
        self.resize(int(geo.get("width", 900)), int(geo.get("height", 650)))
        x, y = geo.get("x"), geo.get("y")
        if x is not None and y is not None:
            self.move(int(x), int(y))

        self._build_menu_bar()
        self._build_central_widget()
        self._build_status_bar()

        # Apply the saved theme preference
        apply_stylesheet(self._app, dark=self._config.dark_mode)
        self._update_dark_mode_action()

        # Auto-detect or load cached AC path on startup
        self._init_ac_path()

        # Clean up expired backups once at startup (not on every car switch)
        self._cleanup_all_backups()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_menu_bar(self) -> None:
        """Creates the top menu bar with File, Settings, and Help menus."""
        menubar: QMenuBar = self.menuBar()

        # --- File menu ---
        file_menu: QMenu = menubar.addMenu("File")

        open_ac_action = QAction("Open AC Installation...", self)
        open_ac_action.triggered.connect(self._browse_ac_path)
        file_menu.addAction(open_ac_action)

        refresh_action = QAction("Refresh Car List", self)
        refresh_action.triggered.connect(self._refresh_car_list)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # --- Settings menu ---
        settings_menu: QMenu = menubar.addMenu("Settings")

        self._dark_mode_action = QAction("Dark Mode", self)
        self._dark_mode_action.setCheckable(True)
        self._dark_mode_action.triggered.connect(self._toggle_dark_mode)
        settings_menu.addAction(self._dark_mode_action)

        # --- Help menu ---
        help_menu: QMenu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_central_widget(self) -> None:
        """Constructs the main content area of the window."""
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setSpacing(12)
        root_layout.setContentsMargins(16, 12, 16, 12)

        # Section: AC installation path
        root_layout.addWidget(self._build_ac_section())

        # Section: Target car selection
        root_layout.addWidget(self._build_car_section())

        # Section: Skin list with add/remove controls
        root_layout.addWidget(self._build_skin_section(), stretch=1)

        # Section: Options checkboxes
        root_layout.addWidget(self._build_options_section())

        # Section: Bottom action buttons
        root_layout.addLayout(self._build_action_buttons())

    def _build_ac_section(self) -> QGroupBox:
        """Builds the AC installation path row."""
        group = QGroupBox("AC Installation")
        layout = QHBoxLayout(group)
        layout.setSpacing(8)

        self._ac_path_input = QLineEdit()
        self._ac_path_input.setPlaceholderText("Assetto Corsa installation folder...")
        self._ac_path_input.setReadOnly(True)

        auto_btn = QPushButton("Auto-detect")
        auto_btn.setToolTip("Try to find the AC installation automatically via Steam")
        auto_btn.clicked.connect(self._auto_detect_ac)

        browse_btn = QPushButton("Browse...")
        browse_btn.setToolTip("Manually select the AC installation folder")
        browse_btn.clicked.connect(self._browse_ac_path)

        layout.addWidget(self._ac_path_input, stretch=1)
        layout.addWidget(auto_btn)
        layout.addWidget(browse_btn)
        return group

    def _build_car_section(self) -> QGroupBox:
        """Builds the target car selection dropdown."""
        group = QGroupBox("Target Car")
        layout = QHBoxLayout(group)
        layout.setSpacing(8)

        self._car_combo = QComboBox()
        self._car_combo.setPlaceholderText("Select a car...")
        self._car_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._car_combo.currentIndexChanged.connect(self._on_car_changed)

        self._car_info_label = QLabel("")
        self._car_info_label.setStyleSheet("color: grey; font-size: 11px;")

        layout.addWidget(self._car_combo, stretch=1)
        layout.addWidget(self._car_info_label)
        return group

    def _build_skin_section(self) -> QGroupBox:
        """Builds the skin list table with its add/remove buttons."""
        group = QGroupBox("Skins to Inject")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Top bar: Add and Remove buttons
        top_bar = QHBoxLayout()
        add_btn = QPushButton("Add ZIP / Folder...")
        add_btn.setToolTip("Browse for a skin ZIP file or folder to add")
        add_btn.clicked.connect(self._browse_add_skin)

        self._remove_btn = QPushButton("Remove Selected")
        self._remove_btn.setToolTip("Remove the selected skins from the list")
        self._remove_btn.clicked.connect(self._remove_selected_skins)

        top_bar.addWidget(add_btn)
        top_bar.addWidget(self._remove_btn)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # The custom skin table widget
        self._skin_list = SkinListWidget()
        self._skin_list.files_dropped.connect(self._handle_dropped_files)
        self._skin_list.rename_requested.connect(self._on_rename_requested)
        layout.addWidget(self._skin_list, stretch=1)

        return group

    def _build_options_section(self) -> QGroupBox:
        """Builds the Options section (backup checkbox only)."""
        group = QGroupBox("Options")
        layout = QHBoxLayout(group)
        layout.setSpacing(20)

        retention = self._config.backup_retention_days
        self._backup_checkbox = QCheckBox(f"Create backups (auto-delete after {retention} days)")
        self._backup_checkbox.setChecked(self._config.create_backups)
        self._backup_checkbox.toggled.connect(
            lambda v: setattr(self._config, "create_backups", v)
        )

        layout.addWidget(self._backup_checkbox)
        layout.addStretch()
        return group

    def _build_action_buttons(self) -> QHBoxLayout:
        """Builds the bottom row of action buttons."""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        backup_btn = QPushButton("Manage Backups")
        backup_btn.setToolTip("View and restore backups for the selected car")
        backup_btn.clicked.connect(self._open_backup_dialog)

        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setToolTip("Remove all staged skins from the list")
        clear_btn.clicked.connect(self._clear_all)

        self._inject_btn = QPushButton("Inject Skins")
        self._inject_btn.setObjectName("primaryButton")
        self._inject_btn.setToolTip("Copy the selected skins into the chosen car's skins folder")
        self._inject_btn.clicked.connect(self._run_injection)
        self._inject_btn.setMinimumWidth(130)

        layout.addWidget(backup_btn)
        layout.addStretch()
        layout.addWidget(clear_btn)
        layout.addWidget(self._inject_btn)
        return layout

    def _build_status_bar(self) -> None:
        """Sets up the status bar at the bottom of the window."""
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._set_status("Ready.")

    # ------------------------------------------------------------------
    # AC Path Initialisation
    # ------------------------------------------------------------------

    def _init_ac_path(self) -> None:
        """
        On startup, tries to use the cached AC path from config.
        If none is saved (or if auto-detect is enabled), runs auto-detection.
        """
        cached = self._config.ac_path
        if cached and Path(cached).is_dir():
            self._set_ac_path(Path(cached))
            log.info("Using cached AC path: %s", cached)
        elif self._config.get("auto_detect_on_startup", True):
            self._auto_detect_ac()

    def _auto_detect_ac(self) -> None:
        """Runs the AC installation detector and updates the UI accordingly."""
        self._set_status("Detecting Assetto Corsa installation...")
        found = find_ac_installation()
        if found:
            self._set_ac_path(found)
            self._set_status(f"AC installation found: {found}")
        else:
            self._set_status("Could not auto-detect AC. Please browse manually.")
            QMessageBox.warning(
                self,
                "AC Not Found",
                "Could not automatically find your Assetto Corsa installation.\n\n"
                "Please click 'Browse...' to locate it manually.",
            )

    def _browse_ac_path(self) -> None:
        """Opens a folder browser for the user to manually select the AC installation."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Assetto Corsa Installation Folder"
        )
        if folder:
            path = Path(folder)
            # Validate that the selected folder looks like an AC installation
            if (path / "content" / "cars").is_dir():
                self._set_ac_path(path)
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Folder",
                    "The selected folder does not appear to be a valid "
                    "Assetto Corsa installation.\n\n"
                    "Please select the folder containing the 'content/cars' directory.",
                )

    def _set_ac_path(self, path: Path) -> None:
        """
        Updates the AC path in the UI, config, and loads the car list.
        """
        self._ac_root = path
        self._config.ac_path = str(path)
        self._ac_path_input.setText(str(path))
        self._refresh_car_list()

    def _cleanup_all_backups(self) -> None:
        """
        Runs expired-backup cleanup once at startup across all cars that have
        a backup folder. Much cheaper than running on every car dropdown change.
        """
        if not self._ac_root:
            return
        cars_path = get_cars_path(self._ac_root)
        if not cars_path.is_dir():
            return
        total = 0
        for car_dir in cars_path.iterdir():
            if car_dir.is_dir():
                total += cleanup_old_backups(car_dir)
        if total:
            log.info("Startup cleanup: removed %d expired backup(s).", total)

    # ------------------------------------------------------------------
    # Car List Management
    # ------------------------------------------------------------------

    def _refresh_car_list(self) -> None:
        """Scans the AC cars directory and repopulates the car dropdown."""
        if not self._ac_root:
            return

        cars_path = get_cars_path(self._ac_root)
        self._cars = get_car_list(cars_path)

        self._car_combo.clear()
        for folder_name, display_name in self._cars:
            self._car_combo.addItem(display_name, userData=folder_name)

        # Restore the previously selected car if possible
        last = self._config.last_selected_car
        if last:
            idx = self._car_combo.findData(last)
            if idx >= 0:
                self._car_combo.setCurrentIndex(idx)

        self._set_status(f"Loaded {len(self._cars)} cars.")
        log.info("Car list refreshed: %d cars found.", len(self._cars))

    def _on_car_changed(self, index: int) -> None:
        """
        Called when the user picks a different car.
        Updates the info label showing how many skins are already installed.
        """
        if index < 0 or not self._ac_root:
            self._car_info_label.setText("")
            return

        folder_name = self._car_combo.currentData()
        if not folder_name:
            return

        self._config.last_selected_car = folder_name

        # Show how many skins are already installed for context
        car_path = get_cars_path(self._ac_root) / folder_name
        existing = get_installed_skin_names(car_path)
        self._car_info_label.setText(f"{len(existing)} skin(s) installed")

    def _get_selected_car_path(self) -> Optional[Path]:
        """Returns the full path to the currently selected car's folder, or None."""
        if not self._ac_root:
            return None
        folder_name = self._car_combo.currentData()
        if not folder_name:
            return None
        return get_cars_path(self._ac_root) / folder_name

    # ------------------------------------------------------------------
    # Adding Skins
    # ------------------------------------------------------------------

    def _browse_add_skin(self) -> None:
        """
        Opens a file/folder browser to let the user select ZIP files or folders.
        Supports selecting multiple files at once.
        """
        # Qt file dialogs don't natively support selecting both files AND folders,
        # so we use a standard file dialog that accepts ZIPs and all files.
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Skin ZIP File(s)",
            "",
            "ZIP Files (*.zip);;All Files (*)",
        )
        if paths:
            self._process_paths([Path(p) for p in paths])

    def _handle_dropped_files(self, paths: List[Path]) -> None:
        """Called when the user drops files or folders onto the skin list."""
        self._process_paths(paths)

    def _process_paths(self, paths: List[Path]) -> None:
        """
        Processes a list of dropped or browsed paths.
        Each path can be either a ZIP file or a folder.
        Extracts ZIPs, validates each found skin, and adds valid/warned skins to the list.
        Unsupported files are collected and shown in a single warning dialog.
        """
        unsupported = []
        for path in paths:
            if path.suffix.lower() == ".zip":
                self._add_from_zip(path)
            elif path.is_dir():
                self._add_from_folder(path)
            else:
                unsupported.append(path.name)

        if unsupported:
            names = "\n".join(f"  • {n}" for n in unsupported)
            QMessageBox.warning(
                self,
                "Unsupported Files",
                f"The following file(s) are not ZIP files or folders and were ignored:\n\n{names}",
            )

    def _add_from_zip(self, zip_path: Path) -> None:
        """Extracts skins from a ZIP file and adds them to the staging list."""
        self._set_status(f"Extracting {zip_path.name}...")
        try:
            extracted_paths = extract_skins_from_zip(zip_path)
        except InvalidSkinZipError as e:
            QMessageBox.critical(self, "Invalid ZIP File", str(e))
            self._set_status("Ready.")
            return
        except Exception as e:
            QMessageBox.critical(self, "Extraction Error", f"Failed to extract ZIP:\n{e}")
            log.error("ZIP extraction error for %s: %s", zip_path, e)
            self._set_status("Extraction failed.")
            return

        for skin_path in extracted_paths:
            skin = Skin(source_path=skin_path, from_zip=True)
            self._validate_and_add_skin(skin)

        self._set_status(f"Added {len(extracted_paths)} skin(s) from {zip_path.name}.")

    def _add_from_folder(self, folder_path: Path) -> None:
        """Adds a skin directly from a folder (no extraction needed)."""
        skin = Skin(source_path=folder_path, from_zip=False)
        self._validate_and_add_skin(skin)
        self._set_status(f"Added skin from folder: {folder_path.name}")

    def _validate_and_add_skin(self, skin: Skin) -> None:
        """
        Validates a skin and adds it to the list.
        If the skin is invalid (no livery.png), shows an error and does NOT add it.
        If it has warnings, adds it but shows the warning status in the list.
        """
        validation = validate_skin(skin.source_path)

        if not validation.is_valid:
            # Invalid skin — show error dialog and reject it
            QMessageBox.critical(
                self,
                "Invalid Skin",
                f"The skin '{skin.name}' is invalid and cannot be injected:\n\n"
                + "\n".join(validation.errors)
                + "\n\nPlease check that you have selected the correct file.",
            )
            log.warning("Rejected invalid skin: %s", skin.name)
            return

        self._skin_list.add_skin(skin, validation)
        log.info("Added skin to list: %s (valid=%s)", skin.name, validation.is_valid)

    # ------------------------------------------------------------------
    # Skin List Actions
    # ------------------------------------------------------------------

    def _remove_selected_skins(self) -> None:
        """Removes the rows currently selected in the skin list."""
        self._skin_list.remove_selected_rows()
        self._update_status_from_list()

    def _clear_all(self) -> None:
        """Clears all staged skins and cleans up extracted temp files."""
        self._skin_list.clear_all()
        cleanup_temp_dir()
        self._set_status("Skin list cleared.")

    def _on_rename_requested(self, row: int, current_name: str) -> None:
        """Opens the rename dialog when the user double-clicks a skin name."""
        dialog = RenameDialog(current_name, parent=self)
        if dialog.exec():
            new_name = dialog.get_new_name()
            if new_name and new_name != current_name:
                self._skin_list.rename_skin_at_row(row, new_name)
                log.info("Skin at row %d renamed: %s → %s", row, current_name, new_name)

    # ------------------------------------------------------------------
    # Injection
    # ------------------------------------------------------------------

    def _run_injection(self) -> None:
        """
        Validates preconditions and runs the full skin injection workflow.
        """
        # Guard: must have a selected car
        car_path = self._get_selected_car_path()
        if not car_path:
            QMessageBox.warning(self, "No Car Selected", "Please select a target car first.")
            return

        # Guard: must have at least one enabled skin
        skins = self._skin_list.get_skins()
        enabled_skins = [s for s in skins if s.enabled]
        if not enabled_skins:
            QMessageBox.warning(
                self, "No Skins Selected",
                "Please add at least one skin and make sure it is checked."
            )
            return

        self._set_status("Injecting skins...")
        self._inject_btn.setEnabled(False)

        result = inject_skins(
            skins=skins,
            car_path=car_path,
            create_backups=self._config.create_backups,
            retention_days=self._config.backup_retention_days,
            on_conflict=self._handle_conflict,
        )

        self._inject_btn.setEnabled(True)
        self._show_injection_summary(result)

        # Refresh the installed skin count label
        self._on_car_changed(self._car_combo.currentIndex())

    def _handle_conflict(self, skin_name: str):
        """
        Called by the injector when a skin name already exists.
        Always asks the user what to do: Overwrite, Rename, or Skip.
        Returns (ConflictAction, new_name_or_None).
        """
        dialog = ConflictDialog(skin_name, parent=self)
        dialog.exec()
        action = dialog.get_action()

        if action == ConflictAction.RENAME:
            rename_dialog = RenameDialog(skin_name, parent=self)
            if rename_dialog.exec():
                new_name = rename_dialog.get_new_name()
                if new_name:
                    return ConflictAction.RENAME, new_name
            # User cancelled the rename dialog → cancel the whole injection run
            return ConflictAction.CANCEL, None

        return action, None

    def _show_injection_summary(self, result: InjectionResult) -> None:
        """Shows a summary dialog after injection completes."""
        summary = result.summary_text()
        self._set_status(f"Done — {summary}")

        if result.failed:
            failures = "\n".join(f"  • {r.skin_name}: {r.error}" for r in result.failed)
            QMessageBox.warning(
                self,
                "Injection Completed with Errors",
                f"{summary}\n\nFailed skins:\n{failures}",
            )
        else:
            QMessageBox.information(self, "Injection Complete", summary)

    # ------------------------------------------------------------------
    # Backup Dialog
    # ------------------------------------------------------------------

    def _open_backup_dialog(self) -> None:
        """Opens the Manage Backups dialog for the currently selected car."""
        car_path = self._get_selected_car_path()
        if not car_path:
            QMessageBox.warning(self, "No Car Selected", "Please select a car first.")
            return

        car_name = self._car_combo.currentText()
        backups = get_available_backups(car_path)

        dialog = BackupDialog(car_name, backups, parent=self)
        if dialog.exec():
            backup = dialog.get_selected_backup()
            if backup:
                success = restore_backup(backup, car_path)
                if success:
                    QMessageBox.information(
                        self,
                        "Restore Successful",
                        f"Backup of '{backup['original_name']}' has been restored.",
                    )
                    self._on_car_changed(self._car_combo.currentIndex())
                else:
                    QMessageBox.critical(
                        self,
                        "Restore Failed",
                        f"Failed to restore backup '{backup['original_name']}'.\n"
                        "Check the log file for details.",
                    )

    # ------------------------------------------------------------------
    # Dark Mode
    # ------------------------------------------------------------------

    def _toggle_dark_mode(self) -> None:
        """Toggles between dark and light mode and saves the preference."""
        self._config.dark_mode = not self._config.dark_mode
        apply_stylesheet(self._app, dark=self._config.dark_mode)
        self._update_dark_mode_action()
        log.info("Dark mode: %s", self._config.dark_mode)

    def _update_dark_mode_action(self) -> None:
        """Keeps the menu checkmark in sync with the current dark mode state."""
        self._dark_mode_action.setChecked(self._config.dark_mode)

    # ------------------------------------------------------------------
    # Status Bar
    # ------------------------------------------------------------------

    def _set_status(self, message: str) -> None:
        """Updates the status bar message."""
        self._status_bar.showMessage(message)

    def _update_status_from_list(self) -> None:
        """Refreshes the status bar based on the current contents of the skin list."""
        skins = self._skin_list.get_skins()
        enabled = sum(1 for s in skins if s.enabled)
        self._set_status(f"{enabled} skin(s) ready for injection.")

    # ------------------------------------------------------------------
    # About Dialog
    # ------------------------------------------------------------------

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About AC Skin Injector",
            f"<b>Assetto Corsa Skin Injector</b><br>"
            f"Version {APP_VERSION}<br><br>"
            "Easily install car skins into your Assetto Corsa installation.<br><br>"
            "Supports ZIP files and folders with automatic skin detection.",
        )

    # ------------------------------------------------------------------
    # Window close — save config
    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Saves config and cleans up temp files when the window is closed.
        """
        # Persist window size and position
        geo = self.geometry()
        self._config.set("window_geometry", {
            "width": geo.width(),
            "height": geo.height(),
            "x": geo.x(),
            "y": geo.y(),
        })
        self._config.save()
        cleanup_temp_dir()
        log.info("Application closed.")
        event.accept()
