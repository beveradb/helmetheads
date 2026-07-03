"""Artistic/poster-style render of the Cayce bbox via prettymaps."""

from pathlib import Path

import prettymaps

from maptools import CAYCE_BBOX

ROOT = Path(__file__).resolve().parent.parent  # map/
CENTER = (
    (CAYCE_BBOX.south + CAYCE_BBOX.north) / 2,
    (CAYCE_BBOX.west + CAYCE_BBOX.east) / 2,
)
RADIUS_M = 3040  # half ~6.08 km bbox width; circle=False gives square

out = ROOT / "previews" / "prettymaps.png"
out.parent.mkdir(parents=True, exist_ok=True)
# show=False: the installed prettymaps defaults to show=True, which blocks in the
# macOS GUI backend's event loop before plot() returns. Headless render only.
plot = prettymaps.plot(
    CENTER, radius=RADIUS_M, circle=False, preset="barcelona", show=False
)
plot.fig.savefig(out, dpi=300, bbox_inches="tight")
print(f"saved {out}")
