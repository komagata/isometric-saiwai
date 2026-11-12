#!/usr/bin/env bash
# Cut the rendered map into Deep Zoom pyramids and assemble site/, without rendering anything.
#   ./site.sh              from out/full-4.png, and out/full-4-v<look>.png for the other views in scripts/config.py
# Every run writes the tiles to a fresh folder (tiles-<stamp>/), named in map.json, so browsers never mix cached
# tiles of an older version with a new one.
set -euo pipefail
builtin cd "$(dirname "$0")"
SCALE="${SCALE:-2}"
SITE=site
VIEWS=$(uv run --no-sync python -c 'import sys;sys.path.insert(0,"scripts");from config import VIEWS;print(*VIEWS)')

stamp=$(date +%Y%m%d-%H%M%S)
rm -rf "$SITE" && mkdir -p "$SITE/tiles-$stamp"

pyramid() {  # image, name under tiles-<stamp>/
  vips dzsave "$1" "$SITE/tiles-$stamp/$2" --tile-size 1024 --overlap 0 --suffix '.webp[Q=90]'
  rm -f "$SITE/tiles-$stamp/$2.dzi" "$SITE/tiles-$stamp/$2_files/vips-properties.xml"
}

for look in $VIEWS; do
  # Looking north-east (45) keeps the names it always had; the other views go into a folder of their own.
  suffix=$([ "$look" = 45 ] && echo "" || echo "-v$look")
  dir=$([ -z "$suffix" ] && echo "" || echo "v$look/")
  full="out/full-$SCALE$suffix.png"
  [ -f "$full" ] || { echo "skipping view $look: no $full" >&2; continue; }
  pyramid "$full" "${dir}saiwai"
  # The buildings and trees once more, transparent elsewhere: the viewer lays them over the cars and walkers behind them.
  objects="out/objects-$SCALE$suffix.png"
  if [ -f "$objects" ]; then
    vips bandjoin "$full $objects" out/objects.v
    pyramid out/objects.v "${dir}objects"
    rm -f out/objects.v
  fi
done

python3 - "$SCALE" "$stamp" "$SITE" $VIEWS <<'PY'
import json, os, sys
scale, stamp, site, *views = sys.argv[1:]
m = json.load(open(f"out/tiles-{scale}/layout.json"))
m["views"] = []
for look in views:
    base = f"tiles-{stamp}/" + ("" if look == "45" else f"v{look}/")
    if not os.path.isdir(f"{site}/{base}saiwai_files"):
        continue
    view = {"look": int(look), "tiles": f"{base}saiwai_files/"}
    if os.path.isdir(f"{site}/{base}objects_files"):
        view["objects"] = f"{base}objects_files/"
    m["views"].append(view)
m.update({k: m["views"][0][k] for k in ("tiles", "objects") if k in m["views"][0]})
json.dump(m, open(f"{site}/map.json", "w"))
PY
cp viewer/index.html viewer/geo.js viewer/projection.js viewer/en.json data/build/places.json data/build/hotspots.json data/build/routes.json data/build/history.json data/build/traffic.json data/build/terrain-viewer.json data/build/source-manifest.json data/build/geodata.zip DATA_SOURCES.md "$SITE/"
cp data/build/lidar-coverage.png "$SITE/"
cp -r viewer/music "$SITE/music"
# Actual mapped street-lamp locations (decorative light, no guessed village centre).
uv run --no-sync python scripts/site_metadata.py
mkdir -p "$SITE/vendor"
cp viewer/vendor/openseadragon.min.js viewer/vendor/OpenSeadragon-LICENSE.txt "$SITE/vendor/"
touch "$SITE/.nojekyll"
echo "$SITE/ is ready: $(find "$SITE" -type f | wc -l) files, $(du -sh "$SITE" | cut -f1)"
