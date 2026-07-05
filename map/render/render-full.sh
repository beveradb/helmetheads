#!/usr/bin/env bash
# Full print-resolution renders: 14400 px wide raster of base + overlay, plus vector PDFs.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out  # ensure the bind-mount source exists (host-owned) if clip.sh wasn't run first

./render.sh /checkouts/openstreetmap-carto/mapnik-print.xml full-osm-carto.png 14400
./render.sh /checkouts/cyclosm-lite/mapnik-print.xml full-cyclosm-lite.png 14400

# Vector PDFs via cairo (nik4 picks the backend from the extension).
# render.sh's PIL check will fail on PDFs — invoke nik4.py directly here.
# Note: the tools image ships the CLI as nik4.py (no bare `nik4` shim on PATH).
docker compose run --rm tools \
  nik4.py --bbox -81.100988 33.943360 -81.035242 33.998016 \
       --size-px 14400 0 --ppi 300 \
       /checkouts/openstreetmap-carto/mapnik-print.xml /out/full-osm-carto.pdf
docker compose run --rm tools \
  nik4.py --bbox -81.100988 33.943360 -81.035242 33.998016 \
       --size-px 14400 0 --ppi 300 \
       /checkouts/cyclosm-lite/mapnik-print.xml /out/full-cyclosm-lite.pdf
ls -la out/full-*
