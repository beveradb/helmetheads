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

## Phase 2 — print-resolution rendering

Requires Docker (for the render stack) and `uv` on the host (the render/composite
helpers call `uv run`). From `render/`:

    docker compose build tools && docker compose up -d db
    ./checkout-styles.sh   # osm-carto (pinned tag) + cyclosm master/lite
    ./clip.sh              # expects ~/Downloads/south-carolina-260703.osm.pbf
    ./import.sh            # both databases
    ./build-osm-carto.sh   # external data (slow first run) + fonts + carto compile
    ./build-cyclosm.sh     # patch + shapefiles + carto compile, both variants
    ./render-full.sh       # 14400px renders + vector PDFs

Then from `map/`:

    uv run python scripts/composite_print.py   # base + overlay -> render/out/full-composite.png
    uv run python scripts/letter_crop.py       # true-scale 8x10.5in test crop around school

Print `render/out/letter-test.png` at **Actual Size** (no scaling) to judge
label legibility before ordering wall print. `./audit-bike-infra.sh`
reports the area's cycling infrastructure mapped in OSM.
