#!/usr/bin/env bash
# Fetch club's brand fonts (used by site) for the poster.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p fonts
base="https://github.com/google/fonts/raw/main"
fetch() { [ -f "fonts/$2" ] || curl -fsSL -L "$1" -o "fonts/$2"; }
fetch "$base/ofl/bebasneue/BebasNeue-Regular.ttf" BebasNeue-Regular.ttf
# Montserrat variable font (handles all weights: 400 regular, 600 semi-bold, etc.)
fetch "$base/ofl/montserrat/Montserrat%5Bwght%5D.ttf" Montserrat.ttf
echo "Fonts fetched:"
ls -lh fonts/
