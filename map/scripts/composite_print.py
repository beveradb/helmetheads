"""Composite the print-resolution cyclosm-lite overlay onto the osm-carto base."""

from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # 14400x14435 exceeds PIL's decompression-bomb default

OUT = Path(__file__).resolve().parent.parent / "render" / "out"

base = Image.open(OUT / "full-osm-carto.png").convert("RGBA")
overlay = Image.open(OUT / "full-cyclosm-lite.png").convert("RGBA")
assert base.size == overlay.size, (base.size, overlay.size)
composite = Image.alpha_composite(base, overlay)
composite.convert("RGB").save(OUT / "full-composite.png")
print("saved", OUT / "full-composite.png", composite.size)
