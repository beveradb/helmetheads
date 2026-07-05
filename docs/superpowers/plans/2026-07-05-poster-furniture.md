# Poster Furniture (Phase 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compose the print-ready 48×48 in Helmet Heads wall-map poster — title band, logo, legend, scale bar, north arrow, school marker — over the Phase 2 map, output as a vector PDF plus proofs, all script-generated and reproducible.

**Architecture:** Extend `maptools.py` with an aspect-fit helper, re-render the base+overlay at a trimmed bbox that fills the sub-band map slot (`render/render-poster.sh` → `poster-map.png`), then a Python builder (`map/scripts/build_poster.py`) assembles an SVG (vector furniture + embedded map raster) which `render/build-poster.sh` converts to PDF + 300 dpi PNG + letter-size proofs via `rsvg-convert` in the tools container. Brand fonts (Bebas Neue, Montserrat) are fetched into the container's font path.

**Tech Stack:** Phase 1 `map/` uv env (PIL, maptools) for geometry/compositing; Phase 2 Docker tools image (nik4 for the render) + `librsvg2-bin` (added) for SVG→PDF/PNG; brand fonts from Google Fonts; vector logo `logo.svg` / `logo-3000px.png` from the repo root.

## Global Constraints

- Canvas: **14400×14400 px** (48×48 in @ 300 dpi). Title band: top **900 px** (3 in). Map slot: **14400×13500 px** at y=900.
- Brand palette: maroon `#71161c`, red `#e63946`, amber `#f59e0b`, cream `#f4ede3`, ink `#231f20`.
- Fonts: **Bebas Neue** (display: wordmark, "RIDE MAP", legend/section headers), **Montserrat** (subtitle, labels, legend rows, attribution). Fetched to `map/render/fonts/` and installed into the container fontconfig before rendering.
- Map bbox (tight print bbox, Phase 2): W `-81.100988`, S `33.943360`, E `-81.035242`, N `33.998016`. School: `-81.056747, 33.981738`. Overlay opacity stays **0.5**.
- **Trimmed poster bbox:** keep W/E and the bbox's center latitude; trim N-S so the mercator aspect = 13500/14400 = **0.9375** (fills the map slot at 14400 px wide → 13500 px tall). Computed by `fit_bbox_to_aspect` (Task 1), never hand-typed.
- Git-ignore all generated output (`render/out/`, `render/fonts/` — add fonts/ to the existing render ignore). Commit only scripts + the two doc files. **Never push.**
- Assets consumed from the **repo root** (one level above `map/`): `logo.svg`, `logo-3000px.png`. They exist and are committed.
- All render/convert commands run in the tools container from `map/render/`; Python geometry/compositing runs in the `map/` uv env. Docker must be running (else BLOCKED).

---

### Task 1: Aspect-fit bbox helpers in maptools (TDD)

**Files:**
- Modify: `map/scripts/maptools.py`
- Modify: `map/scripts/test_maptools.py`

**Interfaces:**
- Consumes: existing `BBox`, `CAYCE_BBOX`, `deg2xy`, `mercator_aspect`.
- Produces:
  - `y_to_lat(y: float) -> float` — inverse of deg2xy's y at zoom 0 (Web-Mercator y-fraction → latitude degrees).
  - `fit_bbox_to_aspect(bbox: BBox, aspect: float) -> BBox` — returns a bbox with the same west/east and the same center latitude, whose N-S extent is set so `mercator_aspect(result) == aspect` (used with aspect 0.9375). Trims (or extends) symmetrically about the center latitude.

- [ ] **Step 1: Add failing tests to `map/scripts/test_maptools.py`**

```python
from maptools import (
    CAYCE_BBOX, deg2xy, fit_bbox_to_aspect, mercator_aspect, y_to_lat,
)


def test_y_to_lat_inverts_deg2xy():
    for lat in (33.94, 33.97, 33.998, 0.0, 51.5):
        _, y = deg2xy(lat, 0.0, 0)
        assert abs(y_to_lat(y) - lat) < 1e-9


def test_fit_bbox_to_aspect_hits_target_aspect():
    fitted = fit_bbox_to_aspect(CAYCE_BBOX, 0.9375)
    assert abs(mercator_aspect(fitted) - 0.9375) < 1e-6


def test_fit_bbox_preserves_west_east_and_center_lat():
    fitted = fit_bbox_to_aspect(CAYCE_BBOX, 0.9375)
    assert fitted.west == CAYCE_BBOX.west and fitted.east == CAYCE_BBOX.east
    assert abs((fitted.south + fitted.north) / 2 - (CAYCE_BBOX.south + CAYCE_BBOX.north) / 2) < 1e-9


def test_fit_bbox_to_smaller_aspect_trims_north_south():
    # 0.9375 < current (~1.0024): N-S must shrink, so it stays inside the original.
    fitted = fit_bbox_to_aspect(CAYCE_BBOX, 0.9375)
    assert fitted.north < CAYCE_BBOX.north and fitted.south > CAYCE_BBOX.south
```

- [ ] **Step 2: Run tests to confirm they fail**

Run (from `map/`): `uv run pytest scripts/test_maptools.py -v`
Expected: the four new tests fail with `ImportError` (names not defined).

- [ ] **Step 3: Implement in `map/scripts/maptools.py`** (append these functions; add `import math` already present)

```python
def y_to_lat(y: float) -> float:
    """Inverse of deg2xy's y at zoom 0: Web-Mercator y-fraction -> latitude degrees."""
    return math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * y))))


def fit_bbox_to_aspect(bbox: BBox, aspect: float) -> BBox:
    """Return a bbox with the same west/east and center latitude whose
    mercator_aspect equals `aspect`, by adjusting the N-S extent symmetrically."""
    x_w, _ = deg2xy(0.0, bbox.west, 0)
    x_e, _ = deg2xy(0.0, bbox.east, 0)
    _, y_n = deg2xy(bbox.north, 0.0, 0)
    _, y_s = deg2xy(bbox.south, 0.0, 0)
    y_center = (y_n + y_s) / 2.0
    dy = aspect * (x_e - x_w)  # desired mercator height
    north = y_to_lat(y_center - dy / 2.0)
    south = y_to_lat(y_center + dy / 2.0)  # y increases southward
    return BBox(west=bbox.west, south=south, east=bbox.east, north=north)
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `uv run pytest scripts/test_maptools.py -v`
Expected: all tests pass (the original 5 + 4 new = 9).

- [ ] **Step 5: Commit**

```bash
git add scripts/maptools.py scripts/test_maptools.py
git commit -m "feat(map): aspect-fit bbox helper for poster map slot"
```

---

### Task 2: Render the poster map (trimmed bbox, full width)

**Files:**
- Create: `map/render/render-poster.sh`
- Create: `map/scripts/composite_poster.py`

**Interfaces:**
- Consumes: `checkouts/{openstreetmap-carto,cyclosm-lite}/mapnik-print.xml` (Phase 2 builds); `maptools.fit_bbox_to_aspect`; nik4.py in the tools image.
- Produces: `render/out/poster-map.png` — the 50%-overlay composite at **14400×13500** covering the trimmed bbox. Also leaves `render/out/poster-base.png` and `render/out/poster-overlay.png`.

- [ ] **Step 1: Create `map/render/render-poster.sh`**

```bash
#!/usr/bin/env bash
# Render osm-carto + cyclosm-lite at the trimmed poster bbox (fills the 14400x13500
# map slot below the title band). Height is derived by nik4 from the bbox aspect.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out

# Compute the trimmed bbox (same E/W + center lat as the print bbox, mercator aspect 0.9375).
read -r W S E N < <(cd .. && uv run python -c "
from maptools import CAYCE_BBOX, fit_bbox_to_aspect
b = fit_bbox_to_aspect(CAYCE_BBOX, 13500/14400)
print(b.west, b.south, b.east, b.north)
")
echo "poster bbox: W=$W S=$S E=$E N=$N"

for pair in "openstreetmap-carto poster-base.png" "cyclosm-lite poster-overlay.png"; do
  set -- $pair
  docker compose run --rm tools \
    nik4.py --bbox "$W" "$S" "$E" "$N" --size-px 14400 0 --ppi 300 \
      "/checkouts/$1/mapnik-print.xml" "/out/$2"
done
ls -la out/poster-base.png out/poster-overlay.png
```

- [ ] **Step 2: Create `map/scripts/composite_poster.py`**

```python
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
```

- [ ] **Step 3: Render and composite**

```bash
chmod +x render-poster.sh
./render-poster.sh
cd .. && uv run python scripts/composite_poster.py
```

Expected: both renders are **14400×13500** (identical); `poster-map.png` saved at 14400×13500. If nik4 yields 14400×13499 or ×13501 (rounding), that is acceptable — the builder scales the image to the 14400×13500 slot. If width isn't 14400, stop and report (bbox aspect wrong).

- [ ] **Step 4: Visual check (downscaled)**

```bash
uv run python -c "
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
im=Image.open('render/out/poster-map.png'); print(im.size)
s=im.copy(); s.thumbnail((900,900)); s.save('$SCRATCH/poster-map-small.png')
"
```
(Replace `$SCRATCH` with the session scratchpad dir.) Read the small copy: confirm it's the Cayce map with the 50% cycling overlay, school area roughly centered, no title band yet (that's Task 3).

- [ ] **Step 5: Commit**

```bash
cd render && git add render-poster.sh ../scripts/composite_poster.py
git commit -m "feat(map): render poster map at trimmed bbox, 50% overlay composite"
```

---

### Task 3: Fonts + tools image, and the SVG poster builder

**Files:**
- Modify: `map/render/Dockerfile.tools` (add `librsvg2-bin`, `fontconfig`)
- Modify: `map/.gitignore` (add `render/fonts/`)
- Create: `map/render/get-poster-fonts.sh`
- Create: `map/scripts/build_poster.py`

**Interfaces:**
- Consumes: `render/out/poster-map.png`; repo-root `logo.svg` / `logo-3000px.png`; `maptools` (school placement, scale). 
- Produces: `render/fonts/{BebasNeue-Regular.ttf,Montserrat-Regular.ttf,Montserrat-SemiBold.ttf}`; `render/out/poster.svg` referencing `poster-map.png`, `logo-3000px.png`, and the fonts by absolute container path.

- [ ] **Step 1: Add to `map/render/Dockerfile.tools`** (extend the apt list; keep everything else)

Add `librsvg2-bin fontconfig` to the `apt-get install` package list (so `rsvg-convert` and `fc-cache` are available). Then rebuild in Step 4.

- [ ] **Step 2: Append `render/fonts/` to `map/.gitignore`**

```gitignore
render/fonts/
```

- [ ] **Step 3: Create `map/render/get-poster-fonts.sh`**

```bash
#!/usr/bin/env bash
# Fetch the club's brand fonts (used by the site) for the poster.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p fonts
base="https://github.com/google/fonts/raw/main"
fetch() { [ -f "fonts/$2" ] || curl -fsSL "$1" -o "fonts/$2"; }
fetch "$base/ofl/bebasneue/BebasNeue-Regular.ttf" BebasNeue-Regular.ttf
fetch "$base/ofl/montserrat/Montserrat%5Bwght%5D.ttf" Montserrat.ttf
ls -la fonts/
```

(If a URL 404s — Google Fonts repo paths occasionally move — find the current path for that family in `github.com/google/fonts` and update the URL, keeping the output filename. Montserrat ships as a variable font here; that is fine for rsvg/fontconfig. Record any URL change.)

- [ ] **Step 4: Build/verify fonts in the container**

```bash
chmod +x get-poster-fonts.sh && ./get-poster-fonts.sh
docker compose build tools
# Install fonts into the container fontconfig and confirm they resolve:
docker compose run --rm tools bash -c "
  mkdir -p /usr/share/fonts/truetype/poster &&
  cp /render/fonts/*.ttf /usr/share/fonts/truetype/poster/ && fc-cache -f >/dev/null &&
  fc-match 'Bebas Neue' && fc-match 'Montserrat'
"
```

Expected: `fc-match` reports Bebas Neue and Montserrat resolving to the copied TTFs (not a fallback like DejaVu). If they fall back, the family names in `build_poster.py` (Step 5) must match what `fc-scan /render/fonts/*.ttf | grep family` reports — use those exact names and note it.

- [ ] **Step 5: Create `map/scripts/build_poster.py`**

```python
"""Assemble the Helmet Heads poster SVG: title band, logo, map, school marker,
legend, scale bar, north arrow, attribution. Vector furniture + embedded map raster.
Coordinates are in the 14400x14400 px canvas (48in @ 300dpi)."""

from pathlib import Path

from maptools import CAYCE_BBOX, deg2xy, fit_bbox_to_aspect

# --- geometry ---
W = H = 14400
BAND_H = 900
MAP_Y = BAND_H
MAP_W, MAP_H = 14400, 13500
SCHOOL_LAT, SCHOOL_LON = 33.981738, -81.056747

ROOT = Path(__file__).resolve().parent.parent  # map/
REPO = ROOT.parent
OUT = ROOT / "render" / "out"
FONTS = ROOT / "render" / "fonts"

# Colors
MAROON, RED, AMBER, CREAM, INK = "#71161c", "#e63946", "#f59e0b", "#f4ede3", "#231f20"

bbox = fit_bbox_to_aspect(CAYCE_BBOX, MAP_H / MAP_W)

# School pixel position within the map slot (mercator fractions, zoom cancels).
xw, yn = deg2xy(bbox.north, bbox.west, 0)
xe, ys = deg2xy(bbox.south, bbox.east, 0)
xs, ysc = deg2xy(SCHOOL_LAT, SCHOOL_LON, 0)
sx = (xs - xw) / (xe - xw) * MAP_W
sy = MAP_Y + (ysc - yn) / (ys - yn) * MAP_H

# Scale bar: ground metres across the full width, then px per mile / km.
ground_m = (bbox.east - bbox.west) * (40075017.0 / 360.0) * __import__("math").cos(
    __import__("math").radians((bbox.north + bbox.south) / 2))
ppm = MAP_W / ground_m
mile_px, km_px = 1609.344 * ppm, 1000.0 * ppm

# Fonts embedded via @font-face so rsvg uses them regardless of install name.
def font_face(family, fname):
    return f"@font-face{{font-family:'{family}';src:url('file://{FONTS/fname}');}}"

faces = "\n".join([
    font_face("Bebas Neue", "BebasNeue-Regular.ttf"),
    font_face("Montserrat", "Montserrat.ttf"),
])

# Legend rows: (kind, color, dash, label). kind: line|swatch|star
LEGEND = [
    ("line", "#1f4fd6", None, "Greenway / cycle track"),
    ("line", "#1f4fd6", "26,18", "On-road cycle route"),
    ("line", RED, "10,14", "Cycle lane"),
    ("swatch", "#b8dfa9", None, "Park"),
    ("star", MAROON, None, "School"),
]

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")

parts = []
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}">')
parts.append(f'<style>{faces}</style>')
parts.append(f'<rect width="{W}" height="{H}" fill="{CREAM}"/>')

# Map image
parts.append(f'<image x="0" y="{MAP_Y}" width="{MAP_W}" height="{MAP_H}" '
             f'href="file://{OUT/"poster-map.png"}" preserveAspectRatio="none"/>')

# Title band
parts.append(f'<rect width="{W}" height="{BAND_H}" fill="{MAROON}"/>')
# Logo (transparent PNG) left-aligned in the band
logo_h = 700
logo_w = round(logo_h * 3000 / 3643)
parts.append(f'<image x="120" y="{(BAND_H-logo_h)//2}" width="{logo_w}" height="{logo_h}" '
             f'href="file://{REPO/"logo-3000px.png"}"/>')
tx = 120 + logo_w + 120
parts.append(f'<text x="{tx}" y="590" font-family="Bebas Neue" font-size="500" '
             f'fill="{CREAM}" letter-spacing="8">HELMET HEADS</text>')
parts.append(f'<text x="{tx+8}" y="770" font-family="Montserrat" font-size="150" '
             f'font-weight="600" fill="{CREAM}">Brookland-Cayce Cycling Club</text>')
parts.append(f'<text x="{W-160}" y="470" font-family="Bebas Neue" font-size="300" '
             f'fill="{AMBER}" text-anchor="end" letter-spacing="6">RIDE MAP</text>')
parts.append(f'<text x="{W-160}" y="650" font-family="Montserrat" font-size="140" '
             f'fill="{CREAM}" text-anchor="end">Cayce, South Carolina</text>')

# School marker: star + callout pill
def star(cx, cy, r, fill, stroke, sw):
    import math
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        pts.append(f"{cx+rad*math.cos(ang):.1f},{cy+rad*math.sin(ang):.1f}")
    return (f'<polygon points="{" ".join(pts)}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')

parts.append(star(sx, sy, 150, MAROON, CREAM, 22))
pill_w, pill_h = 1150, 210
px0, py0 = sx + 120, sy - pill_h / 2
parts.append(f'<rect x="{px0:.0f}" y="{py0:.0f}" width="{pill_w}" height="{pill_h}" '
             f'rx="40" fill="{CREAM}" fill-opacity="0.92" stroke="{MAROON}" stroke-width="8"/>')
parts.append(f'<text x="{px0+50:.0f}" y="{sy+45:.0f}" font-family="Montserrat" '
             f'font-size="120" font-weight="600" fill="{INK}">Brookland-Cayce HS</text>')

# Legend panel (bottom-right)
lp_w, lp_h = 3560, 1760
lx, ly = W - lp_w - 200, H - lp_h - 200
parts.append(f'<rect x="{lx}" y="{ly}" width="{lp_w}" height="{lp_h}" rx="60" '
             f'fill="{CREAM}" fill-opacity="0.94" stroke="{INK}" stroke-width="8"/>')
parts.append(f'<text x="{lx+90}" y="{ly+230}" font-family="Bebas Neue" font-size="200" '
             f'fill="{MAROON}" letter-spacing="4">LEGEND</text>')
row_y = ly + 430
for kind, color, dash, label in LEGEND:
    swx = lx + 120
    if kind == "line":
        d = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(f'<line x1="{swx}" y1="{row_y}" x2="{swx+360}" y2="{row_y}" '
                     f'stroke="{color}" stroke-width="26"{d}/>')
    elif kind == "swatch":
        parts.append(f'<rect x="{swx}" y="{row_y-70}" width="360" height="140" '
                     f'rx="16" fill="{color}" stroke="{INK}" stroke-width="4"/>')
    else:
        parts.append(star(swx + 180, row_y, 90, MAROON, CREAM, 12))
    parts.append(f'<text x="{swx+470}" y="{row_y+55}" font-family="Montserrat" '
                 f'font-size="140" fill="{INK}">{esc(label)}</text>')
    row_y += 250

# Scale bar + north arrow (bottom-left)
sbx, sby = 260, H - 360
for length, lbl, off in [(mile_px, "1 mile", 0), (km_px, "1 km", 150)]:
    y = sby + off
    parts.append(f'<line x1="{sbx}" y1="{y}" x2="{sbx+length:.0f}" y2="{y}" '
                 f'stroke="{INK}" stroke-width="14"/>')
    for xx in (sbx, sbx + length):
        parts.append(f'<line x1="{xx:.0f}" y1="{y-28}" x2="{xx:.0f}" y2="{y+28}" '
                     f'stroke="{INK}" stroke-width="14"/>')
    parts.append(f'<text x="{sbx+length+40:.0f}" y="{y+45}" font-family="Montserrat" '
                 f'font-size="120" fill="{INK}">{lbl}</text>')
# North arrow
nax, nay = sbx + 120, sby - 360
parts.append(f'<polygon points="{nax},{nay-160} {nax-70},{nay+60} {nax},{nay} '
             f'{nax+70},{nay+60}" fill="{INK}"/>')
parts.append(f'<text x="{nax}" y="{nay+230}" font-family="Bebas Neue" font-size="160" '
             f'fill="{INK}" text-anchor="middle">N</text>')

# Attribution footer
parts.append(f'<text x="{W//2}" y="{H-90}" font-family="Montserrat" font-size="96" '
             f'fill="{INK}" text-anchor="middle" opacity="0.85">'
             f'Map data © OpenStreetMap contributors (ODbL) · Cycling data © CyclOSM '
             f'· Made for the Helmet Heads cycling club</text>')

parts.append("</svg>")
(OUT / "poster.svg").write_text("\n".join(parts))
print("saved", OUT / "poster.svg", "school@", (round(sx), round(sy)),
      "mile_px", round(mile_px))
```

- [ ] **Step 6: Build the SVG**

```bash
cd .. && uv run python scripts/build_poster.py
```

Expected: prints the saved path, the school pixel position (should be roughly centered horizontally, upper-middle vertically), and `mile_px` (~3800). No exception.

- [ ] **Step 7: Commit**

```bash
git add render/Dockerfile.tools .gitignore render/get-poster-fonts.sh scripts/build_poster.py
git commit -m "feat(map): poster fonts + SVG furniture builder"
```

---

### Task 4: Render poster to PDF + proofs, handoff

**Files:**
- Create: `map/render/build-poster.sh`

**Interfaces:**
- Consumes: `render/out/poster.svg`, fonts, `rsvg-convert` in the tools image; `map/` uv env for the proof crops.
- Produces: `render/out/poster.pdf` (vector furniture + embedded map), `render/out/poster-proof.png` (300 dpi full-poster proof, downscaled for viewing), and two 100%-scale US-letter proof crops (`poster-letter-title.png`, `poster-letter-legend.png`).

- [ ] **Step 1: Create `map/render/build-poster.sh`**

```bash
#!/usr/bin/env bash
# Convert the poster SVG to a print-ready PDF and a PNG proof via rsvg-convert.
set -euo pipefail
cd "$(dirname "$0")"

# Ensure brand fonts are resolvable inside the container.
docker compose run --rm tools bash -c "
  set -e
  mkdir -p /usr/share/fonts/truetype/poster
  cp /render/fonts/*.ttf /usr/share/fonts/truetype/poster/
  fc-cache -f >/dev/null
  cd /out
  rsvg-convert -f pdf -o poster.pdf poster.svg
  rsvg-convert -f png -o poster-proof-full.png poster.svg
"
ls -la out/poster.pdf out/poster-proof-full.png
```

- [ ] **Step 2: Render PDF + proof**

```bash
chmod +x build-poster.sh && ./build-poster.sh
```

Expected: `poster.pdf` (tens of MB — embeds the map raster) and `poster-proof-full.png` (14400×14400) produced. If `rsvg-convert` errors on the `file://` font-face or image href, switch those to plain absolute paths (drop `file://`) in `build_poster.py`, rebuild the SVG, and note it. If the wordmark/labels render in a fallback font (thin/serif), the font-face src path is wrong — fix the path, not the family name.

- [ ] **Step 3: Make proof crops (100% scale, US-letter) + downscaled full proof**

```bash
cd .. && uv run python -c "
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
im=Image.open('render/out/poster-proof-full.png'); print('poster', im.size)
# Downscaled whole-poster proof for review
s=im.copy(); s.thumbnail((1000,1000)); s.save('$SCRATCH/poster-proof-small.png')
# 100%-scale letter crops (2400x3150) of the title band and the legend corner
im.crop((0,0,2400,3150)).save('render/out/poster-letter-title.png', dpi=(300,300))
w,h=im.size
im.crop((w-2400,h-3150,w,h)).save('render/out/poster-letter-legend.png', dpi=(300,300))
print('crops saved')
"
```

(Replace `$SCRATCH`.) Read `poster-proof-small.png`: confirm the whole poster reads — maroon band with logo + "HELMET HEADS" in Bebas Neue, subtitle, "RIDE MAP", the map filling below with the school ★ + callout, legend panel bottom-right, scale bar + north arrow bottom-left, attribution footer. Note any overlap/clipping/font-fallback for a tuning pass.

- [ ] **Step 4: Commit**

```bash
cd render && git add build-poster.sh
git commit -m "feat(map): render poster to print-ready PDF + letter proofs"
```

- [ ] **Step 5: Hand to the user (Phase 3 decision gate)**

Copy `render/out/poster.pdf` and the two `poster-letter-*.png` crops somewhere handy (e.g. `~/Downloads/`), and tell the user: review the full `poster.pdf`; print the two letter crops at **Actual Size** to check the title-band and legend text sharpness; confirm the layout/branding or request tweaks (band height, font sizes, legend wording, marker position). After approval, the remaining step is exporting the final file per the print shop's spec (bleed/format) — planned once the shop's requirements are known.
