#!/usr/bin/env bash
# Import the clipped extract into both style databases.
set -euo pipefail
cd "$(dirname "$0")"

# 1) osm-carto: flex output into db "gis" (per its INSTALL.md; osm2pgsql >= 1.8).
docker compose run --rm -w /checkouts/openstreetmap-carto tools \
  osm2pgsql -O flex -S openstreetmap-carto-flex.lua --slim -d gis /data/cayce.osm.pbf

# osm-carto post-import SQL (files present in recent releases; skip any that don't exist).
for f in indexes.sql functions.sql common-values.sql; do
  docker compose run --rm -w /checkouts/openstreetmap-carto tools \
    bash -c "if [ -f $f ]; then psql -v ON_ERROR_STOP=1 -d gis -f $f; else echo 'skip $f (not in this release)'; fi"
done

# 2) CyclOSM: legacy pgsql output with hstore into db "osm" (per its docs/INSTALL.md).
docker compose run --rm tools \
  osm2pgsql -c -G --slim --hstore -d osm /data/cayce.osm.pbf

docker compose run --rm -w /checkouts/cyclosm tools psql -d osm -f views.sql
