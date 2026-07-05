# Map Style Previews (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render the Cayce, SC bbox in 6 candidate map styles at ~3000 px and produce a `compare.html` contact sheet so the user can pick a style direction for the final 48×48 in print.

**Architecture:** A small Python project under `map/` with three independent renderers sharing one pure-math module (`maptools.py`): (1) tile stitching from public OSM/CyclOSM tile servers, (2) MapLibre GL headless screenshots of OpenFreeMap styles via Playwright, (3) a prettymaps artistic render. Outputs land in `map/previews/` (git-ignored) and are reviewed via a static `compare.html`.

**Tech Stack:** Python ≥3.11 managed with `uv`; `requests` + `Pillow` (stitching); `playwright` (headless Chromium for MapLibre); `prettymaps` (artistic render); `pytest` (tile-math tests).

## Global Constraints

- Bbox (WGS84, from spec / `map-area-corners.txt`): W `-81.100988`, S `33.943360`, E `-81.035242`, N `33.998016`. School: `-81.056747, 33.981738`.
- Tile zoom for stitched previews: `16`.
- Tile requests MUST send User-Agent `HelmetHeadsMapPreview/1.0 (one-off print preview; andrew@beveridge.uk)` and sleep ≥0.25 s between uncached downloads (OSM tile usage policy).
- All preview outputs go to `map/previews/`, tile cache to `map/cache/` — both git-ignored (this repo deploys as a static site; don't ship multi-MB previews).
- All commands below run from the `map/` directory unless stated otherwise.
- This repo's workflow: execute in an isolated worktree (superpowers:using-git-worktrees), never commit to main directly.

---

### Task 1: Scaffold the `map/` project

**Files:**
- Create: `map/pyproject.toml`
- Create: `map/.gitignore`
- Create: `map/README.md`
- Commit (already written, currently untracked): `docs/superpowers/specs/2026-07-03-print-map-design.md`, `docs/superpowers/plans/2026-07-03-map-style-previews.md`

**Interfaces:**
- Consumes: nothing.
- Produces: a `uv`-managed Python env that Tasks 2–6 run inside via `uv run`.

- [ ] **Step 1: Create `map/pyproject.toml`**

```toml
[project]
name = "helmetheads-map"
version = "0.1.0"
description = "Print-map rendering pipeline for the Helmet Heads bike room wall map"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.32",
    "pillow>=10",
    "playwright>=1.45",
    "prettymaps>=1.0",
]

[dependency-groups]
dev = ["pytest>=8"]
```

- [ ] **Step 2: Create `map/.gitignore`**

```gitignore
previews/
cache/
.venv/
__pycache__/
```

- [ ] **Step 3: Create `map/README.md`**

```markdown
# Helmet Heads wall map pipeline

Renders the club riding area of Cayce, SC (bbox in `../map-area-corners.txt`)
for a ~48×48 in wall print. Spec: `../docs/superpowers/specs/2026-07-03-print-map-design.md`.

## Phase 1 — style previews

Setup (once):

    uv sync
    uv run playwright install chromium

Render all previews:

    uv run python scripts/stitch_tiles.py        # osm-carto, cyclosm
    uv run python scripts/render_maplibre.py     # positron, bright, liberty
    uv run python scripts/render_prettymaps.py   # artistic

Then open `compare.html` in a browser.

Bonus reference render: submit the bbox at https://print.get-map.org (MapOSMatic)
and drop the PDF into `previews/` manually.

Data/tiles © OpenStreetMap contributors (ODbL). Preview tiles courtesy of
OSMF (osm-carto), CyclOSM/OSM France, and OpenFreeMap — previews are for
internal style comparison, not redistribution.
```

- [ ] **Step 4: Verify the environment builds**

Run (from `map/`): `uv sync && uv run playwright install chromium`
Expected: lockfile created, deps resolve (prettymaps pulls osmnx/geopandas — slow first time), Chromium downloads without error.

- [ ] **Step 5: Commit** (from the repo root)

```bash
git add map/pyproject.toml map/uv.lock map/.gitignore map/README.md \
  docs/superpowers/specs/2026-07-03-print-map-design.md \
  docs/superpowers/plans/2026-07-03-map-style-previews.md
git commit -m "feat(map): scaffold Phase 1 style-preview pipeline (spec + plan + uv project)"
```

---

### Task 2: Tile/mercator math module (`maptools.py`) — TDD

**Files:**
- Create: `map/scripts/maptools.py`
- Test: `map/scripts/test_maptools.py`

**Interfaces:**
- Consumes: nothing.
- Produces (used by Tasks 3–5):
  - `BBox(west, south, east, north)` NamedTuple of floats; constant `CAYCE_BBOX: BBox`; constant `TILE_SIZE = 256`.
  - `deg2xy(lat: float, lon: float, zoom: int) -> tuple[float, float]` — fractional slippy-tile coords.
  - `deg2num(lat: float, lon: float, zoom: int) -> tuple[int, int]` — integer tile indices.
  - `tile_range(bbox: BBox, zoom: int) -> tuple[range, range]` — inclusive x and y tile ranges covering the bbox.
  - `crop_box(bbox: BBox, zoom: int) -> tuple[int, int, int, int]` — (left, top, right, bottom) pixel crop within the stitched tile grid.
  - `mercator_aspect(bbox: BBox) -> float` — bbox height/width ratio in Web-Mercator units.

- [ ] **Step 1: Write the failing tests** — `map/scripts/test_maptools.py`

```python
from maptools import CAYCE_BBOX, crop_box, deg2num, deg2xy, mercator_aspect, tile_range


def test_deg2xy_origin_is_center_of_world():
    assert deg2xy(0.0, 0.0, 0) == (0.5, 0.5)


def test_deg2num_london_z10():
    # Known slippy tile for central London at z10.
    assert deg2num(51.5074, -0.1278, 10) == (511, 340)


def test_tile_range_cayce_z16():
    xs, ys = tile_range(CAYCE_BBOX, 16)
    assert (xs.start, xs.stop - 1) == (18004, 18015)
    assert (ys.start, ys.stop - 1) == (26180, 26191)


def test_crop_box_lies_within_stitched_image():
    xs, ys = tile_range(CAYCE_BBOX, 16)
    left, top, right, bottom = crop_box(CAYCE_BBOX, 16)
    assert 0 <= left < right <= len(xs) * 256
    assert 0 <= top < bottom <= len(ys) * 256


def test_cayce_bbox_is_nearly_square_in_mercator():
    assert abs(mercator_aspect(CAYCE_BBOX) - 1.0) < 0.02
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest scripts/test_maptools.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'maptools'`

- [ ] **Step 3: Implement `map/scripts/maptools.py`**

```python
"""Slippy-tile and Web-Mercator math shared by the preview renderers."""

import math
from typing import NamedTuple

TILE_SIZE = 256


class BBox(NamedTuple):
    west: float
    south: float
    east: float
    north: float


# From map-area-corners.txt — the club riding area around BCHS, Cayce, SC.
CAYCE_BBOX = BBox(west=-81.100988, south=33.943360, east=-81.035242, north=33.998016)


def deg2xy(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    n = 2**zoom
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def deg2num(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    x, y = deg2xy(lat, lon, zoom)
    return int(x), int(y)


def tile_range(bbox: BBox, zoom: int) -> tuple[range, range]:
    x_min, y_min = deg2num(bbox.north, bbox.west, zoom)
    x_max, y_max = deg2num(bbox.south, bbox.east, zoom)
    return range(x_min, x_max + 1), range(y_min, y_max + 1)


def crop_box(bbox: BBox, zoom: int) -> tuple[int, int, int, int]:
    """Pixel crop (left, top, right, bottom) of the bbox within the stitched tile grid."""
    xs, ys = tile_range(bbox, zoom)
    x_w, y_n = deg2xy(bbox.north, bbox.west, zoom)
    x_e, y_s = deg2xy(bbox.south, bbox.east, zoom)
    return (
        round((x_w - xs.start) * TILE_SIZE),
        round((y_n - ys.start) * TILE_SIZE),
        round((x_e - xs.start) * TILE_SIZE),
        round((y_s - ys.start) * TILE_SIZE),
    )


def mercator_aspect(bbox: BBox) -> float:
    """Height/width ratio of the bbox in Web-Mercator units (for render viewports)."""
    x_w, y_n = deg2xy(bbox.north, bbox.west, 0)
    x_e, y_s = deg2xy(bbox.south, bbox.east, 0)
    return (y_s - y_n) / (x_e - x_w)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest scripts/test_maptools.py -v`
Expected: 5 passed. (If `test_tile_range_cayce_z16` fails by exactly ±1 on a boundary, re-derive the expected tile indices from the formula by hand before touching the implementation — the other four tests pin the math.)

- [ ] **Step 5: Commit**

```bash
git add scripts/maptools.py scripts/test_maptools.py
git commit -m "feat(map): tile/mercator math with tests"
```

---

### Task 3: Tile-stitched previews — OSM Carto + CyclOSM

**Files:**
- Create: `map/scripts/stitch_tiles.py`

**Interfaces:**
- Consumes: `CAYCE_BBOX`, `TILE_SIZE`, `tile_range`, `crop_box` from `maptools`.
- Produces: `map/previews/osm-carto.png` and `map/previews/cyclosm.png` (~3064×3071 px). CLI: `uv run python scripts/stitch_tiles.py [style ...]` with styles `osm-carto`, `cyclosm` (default: both).

- [ ] **Step 1: Implement `map/scripts/stitch_tiles.py`**

```python
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
```

- [ ] **Step 2: Run it (both styles)**

Run: `uv run python scripts/stitch_tiles.py`
Expected: progress to `144/144 tiles` per style (~1–2 min each on first run), then `saved .../previews/osm-carto.png` and `saved .../previews/cyclosm.png`.

- [ ] **Step 3: Verify output dimensions and content**

Run: `uv run python -c "from PIL import Image; [print(s, Image.open(f'previews/{s}.png').size) for s in ('osm-carto','cyclosm')]"`
Expected: both ~`(3064, 3071)` (±2 px). Open one PNG and eyeball: the Congaree River should cross the NE corner and the street grid of Cayce should fill the frame.

- [ ] **Step 4: Verify the cache makes re-runs instant**

Run: `uv run python scripts/stitch_tiles.py osm-carto`
Expected: completes in seconds (no network fetches).

- [ ] **Step 5: Commit**

```bash
git add scripts/stitch_tiles.py
git commit -m "feat(map): stitched osm-carto and cyclosm previews"
```

---

### Task 4: MapLibre headless renders — Positron / Bright / Liberty

**Files:**
- Create: `map/scripts/maplibre.html`
- Create: `map/scripts/render_maplibre.py`

**Interfaces:**
- Consumes: `CAYCE_BBOX`, `mercator_aspect` from `maptools`; Playwright Chromium installed in Task 1.
- Produces: `map/previews/positron.png`, `map/previews/bright.png`, `map/previews/liberty.png` (3200 px wide; viewport 1600 × round(1600·aspect) at deviceScaleFactor 2). CLI: `uv run python scripts/render_maplibre.py`.

- [ ] **Step 1: Create `map/scripts/maplibre.html`**

```html
<!doctype html>
<meta charset="utf-8" />
<title>Helmet Heads style preview</title>
<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.css" />
<script src="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.js"></script>
<style>
  html, body, #map { margin: 0; width: 100%; height: 100%; }
</style>
<div id="map"></div>
<script>
  const params = new URLSearchParams(location.search);
  const map = new maplibregl.Map({
    container: "map",
    style: params.get("style"),
    bounds: [[-81.100988, 33.943360], [-81.035242, 33.998016]],
    fitBoundsOptions: { padding: 0 },
    attributionControl: { compact: false },
    fadeDuration: 0,
  });
  map.once("idle", () => { window._mapReady = true; });
</script>
```

- [ ] **Step 2: Implement `map/scripts/render_maplibre.py`**

```python
"""Screenshot MapLibre GL renders of vector-tile styles for the Cayce bbox."""

from pathlib import Path

from playwright.sync_api import sync_playwright

from maptools import CAYCE_BBOX, mercator_aspect

STYLES = {
    "positron": "https://tiles.openfreemap.org/styles/positron",
    "bright": "https://tiles.openfreemap.org/styles/bright",
    "liberty": "https://tiles.openfreemap.org/styles/liberty",
}
ROOT = Path(__file__).resolve().parent.parent  # map/
WIDTH = 1600
HEIGHT = round(WIDTH * mercator_aspect(CAYCE_BBOX))


def render(name: str, style_url: str) -> Path:
    out = ROOT / "previews" / f"{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    page_url = (ROOT / "scripts" / "maplibre.html").as_uri() + f"?style={style_url}"
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(
            viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=2
        )
        page.goto(page_url)
        page.wait_for_function("window._mapReady === true", timeout=120_000)
        page.screenshot(path=str(out))
        browser.close()
    return out


if __name__ == "__main__":
    for name, url in STYLES.items():
        print(f"saved {render(name, url)}")
```

- [ ] **Step 3: Run it**

Run: `uv run python scripts/render_maplibre.py`
Expected: `saved .../previews/positron.png`, `bright.png`, `liberty.png` (~30–90 s total).

- [ ] **Step 4: Verify output dimensions and content**

Run: `uv run python -c "from PIL import Image; [print(s, Image.open(f'previews/{s}.png').size) for s in ('positron','bright','liberty')]"`
Expected: all `(3200, ~3208)`. Open `positron.png` and eyeball: greyscale base, same area as the Task 3 stitches (river in NE corner), MapLibre attribution visible bottom-right.

- [ ] **Step 5: Commit**

```bash
git add scripts/maplibre.html scripts/render_maplibre.py
git commit -m "feat(map): headless MapLibre previews (positron, bright, liberty)"
```

---

### Task 5: prettymaps artistic render

**Files:**
- Create: `map/scripts/render_prettymaps.py`

**Interfaces:**
- Consumes: `CAYCE_BBOX` from `maptools`.
- Produces: `map/previews/prettymaps.png`. CLI: `uv run python scripts/render_prettymaps.py`.

- [ ] **Step 1: Implement `map/scripts/render_prettymaps.py`**

```python
"""Artistic/poster-style render of the Cayce bbox via prettymaps."""

from pathlib import Path

import prettymaps

from maptools import CAYCE_BBOX

ROOT = Path(__file__).resolve().parent.parent  # map/
CENTER = (
    (CAYCE_BBOX.south + CAYCE_BBOX.north) / 2,
    (CAYCE_BBOX.west + CAYCE_BBOX.east) / 2,
)
RADIUS_M = 3040  # half the ~6.08 km bbox width; circle=False gives a square

out = ROOT / "previews" / "prettymaps.png"
out.parent.mkdir(parents=True, exist_ok=True)
plot = prettymaps.plot(CENTER, radius=RADIUS_M, circle=False, preset="barcelona")
plot.fig.savefig(out, dpi=300, bbox_inches="tight")
print(f"saved {out}")
```

- [ ] **Step 2: Run it**

Run: `uv run python scripts/render_prettymaps.py`
Expected: Overpass download takes a few minutes for a 6 km square, then `saved .../previews/prettymaps.png`. If the `prettymaps.plot(...)` signature errors, the installed version's API has drifted — fetch current docs (`npx ctx7@latest library "prettymaps" "plot square area preset savefig"`) and adapt only the call site; keep CENTER/RADIUS_M/out unchanged.

- [ ] **Step 3: Verify output**

Run: `uv run python -c "from PIL import Image; print(Image.open('previews/prettymaps.png').size)"`
Expected: a large PNG (exact size depends on prettymaps figure defaults; anything ≥2000 px wide is fine). Eyeball: stylized poster look, same street network as the other previews.

- [ ] **Step 4: Commit**

```bash
git add scripts/render_prettymaps.py
git commit -m "feat(map): prettymaps artistic preview"
```

---

### Task 6: Contact sheet + full run

**Files:**
- Create: `map/compare.html`

**Interfaces:**
- Consumes: the six PNGs in `map/previews/` from Tasks 3–5.
- Produces: `map/compare.html` — the user's review artifact (the Phase 1 decision gate).

- [ ] **Step 1: Create `map/compare.html`**

```html
<!doctype html>
<html lang="en">
<meta charset="utf-8" />
<title>Helmet Heads map — style comparison</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 1.5rem; background: #f4f4f4; }
  h1 { font-size: 1.3rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 1.5rem; }
  figure { margin: 0; background: #fff; padding: .75rem; border-radius: 8px; box-shadow: 0 1px 4px rgb(0 0 0 / .15); }
  figure img { width: 100%; height: auto; display: block; cursor: zoom-in; }
  figcaption { padding-top: .5rem; font-weight: 600; }
  figcaption small { font-weight: 400; color: #555; display: block; }
  footer { margin-top: 2rem; font-size: .8rem; color: #555; }
</style>
<h1>Helmet Heads wall map — style candidates (click an image to open full size)</h1>
<div class="grid">
  <figure><a href="previews/osm-carto.png" target="_blank"><img loading="lazy" src="previews/osm-carto.png" alt="OSM Carto" /></a>
    <figcaption>OSM Carto <small>Classic openstreetmap.org look — colorful, dense</small></figcaption></figure>
  <figure><a href="previews/cyclosm.png" target="_blank"><img loading="lazy" src="previews/cyclosm.png" alt="CyclOSM" /></a>
    <figcaption>CyclOSM <small>Cycling-focused — bike lanes/routes emphasized</small></figcaption></figure>
  <figure><a href="previews/positron.png" target="_blank"><img loading="lazy" src="previews/positron.png" alt="Positron" /></a>
    <figcaption>Positron <small>Minimal light greyscale — markers pop</small></figcaption></figure>
  <figure><a href="previews/bright.png" target="_blank"><img loading="lazy" src="previews/bright.png" alt="Bright" /></a>
    <figcaption>Bright <small>Clean but colored middle ground</small></figcaption></figure>
  <figure><a href="previews/liberty.png" target="_blank"><img loading="lazy" src="previews/liberty.png" alt="Liberty" /></a>
    <figcaption>Liberty <small>Minimal with character (OpenFreeMap default)</small></figcaption></figure>
  <figure><a href="previews/prettymaps.png" target="_blank"><img loading="lazy" src="previews/prettymaps.png" alt="prettymaps" /></a>
    <figcaption>prettymaps <small>Artistic/poster style — few or no labels</small></figcaption></figure>
</div>
<footer>Data © OpenStreetMap contributors (ODbL). Tiles/styles: OSMF, CyclOSM/OSM France, OpenFreeMap. Internal comparison use.</footer>
</html>
```

- [ ] **Step 2: Full pipeline run from clean previews**

Run (from `map/`):

```bash
rm -rf previews
uv run python scripts/stitch_tiles.py
uv run python scripts/render_maplibre.py
uv run python scripts/render_prettymaps.py
ls previews
```

Expected: `cyclosm.png  liberty.png  osm-carto.png  positron.png  bright.png  prettymaps.png` (tile stitches are fast — cache warm from Task 3).

- [ ] **Step 3: Verify the contact sheet renders**

Run: `open compare.html`
Expected: all six previews visible in the grid, captions correct, clicking opens full size.

- [ ] **Step 4: Commit**

```bash
git add compare.html
git commit -m "feat(map): style-comparison contact sheet"
```

- [ ] **Step 5: Hand to the user (Phase 1 decision gate)**

Tell the user: previews are ready — open `map/compare.html`, optionally add a MapOSMatic PDF (see `map/README.md`), and pick the style direction. Phase 2 (final print pipeline) gets planned only after that decision.
