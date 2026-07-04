#!/usr/bin/env bash
# Clip the South Carolina extract to the print bbox + 0.02° margin.
set -euo pipefail
cd "$(dirname "$0")"

SRC="${1:-$HOME/Downloads/south-carolina-260703.osm.pbf}"
mkdir -p ../data
[ -f ../data/south-carolina.osm.pbf ] || cp "$SRC" ../data/south-carolina.osm.pbf

docker compose run --rm tools osmium extract \
  --bbox -81.120988,33.923360,-81.015242,34.018016 \
  --set-bounds --overwrite \
  -o /data/cayce.osm.pbf /data/south-carolina.osm.pbf
docker compose run --rm tools osmium fileinfo -e /data/cayce.osm.pbf
