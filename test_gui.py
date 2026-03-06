# test_gui.py
# -----------
# Automated test: creates MainWindow offscreen and verifies it initialises correctly.
# Also tests that all core modules import without error.

import sys
import os
import traceback
import tempfile
import pathlib

# Point to our source
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

results = []

# ── Test 1: Core module imports ───────────────────────────────────────────────
try:
    from utils.config import Config
    from utils.logger import setup_logger
    from core.ac_detector import find_ac_installation, get_cars_path
    from core.car_scanner import get_car_list, get_installed_skin_names
    from core.zip_handler import extract_skins_from_zip, InvalidSkinZipError
    from core.skin_validator import validate_skin, ValidationResult
    from core.backup_manager import create_backup, restore_backup, cleanup_old_backups
    from core.skin_injector import inject_skins, InjectionResult, ConflictAction
    results.append('PASS  Core module imports')
except Exception as e:
    results.append(f'FAIL  Core module imports: {traceback.format_exc()}')

# ── Test 2: Config initialisation ─────────────────────────────────────────────
try:
    cfg = Config()
    cfg.set('test_key', 'test_value')
    assert cfg.get('test_key') == 'test_value', "Config read/write mismatch"
    results.append('PASS  Config initialisation')
except Exception as e:
    results.append(f'FAIL  Config initialisation: {e}')

# ── Test 3: GUI module imports ────────────────────────────────────────────────
try:
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    from PySide6.QtWidgets import QApplication
    from gui.styles import apply_stylesheet, LIGHT_STYLESHEET, DARK_STYLESHEET
    from gui.dialogs import ConflictDialog
    from gui.skin_list_widget import SkinListWidget
    from gui.main_window import MainWindow
    results.append('PASS  GUI module imports')
except Exception as e:
    results.append(f'FAIL  GUI module imports: {traceback.format_exc()}')

# ── Test 4: Stylesheets (light + dark) ────────────────────────────────────────
try:
    assert len(LIGHT_STYLESHEET) > 100, "Light stylesheet too short"
    assert len(DARK_STYLESHEET)  > 100, "Dark stylesheet too short"
    assert LIGHT_STYLESHEET != DARK_STYLESHEET, "Light and dark stylesheets are identical"
    results.append('PASS  Stylesheets (light + dark)')
except Exception as e:
    results.append(f'FAIL  Stylesheets: {e}')

# ── Test 5: MainWindow creation ───────────────────────────────────────────────
try:
    app = QApplication.instance() or QApplication(sys.argv)
    cfg2 = Config()
    w = MainWindow(cfg2, app)
    w.show()
    title = w.windowTitle()
    assert title, "Window title is empty"
    results.append(f'PASS  MainWindow creation (title="{title}")')
    w.close()
except Exception as e:
    results.append(f'FAIL  MainWindow creation: {traceback.format_exc()}')

# ── Print results ─────────────────────────────────────────────────────────────
print()
for r in results:
    print(r)
print()

failures = [r for r in results if r.startswith('FAIL')]
print(f"Results: {len(results) - len(failures)} passed, {len(failures)} failed")
if failures:
    sys.exit(1)
