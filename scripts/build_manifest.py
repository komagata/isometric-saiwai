"""Publish bounded geographic derivatives, exact source receipts and honest coverage limits."""
import json,gzip,zipfile
import numpy as np
from config import *
from japan import osm_polygon

def main():
    dtm=np.load(BUILD/'dtm.npy',mmap_mode='r');step=10
    # Sample at same metre coordinates as viewer (grid includes boundary).
    rr=np.clip(np.arange(0,dtm.shape[0]+1,step),0,dtm.shape[0]-1);cc=np.clip(np.arange(0,dtm.shape[1]+1,step),0,dtm.shape[1]-1)
    a=dtm[np.ix_(rr,cc)]
    grid=dict(xmin=XMIN,ymax=YMAX,step=step,width=a.shape[1],height=a.shape[0],values=a.round(2).ravel().tolist())
    (BUILD/'terrain-viewer.json').write_text(json.dumps(grid,separators=(',',':')))
    boundary=json.loads((RAW/'osm_boundary.json').read_text())
    geom=osm_polygon(next(e for e in boundary['elements'] if e['type']=='relation'))
    from shapely.geometry import mapping
    (BUILD/'ward-boundary.geojson').write_text(json.dumps(dict(type='Feature',geometry=mapping(geom),properties=dict(name='幸区',crs='EPSG:32654',source='OpenStreetMap contributors, ODbL')),ensure_ascii=False))
    receipts=[]
    for path in sorted(RAW.rglob('*.source.json')):
        receipts.append(dict(cache=str(path.relative_to(RAW)),**json.loads(path.read_text())))
    meta=json.loads((RAW/'plateau/metadata.json').read_text())['result']
    manifest=dict(title='幸区の小さな地図',retrieved_date='2026-11-12',crs='EPSG:32654',bbox=[XMIN,YMIN,XMAX,YMAX],ward_osm_bounds=[35.5261645,139.654139,35.5620586,139.704239],plateau=dict(dataset=meta['name'],version='2022 v4',license=meta['license_title'],license_url=meta['license_url'],resources=[dict(name=r['name'],url=r['url']) for r in meta['resources'] if r.get('url','').startswith('https://') and 'v4' in r.get('name','')]),sources=[dict(name='国土地理院 seamlessphoto / DEM5A, fallback DEM10B',url='https://maps.gsi.go.jp/help/use.html',license='国土地理院コンテンツ利用規約; PDL1.0 / attribution',dates='Continuous mosaics; per-cell capture/survey year not provided in tile receipt'),dict(name='Kanagawa 3D Point Cloud 2022 LP Original LAS',url='https://registry.opendata.aws/kanagawa_pointcloud/',license='CC BY 4.0'),dict(name='OpenStreetMap contributors',url='https://www.openstreetmap.org/copyright',license='ODbL 1.0')],receipts=receipts,limitations=['Most PLATEAU buildings are LoD1; no invented roof form; roof colour only from aerial centroid, not corrected roof textures.','LAS DSM covers only measured cells: see coverage PNG and lidar.npz. GSI DTM is NOT DSM.','Measured canopy uses DSM-DTM supported by aerial/OSM woodland, with PLATEAU roofs+2m excluded. LAS classes alone miss tall canopy. Estimated tree heights outside LAS coverage are nominal 8 m; crown radius is inferred.','Terrain resampled to 1 m textures / 10 m geometry from coarser GSI DEM; no extra accuracy implied.','Absolute source elevations retained, no vertical epoch/geoid adjustment. Source boundary/roof/terrain mismatch remains possible.','Road widths without width tags are cartographic estimates. Bridges shown at bare-earth level; animated traffic excludes bridges and tunnels.','Animated vehicles/birds, building windows and night lights are decorative, not live observations.','Upstream repository has no formal LICENSE file; README invites adaptation/publication. Original authorship retained, no broad relicensing.'])
    for name in ('terrain','building','tree'):
        manifest[name]=json.loads((BUILD/f'{name}_summary.json').read_text())
    (BUILD/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(BUILD/'geodata.zip','w',zipfile.ZIP_DEFLATED) as z:
        for n in ('buildings.geojson','buildings.bin','buildings.json','trees.json','osm-derived.geojson.gz','ward-boundary.geojson','terrain-viewer.json','lidar.npz','lidar-coverage.png','building-footprints.png','source-manifest.json'):
            z.write(BUILD/n,n)
        for n in ('osm_map.json','osm_boundary.json'):z.write(RAW/n,n)
        z.write(ROOT/'DATA_SOURCES.md','DATA_SOURCES.md')
    print(f'Source manifest: {len(receipts)} receipts; geodata {(BUILD/"geodata.zip").stat().st_size/1e6:.1f} MB',flush=True)
if __name__=='__main__':main()
