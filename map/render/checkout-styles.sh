#!/usr/bin/env bash
# Shallow-clone the two style repos (osm-carto pinned to its latest release tag).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p checkouts

if [ ! -d checkouts/openstreetmap-carto ]; then
  git clone --depth 1 https://github.com/gravitystorm/openstreetmap-carto.git checkouts/openstreetmap-carto
  TAG=$(git -C checkouts/openstreetmap-carto ls-remote --tags --sort=-v:refname origin 'v*' | head -1 | sed 's|.*refs/tags/||; s|\^{}||')
  git -C checkouts/openstreetmap-carto fetch --depth 1 origin "refs/tags/$TAG:refs/tags/$TAG"
  git -C checkouts/openstreetmap-carto checkout "$TAG"
  echo "openstreetmap-carto pinned to $TAG"
fi

[ -d checkouts/cyclosm ] || \
  git clone --depth 1 -b master https://github.com/cyclosm/cyclosm-cartocss-style.git checkouts/cyclosm
[ -d checkouts/cyclosm-lite ] || \
  git clone --depth 1 -b lite https://github.com/cyclosm/cyclosm-cartocss-style.git checkouts/cyclosm-lite
