#!/usr/bin/env python3
"""Download shapefile archives referenced by a project.mml (kosmtik-fetch-remote's job).

Usage: fetch-shapefiles.py <path/to/project.mml>
Looks for Datasource dicts having both a local `file` path and a remote URL
(in `file` itself or in a sibling key such as `url`); downloads and unzips
into the expected location, relative to the mml's directory. Skips anything
already present.

Extended (CyclOSM support): when the `file` field IS an HTTP URL (no sibling `url`
key), the zip is downloaded, extracted into data/<stem>/, and the mml `file` field
is updated in-place to point to the local .shp path. The mml is re-written so that
carto sees a local file path rather than the remote URL.
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

# jobs: list of (local_file_str_or_None, url_str, dict_node_or_None)
# When node is not None, the mml dict node's "file" field will be patched to the
# resolved local path after download, and the mml file will be re-written.
jobs = []


def scan(node):
    if isinstance(node, dict):
        f, url = node.get("file"), node.get("url")
        if isinstance(f, str) and isinstance(url, str) and url.startswith("http"):
            jobs.append((f, url, None))
        elif isinstance(f, str) and f.startswith("http"):
            # file IS the download URL — need to patch node after download
            jobs.append((None, f, node))
        for value in node.values():
            scan(value)
    elif isinstance(node, list):
        for value in node:
            scan(value)


scan(mml)
mml_modified = False
for local, url, node in jobs:
    if local is not None:
        # classic case: download to the local path alongside the mml
        target_dir = (root / local).parent
        marker = root / local
        if marker.exists():
            print(f"have {local}")
            continue
        print(f"fetch {url} -> {target_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)
        payload = urlopen(url, timeout=120).read()
        if url.endswith(".zip"):
            zipfile.ZipFile(io.BytesIO(payload)).extractall(target_dir)
        else:
            (target_dir / Path(url).name).write_bytes(payload)
    else:
        # CyclOSM case: file IS the HTTP zip URL; download into data/ (the zip
        # typically contains its own stem/ subdirectory) and patch the mml node
        # so carto gets a local path.  Use rglob to find the .shp regardless of
        # the exact internal structure the zip creates.
        data_dir = root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        shp_files = list(data_dir.rglob("*.shp"))
        stem = Path(url).stem  # e.g. simplified-land-polygons-complete-3857
        # narrow to shp files under the expected stem directory
        shp_files = [s for s in shp_files if stem in str(s)]
        if not shp_files:
            print(f"fetch {url} -> {data_dir}")
            payload = urlopen(url, timeout=120).read()
            if url.endswith(".zip"):
                zipfile.ZipFile(io.BytesIO(payload)).extractall(data_dir)
            else:
                (data_dir / Path(url).name).write_bytes(payload)
            shp_files = [s for s in data_dir.rglob("*.shp") if stem in str(s)]
        if shp_files and node is not None:
            local_path = shp_files[0].relative_to(root)
            print(f"patch mml file {url!r} -> {local_path}")
            node["file"] = str(local_path)
            mml_modified = True
        elif not shp_files:
            print(f"WARNING: no .shp found under {data_dir}/{stem} after download")

if mml_modified:
    with open(mml_path, "w") as f:
        yaml.dump(mml, f, default_flow_style=False)
    print("re-wrote mml with local shapefile paths")
print(f"{len(jobs)} remote datasource(s) processed")
