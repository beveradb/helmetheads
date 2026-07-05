#!/usr/bin/env bash
# Convert the poster SVG to a print-ready PDF and a PNG proof via rsvg-convert
# (in the tools container). Brand fonts are installed into fontconfig first so
# the wordmark/labels resolve by family name. poster.svg references its raster
# inputs (poster-map.png, logo.png) by relative path, colocated in render/out/.
set -euo pipefail
cd "$(dirname "$0")"

docker compose run --rm tools bash -c '
  set -e
  mkdir -p /usr/share/fonts/truetype/poster
  cp /render/fonts/*.ttf /usr/share/fonts/truetype/poster/
  fc-cache -f >/dev/null
  cd /out
  rsvg-convert -f pdf -o poster.pdf poster.svg
  rsvg-convert -f png -o poster-proof-full.png poster.svg
'
ls -la out/poster.pdf out/poster-proof-full.png
