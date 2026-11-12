"""Source adapters shared by the Japan pipeline. No network I/O here."""
import json
import math
import struct
import xml.etree.ElementTree as ET
import zipfile
from functools import lru_cache
import numpy as np
from PIL import Image
from pyproj import Transformer
from scipy import ndimage as ndi
from shapely import make_valid
from shapely.geometry import Polygon, LineString, box
from shapely.ops import polygonize, unary_union
from config import RAW, BUILD, XMIN, XMAX, YMIN, YMAX, GROUND_RES
from geo import wgs_to_rd
NS={'b':'http://www.opengis.net/citygml/building/2.0','g':'http://www.opengis.net/gml'}
EXTENT=box(XMIN,YMIN,XMAX,YMAX)

def osm_elements():
    return json.loads((RAW/'osm_map.json').read_text())['elements']

def osm_xy(geometry):
    return [wgs_to_rd(p['lat'],p['lon']) for p in geometry if p and 'lat' in p]

def polygon_parts(g):
    if g.is_empty: return []
    if g.geom_type=='Polygon': return [g]
    return [p for part in getattr(g,'geoms',[]) for p in polygon_parts(part)]

def osm_polygon(element):
    if element['type']=='way':
        pts=osm_xy(element.get('geometry',[]))
        if len(pts)<4 or pts[0]!=pts[-1]: return Polygon()
        return make_valid(Polygon(pts))
    if element['type']!='relation': return Polygon()
    rings={}
    for role in ('outer','inner'):
        lines=[LineString(osm_xy(m['geometry'])) for m in element.get('members',[]) if m.get('role','outer')==role and len(m.get('geometry',[]))>1]
        rings[role]=unary_union(list(polygonize(unary_union(lines)))) if lines else Polygon()
    return make_valid(rings['outer'].difference(rings['inner']))

def building_surfaces(building):
    """Select one LoD only. Explicit lat/lon/elevation order of EPSG:6697."""
    for lod in (3,2,1):
        nodes=building.findall(f'.//b:lod{lod}Solid',NS)
        nodes += building.findall(f'.//b:lod{lod}MultiSurface',NS)
        if not nodes: continue
        surfaces=[]; seen=set()
        for node in nodes:
            for p in node.findall('.//g:Polygon',NS):
                ident=p.get('{http://www.opengis.net/gml}id') or '|'.join(' '.join((v.text or '').split()) for v in p.findall('.//g:posList',NS))
                if ident and ident in seen: continue
                seen.add(ident)
                rings=[]
                for tag in ('exterior','interior'):
                    for ring in p.findall(f'g:{tag}/g:LinearRing/g:posList',NS):
                        a=np.fromstring(ring.text or '',sep=' ')
                        if len(a)<9 or len(a)%3: continue
                        a=a.reshape(-1,3)
                        x,y=wgs_to_rd(a[:,0],a[:,1])
                        pts=np.column_stack([x,y,a[:,2]])
                        if np.allclose(pts[0],pts[-1]): pts=pts[:-1]
                        if len(pts)>=3: rings.append(pts)
                if rings: surfaces.append(rings)
        if surfaces: return lod,surfaces
    return 0,[]

def mesh_bounds(name):
    mesh=name.split('/')[-1].split('_')[0]
    if len(mesh)!=8 or not mesh.isdigit(): return None
    lat=int(mesh[:2])*2/3+int(mesh[4])/12+int(mesh[6])/120
    lon=int(mesh[2:4])+100+int(mesh[5])/8+int(mesh[7])/80
    return (lat,lon,lat+1/120,lon+1/80)

@lru_cache(maxsize=32)
def gsi_tile(layer,z,x,y):
    path=RAW/'gsi'/layer/str(z)/str(x)/(str(y)+('.jpg' if layer=='seamlessphoto' else '.txt'))
    if not path.exists(): return None
    if layer=='seamlessphoto': return np.asarray(Image.open(path).convert('RGB'))
    return np.genfromtxt(path,delimiter=',',missing_values='e',filling_values=np.nan,dtype=np.float32)

def sample_gsi(lat,lon,layer,z):
    tx=(lon+180)/360*2**z
    ty=(1-np.arcsinh(np.tan(np.radians(lat)))/np.pi)/2*2**z
    xx,yy=np.floor(tx).astype(int),np.floor(ty).astype(int)
    shape=lat.shape+((3,) if layer=='seamlessphoto' else ())
    result=np.full(shape,np.nan,np.float32)
    pairs=np.unique(np.column_stack([xx.ravel(),yy.ravel()]),axis=0)
    for x,y in pairs:
        tile=gsi_tile(layer,z,int(x),int(y))
        if tile is None: continue
        m=(xx==x)&(yy==y)
        # Nearest sample preserves pixel edges and does not interpolate DEM no-data.
        c=np.clip(((tx[m]-x)*256).astype(int),0,255)
        r=np.clip(((ty[m]-y)*256).astype(int),0,255)
        result[m]=tile[r,c]
    return result

def raster_xy(res):
    x=np.arange(XMIN+res/2,XMAX,res); y=np.arange(YMAX-res/2,YMIN,-res)
    return np.meshgrid(x,y)

@lru_cache(maxsize=1)
def terrain():
    return np.load(BUILD/'dtm.npy')

def height(x,y):
    a=terrain(); r=np.clip(((YMAX-np.asarray(y))/GROUND_RES).astype(int),0,a.shape[0]-1);c=np.clip(((np.asarray(x)-XMIN)/GROUND_RES).astype(int),0,a.shape[1]-1)
    return a[r,c]

def traffic_directions(oneway):
    return [-1] if oneway==-1 else [1] if oneway else [1,-1]

def las_chunks(path,chunk_size=500000):
    """Stream uncompressed LAS format 1 inside ZIP; scale/offset from LAS public header."""
    with zipfile.ZipFile(path) as z:
        name=next(n for n in z.namelist() if n.lower().endswith('.las'))
        with z.open(name) as f:
            h=f.read(227)
            if h[:4]!=b'LASF' or h[104]!=1: raise ValueError(f'Unsupported LAS format: {path}')
            off=struct.unpack_from('<I',h,96)[0]; size=struct.unpack_from('<H',h,105)[0]; count=struct.unpack_from('<I',h,107)[0]
            scale=np.array(struct.unpack_from('<3d',h,131)); origin=np.array(struct.unpack_from('<3d',h,155))
            f.read(off-227)
            dtype=np.dtype({'names':['x','y','z','classification'],'formats':['<i4','<i4','<i4','u1'],'offsets':[0,4,8,15],'itemsize':size})
            for start in range(0,count,chunk_size):
                n=min(chunk_size,count-start); a=np.frombuffer(f.read(n*size),dtype=dtype)
                xyz=np.column_stack([a['x'],a['y'],a['z']])*scale+origin
                yield xyz,a['classification']&31

def measured_canopy(dsm,dtm,coverage,support,building_footprints):
    """Measured top minus bare earth, supported as vegetation, with roofs excluded.
    LAS classes are intentionally not a canopy gate: this source's class 3 misses
    tall woodland. Genuine DSM gaps remain unknown, rather than ground-height zero.
    """
    values=np.where(support & ~building_footprints,np.maximum(0,dsm-dtm),0)
    return np.where(coverage,values,np.nan).astype(np.float32)

def building_footprint_mask(res=2):
    """Raster union of actual PLATEAU faces, plus a conservative one-cell roof margin."""
    from PIL import ImageDraw
    from config import CX,CY
    w,h=int((XMAX-XMIN)/res),int((YMAX-YMIN)/res)
    image=Image.new('1',(w,h),0);draw=ImageDraw.Draw(image)
    verts=np.fromfile(BUILD/'buildings.bin',np.float32).reshape(-1,3,12)
    for tri in verts:
        # Vertical faces project to lines; filling them includes footprint boundaries.
        pts=[((float(p[0])+CX-XMIN)/res,(YMAX-CY+float(p[2]))/res) for p in tri]
        draw.polygon(pts,fill=1)
    return ndi.binary_dilation(np.asarray(image),iterations=1)
