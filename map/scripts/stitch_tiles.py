"""Stitch public raster tiles for the Cayce bbox into preview PNGs.

One-off, low-volume use: identifying User-Agent, on-disk cache, polite delay.
"""

import sys
import time
from pathlib import Path

import requests
from PIL import Image

from maptools import CAYCE_BBOX, TILE_SIZE, crop_box, tile_range

ZOOM = 16
USER_AGENT = "HelmetHeadsMapPreview/1.0 (one-off print preview; andrew@beveridge.uk)"
STYLES = {
    "osm-carto": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "cyclosm": "https://a.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png",
}
ROOT = Path(__file__).resolve().parent.parent  # map/
CACHE = ROOT / "cache"
PREVIEWS = ROOT / "previews"


def fetch_tile(style: str, url_tpl: str, z: int, x: int, y: int) -> Image.Image:
    cached = CACHE / style / str(z) / str(x) / f"{y}.png"
    if not cached.exists():
        cached.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(
            url_tpl.format(z=z, x=x, y=y),
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        resp.raise_for_status()
        cached.write_bytes(resp.content)
        time.sleep(0.25)
    return Image.open(cached).convert("RGB")


def stitch(style: str) -> Path:
    url_tpl = STYLES[style]
    xs, ys = tile_range(CAYCE_BBOX, ZOOM)
    canvas = Image.new("RGB", (len(xs) * TILE_SIZE, len(ys) * TILE_SIZE))
    total, done = len(xs) * len(ys), 0
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            canvas.paste(fetch_tile(style, url_tpl, ZOOM, x, y), (i * TILE_SIZE, j * TILE_SIZE))
            done += 1
            print(f"\r{style}: {done}/{total} tiles", end="", flush=True)
    print()
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    out = PREVIEWS / f"{style}.png"
    canvas.crop(crop_box(CAYCE_BBOX, ZOOM)).save(out)
    return out


if __name__ == "__main__":
    for style in sys.argv[1:] or list(STYLES):
        print(f"saved {stitch(style)}")
