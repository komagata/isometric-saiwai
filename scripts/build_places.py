"""Search locally sourced landmarks and named OSM places; no invented addresses."""
import json
from config import *
from japan import osm_elements,height
from geo import wgs_to_rd

def main():
    places=json.loads((BUILD/'landmarks.json').read_text())['places'];seen={p['name'] for p in places}
    for e in osm_elements():
        t=e.get('tags',{});name=t.get('name:ja') or t.get('name')
        if not name or name in seen:continue
        geom=e.get('geometry',[]) or [q for m in e.get('members',[]) for q in m.get('geometry',[])]
        if e['type']=='node':lat,lon=e['lat'],e['lon']
        elif geom:lat=sum(p['lat'] for p in geom)/len(geom);lon=sum(p['lon'] for p in geom)/len(geom)
        else:continue
        x,y=wgs_to_rd(lat,lon)
        if XMIN<=x<=XMAX and YMIN<=y<=YMAX:
            places.append(dict(name=name,x=round(x,2),y=round(y,2),h=float(height(x,y))+2,note='OpenStreetMap'));seen.add(name)
    (BUILD/'places.json').write_text(json.dumps(places,ensure_ascii=False,separators=(',',':')));print(len(places),'search places')
if __name__=='__main__':main()
