#!/usr/bin/env bash
# Render osm-carto + cyclosm-lite at the trimmed poster bbox (fills the 14400x13500
# map slot below the title band). Height is derived by nik4 from the bbox aspect.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out

# Compute the trimmed bbox (same E/W + center lat as the print bbox, mercator aspect 0.9375).
read -r W S E N < <(cd .. && uv run python -c "
import sys; sys.path.insert(0, 'scripts')
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
