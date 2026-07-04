#!/usr/bin/env bash
# Patch DB connection + fetch shapefiles + compile CyclOSM (master) and CyclOSM-lite (lite branch).
set -euo pipefail
cd "$(dirname "$0")"

for variant in cyclosm cyclosm-lite; do
  docker compose run --rm -w "/checkouts/$variant" tools \
    python3 /render/patch-mml.py project.mml osm
  docker compose run --rm -w "/checkouts/$variant" tools \
    python3 /render/fetch-shapefiles.py project.mml
  # CyclOSM-lite: replicate localconfig-lite.js — filter to cyclosm-lite layers,
  # wrap table queries to inject is_lite=1, add palette-lite.mss stylesheet.
  if [[ "$variant" == "cyclosm-lite" ]]; then
    docker compose run --rm -w "/checkouts/$variant" tools \
      python3 /render/patch-cyclosm-lite.py project.mml
  fi
  docker compose run --rm -w "/checkouts/$variant" tools \
    bash -c 'carto -a "3.0.22" project.mml > mapnik-print.xml'
done
