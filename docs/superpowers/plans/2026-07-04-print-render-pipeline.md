# Print Render Pipeline (Phase 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render the chosen style (OSM Carto base + CyclOSM-lite cycling overlay) at print resolution (48 in @ 300 dpi) from local OSM data, produce a composite plus a true-scale US-letter test crop around the school, and audit the area's bike-infra mapping.

**Architecture:** A Docker environment under `map/render/`: one PostGIS container with two databases (`gis` for osm-carto's flex import, `osm` for CyclOSM's hstore import), and one `tools` container (osm2pgsql, osmium, carto, mapnik + nik4, fonts) that imports the user's South Carolina extract clipped to the bbox (+margin), compiles both CartoCSS styles to Mapnik XML with plain `carto` (no kosmtik — avoids node-mapnik native builds), and renders with Nik4 (CyclOSM's own recommended print tool). Two small helper scripts replace kosmtik's roles: `patch-mml.py` points any style's postgis datasources at our DB, and `fetch-shapefiles.py` downloads the shapefiles a project.mml references by URL. Compositing and cropping reuse the Phase 1 Python env (`map/`, PIL + maptools).

**Tech Stack:** Docker Compose; `postgis/postgis:16-3.4`; Debian-based tools image (osm2pgsql ≥1.8, osmium-tool, nodejs+carto, python3-mapnik, nik4, Noto fonts, gdal-bin); upstream style repos `gravitystorm/openstreetmap-carto` (latest release tag) and `cyclosm/cyclosm-cartocss-style` (`master` + `lite` branches); Phase 1 `map/` uv project for compositing.

## Global Constraints

- Bbox (WGS84): W `-81.100988`, S `33.943360`, E `-81.035242`, N `33.998016`. School: `-81.056747, 33.981738`.
- Clip the PBF with a **0.02° margin** on every side (features/labels crossing the print edge must render correctly): extract bbox `-81.120988,33.923360,-81.015242,34.018016`.
- Print target: 48 in @ 300 dpi → nik4 `--bbox` renders at width 14400 px (height follows the bbox's mercator aspect ≈ 1.00241 → ≈ 14435 px).
- Source data: `~/Downloads/south-carolina-260703.osm.pbf` (user-downloaded, 2026-07-03). Copy into `map/data/` — never commit it.
- Git-ignore all bulky/generated content: `map/data/`, `map/render/checkouts/`, `map/render/external-data/`, `map/render/out/`. Commit only scripts, Dockerfiles, compose, config, docs.
- Commit as you go; **never push** (user instruction: nothing is pushed until the final map is approved).
- **Upstream-drift clause:** the two style repos evolve. Commands below follow their docs as of 2026-07 (osm-carto INSTALL.md: flex import via `openstreetmap-carto-flex.lua` into db `gis`, `scripts/get-external-data.py`, `scripts/get-fonts.py`, `carto -a "3.0.22"`; CyclOSM docs/INSTALL.md: `osm2pgsql -c -G --slim --hstore -d osm`, `views.sql`). If a checked-out repo's docs differ, **follow the checkout's own docs**, keep our file/db names and paths, and record the deviation in your report.
- All commands run from `map/render/` unless stated otherwise. Docker must be running; if the Docker daemon is unavailable, report BLOCKED.

---

### Task 1: Render scaffold, data clip, style checkouts

**Files:**
- Create: `map/render/docker-compose.yml`
- Create: `map/render/Dockerfile.tools`
- Create: `map/render/db-init/01-create-dbs.sql`
- Create: `map/render/clip.sh`
- Create: `map/render/checkout-styles.sh`
- Modify: `map/.gitignore`

**Interfaces:**
- Consumes: `~/Downloads/south-carolina-260703.osm.pbf`.
- Produces: running `db` service (databases `gis` and `osm`, postgis+hstore); `tools` image with all render dependencies; `map/data/cayce.osm.pbf` (clipped extract); checkouts at `map/render/checkouts/{openstreetmap-carto,cyclosm,cyclosm-lite}`. Later tasks run everything via `docker compose run --rm tools <cmd>`; the `map/render/` dir itself is mounted at `/render` inside the container.

- [ ] **Step 1: Append to `map/.gitignore`**

```gitignore
data/
render/checkouts/
render/external-data/
render/out/
```

- [ ] **Step 2: Create `map/render/docker-compose.yml`**

```yaml
services:
  db:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_PASSWORD: renderpass
    volumes:
      - dbdata:/var/lib/postgresql/data
      - ./db-init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 20
    shm_size: 1g

  tools:
    build:
      context: .
      dockerfile: Dockerfile.tools
    depends_on:
      db:
        condition: service_healthy
    environment:
      PGHOST: db
      PGUSER: postgres
      PGPASSWORD: renderpass
    volumes:
      - .:/render
      - ../data:/data
      - ./checkouts:/checkouts
      - ./external-data:/external-data
      - ./out:/out
    working_dir: /checkouts

volumes:
  dbdata:
```

- [ ] **Step 3: Create `map/render/Dockerfile.tools`**

```dockerfile
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    osm2pgsql osmium-tool postgresql-client \
    python3 python3-pip python3-mapnik python3-psycopg2 python3-yaml python3-requests \
    mapnik-utils gdal-bin curl ca-certificates git unzip \
    nodejs npm \
    fonts-dejavu-core fonts-noto fonts-noto-cjk \
    fonts-hanazono fonts-unifont \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g carto
RUN pip3 install --break-system-packages nik4

CMD ["bash"]
```

- [ ] **Step 4: Create `map/render/db-init/01-create-dbs.sql`**

```sql
CREATE DATABASE gis;
CREATE DATABASE osm;
\c gis
CREATE EXTENSION postgis;
CREATE EXTENSION hstore;
\c osm
CREATE EXTENSION postgis;
CREATE EXTENSION hstore;
```

- [ ] **Step 5: Create `map/render/clip.sh`**

```bash
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
```

- [ ] **Step 6: Create `map/render/checkout-styles.sh`**

```bash
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
```

- [ ] **Step 7: Run it all**

```bash
chmod +x clip.sh checkout-styles.sh
docker compose build tools
docker compose up -d db
./checkout-styles.sh
./clip.sh
```

Expected: tools image builds; db healthy; three checkouts exist (note the pinned osm-carto tag for the report); `osmium fileinfo -e` shows the clipped extract with the margin bbox and a plausible object count (tens of thousands of nodes, not millions or zero).

- [ ] **Step 8: Verify databases**

Run: `docker compose exec db psql -U postgres -c '\l' | grep -E 'gis|osm'`
Expected: both databases listed.

- [ ] **Step 9: Commit** (scripts and config only — checkouts/data are ignored)

```bash
git add ../.gitignore docker-compose.yml Dockerfile.tools db-init/01-create-dbs.sql clip.sh checkout-styles.sh
git commit -m "feat(map): Phase 2 render scaffold — docker stack, data clip, style checkouts"
```

---

### Task 2: Import data into both databases

**Files:**
- Create: `map/render/import.sh`

**Interfaces:**
- Consumes: `db` service, `tools` image, `/data/cayce.osm.pbf`, checkouts from Task 1.
- Produces: populated `gis` (osm-carto flex schema + indexes/functions) and `osm` (legacy hstore schema + CyclOSM views) databases. Idempotent: re-running re-creates tables (`osm2pgsql -c` / `--slim` drop-and-recreate on flex).

- [ ] **Step 1: Create `map/render/import.sh`**

```bash
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
```

- [ ] **Step 2: Run it**

```bash
chmod +x import.sh && ./import.sh
```

Expected: both imports finish in under a minute (small extract). If the osm-carto flex lua filename differs in the pinned release, use the name its INSTALL.md gives (upstream-drift clause) and note it.

- [ ] **Step 3: Verify row counts**

```bash
docker compose run --rm tools psql -d gis -c "SELECT count(*) FROM planet_osm_line;"
docker compose run --rm tools psql -d osm -c "SELECT count(*) FROM planet_osm_line;"
```

Expected: thousands of rows in each (non-zero; exact counts differ between schemas).

- [ ] **Step 4: Commit**

```bash
git add import.sh
git commit -m "feat(map): import clipped extract into osm-carto (gis) and cyclosm (osm) databases"
```

---

### Task 3: Style-build helpers + osm-carto build + smoke render

**Files:**
- Create: `map/render/patch-mml.py`
- Create: `map/render/fetch-shapefiles.py`
- Create: `map/render/build-osm-carto.sh`
- Create: `map/render/render.sh`

**Interfaces:**
- Consumes: populated `gis` db; osm-carto checkout.
- Produces:
  - `patch-mml.py <project.mml> <dbname>` — rewrites every postgis datasource in a project.mml (YAML) to `host=db user=postgres password=renderpass dbname=<dbname>`; used for all three styles.
  - `fetch-shapefiles.py <project.mml>` — downloads/unzips any layer datasource that carries a remote-archive URL alongside a local `file:` path (kosmtik-fetch-remote's job, ~40 lines); used by Task 4 (osm-carto gets its data via `get-external-data.py` instead).
  - `render.sh <xml-path-inside-container> <out-name> <width_px>` — shared nik4 wrapper (bbox baked in, `--ppi 300`), verifies output via the Phase 1 uv env.
  - `checkouts/openstreetmap-carto/mapnik-print.xml`; smoke render `out/smoke-osm-carto.png`.

- [ ] **Step 1: Create `map/render/patch-mml.py`**

```python
#!/usr/bin/env python3
"""Point every postgis datasource in a carto project.mml at our containerized DB.

Usage: patch-mml.py <path/to/project.mml> <dbname>
Works on any style (osm-carto uses a shared `_parts` block; CyclOSM sets
per-layer Datasources) by walking the whole YAML tree.
"""

import sys

import yaml

CONN = {"host": "db", "port": 5432, "user": "postgres", "password": "renderpass"}


def patch(node, dbname, count=0):
    if isinstance(node, dict):
        if node.get("type") == "postgis" or "dbname" in node:
            node.update(CONN, dbname=dbname)
            count += 1
        for value in node.values():
            count = patch(value, dbname, count)
    elif isinstance(node, list):
        for value in node:
            count = patch(value, dbname, count)
    return count


path, dbname = sys.argv[1], sys.argv[2]
with open(path) as f:
    mml = yaml.safe_load(f)
n = patch(mml, dbname)
with open(path, "w") as f:
    yaml.dump(mml, f, default_flow_style=False)
print(f"patched {n} datasource block(s) in {path} -> dbname={dbname}")
```

- [ ] **Step 2: Create `map/render/fetch-shapefiles.py`**

```python
#!/usr/bin/env python3
"""Download shapefile archives referenced by a project.mml (kosmtik-fetch-remote's job).

Usage: fetch-shapefiles.py <path/to/project.mml>
Looks for Datasource dicts having both a local `file` path and a remote URL
(in `file` itself or in a sibling key such as `url`); downloads and unzips
into the expected location, relative to the mml's directory. Skips anything
already present.
"""

import io
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen

import yaml

mml_path = Path(sys.argv[1]).resolve()
root = mml_path.parent
with open(mml_path) as f:
    mml = yaml.safe_load(f)

jobs = []


def scan(node):
    if isinstance(node, dict):
        f, url = node.get("file"), node.get("url")
        if isinstance(f, str) and isinstance(url, str) and url.startswith("http"):
            jobs.append((f, url))
        elif isinstance(f, str) and f.startswith("http"):
            jobs.append((None, f))
        for value in node.values():
            scan(value)
    elif isinstance(node, list):
        for value in node:
            scan(value)


scan(mml)
for local, url in jobs:
    target_dir = (root / local).parent if local else root / "data"
    marker = root / local if local else None
    if marker and marker.exists():
        print(f"have {local}")
        continue
    print(f"fetch {url} -> {target_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = urlopen(url, timeout=120).read()
    if url.endswith(".zip"):
        zipfile.ZipFile(io.BytesIO(payload)).extractall(target_dir)
    else:
        (target_dir / Path(url).name).write_bytes(payload)
print(f"{len(jobs)} remote datasource(s) processed")
```

(If a style's mml encodes remote archives differently — e.g. nested `Datasource: {file: ...}` plus a top-level `url` sibling — extend `scan` to that shape at execution time; the contract stays "make every `file:` path referenced by the mml exist locally".)

- [ ] **Step 3: Create `map/render/build-osm-carto.sh`**

```bash
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
```

- [ ] **Step 4: Create `map/render/render.sh`** — shared nik4 wrapper

```bash
#!/usr/bin/env bash
# render.sh <style-xml-path-inside-container> <output-name> <width_px>
# Renders the print bbox at 300 ppi (nik4 scales line widths/labels accordingly).
set -euo pipefail
cd "$(dirname "$0")"
XML="$1"; OUT="$2"; WIDTH="$3"

docker compose run --rm tools \
  nik4 --bbox -81.100988 33.943360 -81.035242 33.998016 \
       --size-px "$WIDTH" 0 --ppi 300 \
       "$XML" "/out/$OUT"

# Verify via the Phase 1 uv env (PIL lives there, not in the tools image).
(cd .. && uv run python -c "
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
im = Image.open('render/out/$OUT')
print('$OUT', im.mode, im.size)
")
```

(nik4 flag semantics to preserve if the installed version spells them differently — `nik4 --help` is authoritative: fixed lon/lat bbox; explicit pixel width with height derived from the bbox aspect; ppi 300 so nik4 raises Mapnik's scale factor for print. The PDF outputs in Task 5 skip the PIL check — PIL doesn't read PDFs; `ls -la` size is enough there.)

- [ ] **Step 5: Build and smoke-render**

```bash
chmod +x build-osm-carto.sh render.sh patch-mml.py fetch-shapefiles.py
./build-osm-carto.sh
./render.sh /checkouts/openstreetmap-carto/mapnik-print.xml smoke-osm-carto.png 2000
```

Expected: external-data step is the slow one (large downloads, first run only); carto compiles with warnings but no errors; smoke PNG ≈ 2000×2005 and visually matches Phase 1's `map/previews/osm-carto.png` (same area/style — compare side by side; fonts must not be missing/boxy).

- [ ] **Step 6: Commit**

```bash
git add patch-mml.py fetch-shapefiles.py build-osm-carto.sh render.sh
git commit -m "feat(map): osm-carto print build + mml helpers + shared nik4 wrapper"
```

---

### Task 4: Build CyclOSM full + lite styles and smoke-render

**Files:**
- Create: `map/render/build-cyclosm.sh`

**Interfaces:**
- Consumes: populated `osm` db; cyclosm + cyclosm-lite checkouts; `patch-mml.py`, `fetch-shapefiles.py`, `render.sh` from Task 3.
- Produces: `checkouts/cyclosm/mapnik-print.xml` and `checkouts/cyclosm-lite/mapnik-print.xml`; smoke renders `out/smoke-cyclosm.png` (full style, opaque) and `out/smoke-cyclosm-lite.png` (overlay, transparent background); `out/smoke-composite.png`.

- [ ] **Step 1: Create `map/render/build-cyclosm.sh`**

```bash
#!/usr/bin/env bash
# Patch DB connection + fetch shapefiles + compile CyclOSM (master) and CyclOSM-lite (lite branch).
set -euo pipefail
cd "$(dirname "$0")"

for variant in cyclosm cyclosm-lite; do
  docker compose run --rm -w "/checkouts/$variant" tools \
    python3 /render/patch-mml.py project.mml osm
  docker compose run --rm -w "/checkouts/$variant" tools \
    python3 /render/fetch-shapefiles.py project.mml
  docker compose run --rm -w "/checkouts/$variant" tools \
    bash -c 'carto -a "3.0.22" project.mml > mapnik-print.xml'
done
```

(CyclOSM's docs use kosmtik for export, but kosmtik drives the same carto compiler — we call it directly to avoid node-mapnik. If `carto` fails on a kosmtik-only construct in the mml, fix by simplifying that construct in the checkout — it's a disposable clone — and record the change. The lite branch may lag master; if its project.mml import fails against the current `views.sql` schema, run the master checkout's `views.sql` variant noted in the lite branch's own docs.)

- [ ] **Step 2: Build and smoke-render both**

```bash
chmod +x build-cyclosm.sh
./build-cyclosm.sh
./render.sh /checkouts/cyclosm/mapnik-print.xml smoke-cyclosm.png 2000
./render.sh /checkouts/cyclosm-lite/mapnik-print.xml smoke-cyclosm-lite.png 2000
```

Expected: both XMLs compile; `smoke-cyclosm.png` visually matches Phase 1's `map/previews/cyclosm.png`; `smoke-cyclosm-lite.png` is RGBA with a fully transparent background (verify: alpha extrema include 0, majority of pixels transparent) showing only cycling infrastructure. If lite renders opaque, remove/override the `background-color` in its compiled XML or use nik4's transparency option (`nik4 --help`) — resolve before proceeding.

- [ ] **Step 3: Verify overlay alignment and composite**

```bash
(cd .. && uv run python -c "
from PIL import Image
base = Image.open('render/out/smoke-osm-carto.png').convert('RGBA')
lite = Image.open('render/out/smoke-cyclosm-lite.png').convert('RGBA')
assert base.size == lite.size, (base.size, lite.size)
Image.alpha_composite(base, lite).save('render/out/smoke-composite.png')
print('composite ok', base.size)
")
```

Expected: sizes match exactly; `out/smoke-composite.png` looks like Phase 1's chosen `osm-carto-cyclosm-overlay` preview (bike lanes/trails over carto base) — this is the definitive stack validation.

- [ ] **Step 4: Commit**

```bash
git add build-cyclosm.sh
git commit -m "feat(map): cyclosm + cyclosm-lite print builds, smoke composite validates stack"
```

---

### Task 5: Full-resolution renders, composite, letter test crop

**Files:**
- Create: `map/render/render-full.sh`
- Create: `map/scripts/composite_print.py`
- Create: `map/scripts/letter_crop.py`

**Interfaces:**
- Consumes: both `mapnik-print.xml` files; `render.sh`; Phase 1 `map/` uv env (PIL, maptools: `CAYCE_BBOX`, `deg2xy`).
- Produces: `out/full-osm-carto.png` + `out/full-cyclosm-lite.png` (14400 px wide, ≈14435 high, identical sizes); `out/full-composite.png`; `out/letter-test.png` (2400×3150 = 8×10.5 in @ 300 dpi, centered on the school, 300 dpi metadata); vector `out/full-osm-carto.pdf` + `out/full-cyclosm-lite.pdf` (furniture-phase inputs).

- [ ] **Step 1: Create `map/render/render-full.sh`**

```bash
#!/usr/bin/env bash
# Full print-resolution renders: 14400 px wide raster of base + overlay, plus vector PDFs.
set -euo pipefail
cd "$(dirname "$0")"

./render.sh /checkouts/openstreetmap-carto/mapnik-print.xml full-osm-carto.png 14400
./render.sh /checkouts/cyclosm-lite/mapnik-print.xml full-cyclosm-lite.png 14400

# Vector PDFs via cairo (nik4 picks the backend from the extension).
# render.sh's PIL check will fail on PDFs — invoke nik4 directly here.
docker compose run --rm tools \
  nik4 --bbox -81.100988 33.943360 -81.035242 33.998016 \
       --size-px 14400 0 --ppi 300 \
       /checkouts/openstreetmap-carto/mapnik-print.xml /out/full-osm-carto.pdf
docker compose run --rm tools \
  nik4 --bbox -81.100988 33.943360 -81.035242 33.998016 \
       --size-px 14400 0 --ppi 300 \
       /checkouts/cyclosm-lite/mapnik-print.xml /out/full-cyclosm-lite.pdf
ls -la out/full-*
```

- [ ] **Step 2: Create `map/scripts/composite_print.py`**

```python
"""Composite the print-resolution cyclosm-lite overlay onto the osm-carto base."""

from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # 14400x14435 exceeds PIL's decompression-bomb default

OUT = Path(__file__).resolve().parent.parent / "render" / "out"

base = Image.open(OUT / "full-osm-carto.png").convert("RGBA")
overlay = Image.open(OUT / "full-cyclosm-lite.png").convert("RGBA")
assert base.size == overlay.size, (base.size, overlay.size)
composite = Image.alpha_composite(base, overlay)
composite.convert("RGB").save(OUT / "full-composite.png")
print("saved", OUT / "full-composite.png", composite.size)
```

- [ ] **Step 3: Create `map/scripts/letter_crop.py`**

```python
"""Crop a US-letter-printable section (8 x 10.5 in @ 300 dpi) from the full-size
composite, centered on the school, for a true-scale home test print."""

from pathlib import Path

from PIL import Image

from maptools import CAYCE_BBOX, deg2xy

Image.MAX_IMAGE_PIXELS = None

SCHOOL_LAT, SCHOOL_LON = 33.981738, -81.056747
CROP_W, CROP_H = 2400, 3150  # 8 x 10.5 in at 300 dpi

OUT = Path(__file__).resolve().parent.parent / "render" / "out"
im = Image.open(OUT / "full-composite.png")

# School's fractional position within the bbox, in mercator space (zoom cancels out).
x_w, y_n = deg2xy(CAYCE_BBOX.north, CAYCE_BBOX.west, 0)
x_e, y_s = deg2xy(CAYCE_BBOX.south, CAYCE_BBOX.east, 0)
x_school, y_school = deg2xy(SCHOOL_LAT, SCHOOL_LON, 0)
fx = (x_school - x_w) / (x_e - x_w)
fy = (y_school - y_n) / (y_s - y_n)

cx, cy = round(im.width * fx), round(im.height * fy)
left = min(max(cx - CROP_W // 2, 0), im.width - CROP_W)
top = min(max(cy - CROP_H // 2, 0), im.height - CROP_H)
crop = im.crop((left, top, left + CROP_W, top + CROP_H))
crop.save(OUT / "letter-test.png", dpi=(300, 300))
print("saved", OUT / "letter-test.png", crop.size, "school at fraction", (round(fx, 3), round(fy, 3)))
```

- [ ] **Step 4: Run everything**

```bash
chmod +x render-full.sh
./render-full.sh          # the 14400px renders take a while; PDFs likewise
cd .. && uv run python scripts/composite_print.py && uv run python scripts/letter_crop.py
```

Expected: `full-osm-carto.png` and `full-cyclosm-lite.png` at 14400×~14435 with **identical** sizes; composite saved; `letter-test.png` at 2400×3150 with 300 dpi metadata, school near center (fx≈0.67, fy≈0.30); both PDFs nonzero and plausibly large. If a full-res nik4 render dies from memory, raise Docker's memory limit first (each RGBA buffer is ~830 MB; compositing peaks ~2.5 GB); only as a last resort split into two half-width renders.

- [ ] **Step 5: Sanity-check label size at print scale**

Open `letter-test.png` and measure: residential street-name labels should be roughly 0.10–0.15 in tall when printed (30–45 px in the crop). Record observed sizes in the report — this feeds the user's print-test verdict. (Tuning lever if too small, for later — do NOT tune preemptively: raise `--ppi` above 300 in `render.sh`, or edit `text-size` in the styles' `.mss` and rebuild.)

- [ ] **Step 6: Commit**

```bash
cd render
git add render-full.sh ../scripts/composite_print.py ../scripts/letter_crop.py
git commit -m "feat(map): full print-res renders, composite, and true-scale letter test crop"
```

---

### Task 6: Bike-infra audit, README, handoff

**Files:**
- Create: `map/render/audit-bike-infra.sh`
- Create: `map/render/AUDIT.md` (generated report, committed — small, documents data quality at render time)
- Modify: `map/README.md`

**Interfaces:**
- Consumes: populated `osm` db; all Phase 2 outputs.
- Produces: the audit report; updated README covering the Phase 2 workflow; the user handoff (print `letter-test.png` at Actual Size).

- [ ] **Step 1: Create `map/render/audit-bike-infra.sh`**

```bash
#!/usr/bin/env bash
# Summarize the cycling infrastructure mapped in OSM within the print bbox.
set -euo pipefail
cd "$(dirname "$0")"

{
  echo "# Bike-infrastructure audit (print bbox, OSM data of 2026-07-03)"
  echo
  echo "Generated by audit-bike-infra.sh — re-run after editing OSM + re-importing."
  echo
  echo '## Dedicated cycleways (highway=cycleway)'
  echo '```'
  docker compose run --rm -T tools psql -d osm -Atc \
    "SELECT coalesce(name,'(unnamed)') || ' — ' || round(sum(ST_Length(way))::numeric) || ' m'
     FROM planet_osm_line WHERE highway='cycleway' GROUP BY name ORDER BY sum(ST_Length(way)) DESC;"
  echo '```'
  echo
  echo '## Streets with cycle lanes/tracks (cycleway* tags)'
  echo '```'
  docker compose run --rm -T tools psql -d osm -Atc \
    "SELECT DISTINCT coalesce(name,'(unnamed)') || ' [' ||
       concat_ws(',', tags->'cycleway', tags->'cycleway:left', tags->'cycleway:right', tags->'cycleway:both') || ']'
     FROM planet_osm_line
     WHERE (tags->'cycleway' IS NOT NULL OR tags->'cycleway:left' IS NOT NULL
        OR tags->'cycleway:right' IS NOT NULL OR tags->'cycleway:both' IS NOT NULL)
       AND highway IS NOT NULL ORDER BY 1;"
  echo '```'
  echo
  echo '## Bicycle route relations crossing the area'
  echo '```'
  docker compose run --rm -T tools psql -d osm -Atc \
    "SELECT DISTINCT coalesce(name, tags->'ref', '(unnamed route)')
     FROM planet_osm_line WHERE route='bicycle' ORDER BY 1;"
  echo '```'
} > AUDIT.md

cat AUDIT.md
```

- [ ] **Step 2: Run it**

```bash
chmod +x audit-bike-infra.sh && ./audit-bike-infra.sh
```

Expected: AUDIT.md lists the known corridors (Cayce Riverwalk / Timmerman Trail should appear under cycleways) plus whatever lanes/routes exist. Empty sections are a finding, not an error (they mean under-mapped infra worth editing in OSM). If a query errors on schema differences (e.g., `tags` hstore column name), adjust to the actual `osm` schema (imported with `--hstore`) and note it.

- [ ] **Step 3: Update `map/README.md`** — append after the Phase 1 section:

```markdown
## Phase 2 — print-resolution rendering

Requires Docker. From `render/`:

    docker compose build tools && docker compose up -d db
    ./checkout-styles.sh   # osm-carto (pinned tag) + cyclosm master/lite
    ./clip.sh              # expects ~/Downloads/south-carolina-260703.osm.pbf
    ./import.sh            # both databases
    ./build-osm-carto.sh   # external data (slow first run) + fonts + carto compile
    ./build-cyclosm.sh     # patch + shapefiles + carto compile, both variants
    ./render-full.sh       # 14400px renders + vector PDFs

Then from `map/`:

    uv run python scripts/composite_print.py   # base + overlay -> render/out/full-composite.png
    uv run python scripts/letter_crop.py       # true-scale 8x10.5in test crop around the school

Print `render/out/letter-test.png` at **Actual Size** (no scaling) to judge
label legibility before ordering the wall print. `./audit-bike-infra.sh`
reports how completely the area's cycling infrastructure is mapped in OSM.
```

- [ ] **Step 4: Commit**

```bash
git add audit-bike-infra.sh AUDIT.md ../README.md
git commit -m "feat(map): bike-infra audit + Phase 2 README"
```

- [ ] **Step 5: Hand to the user (Phase 2 decision gate)**

Tell the user: print `map/render/out/letter-test.png` on US letter at **Actual Size / 100% scale** and check street-name legibility at arm's length and from a few feet; review `AUDIT.md` for missing bike infra (fix in OSM → re-download extract → re-run clip/import/render if desired); the furniture phase (title, legend, logo, scale bar in Inkscape, final print PDF) gets planned after this verdict.
