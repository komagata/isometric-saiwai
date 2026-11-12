"""Saiwai Ward plus a rounded context margin, UTM zone 54N (EPSG:32654), metres."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
RAW, BUILD = ROOT / 'data/raw', ROOT / 'data/build'
# Exact OSM ward envelope: 35.5261645..35.5620586, 139.654139..139.704239.
# All boundary vertices fit inside these 500 m aligned bounds.
XMIN, YMIN, XMAX, YMAX = 377500, 3932000, 383000, 3936500
CX, CY = (XMIN+XMAX)/2, (YMIN+YMAX)/2
CHUNK, GROUND_RES, TERRAIN_RES = 500, 1.0, 10
NX, NY = (XMAX-XMIN)//CHUNK, (YMAX-YMIN)//CHUNK
VIEWS = (45,135,225,315)

def terrain_slab_top(minimum):
    """Keep the decorative base below every actual ground sample, including below sea level."""
    return float(minimum)-1

def write_area():
    BUILD.mkdir(parents=True,exist_ok=True)
    area=dict(xmin=XMIN,ymin=YMIN,xmax=XMAX,ymax=YMAX,cx=CX,cy=CY,chunk=CHUNK,nx=NX,ny=NY,crs='EPSG:32654',vertical_datum='Tokyo Bay mean sea level',terrain_step=TERRAIN_RES)
    summary=BUILD/'terrain_summary.json'
    if summary.exists():
        minimum=json.loads(summary.read_text())['dtm_min']
        area.update(min_terrain=minimum,slab_top=terrain_slab_top(minimum))
    (BUILD/'area.json').write_text(json.dumps(area))
