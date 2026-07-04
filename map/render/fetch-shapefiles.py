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
