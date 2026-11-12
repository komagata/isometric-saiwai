import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import geo

class Geography(unittest.TestCase):
    def test_dsm_canopy_keeps_nonvegetation_returns_and_excludes_roofs(self):
        from japan import measured_canopy
        dtm=np.full((3,4),20.,np.float32)
        dsm=dtm+np.array([[0,0,0,0],[0,18,24,0],[0,0,0,0]],np.float32)
        coverage=np.ones((3,4),bool);coverage[0,0]=False
        # Canopy was not classified as vegetation, but DSM is measured and photo green.
        support=np.ones((3,4),bool);footprint=np.zeros((3,4),bool);footprint[1,2]=True
        chm=measured_canopy(dsm,dtm,coverage,support,footprint)
        self.assertAlmostEqual(chm[1,1],18.)
        self.assertEqual(chm[1,2],0.)
        self.assertTrue(np.isnan(chm[0,0]))
    def test_generated_trees_match_measured_heights_and_avoid_real_roofs(self):
        import json
        from PIL import Image
        root=Path(__file__).resolve().parents[1]/'data/build'
        if not (root/'building-footprints.png').exists():self.skipTest('generated source artifacts not installed')
        roof=np.asarray(Image.open(root/'building-footprints.png'))>0
        lidar=np.load(root/'lidar.npz');dsm=lidar['dsm'];coverage=lidar['coverage'];dtm=np.load(root/'dtm.npy',mmap_mode='r')[1::2,1::2]
        trees=json.loads((root/'trees.json').read_text())
        measured=0
        for tree in trees:
            c=int((tree['x']-377500)/2);r=int((3936500-tree['y'])/2)
            self.assertFalse(roof[r,c])
            if tree['provenance'].startswith('measured'):
                measured+=1
                self.assertTrue(coverage[r,c])
                self.assertAlmostEqual(tree['height'],float(dsm[r,c]-dtm[r,c]),delta=.011)
            else:
                self.assertFalse(coverage[r,c])
                self.assertEqual(tree['height'],8)
        self.assertGreater(measured,0)
        summary=json.loads((root/'tree_summary.json').read_text())
        self.assertGreater(summary['hill_patch_above_3m'],1000)
        self.assertGreater(summary['hill_patch_measured_trees'],50)
    def test_slab_top_is_below_negative_terrain(self):
        from config import terrain_slab_top
        for minimum in (-3.6400001,0,31.78):
            self.assertLess(terrain_slab_top(minimum),minimum)
            self.assertAlmostEqual(terrain_slab_top(minimum),minimum-1)
    def test_empty_local_tour_keeps_viewer_json_contract(self):
        import tempfile,json
        from unittest.mock import patch
        import build_history
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(build_history,'BUILD',Path(tmp)):
                build_history.main()
            data=json.loads((Path(tmp)/'history.json').read_text())
            self.assertIsInstance(data,dict)
            self.assertEqual(data['stops'],[])
    def test_saiwai_utm_and_roundtrip(self):
        x, y = geo.wgs_to_rd(35.5512, 139.6715)
        self.assertTrue(379000 < x < 381000, (x,y))
        self.assertTrue(3934000 < y < 3936000, (x,y))
        np.testing.assert_allclose(geo.rd_to_wgs(x, y), [35.5512,139.6715], atol=1e-8)
    def test_all_extent_corners_roundtrip(self):
        from config import XMIN,XMAX,YMIN,YMAX
        for x in (XMIN,XMAX):
            for y in (YMIN,YMAX):
                np.testing.assert_allclose(geo.wgs_to_rd(*geo.rd_to_wgs(x,y)),[x,y],atol=.01)
    def test_multipolygon_inner_ring_is_a_hole(self):
        from japan import osm_polygon
        outer=[{'lat':35.54,'lon':139.67},{'lat':35.54,'lon':139.68},{'lat':35.55,'lon':139.68},{'lat':35.55,'lon':139.67},{'lat':35.54,'lon':139.67}]
        inner=[{'lat':35.542,'lon':139.672},{'lat':35.542,'lon':139.674},{'lat':35.544,'lon':139.674},{'lat':35.544,'lon':139.672},{'lat':35.542,'lon':139.672}]
        obj={'type':'relation','members':[{'role':'outer','geometry':outer},{'role':'inner','geometry':inner}]}
        g=osm_polygon(obj)
        from shapely.geometry import Point
        self.assertFalse(g.contains(Point(*geo.wgs_to_rd(35.543,139.673))))
        self.assertTrue(g.contains(Point(*geo.wgs_to_rd(35.548,139.678))))
    def test_citygml_selects_highest_lod_and_keeps_measured_elevation(self):
        from japan import building_surfaces
        ns='xmlns:b="http://www.opengis.net/citygml/building/2.0" xmlns:g="http://www.opengis.net/gml"'
        ring=lambda z:f'<g:Polygon><g:exterior><g:LinearRing><g:posList>35.55 139.67 {z} 35.55 139.671 {z} 35.551 139.671 {z} 35.55 139.67 {z}</g:posList></g:LinearRing></g:exterior></g:Polygon>'
        e=ET.fromstring(f'<b:Building {ns}><b:lod1Solid>{ring(8)}</b:lod1Solid><b:lod2Solid><g:Solid><g:surfaceMember xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="#roof"/></g:Solid></b:lod2Solid><b:boundedBy><b:RoofSurface><b:lod2MultiSurface>{ring(37.25)}</b:lod2MultiSurface></b:RoofSurface></b:boundedBy></b:Building>')
        lod, surfaces=building_surfaces(e)
        self.assertEqual(lod,2)
        self.assertEqual(len(surfaces),1)
        np.testing.assert_allclose(surfaces[0][0][:,2],37.25)
    def test_actual_plateau_xlink_roof_geometry(self):
        import zipfile
        from japan import building_surfaces,NS
        archive=Path(__file__).resolve().parents[1]/'data/raw/plateau/kawasaki-2022-v4.zip'
        if not archive.exists():self.skipTest('large source cache not installed')
        with zipfile.ZipFile(archive) as z:
            with z.open('udx/bldg/53392535_bldg_6697_op.gml') as f:
                for _,e in ET.iterparse(f,events=('end',)):
                    if e.tag!=f'{{{NS["b"]}}}Building':continue
                    if e.get(f'{{{NS["g"]}}}id')=='bldg_138ba376-4817-4b03-9abc-552d06b4c6ff':
                        lod,faces=building_surfaces(e)
                        self.assertEqual(lod,2)
                        zvalues=np.concatenate([r[0][:,2] for r in faces])
                        self.assertGreater(float(zvalues.max()-zvalues.min()),3)
                        self.assertGreaterEqual(len(faces),6)
                        return
                    e.clear()
        self.fail('source building missing')
    def test_traffic_offsets_left_and_reverses_oneway(self):
        from japan import traffic_directions
        self.assertEqual(traffic_directions(-1),[-1])
        self.assertEqual(traffic_directions(0),[1,-1])
        from build_traffic import offset
        self.assertLess(offset([[0,0],[10,0]],-1.5)[0,1],0)

if __name__=='__main__': unittest.main()
