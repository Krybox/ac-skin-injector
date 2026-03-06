"""
test_core.py - Quick sanity tests for core logic modules.
Run with: python test_core.py
"""
import sys, tempfile, zipfile
sys.path.insert(0, "src")

from pathlib import Path
from core.zip_handler import extract_skins_from_zip, InvalidSkinZipError, cleanup_temp_dir
from core.skin_validator import validate_skin

tmp = tempfile.mkdtemp()
passed = 0
failed = 0

def ok(name):
    global passed
    print(f"  PASS  {name}")
    passed += 1

def fail(name, reason=""):
    global failed
    print(f"  FAIL  {name}: {reason}")
    failed += 1

# --- Test 1: livery.png at ZIP root ---
try:
    z1 = Path(tmp) / "my_skin.zip"
    with zipfile.ZipFile(z1, "w") as zf:
        zf.writestr("livery.png", b"fake")
        zf.writestr("preview.jpg", b"fake")
        zf.writestr("ui_skin.json", '{"skinname":"Test"}')
    r1 = extract_skins_from_zip(z1)
    assert len(r1) == 1, f"expected 1 skin, got {len(r1)}"
    assert r1[0].name == "my_skin", f"expected 'my_skin', got '{r1[0].name}'"
    v1 = validate_skin(r1[0])
    assert v1.is_valid and v1.has_livery and v1.has_preview and v1.has_ui_json
    ok("Root-level skin ZIP")
except Exception as e:
    fail("Root-level skin ZIP", e)

# --- Test 2: skin folder inside ZIP ---
try:
    z2 = Path(tmp) / "racing_livery.zip"
    with zipfile.ZipFile(z2, "w") as zf:
        zf.writestr("racing_livery/livery.png", b"fake")
        zf.writestr("racing_livery/preview.jpg", b"fake")
    r2 = extract_skins_from_zip(z2)
    assert len(r2) == 1 and r2[0].name == "racing_livery"
    v2 = validate_skin(r2[0])
    assert v2.is_valid and not v2.has_ui_json and len(v2.warnings) == 1
    ok("Single folder inside ZIP")
except Exception as e:
    fail("Single folder inside ZIP", e)

# --- Test 3: multi-skin ZIP ---
try:
    z3 = Path(tmp) / "pack.zip"
    with zipfile.ZipFile(z3, "w") as zf:
        zf.writestr("red_skin/livery.png", b"fake")
        zf.writestr("blue_skin/livery.png", b"fake")
    r3 = extract_skins_from_zip(z3)
    assert len(r3) == 2 and {x.name for x in r3} == {"red_skin", "blue_skin"}
    ok("Multi-skin ZIP")
except Exception as e:
    fail("Multi-skin ZIP", e)

# --- Test 4: deeply nested ZIP with custom DDS ---
try:
    z4 = Path(tmp) / "deep.zip"
    with zipfile.ZipFile(z4, "w") as zf:
        zf.writestr("content/cars/some_car/skins/my_skin/livery.png", b"fake")
        zf.writestr("content/cars/some_car/skins/my_skin/EXT_Skin_AO.dds", b"dds data")
        zf.writestr("content/cars/some_car/skins/my_skin/subfolder/decals.dds", b"dds2")
    r4 = extract_skins_from_zip(z4)
    assert len(r4) == 1 and r4[0].name == "my_skin"
    files = {f.name for f in r4[0].iterdir()}
    assert "livery.png" in files and "EXT_Skin_AO.dds" in files
    # Check subfolder was also copied
    subfolder = r4[0] / "subfolder"
    assert subfolder.is_dir(), "subfolder should be copied"
    ok("Deeply nested ZIP with custom DDS + subfolder")
except Exception as e:
    fail("Deeply nested ZIP with custom DDS + subfolder", e)

# --- Test 5: invalid ZIP (no livery.png) ---
try:
    z5 = Path(tmp) / "invalid.zip"
    with zipfile.ZipFile(z5, "w") as zf:
        zf.writestr("readme.txt", "hello")
    try:
        extract_skins_from_zip(z5)
        fail("Invalid ZIP rejected", "should have raised InvalidSkinZipError")
    except InvalidSkinZipError:
        ok("Invalid ZIP rejected correctly")
except Exception as e:
    fail("Invalid ZIP rejected", e)

# --- Test 6: validation warnings ---
try:
    import os
    skin_dir = Path(tmp) / "warn_skin"
    skin_dir.mkdir()
    (skin_dir / "livery.png").write_bytes(b"fake")
    # No preview.jpg, no ui_skin.json
    v = validate_skin(skin_dir)
    assert v.is_valid, "should be valid (livery.png present)"
    assert len(v.warnings) == 2, f"expected 2 warnings, got {len(v.warnings)}"
    ok("Validation warnings (missing preview + json)")
except Exception as e:
    fail("Validation warnings", e)

# --- Test 7: validation error (no livery.png) ---
try:
    skin_dir2 = Path(tmp) / "invalid_skin"
    skin_dir2.mkdir()
    (skin_dir2 / "some_texture.dds").write_bytes(b"fake")
    v2 = validate_skin(skin_dir2)
    assert not v2.is_valid
    assert len(v2.errors) == 1
    ok("Validation error (no livery.png)")
except Exception as e:
    fail("Validation error", e)

cleanup_temp_dir()
print()
print(f"Results: {passed} passed, {failed} failed")
if failed > 0:
    sys.exit(1)
