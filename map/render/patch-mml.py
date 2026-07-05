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
