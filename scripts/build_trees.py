"""Measured DSM-DTM canopy with PLATEAU roof exclusion and aerial/OSM support.
Outside measured DSM coverage, OSM/aerial placements retain explicitly estimated 8m height.
LAS vegetation classes are audit data: they miss much tall canopy in this source.
"""
import json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw
from config import *
from japan import osm_elements,osm_polygon,polygon_parts,height,measured_canopy,building_footprint_mask
from geo import wgs_to_rd

def main():
    lidar=np.load(BUILD/'lidar.npz');coverage=lidar['coverage'];dsm=lidar['dsm']
    aerial=np.load(BUILD/'aerial.npy',mmap_mode='r')[1::2,1::2].astype(np.float32)
    green=(aerial[:,:,1]>aerial[:,:,0]*1.10)&(aerial[:,:,1]>aerial[:,:,2]*1.06)&(aerial[:,:,1]>45)
    green=ndi.binary_dilation(green,iterations=1)
    mapped=Image.new('1',(dsm.shape[1],dsm.shape[0]),0);wood=mapped.copy()
    mapped_draw=ImageDraw.Draw(mapped);wood_draw=ImageDraw.Draw(wood);points=[]
    for e in osm_elements():
        t=e.get('tags',{})
        if e['type']=='node' and t.get('natural')=='tree':points.append(wgs_to_rd(e['lat'],e['lon']))
        is_wood=t.get('natural')=='wood' or t.get('landuse')=='forest'
        if not is_wood and t.get('natural')!='scrub' and t.get('landuse') not in ('grass','meadow') and t.get('leisure') not in ('park','garden'):continue
        for poly in polygon_parts(osm_polygon(e)):
            px=lambda ring:[((x-XMIN)/2,(YMAX-y)/2) for x,y in ring.coords]
            for draw in ([mapped_draw,wood_draw] if is_wood else [mapped_draw]):
                draw.polygon(px(poly.exterior),fill=1)
                for hole in poly.interiors:draw.polygon(px(hole),fill=0)
    footprint=building_footprint_mask(2)
    Image.fromarray((footprint*255).astype(np.uint8)).save(BUILD/'building-footprints.png')
    base=np.load(BUILD/'dtm.npy',mmap_mode='r')[1::2,1::2]
    chm=measured_canopy(dsm,base,coverage,green|np.asarray(wood),footprint)
    np.save(BUILD/'chm.npy',chm)
    heights=np.nan_to_num(chm,nan=0)
    candidate=(heights>3)&(heights<45)
    # Reject isolated single-return speckles; retain compact individual crowns.
    candidate &= ndi.convolve(candidate.astype(np.uint8),np.ones((3,3),np.uint8),mode='constant')>=3
    peaks=candidate&(heights==ndi.maximum_filter(heights,size=5))
    rr,cc=np.where(peaks);order=np.argsort(heights[rr,cc])[::-1]
    blocked=np.zeros(chm.shape,bool);rows=[];records=[];rng=np.random.default_rng(14130)
    def add(x,y,h,r,source):
        ground=float(height(x,y));seed=float(rng.random())
        rows.append([x-CX,CY-y,h,r,max(1,h*.45),0,ground,0,0,seed])
        records.append(dict(x=round(x,2),y=round(y,2),height=round(h,2),radius=round(r,2),ground=round(ground,2),provenance=source))
    for i in order:
        r,c=rr[i],cc[i]
        if blocked[r,c]:continue
        ht=float(heights[r,c]);rad=float(np.clip(ht*.22,1.5,6))
        x,y=XMIN+(c+.5)*2,YMAX-(r+.5)*2
        add(x,y,ht,rad,'measured: Kanagawa LAS 2022 DSM minus GSI DTM; aerial/OSM woodland support; PLATEAU roof excluded')
        d=max(2,int(rad));blocked[max(0,r-d):r+d+1,max(0,c-d):c+d+1]=True
    measured=len(rows)
    estimated_candidate=green&np.asarray(mapped)&~coverage&~footprint
    for r in range(2,chm.shape[0]-2,5):
        for c in range(2,chm.shape[1]-2,5):
            if estimated_candidate[r-1:r+2,c-1:c+2].mean()>.6:points.append((XMIN+(c+.5)*2,YMAX-(r+.5)*2))
    for x,y in points:
        if not(XMIN<=x<XMAX and YMIN<y<=YMAX):continue
        r,c=int((YMAX-y)/2),int((x-XMIN)/2)
        if coverage[r,c] or footprint[r,c]:continue
        add(x,y,8,2.8,'estimated: mapped OSM tree or green aerial within OSM park/wood; nominal 8 m; PLATEAU roof excluded')
    np.asarray(rows,np.float32).reshape(-1,10).tofile(BUILD/'trees.bin')
    (BUILD/'trees.json').write_text(json.dumps(records,separators=(',',':')))
    # Actual source acceptance patch around the zoo hill, not an invented scene.
    x,y=wgs_to_rd(35.54916456,139.66564829);r,c=int((YMAX-y)/2),int((x-XMIN)/2);patch=chm[r-70:r+70,c-70:c+70]
    summary=dict(total=len(rows),measured_canopy_peaks=measured,estimated_outside_coverage=len(rows)-measured,method='Measured DSM-DTM, aerial green or OSM woodland support, PLATEAU projected footprint plus 2m margin excluded; LAS vegetation classes audit only',hill_patch_above_3m=int(np.count_nonzero(patch>3)),hill_patch_max_m=float(np.nanmax(patch)),hill_patch_measured_trees=int(sum(abs(p['x']-x)<140 and abs(p['y']-y)<140 and p['provenance'].startswith('measured') for p in records)),limitations='Source classification misses tall canopy. Crown radius inferred from measured height; no individual-tree species inventory. Conservative building exclusion also omits rooftop gardens. DSM gaps remain NaN.')
    (BUILD/'tree_summary.json').write_text(json.dumps(summary,indent=2));print(summary,flush=True)
if __name__=='__main__':main()
