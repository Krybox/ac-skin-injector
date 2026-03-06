"""
styles.py
---------
Defines the light and dark mode Qt stylesheets for the entire application.
Call apply_stylesheet(app, dark=True/False) to switch themes at runtime.
"""

from PySide6.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# Light theme — clean, neutral grey palette
# ---------------------------------------------------------------------------
LIGHT_STYLESHEET = """
QWidget {
    background-color: #f5f5f5;
    color: #1e1e1e;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog {
    background-color: #f0f0f0;
}

/* Top menu bar */
QMenuBar {
    background-color: #e8e8e8;
    border-bottom: 1px solid #cccccc;
    padding: 2px;
}
QMenuBar::item:selected {
    background-color: #d0d0d0;
    border-radius: 3px;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #cccccc;
}
QMenu::item:selected {
    background-color: #e0ecff;
}

/* Input fields */
QLineEdit, QComboBox {
    background-color: #ffffff;
    border: 1px solid #bbbbbb;
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: #4a90d9;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #4a90d9;
}
QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}

/* Standard buttons */
QPushButton {
    background-color: #e0e0e0;
    border: 1px solid #b0b0b0;
    border-radius: 5px;
    padding: 6px 16px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #d0d8e8;
    border-color: #4a90d9;
}
QPushButton:pressed {
    background-color: #b8c8e0;
}
QPushButton:disabled {
    background-color: #ececec;
    color: #aaaaaa;
    border-color: #cccccc;
}

/* Primary action button (Inject Skins) */
QPushButton#primaryButton {
    background-color: #4a90d9;
    color: white;
    border: none;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background-color: #3a7fc8;
}
QPushButton#primaryButton:pressed {
    background-color: #2e6bb5;
}
QPushButton#primaryButton:disabled {
    background-color: #a0b8d8;
}

/* Danger button (Clear All) */
QPushButton#dangerButton {
    background-color: #e05252;
    color: white;
    border: none;
}
QPushButton#dangerButton:hover {
    background-color: #cc3e3e;
}

/* Table / List widget */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
    gridline-color: #e8e8e8;
}
QTableWidget::item {
    padding: 4px;
}
QTableWidget::item:selected {
    background-color: #d0e4f7;
    color: #1e1e1e;
}
QHeaderView::section {
    background-color: #eeeeee;
    border: none;
    border-bottom: 1px solid #cccccc;
    padding: 5px 8px;
    font-weight: 600;
}

/* Checkboxes */
QCheckBox {
    spacing: 6px;
}

/* Group boxes */
QGroupBox {
    border: 1px solid #cccccc;
    border-radius: 5px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
}

/* Status bar at the bottom */
QStatusBar {
    background-color: #e8e8e8;
    border-top: 1px solid #cccccc;
    color: #444444;
    font-size: 12px;
}

/* Scroll bars */
QScrollBar:vertical {
    background: #f0f0f0;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #b0b0b0;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #888888;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Label styling */
QLabel#sectionLabel {
    font-weight: 600;
    color: #333333;
}

/* Drop zone label */
QLabel#dropZoneLabel {
    color: #999999;
    font-size: 12px;
    border: 2px dashed #cccccc;
    border-radius: 6px;
    padding: 12px;
}
"""

# ---------------------------------------------------------------------------
# Dark theme — dark blue-grey palette
# ---------------------------------------------------------------------------
DARK_STYLESHEET = """
QWidget {
    background-color: #1e2128;
    color: #e0e0e0;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog {
    background-color: #1e2128;
}

/* Top menu bar */
QMenuBar {
    background-color: #252830;
    border-bottom: 1px solid #3a3f4b;
    padding: 2px;
}
QMenuBar::item:selected {
    background-color: #3a3f4b;
    border-radius: 3px;
}
QMenu {
    background-color: #2c3040;
    border: 1px solid #3a3f4b;
}
QMenu::item:selected {
    background-color: #3a5a8a;
}

/* Input fields */
QLineEdit, QComboBox {
    background-color: #2c3040;
    border: 1px solid #3a3f4b;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0e0;
    selection-background-color: #3a5a8a;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #4a90d9;
}
QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #2c3040;
    border: 1px solid #3a3f4b;
    selection-background-color: #3a5a8a;
}

/* Standard buttons */
QPushButton {
    background-color: #2c3040;
    border: 1px solid #3a3f4b;
    border-radius: 5px;
    padding: 6px 16px;
    color: #e0e0e0;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #3a3f4b;
    border-color: #4a90d9;
}
QPushButton:pressed {
    background-color: #2a3550;
}
QPushButton:disabled {
    background-color: #252830;
    color: #555555;
    border-color: #333333;
}

/* Primary action button (Inject Skins) */
QPushButton#primaryButton {
    background-color: #3a70b5;
    color: white;
    border: none;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background-color: #4a80c5;
}
QPushButton#primaryButton:pressed {
    background-color: #2a60a5;
}
QPushButton#primaryButton:disabled {
    background-color: #2a3f5f;
    color: #667788;
}

/* Danger button (Clear All) */
QPushButton#dangerButton {
    background-color: #8b2020;
    color: white;
    border: none;
}
QPushButton#dangerButton:hover {
    background-color: #a02828;
}

/* Table / List widget */
QTableWidget {
    background-color: #252830;
    border: 1px solid #3a3f4b;
    border-radius: 4px;
    gridline-color: #2e3440;
    color: #e0e0e0;
}
QTableWidget::item {
    padding: 4px;
}
QTableWidget::item:selected {
    background-color: #2a3f5f;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #2c3040;
    border: none;
    border-bottom: 1px solid #3a3f4b;
    padding: 5px 8px;
    font-weight: 600;
    color: #c0c0c0;
}

/* Checkboxes */
QCheckBox {
    spacing: 6px;
    color: #e0e0e0;
}

/* Group boxes */
QGroupBox {
    border: 1px solid #3a3f4b;
    border-radius: 5px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: 600;
    color: #c0c0c0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    color: #a0a8b8;
}

/* Status bar at the bottom */
QStatusBar {
    background-color: #252830;
    border-top: 1px solid #3a3f4b;
    color: #a0a8b8;
    font-size: 12px;
}

/* Scroll bars */
QScrollBar:vertical {
    background: #252830;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #3a3f4b;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #5a6070;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Label styling */
QLabel#sectionLabel {
    font-weight: 600;
    color: #a0a8b8;
}

/* Drop zone label */
QLabel#dropZoneLabel {
    color: #555f70;
    font-size: 12px;
    border: 2px dashed #3a3f4b;
    border-radius: 6px;
    padding: 12px;
}
"""


def apply_stylesheet(app: QApplication, dark: bool = False):
    """
    Applies either the light or dark stylesheet to the entire application.
    Call this at startup and whenever the user toggles the theme.
    """
    app.setStyleSheet(DARK_STYLESHEET if dark else LIGHT_STYLESHEET)
