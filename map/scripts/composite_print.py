"""Composite the print-resolution cyclosm-lite overlay onto the osm-carto base.

The overlay's opacity is scaled by OVERLAY_OPACITY so the street grid and names
underneath the blue cycling lines stay readable. 1.0 = fully opaque overlay,
0.5 = half-transparent (street names show through).
"""

from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # 14400x14435 exceeds PIL's decompression-bomb default

OVERLAY_OPACITY = 0.5

OUT = Path(__file__).resolve().parent.parent / "render" / "out"

base = Image.open(OUT / "full-osm-carto.png").convert("RGBA")
overlay = Image.open(OUT / "full-cyclosm-lite.png").convert("RGBA")
assert base.size == overlay.size, (base.size, overlay.size)

# Scale the overlay's alpha channel: transparent stays transparent, opaque
# cycling lines become semi-transparent so the base shows through.
alpha = overlay.getchannel("A").point(lambda a: round(a * OVERLAY_OPACITY))
overlay.putalpha(alpha)

composite = Image.alpha_composite(base, overlay)
composite.convert("RGB").save(OUT / "full-composite.png")
print("saved", OUT / "full-composite.png", composite.size, f"(overlay opacity {OVERLAY_OPACITY})")
