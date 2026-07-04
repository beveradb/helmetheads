#!/usr/bin/env bash
# Fetch external data + fonts for osm-carto, patch DB connection, compile to Mapnik XML.
set -euo pipefail
cd "$(dirname "$0")"

# External shapefiles/data (world water polygons etc. — several GB on first run,
# cached in ./external-data). Connection comes from PG* env vars in the container.
docker compose run --rm -w /checkouts/openstreetmap-carto tools \
  python3 scripts/get-external-data.py -D /external-data -d gis

# Fonts (Noto downloads into the checkout; apt fonts cover the fallbacks).
docker compose run --rm -w /checkouts/openstreetmap-carto tools python3 scripts/get-fonts.py

# Point the style at our containerized DB, then compile (Mapnik API ver per INSTALL.md).
docker compose run --rm -w /checkouts/openstreetmap-carto tools \
  python3 /render/patch-mml.py project.mml gis
docker compose run --rm -w /checkouts/openstreetmap-carto tools \
  bash -c 'carto -a "3.0.22" project.mml > mapnik-print.xml'
