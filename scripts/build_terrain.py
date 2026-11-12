"""GSI bare-earth terrain/aerial and bounded, classified 2022 Kanagawa LAS DSM."""
import json
from collections import Counter
import numpy as np
from PIL import Image
from pyproj import Transformer
from scipy import ndimage as ndi
from config import *
from japan import raster_xy, sample_gsi, las_chunks
from geo import rd_to_wgs

def main():
    write_area()
    # Process bands to avoid holding a full geographic mesh in memory.
    w,h=int((XMAX-XMIN)/GROUND_RES),int((YMAX-YMIN)/GROUND_RES)
    dtm=np.full((h,w),np.nan,np.float32); aerial=np.zeros((h,w,3),np.uint8)
    for r in range(0,h,128):
        nr=min(128,h-r)
        xx,yy=np.meshgrid(XMIN+(np.arange(w)+.5)*GROUND_RES,YMAX-(np.arange(r,r+nr)+.5)*GROUND_RES)
        lat,lon=rd_to_wgs(xx,yy)
        d=sample_gsi(lat,lon,'dem5a',15)
        fallback=sample_gsi(lat,lon,'dem',14)
        dtm[r:r+nr]=np.where(np.isfinite(d),d,fallback)
        photo=sample_gsi(lat,lon,'seamlessphoto',17)
        if not np.isfinite(photo).all(): raise RuntimeError('GSI aerial cache has holes inside render bounds')
        aerial[r:r+nr]=photo.astype(np.uint8)
    if not np.isfinite(dtm).all(): raise RuntimeError('GSI DEM cache has holes inside render bounds')
    np.save(BUILD/'dtm.npy',dtm);np.save(BUILD/'aerial.npy',aerial)
    # Measured DSM and classified vegetation on 2 m cells. No extrapolation into gaps.
    res=2; shape=(h//res,w//res)
    dsm=np.full(shape,-np.inf,np.float32);veg=dsm.copy();count=np.zeros(shape,np.uint32)
    ground=dsm.copy(); classes=Counter()
    to_utm=Transformer.from_crs(6677,32654,always_xy=True)
    files=sorted((RAW/'lidar').glob('*.zip'))
    if not files: raise RuntimeError('Measured lidar cache missing; do not substitute DTM for DSM')
    for path in files:
        for xyz,cls in las_chunks(path):
            x,y=to_utm.transform(xyz[:,0],xyz[:,1]);z=xyz[:,2]
            mask=(x>=XMIN)&(x<XMAX)&(y>YMIN)&(y<=YMAX)&np.isfinite(z)&(z>-20)&(z<250)&~np.isin(cls,[7,18])
            x,y,z,cls=x[mask],y[mask],z[mask],cls[mask]
            classes.update(dict(zip(*[a.tolist() for a in np.unique(cls,return_counts=True)])))
            rr=np.clip(((YMAX-y)/res).astype(int),0,shape[0]-1);cc=np.clip(((x-XMIN)/res).astype(int),0,shape[1]-1)
            np.maximum.at(dsm,(rr,cc),z);np.add.at(count,(rr,cc),1)
            m=np.isin(cls,[3,4,5]);np.maximum.at(veg,(rr[m],cc[m]),z[m])
            m=np.isin(cls,[2,8]);np.maximum.at(ground,(rr[m],cc[m]),z[m])
        print('LAS',path.name,flush=True)
    coverage=np.isfinite(dsm)
    # GSI DTM is the shared bare-earth reference; class 2 LAS is retained for audit only.
    base=dtm[1::2,1::2]
    chm=np.where(np.isfinite(veg),np.maximum(0,veg-base),0).astype(np.float32)
    np.savez_compressed(BUILD/'lidar.npz',dsm=np.where(coverage,dsm,np.nan),vegetation_top=np.where(np.isfinite(veg),veg,np.nan),ground=np.where(np.isfinite(ground),ground,np.nan),coverage=coverage,counts=count,resolution=res)
    np.save(BUILD/'chm.npy',chm)
    summary=dict(files=len(files),classes=dict(classes),resolution_m=res,covered_cells=int(coverage.sum()),total_cells=int(coverage.size),coverage_fraction=float(coverage.mean()),dtm_min=float(dtm.min()),dtm_max=float(dtm.max()),vertical_reference='Tokyo Bay mean sea level; no epoch/geoid adjustment',dsm='max valid LAS return; gaps NaN',vegetation='LAS classes 3/4/5 retained for audit; incomplete tall canopy. Main trees use measured DSM-DTM plus aerial/OSM support and PLATEAU roof exclusion')
    (BUILD/'terrain_summary.json').write_text(json.dumps(summary,indent=2)); write_area(); print(summary,flush=True)
    # Terrain grid for each ground tile. Row ordering north -> south.
    out={}
    for ix in range(NX):
        for iy in range(NY):
            x=XMIN+ix*CHUNK+np.arange(CHUNK//TERRAIN_RES+1)*TERRAIN_RES
            y=YMIN+iy*CHUNK+CHUNK-np.arange(CHUNK//TERRAIN_RES+1)*TERRAIN_RES
            xx,yy=np.meshgrid(x,y)
            rr=np.clip(((YMAX-yy)/GROUND_RES).astype(int),0,h-1);cc=np.clip(((xx-XMIN)/GROUND_RES).astype(int),0,w-1)
            out[f'{ix}_{iy}']=dtm[rr,cc].round(2).ravel().tolist()
    (BUILD/'terrain.json').write_text(json.dumps(out,separators=(',',':')))
    Image.fromarray((coverage*255).astype(np.uint8)).save(BUILD/'lidar-coverage.png')
if __name__=='__main__':main()
