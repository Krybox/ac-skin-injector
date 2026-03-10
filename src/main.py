"""
main.py
-------
Application entry point.

Sets up the QApplication, applies the initial stylesheet, creates the main
window, and starts the Qt event loop. Also ensures temp files are cleaned
up if the app exits unexpectedly.
"""

import sys
from pathlib import Path

# Make sure the src folder is on the Python path when running as a script
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from gui.main_window import MainWindow
from gui.styles import apply_stylesheet
from utils.config import Config
from utils.logger import log, get_base_dir

APP_VERSION = "1.0.0"


def main():
    log.info("=" * 50)
    log.info("AC Skin Injector starting up...")

    # Load the portable config (creates defaults on first run)
    config = Config()

    # Create the Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("AC Skin Injector")
    app.setApplicationVersion(APP_VERSION)

    # Set the window icon if the icon file exists
    icon_path = get_base_dir() / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Apply the saved theme before the window is shown to avoid flicker
    apply_stylesheet(app, dark=config.dark_mode)

    # Create and show the main window
    window = MainWindow(config=config, app=app)
    window.show()

    log.info("Main window displayed.")

    # Start the Qt event loop — blocks until the window is closed
    exit_code = app.exec()

    log.info("AC Skin Injector exited with code %d.", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
