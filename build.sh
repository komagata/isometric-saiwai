#!/usr/bin/env bash
# Build Saiwai from the cached/downloadable real source datasets. Default 2 pixels/metre.
set -euo pipefail
builtin cd "$(dirname "$0")"
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/saiwai-uv-cache}"
export SCALE="${SCALE:-2}"
uv sync --locked
uv run --no-sync python scripts/fetch.py
for step in build_terrain build_buildings build_trees build_ground landmarks build_places build_hotspots build_routes build_traffic build_history build_manifest; do
  uv run --no-sync python "scripts/$step.py"
done
[ -d node_modules ] || npm ci --ignore-scripts
VIEWS=$(uv run --no-sync python -c 'import sys;sys.path.insert(0,"scripts");from config import VIEWS;print(*VIEWS)')
for look in $VIEWS; do
  node render/run.mjs all --scale "$SCALE" --tile 2048 --kuwahara 1 --look "$look"
  node render/run.mjs all --scale "$SCALE" --tile 2048 --pass objects --look "$look"
done
layout="out/tiles-$SCALE/layout.json"
read -r W H C < <(python3 -c "import json; d=json.load(open('$layout')); print(d['width'], d['height'], d['cols'])")
join() {
  vips arrayjoin "$(/bin/ls "$1"/*.png | tr '\n' ' ')" out/joined.v --across "$C"
  vips extract_area out/joined.v out/cropped.v 0 0 "$W" "$H"
  vips extract_band out/cropped.v "$2[compression=1]" 0 --n "$3"
  rm -f out/joined.v out/cropped.v
}
for look in $VIEWS; do
  suffix=$([ "$look" = 45 ] && echo "" || echo "-v$look")
  join "out/tiles-$SCALE$suffix" "out/full-$SCALE$suffix.png" 3
  join "out/tiles-$SCALE-objects$suffix" "out/objects-$SCALE$suffix.png" 1
done
./site.sh
