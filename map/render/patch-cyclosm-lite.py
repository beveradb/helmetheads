#!/usr/bin/env python3
"""Apply cyclosm-lite localconfig-lite.js logic to project.mml for carto compilation.

Usage: patch-cyclosm-lite.py <path/to/project.mml>

Replicates what kosmtik's localconfig-lite.js does at render time:
  1. Filter layers to only those with class containing 'cyclosm-lite'.
  2. Wrap every postgis Datasource table query with
       (SELECT *, 1 AS is_lite FROM (<original>) AS inner_data) AS data
     so that mapnik's outer SELECT can find the is_lite column required by MSS filters.
  3. Add palette-lite.mss to the Stylesheet list.

The original project.mml is overwritten in-place.
"""

import sys
from pathlib import Path

import yaml

mml_path = Path(sys.argv[1]).resolve()
with open(mml_path) as f:
    mml = yaml.safe_load(f)

# 1. Filter layers: keep only those with class containing 'cyclosm-lite'
original_count = len(mml.get("Layer", []))
mml["Layer"] = [
    layer
    for layer in mml.get("Layer", [])
    if "cyclosm-lite" in str(layer.get("class", ""))
]
filtered_count = len(mml["Layer"])
print(f"filtered layers: {original_count} -> {filtered_count} (cyclosm-lite class only)")

# 2. Wrap postgis table queries to inject is_lite=1
wrapped = 0
for layer in mml["Layer"]:
    ds = layer.get("Datasource", {})
    if ds.get("type") == "postgis":
        orig_table = ds.get("table", "")
        if orig_table:
            stripped = orig_table.strip()
            # Skip already-wrapped tables (idempotent)
            if "is_lite" in stripped:
                continue
            # Table is always a parenthesised subquery: "( <sql> ) AS data"
            # Strip the outer "(" and ") AS data" to get the raw SQL, then re-wrap.
            # IMPORTANT: do NOT call .strip() on inner_sql — the trailing newline must
            # be preserved so that closing ") AS inner_data" lands on its own line,
            # otherwise it gets eaten by any trailing SQL comment on the last SELECT line.
            if stripped.startswith("(") and stripped.endswith(") AS data"):
                inner_sql = stripped[1 : -len(") AS data")]
                ds["table"] = (
                    f"(SELECT *, 1 AS is_lite FROM ({inner_sql}) AS inner_data) AS data"
                )
            else:
                # Fallback for non-standard table expressions
                ds["table"] = f"(SELECT *, 1 AS is_lite FROM ({stripped}\n) AS inner_data) AS data"
            wrapped += 1
print(f"wrapped {wrapped} postgis table queries with is_lite=1")

# 3. Add palette-lite.mss to Stylesheet list
mml.setdefault("Stylesheet", [])
lite_palette_path = str(mml_path.parent / "palette-lite.mss")
if lite_palette_path not in mml["Stylesheet"]:
    mml["Stylesheet"].append(lite_palette_path)
    print(f"added palette-lite.mss to Stylesheet")

with open(mml_path, "w") as f:
    yaml.dump(mml, f, default_flow_style=False)
print(f"wrote patched mml to {mml_path}")
