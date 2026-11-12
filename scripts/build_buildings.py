"""PLATEAU Kawasaki 2022 CityGML v4 -> upstream 12-float renderer contract.
One highest available LoD per Building; absolute source elevations, no invented storeys/heights.
"""
import json
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
import mapbox_earcut as earcut
import numpy as np
from PIL import Image
from shapely.geometry import box
from config import *
from japan import NS,EXTENT,mesh_bounds,building_surfaces
from geo import wgs_to_rd
from aerial import load_aerial

def triangles(rings):
    # Project a planar 3D face onto the two coordinates with greatest stable area.
    ext=rings[0]; normal=np.zeros(3)
    for a,b in zip(ext,np.roll(ext,-1,axis=0)):normal+=np.cross(a,b)
    norm=np.linalg.norm(normal)
    if norm<1e-7:return None
    normal/=norm
    drop=int(np.argmax(np.abs(normal)))
    pts=np.concatenate(rings); flat=np.delete(pts,drop,axis=1)
    ids=earcut.triangulate_float64(flat,np.cumsum([len(r) for r in rings],dtype=np.uint32))
    return pts,ids.reshape(-1,3),normal

def main():
    write_area();aerial=load_aerial();meta=[];verts=[];lods=Counter();sources=[];derived=[]
    with zipfile.ZipFile(RAW/'plateau/kawasaki-2022-v4.zip') as archive:
        for name in archive.namelist():
            if not name.startswith('udx/bldg/') or not name.endswith('.gml'):continue
            bounds=mesh_bounds(name)
            if bounds is None:continue
            s,w,n,e=bounds; xy=[wgs_to_rd(la,lo) for la in (s,n) for lo in (w,e)]
            if not EXTENT.intersects(box(min(a[0] for a in xy),min(a[1] for a in xy),max(a[0] for a in xy),max(a[1] for a in xy))):continue
            sources.append(name)
            with archive.open(name) as f:
                for _,elem in ET.iterparse(f,events=('end',)):
                    if elem.tag!=f'{{{NS["b"]}}}Building':continue
                    lod,faces=building_surfaces(elem)
                    if not faces:elem.clear();continue
                    points=np.concatenate([f[0] for f in faces]);x,y=points[:,:2].mean(0)
                    if not (XMIN<=x<=XMAX and YMIN<=y<=YMAX):elem.clear();continue
                    lo,hi=float(points[:,2].min()),float(points[:,2].max())
                    pid=elem.get(f'{{{NS["g"]}}}id');index=len(meta)
                    seed=((index*2654435761)%10000)/10000
                    r=int(np.clip((YMAX-y)/GROUND_RES,0,aerial.shape[0]-1));c=int(np.clip((x-XMIN)/GROUND_RES,0,aerial.shape[1]-1))
                    col=aerial[max(0,r-2):r+3,max(0,c-2):c+3].reshape(-1,3).mean(0).astype(int).tolist()
                    item=dict(id=pid,kind='house',axis=0,param=0,rand=seed,height=round(hi-lo,3),base=lo,top=hi,lod=lod,roof_rgb=col,wall_fixed=[185,181,168],frame_fixed=[70,76,80],source='PLATEAU Kawasaki 2022 v4')
                    measured=elem.findtext('b:measuredHeight',default=None,namespaces=NS)
                    if measured:item['measuredHeight']=float(measured)
                    meta.append(item);lods[lod]+=1
                    for rings in faces:
                        face=triangles(rings)
                        if face is None:continue
                        pts,ids,normal=face
                        # Source coordinates east/north/up -> renderer east/up/south.
                        norm=np.array([normal[0],normal[2],-normal[1]])
                        kind=2 if normal[2]>.3 else 0 if normal[2]<-.3 else 1
                        for tri in ids:
                            for p in pts[tri]:
                                verts.append([p[0]-CX,p[2],CY-p[1],*norm,p[0]-x,p[2]-lo,kind,index,-1,-1])
                    # Downloadable per-building positions and actual vertical range, no proprietary textures.
                    derived.append(dict(type='Feature',geometry=dict(type='Point',coordinates=[float(x),float(y)]),properties=item))
                    elem.clear()
            print('PLATEAU',name,len(meta),flush=True)
    if not meta:raise RuntimeError('No source buildings in configured Japan extent')
    np.asarray(verts,np.float32).tofile(BUILD/'buildings.bin')
    (BUILD/'buildings.json').write_text(json.dumps(meta,separators=(',',':')))
    Image.new('RGB',(1,1),(128,128,128)).save(BUILD/'roof_atlas.png')
    (BUILD/'buildings.geojson').write_text(json.dumps(dict(type='FeatureCollection',crs=dict(type='name',properties=dict(name='EPSG:32654')),features=derived),separators=(',',':')))
    summary=dict(buildings=len(meta),vertices=len(verts),lod_counts=dict(lods),min_source_z=min(m['base'] for m in meta),max_source_z=max(m['top'] for m in meta),source_entries=sources,height_provenance='actual CityGML polygon elevations; measuredHeight retained separately; no synthetic extrusion')
    (BUILD/'building_summary.json').write_text(json.dumps(summary,indent=2));print(summary,flush=True)
if __name__=='__main__':main()
