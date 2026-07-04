# Helmet Heads wall map pipeline

Renders the club riding area of Cayce, SC (bbox in `../map-area-corners.txt`)
for a ~48×48 in wall print. Spec: `../docs/superpowers/specs/2026-07-03-print-map-design.md`.

## Phase 1 — style previews

Setup (once):

    uv sync
    uv run playwright install chromium

Render all previews:

    uv run python scripts/stitch_tiles.py        # osm-carto, cyclosm, osm-carto+cyclosm-lite composite
    uv run python scripts/render_maplibre.py     # positron, bright, liberty
    uv run python scripts/render_prettymaps.py   # artistic

Then open `compare.html` in a browser.

Bonus reference render: submit the bbox at https://print.get-map.org (MapOSMatic)
and drop the PDF into `previews/` manually.

Data/tiles © OpenStreetMap contributors (ODbL). Preview tiles courtesy of
OSMF (osm-carto), CyclOSM/OSM France, and OpenFreeMap — previews are for
internal style comparison, not redistribution.
