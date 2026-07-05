"""Assemble the Helmet Heads poster SVG: title band, logo, map, school marker,
legend, scale bar, north arrow, attribution. Vector furniture + embedded map raster.

Coordinates are in the 14400x14400 px canvas (48in @ 300dpi). All raster inputs
(the map, the logo) are colocated with the SVG in render/out/ and referenced by
RELATIVE path, so the SVG renders identically whether rsvg-convert runs on the
host or inside the tools container. Fonts resolve by family name via fontconfig
(the club's Bebas Neue + Montserrat, installed before rendering in build-poster.sh).
"""

import math
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maptools import CAYCE_BBOX, anchored_bbox, deg2xy

# --- canvas / geometry ---
W = H = 14400
BAND_H = 900
MAP_Y = BAND_H
MAP_W, MAP_H = 14400, 13500
SCHOOL_LAT, SCHOOL_LON = 33.981738, -81.056747

ROOT = Path(__file__).resolve().parent.parent  # map/
REPO = ROOT.parent                              # worktree root (holds logo assets)
OUT = ROOT / "render" / "out"

# --- brand palette ---
MAROON, RED, AMBER, CREAM, INK = "#71161c", "#e63946", "#f59e0b", "#f4ede3", "#231f20"
CYCLE_BLUE = "#1f4fd6"
PARK_GREEN = "#b8dfa9"

bbox = anchored_bbox(CAYCE_BBOX, 1.0, MAP_H / MAP_W)  # trim 1mi W + S, anchor NE

# School pixel position within the map slot (mercator fractions, zoom cancels).
xw, yn = deg2xy(bbox.north, bbox.west, 0)
xe, ys = deg2xy(bbox.south, bbox.east, 0)
xs, ysc = deg2xy(SCHOOL_LAT, SCHOOL_LON, 0)
sx = (xs - xw) / (xe - xw) * MAP_W
sy = MAP_Y + (ysc - yn) / (ys - yn) * MAP_H

# Scale bar: ground metres E-W across the full width, then px per mile / km.
lat_mid = math.radians((bbox.north + bbox.south) / 2)
ground_m = math.radians(bbox.east - bbox.west) * 6_378_137.0 * math.cos(lat_mid)
ppm = MAP_W / ground_m
mile_px, km_px = 1609.344 * ppm, 1000.0 * ppm

# Stage the logo next to the SVG so it can be referenced by a relative path
# (works in-container where the repo root is not mounted).
assert (OUT / "poster-map.png").exists(), f"missing {OUT/'poster-map.png'} (run render-poster + composite)"
logo_src = REPO / "logo-3000px.png"
assert logo_src.exists(), f"missing {logo_src}"
shutil.copyfile(logo_src, OUT / "logo.png")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def star(cx, cy, r, fill, stroke, sw):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        pts.append(f"{cx + rad * math.cos(ang):.1f},{cy + rad * math.sin(ang):.1f}")
    return (f'<polygon points="{" ".join(pts)}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')


p = []
p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}">')
p.append(f'<rect width="{W}" height="{H}" fill="{CREAM}"/>')

# --- map (relative href; colocated in render/out/) ---
p.append(f'<image x="0" y="{MAP_Y}" width="{MAP_W}" height="{MAP_H}" '
         f'href="poster-map.png" preserveAspectRatio="none"/>')

# --- title band ---
p.append(f'<rect width="{W}" height="{BAND_H}" fill="{MAROON}"/>')
logo_h = 700
logo_w = round(logo_h * 3000 / 3643)
p.append(f'<image x="120" y="{(BAND_H - logo_h) // 2}" width="{logo_w}" height="{logo_h}" '
         f'href="logo.png"/>')
tx = 120 + logo_w + 120
p.append(f'<text x="{tx}" y="600" font-family="Bebas Neue" font-size="500" '
         f'fill="{CREAM}" letter-spacing="8">HELMET HEADS</text>')
p.append(f'<text x="{tx + 8}" y="780" font-family="Montserrat" font-size="150" '
         f'font-weight="600" fill="{CREAM}">Brookland-Cayce Cycling Club</text>')
p.append(f'<text x="{W - 180}" y="480" font-family="Bebas Neue" font-size="300" '
         f'fill="{AMBER}" text-anchor="end" letter-spacing="6">RIDE MAP</text>')
p.append(f'<text x="{W - 180}" y="660" font-family="Montserrat" font-size="140" '
         f'fill="{CREAM}" text-anchor="end">Cayce, South Carolina</text>')

# --- school marker: star only (no label — it obscured nearby streets) ---
p.append(star(sx, sy, 180, MAROON, CREAM, 26))

# --- legend (bottom-right, over the river/quarry corner) ---
lp_w, lp_h = 3620, 1820
lx, ly = W - lp_w - 200, H - lp_h - 200
p.append(f'<rect x="{lx}" y="{ly}" width="{lp_w}" height="{lp_h}" rx="64" '
         f'fill="{CREAM}" fill-opacity="0.95" stroke="{INK}" stroke-width="8"/>')
p.append(f'<text x="{lx + 100}" y="{ly + 250}" font-family="Bebas Neue" font-size="210" '
         f'fill="{MAROON}" letter-spacing="4">LEGEND</text>')
# rows: (kind, color, dash, label)
rows = [
    ("line", CYCLE_BLUE, None, "Greenway / cycle track"),
    ("line", CYCLE_BLUE, "30,20", "On-road cycle route"),
    ("line", RED, "12,16", "Cycle lane"),
    ("swatch", PARK_GREEN, None, "Park"),
    ("star", MAROON, None, "School"),
]
row_y = ly + 470
sw_x = lx + 130
for kind, color, dash, label in rows:
    if kind == "line":
        d = f' stroke-dasharray="{dash}"' if dash else ""
        p.append(f'<line x1="{sw_x}" y1="{row_y}" x2="{sw_x + 380}" y2="{row_y}" '
                 f'stroke="{color}" stroke-width="28"{d}/>')
    elif kind == "swatch":
        p.append(f'<rect x="{sw_x}" y="{row_y - 74}" width="380" height="148" rx="18" '
                 f'fill="{color}" stroke="{INK}" stroke-width="4"/>')
    else:
        p.append(star(sw_x + 190, row_y, 95, MAROON, CREAM, 12))
    p.append(f'<text x="{sw_x + 500}" y="{row_y + 56}" font-family="Montserrat" '
             f'font-size="150" fill="{INK}">{esc(label)}</text>')
    row_y += 260

# --- scale bar (striped, 1 mile + 1 km) + north arrow (bottom-left) ---
sbx, sby = 280, H - 470
for length, label in [(mile_px, "1 mile"), (km_px, "1 km")]:
    half = length / 2
    p.append(f'<rect x="{sbx:.0f}" y="{sby}" width="{half:.0f}" height="70" '
             f'fill="{INK}" stroke="{INK}" stroke-width="6"/>')
    p.append(f'<rect x="{sbx + half:.0f}" y="{sby}" width="{half:.0f}" height="70" '
             f'fill="{CREAM}" stroke="{INK}" stroke-width="6"/>')
    p.append(f'<text x="{sbx + length + 60:.0f}" y="{sby + 62}" font-family="Montserrat" '
             f'font-size="120" fill="{INK}">{label}</text>')
    sby += 190
# north arrow above the scale
nax, nay = sbx + 130, H - 720
p.append(f'<polygon points="{nax},{nay - 180} {nax - 80},{nay + 70} {nax},{nay + 20} '
         f'{nax + 80},{nay + 70}" fill="{MAROON}" stroke="{CREAM}" stroke-width="10"/>')
p.append(f'<text x="{nax}" y="{nay + 230}" font-family="Bebas Neue" font-size="170" '
         f'fill="{INK}" text-anchor="middle">N</text>')

# --- attribution footer (bottom-center) ---
p.append(f'<text x="{W // 2}" y="{H - 90}" font-family="Montserrat" font-size="100" '
         f'fill="{INK}" text-anchor="middle" opacity="0.8">'
         f'Map data © OpenStreetMap contributors (ODbL) · Cycling data © CyclOSM '
         f'· Made for the Helmet Heads cycling club</text>')

p.append("</svg>")
(OUT / "poster.svg").write_text("\n".join(p))
print("saved", OUT / "poster.svg", "| school@", (round(sx), round(sy)),
      "| mile_px", round(mile_px), "| km_px", round(km_px))
