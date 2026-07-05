# Helmet Heads Wall Map — Design

**Date:** 2026-07-03
**Status:** Phase 1 complete (2026-07-03). Style decided 2026-07-04: **OSM Carto base + CyclOSM-lite cycling overlay** (composite validated by user via compare.html). Phase 2 render backend per this spec: Mapnik + CartoCSS (both chosen styles are CartoCSS-native).

## Goal

Produce a print-ready map of the club's riding area in Cayce, SC for a ~48×48 in
wall print in the BCHS bike room. Students and teachers will draw routes on it
with highlighters/dry-erase markers, so the base map must be light enough for
marks to stand out, with legible street names, emphasized bike infrastructure,
key landmarks, and cartographic furniture (title, logo, legend, scale bar,
north arrow).

## Area

From `map-area-corners.txt` (WGS84):

- School: `-81.056747, 33.981738`
- Bbox: `-81.100988, 33.943360, -81.035242, 33.998016` (W, S, E, N)

The bbox is ~6.07 km × ~6.04 km — effectively square, matching the 48×48 in
target with no cropping. Print scale ≈ 1:5,000 (≈ OSM zoom 16–17).

## Decisions made

| Question | Decision |
|---|---|
| Style | **Decided (2026-07-04): OSM Carto base + CyclOSM-lite transparent cycling overlay** (user reviewed all candidates) |
| Workflow | Local scripted pipeline, reproducible, in this repo under `map/` |
| Content | All street names legible; bike infrastructure emphasized; key POIs (school prominent, parks, river, bridges); title/logo/legend/scale bar/north arrow |
| Print | Local large-format print shop; laminated (gloss = dry-erase friendly) or mounted; target vector PDF, with 300 dpi raster fallback |
| Approach | Two-phase: cheap raster style comparisons first, then build the real print pipeline for the winning style only |

## Phase 1 — Style comparison renders

Render the exact bbox at ~2000 px square in each candidate style so
differences are purely stylistic:

1. **OSM Carto** (classic) — stitched from public tile servers
2. **CyclOSM** (cycling-focused) — stitched from public tile servers
3. **Minimal light** (Positron-style greyscale) — MapLibre static render
4. **Minimal with character** (OpenFreeMap Liberty or Protomaps light) — MapLibre static render
5. **Artistic/poster** — Python `prettymaps` render
6. *(Bonus)* MapOSMatic PDF grab for reference

Implementation notes:

- Tile stitching: small Python script; ~12×12 tiles at z16 per style, polite
  rate limiting and a proper identifying User-Agent (one-off volume, within
  usage policies).
- MapLibre renders: minimal local HTML page loading a style JSON with the bbox
  bounds, screenshotted headlessly via Playwright at high device-pixel-ratio.
- Outputs land in `map/previews/`, plus a `compare.html` contact sheet for
  side-by-side review in a browser.

**Decision gate:** user reviews the contact sheet and picks the style
direction before any Phase 2 work.

## Phase 2 — Final print pipeline (after style decision)

### Data

- Download Geofabrik `south-carolina-latest.osm.pbf`, clip to bbox with
  `osmium extract` — scripted and reproducible; raw data git-ignored.
- **Bike-infra audit:** before final render, check how completely Cayce's bike
  lanes/trails (Riverwalk, Timmerman Trail, on-street lanes) are mapped in
  OSM. If patchy, fix upstream in OSM (potential club activity) and
  re-download.

### Render backend — pick one based on the winning style's heritage

- **MapLibre style JSON → high-res raster:** 14,400 px square (48 in @
  300 dpi), rendered headlessly in tiles and assembled. Easiest to author and
  customize; style JSON versioned in repo. Raster, but indistinguishable from
  vector at print resolution.
- **Mapnik + CartoCSS → true vector PDF:** Docker + PostGIS + osm2pgsql. The
  right tool if OSM Carto or CyclOSM heritage wins; genuine vector output via
  Cairo.

### Furniture & final file

- Compose in Inkscape on a 48×48 in canvas: map layer + title ("Helmet
  Heads"), club logo, legend, scale bar, north arrow, prominent school marker.
- Export print-ready PDF plus 300 dpi TIFF/PNG fallback; add bleed per the
  print shop's spec (ask shop; typically 0.125–0.25 in).

### Verification — true-scale letter test print

Before ordering the large print: crop a section of the **full-size** map
(area around the school) sized exactly to US letter printable area
(~8×10.5 in at 100% print scale, i.e. 2400×3150 px at 300 dpi), print at home
with no scaling ("Actual size"), and check street-name legibility from
arm's length and from a few feet away. Iterate label sizes and re-render
until it reads well, then order the big print.

## Risks

| Risk | Mitigation |
|---|---|
| OSM bike infra under-mapped in Cayce | Audit early; edit OSM upstream and re-render |
| Labels too small/dense at fixed print scale | True-scale letter test print before ordering |
| Raster-only output if MapLibre path chosen | Acceptable at 300 dpi; Mapnik path exists if vector required |
| Public tile usage policies | One-off, low volume, identifying UA; Phase 2 renders locally from downloaded data |

## Phase 3 — cartographic furniture (decided 2026-07-05)

Compose the print-ready poster from the Phase 2 map, script-generated (SVG →
PDF + PNG proof) for reproducibility — not manual Inkscape.

- **Canvas:** 48×48 in (14400×14400 px @ 300 dpi), brand cream (`#f4ede3`).
- **Title band:** top 3 in, maroon (`#71161c`) — Helmet Heads vector logo, "HELMET
  HEADS" wordmark (Bebas Neue), "Brookland-Cayce Cycling Club" subtitle
  (Montserrat), "RIDE MAP · Cayce, SC" at right. Brand fonts match the club site.
- **Map:** the 50%-overlay composite, **re-rendered** to fill the width below the
  band. The area is square but the sub-band slot is slightly wide, so the N-S
  extent is trimmed ~0.15 mi total (split top/bottom; school stays centered) so
  the map fills with no side mats and no post-crop.
- **School marker:** maroon ★ + "Brookland-Cayce HS" callout, placed by lat/lon.
- **Legend:** bottom-right soft-cream panel over the river/quarry corner —
  greenway/cycle track, on-road cycle route, cycle lane, park, school.
- **Scale bar + north arrow:** bottom-left, 1 mile + 1 km, computed from render scale.
- **Attribution footer:** OSM (ODbL) + CyclOSM + Helmet Heads.
- **Output:** `poster.pdf` (vector furniture, embedded map raster) + 300 dpi PNG
  proof; a 100%-scale US-letter proof of the title band and legend for a print check.

## Out of scope

- Web/interactive map for the site (could reuse the pipeline later)
- Route database/overlays — routes are drawn by hand on the physical print
