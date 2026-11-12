"""Augment published map metadata with actual OSM lamps and shared Japan source context."""
import json
from config import ROOT,BUILD,CX,CY
from japan import osm_elements
from geo import wgs_to_rd

def main():
    path=ROOT/'site/map.json';m=json.loads(path.read_text());lamps=[]
    for e in osm_elements():
        if e['type']=='node' and e.get('tags',{}).get('highway')=='street_lamp':
            x,y=wgs_to_rd(e['lat'],e['lon'])
            if m['area']['xmin']<=x<=m['area']['xmax'] and m['area']['ymin']<=y<=m['area']['ymax']:lamps.append([round(x-CX,2),round(CY-y,2)])
    m.update(lamps=lamps,title='幸区の小さな地図',location='川崎市幸区・神奈川県・日本',source_manifest='source-manifest.json',geodata='geodata.zip',data_retrieved='2026-11-12')
    path.write_text(json.dumps(m,ensure_ascii=False,separators=(',',':')))
if __name__=='__main__':main()
