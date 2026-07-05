"""Assemble Helmet Heads poster SVG: title band, logo, map, school marker,
legend, scale bar, north arrow, attribution. Vector furniture + embedded map raster.
Coordinates in 14400x14400 px canvas (48in @ 300dpi)."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
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

# School pixel position within map slot (mercator fractions, zoom cancels).
xw, yn = deg2xy(bbox.north, bbox.west, 0)
xe, ys = deg2xy(bbox.south, bbox.east, 0)
xs, ysc = deg2xy(SCHOOL_LAT, SCHOOL_LON, 0)
sx = (xs - xw) / (xe - xw) * MAP_W
sy = MAP_Y + (ysc - yn) / (ys - yn) * MAP_H

# Scale bar: ground metres across full width, then px per mile.
lat_mid = (bbox.north + bbox.south) / 2
ground_m = (
    math.radians(bbox.east - bbox.west) * 6_371_000 * math.cos(math.radians(lat_mid))
)
mile_px = MAP_W / (ground_m / 1609.344)

# Verify logo and map paths exist before writing SVG
logo_path = REPO / "logo-3000px.png"
map_path = OUT / "poster-map.png"
assert logo_path.exists(), f"Logo not found: {logo_path}"
assert map_path.exists(), f"Poster map not found: {map_path}"

# Font face declarations (absolute container paths used by rsvg-convert).
faces = (
    f"@font-face {{font-family:'Bebas Neue';"
    f" src:url('file://{FONTS}/BebasNeue-Regular.ttf') format('truetype');}}\n"
    f"@font-face {{font-family:'Montserrat';"
    f" src:url('file://{FONTS}/Montserrat.ttf') format('truetype');}}\n"
)

markers = [
    (MAROON, "Brookland-Cayce High School"),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


parts = []
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}">'
)
parts.append(f"<style>{faces}</style>")
parts.append(f'<rect width="{W}" height="{H}" fill="{CREAM}"/>')

# Map image
parts.append(
    f'<image x="0" y="{MAP_Y}" width="{MAP_W}" height="{MAP_H}" '
    f'href="file://{map_path}" preserveAspectRatio="none"/>'
)

# Title band
parts.append(f'<rect width="{W}" height="{BAND_H}" fill="{MAROON}"/>')

# Logo (transparent PNG) left-aligned in band
logo_h = 700
logo_w = round(logo_h * 3000 / 3643)
parts.append(
    f'<image x="120" y="{(BAND_H - logo_h) // 2}" width="{logo_w}" height="{logo_h}" '
    f'href="file://{logo_path}"/>'
)

tx = 120 + logo_w + 120
parts.append(
    f'<text x="{tx}" y="590" font-family="Bebas Neue" font-size="500" '
    f'fill="{CREAM}" letter-spacing="8">HELMET HEADS</text>'
)
parts.append(
    f'<text x="{tx + 8}" y="770" font-family="Montserrat" font-size="150" '
    f'font-weight="600" fill="{CREAM}">Brookland-Cayce Cycling Club</text>'
)
parts.append(
    f'<text x="{W - 160}" y="470" font-family="Bebas Neue" font-size="300" '
    f'fill="{AMBER}" text-anchor="end" letter-spacing="6">RIDE MAP</text>'
)
parts.append(
    f'<text x="{W - 160}" y="650" font-family="Montserrat" font-size="140" '
    f'fill="{CREAM}" text-anchor="end">Cayce, South Carolina</text>'
)

# School marker: star + callout pill
def star(cx, cy, r, fill, stroke, sw):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        pts.append(f"{cx + rad * math.cos(ang):.1f},{cy + rad * math.sin(ang):.1f}")
    return (
        f'<polygon points="{" ".join(pts)}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{sw}"/>'
    )


parts.append(star(sx, sy, 150, MAROON, CREAM, 22))
pill_w, pill_h = 1150, 210
px0, py0 = sx + 120, sy - pill_h / 2
parts.append(
    f'<rect x="{px0:.0f}" y="{py0:.0f}" width="{pill_w}" height="{pill_h}" '
    f'rx="40" fill="{CREAM}" fill-opacity="0.92" stroke="{MAROON}" stroke-width="8"/>'
)
parts.append(
    f'<text x="{px0 + 50:.0f}" y="{sy + 45:.0f}" font-family="Montserrat" '
    f'font-size="120" font-weight="600" fill="{INK}">Brookland-Cayce HS</text>'
)

# Scale bar (1 mile)
sb_px = round(mile_px)
sb_x, sb_y = 200, H - 280
sb_h = 70
# Two-tone striped bar (white + black alternating halves)
parts.append(
    f'<rect x="{sb_x}" y="{sb_y}" width="{sb_px // 2}" height="{sb_h}" '
    f'fill="{INK}" stroke="{INK}" stroke-width="6"/>'
)
parts.append(
    f'<rect x="{sb_x + sb_px // 2}" y="{sb_y}" width="{sb_px // 2}" height="{sb_h}" '
    f'fill="{CREAM}" stroke="{INK}" stroke-width="6"/>'
)
parts.append(
    f'<text x="{sb_x}" y="{sb_y - 40}" font-family="Montserrat" font-size="100" '
    f'fill="{INK}" text-anchor="middle">0</text>'
)
parts.append(
    f'<text x="{sb_x + sb_px}" y="{sb_y - 40}" font-family="Montserrat" font-size="100" '
    f'fill="{INK}" text-anchor="middle">1 mi</text>'
)
parts.append(
    f'<text x="{sb_x + sb_px // 2}" y="{sb_y + sb_h + 100}" '
    f'font-family="Montserrat" font-size="90" fill="{INK}" text-anchor="middle">'
    f'½ mi</text>'
)

# Legend
leg_x, leg_y = 200, H - 650
parts.append(
    f'<rect x="{leg_x - 30}" y="{leg_y - 120}" width="860" height="200" '
    f'rx="30" fill="{CREAM}" fill-opacity="0.88" stroke="{MAROON}" stroke-width="6"/>'
)
for idx, (color, label) in enumerate(markers):
    lx = leg_x
    ly = leg_y + idx * 160
    parts.append(
        f'<polygon points="{lx},{ly - 50} {lx - 35},{ly + 20} {lx + 35},{ly + 20}" '
        f'fill="{color}"/>'
    )
    parts.append(
        f'<text x="{lx + 65}" y="{ly + 20}" font-family="Montserrat" font-size="100" '
        f'fill="{INK}" font-weight="600">{esc(label)}</text>'
    )

# North arrow
na_cx, na_tip = W - 500, H - 520
parts.append(
    f'<polygon points="{na_cx},{na_tip} {na_cx - 80},{na_tip + 260} {na_cx + 80},{na_tip + 260}" '
    f'fill="{MAROON}" stroke="{CREAM}" stroke-width="12"/>'
)
parts.append(
    f'<text x="{na_cx}" y="{na_tip - 40}" font-family="Bebas Neue" font-size="160" '
    f'fill="{INK}" text-anchor="middle">N</text>'
)

# Attribution
parts.append(
    f'<text x="{W - 100}" y="{H - 50}" font-family="Montserrat" font-size="72" '
    f'fill="{INK}" text-anchor="end" opacity="0.65">'
    f'© OpenStreetMap contributors  |  Brookland-Cayce Cycling Club {{}}</text>'.replace(
        "{}", "2024"
    )
)

parts.append("</svg>")

out_path = OUT / "poster.svg"
out_path.write_text("\n".join(parts))
print(
    "saved", out_path,
    "school@", (round(sx), round(sy)),
    "mile_px", round(mile_px),
)
