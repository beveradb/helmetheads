"""Composite the poster overlay (50% opacity) onto the poster base."""

from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

OVERLAY_OPACITY = 0.5
OUT = Path(__file__).resolve().parent.parent / "render" / "out"

base = Image.open(OUT / "poster-base.png").convert("RGBA")
overlay = Image.open(OUT / "poster-overlay.png").convert("RGBA")
assert base.size == overlay.size, (base.size, overlay.size)
overlay.putalpha(overlay.getchannel("A").point(lambda a: round(a * OVERLAY_OPACITY)))
composite = Image.alpha_composite(base, overlay)
composite.convert("RGB").save(OUT / "poster-map.png")
print("saved", OUT / "poster-map.png", composite.size)
