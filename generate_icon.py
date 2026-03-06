# generate_icon.py
# ----------------
# Creates app_icon.png (256x256) and app_icon.ico (multi-size) for the AC Skin Injector.
# Design: dark blue-grey background, bold white "AC" text, red accent strip at bottom.
# Run once: python generate_icon.py

import sys
import os

from PIL import Image, ImageDraw, ImageFont

# Output paths
OUT_DIR = os.path.join(os.path.dirname(__file__), "resources", "icons")
os.makedirs(OUT_DIR, exist_ok=True)

PNG_PATH = os.path.join(OUT_DIR, "app_icon.png")
ICO_PATH = os.path.join(OUT_DIR, "app_icon.ico")

# Color palette
BG_COLOR    = (30, 33, 40)    # #1e2128 dark blue-grey
TEXT_COLOR  = (255, 255, 255) # white
ACCENT_COLOR = (200, 30, 30)  # red accent

def draw_icon(size):
    """Draw the AC icon at the given square pixel size and return an RGBA Image."""
    img = Image.new("RGBA", (size, size), BG_COLOR + (255,))
    draw = ImageDraw.Draw(img)

    # Red accent strip at the bottom — 12% of height
    strip_h = max(4, int(size * 0.12))
    draw.rectangle([(0, size - strip_h), (size, size)], fill=ACCENT_COLOR + (255,))

    # Try to load a bold system font; fall back to Pillow's default
    font = None
    font_size = int(size * 0.45)
    candidate_paths = [
        r"C:\Windows\Fonts\arialbd.ttf",   # Arial Bold
        r"C:\Windows\Fonts\calibrib.ttf",  # Calibri Bold
        r"C:\Windows\Fonts\verdanab.ttf",  # Verdana Bold
        r"C:\Windows\Fonts\arial.ttf",     # Arial regular fallback
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, font_size)
                break
            except Exception:
                pass

    if font is None:
        # Last resort: Pillow built-in bitmap font (very small, but always works)
        font = ImageFont.load_default()

    # Measure and center the "AC" text
    text = "AC"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (size - text_w) / 2 - bbox[0]
    # Shift up slightly to account for accent strip
    text_y = (size - strip_h - text_h) / 2 - bbox[1]
    draw.text((text_x, text_y), text, fill=TEXT_COLOR + (255,), font=font)

    return img

# Build the 256x256 PNG
img256 = draw_icon(256)
img256.save(PNG_PATH, "PNG")
print(f"Saved PNG: {PNG_PATH}  ({os.path.getsize(PNG_PATH)} bytes)")

# Build ICO with multiple sizes for crisp display at every context.
# We save each size as a separate PNG into a temp dir, then let Pillow
# assemble them all into one .ico file via the sizes= list approach.
import tempfile, struct

sizes = [16, 32, 48, 256]
frames = []
for s in sizes:
    img = draw_icon(s)
    # Convert to RGBA to ensure alpha channel is preserved
    frames.append(img.convert("RGBA"))

# Save using Pillow's ICO encoder — pass all frames
# The key is to save the LARGEST frame first and pass append_images
frames_sorted = list(reversed(frames))  # largest first
frames_sorted[0].save(
    ICO_PATH,
    format="ICO",
    sizes=[(s, s) for s in reversed(sizes)],
    append_images=frames_sorted[1:],
)

ico_bytes = os.path.getsize(ICO_PATH)
print(f"Saved ICO: {ICO_PATH}  ({ico_bytes} bytes)")

# If ICO is suspiciously small (<1KB), fall back: write a single 48x48 ICO
if ico_bytes < 1000:
    print("WARNING: ICO seems small, retrying with single 48x48 frame...")
    img48 = draw_icon(48).convert("RGBA")
    img48.save(ICO_PATH, format="ICO")
    print(f"Saved ICO (fallback 48x48): {ICO_PATH}  ({os.path.getsize(ICO_PATH)} bytes)")

print("Done.")
