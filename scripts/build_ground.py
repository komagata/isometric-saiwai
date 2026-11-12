"""GSI photo colours, OSM surfaces with holes, and geometric building/tree shadows.
Ground elevation is GSI bare earth; bridges drawn at terrain level (clearance unknown).
"""
import json, gzip
import numpy as np
from PIL import Image,ImageDraw,ImageEnhance
from shapely.geometry import LineString,mapping
from config import *
from japan import osm_elements,osm_xy,osm_polygon,polygon_parts,EXTENT,height
from sun import SUN_AZIMUTH,SUN_ELEVATION

def main():
    photo=np.load(BUILD/'aerial.npy',mmap_mode='r')
    # Posterise to restrained discrete colours while retaining actual photographic ground layout.
    rgb=(np.asarray(photo,dtype=np.float32)*.77+np.array([37,38,27])).clip(0,255).astype(np.uint8)
    rgb=(rgb//16*16+8).clip(0,255).astype(np.uint8)
    image=Image.fromarray(rgb);polygons=[];source_features=[]
    def paint(g,color):
        nonlocal image
        clipped=g.intersection(EXTENT)
        if clipped.is_empty:return
        xmin,ymin,xmax,ymax=clipped.bounds
        left=max(0,int((xmin-XMIN)/GROUND_RES));top=max(0,int((YMAX-ymax)/GROUND_RES))
        right=min(image.width,int((xmax-XMIN)/GROUND_RES)+2);bottom=min(image.height,int((YMAX-ymin)/GROUND_RES)+2)
        if right<=left or bottom<=top:return
        mask=Image.new('L',(right-left,bottom-top),0);d=ImageDraw.Draw(mask)
        px=lambda ring:[((x-XMIN)/GROUND_RES-left,(YMAX-y)/GROUND_RES-top) for x,y in ring.coords]
        for p in polygon_parts(clipped):
            d.polygon(px(p.exterior),fill=255)
            for hole in p.interiors:d.polygon(px(hole),fill=0)
        image.paste(color,(left,top,right,bottom),mask)
    for e in osm_elements():
        t=e.get('tags',{});g=osm_polygon(e)
        if not g.is_empty and g.intersects(EXTENT):
            color=None
            if t.get('natural')=='water' or t.get('waterway')=='riverbank' or t.get('landuse')=='reservoir':color=(76,130,164)
            elif t.get('natural')=='wood' or t.get('landuse')=='forest':color=(82,119,72)
            elif t.get('leisure') in ('park','garden','pitch') or t.get('landuse') in ('grass','meadow'):color=(124,157,90)
            if color:paint(g,color);source_features.append(dict(type='Feature',geometry=mapping(g.intersection(EXTENT)),properties=t))
        if e['type']!='way' or len(e.get('geometry',[]))<2 or t.get('tunnel')=='yes':continue
        if not (t.get('highway') or t.get('railway')=='rail' or t.get('waterway')):continue
        line=LineString(osm_xy(e['geometry'])).intersection(EXTENT)
        if line.is_empty:continue
        if t.get('railway')=='rail':color=(98,99,95);width=2
        elif t.get('waterway'):color=(76,130,164);width=4
        else:
            hw=t['highway'];width={'motorway':12,'trunk':10,'primary':9,'secondary':8,'tertiary':6,'residential':4,'service':3,'footway':1.5,'path':1.5,'steps':1.5,'cycleway':2}.get(hw,4)
            try:width=float(t.get('width',width))
            except ValueError:pass
            color=(135,135,129) if width>=3 else (183,176,153)
        g=line.buffer(width/2,cap_style=2,join_style=2);paint(g,color)
        source_features.append(dict(type='Feature',geometry=mapping(line),properties={**t,'display_width_m':width,'width_provenance':'OSM width tag' if 'width'in t else 'cartographic class estimate'}))
    # Bake projected shadows using relative building/tree heights, shared absolute ground reference.
    shadow=Image.new('L',image.size,0);d=ImageDraw.Draw(shadow)
    az,el=np.radians(SUN_AZIMUTH),np.radians(SUN_ELEVATION)
    sx,sy=-np.sin(az)/np.tan(el),-np.cos(az)/np.tan(el)
    v=np.fromfile(BUILD/'buildings.bin',np.float32).reshape(-1,12)
    for tri in v.reshape(-1,3,12):
        if tri[0,8]!=2:continue
        x=tri[:,0]+CX;y=CY-tri[:,2];h=np.maximum(0,tri[:,1]-height(x,y))
        d.polygon([((xx+sx*hh-XMIN)/GROUND_RES,(YMAX-yy-sy*hh)/GROUND_RES) for xx,yy,hh in zip(x,y,h)],fill=92)
    trees=np.fromfile(BUILD/'trees.bin',np.float32).reshape(-1,10)
    for x,z,h,r,*_ in trees:
        c=(x+CX+sx*h-XMIN)/GROUND_RES;row=(YMAX-(CY-z+sy*h))/GROUND_RES;rad=r/GROUND_RES
        d.ellipse([c-rad,row-rad,c+rad,row+rad],fill=70)
    a=np.asarray(image).astype(float)*(1-np.asarray(shadow)[:,:,None]/255)
    image=Image.fromarray(a.astype(np.uint8));(BUILD/'ground').mkdir(exist_ok=True)
    px=int(CHUNK/GROUND_RES)
    for ix in range(NX):
        for iy in range(NY):
            row=(NY-1-iy)*px;image.crop((ix*px,row,(ix+1)*px,row+px)).save(BUILD/'ground'/f'{ix}_{iy}.png')
    # Roads are baked into terrain-following texture, avoiding flat upstream road overlays.
    (BUILD/'roads.json').write_text('{"polygons":[],"edges":[]}')
    with gzip.open(BUILD/'osm-derived.geojson.gz','wt') as f:json.dump(dict(type='FeatureCollection',crs=dict(type='name',properties=dict(name='EPSG:32654')),features=source_features),f,separators=(',',':'))
    print(f'{len(source_features)} OSM ground/road/rail/water features; {NX*NY} terrain texture chunks',flush=True)
if __name__=='__main__':main()
