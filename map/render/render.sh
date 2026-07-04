#!/usr/bin/env bash
# render.sh <style-xml-path-inside-container> <output-name> <width_px>
# Renders the print bbox at 300 ppi (nik4 scales line widths/labels accordingly).
#
# Note: the tools image installs the `nik4` PyPI package, which ships its CLI
# entry point as /usr/local/bin/nik4.py (no `nik4` shim on PATH) — confirmed
# via `docker compose run --rm tools nik4.py --help`. Flag semantics below
# (--bbox Xmin Ymin Xmax Ymax, --size-px W H with one 0 allowed, --ppi) match
# the brief's intent unchanged; only the invocation name differs.
set -euo pipefail
cd "$(dirname "$0")"
XML="$1"; OUT="$2"; WIDTH="$3"

docker compose run --rm tools \
  nik4.py --bbox -81.100988 33.943360 -81.035242 33.998016 \
       --size-px "$WIDTH" 0 --ppi 300 \
       "$XML" "/out/$OUT"

# Verify via the Phase 1 uv env (PIL lives there, not in the tools image).
(cd .. && uv run python -c "
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
im = Image.open('render/out/$OUT')
print('$OUT', im.mode, im.size)
")
