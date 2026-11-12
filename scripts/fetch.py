"""Bounded, cached source acquisition. Also callable independently by a network-enabled coordinator.

python3 scripts/fetch.py --group osm|gsi|metadata|all
No credentials. Three concurrent GSI requests; two attempts per URL; atomic cache writes.
"""
import argparse
import hashlib
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / 'data/raw'
# Retrieval envelope; rendered area is checked against the exact OSM ward boundary.
BOUNDS = (35.520, 139.640, 35.580, 139.715)
UA = {'User-Agent': 'isometric-saiwai/0.1 (cached bounded open-data map)'}
PLATEAU_URL = 'https://assets.cms.plateau.reearth.io/assets/40/25bd0a-f174-4f55-a9bd-0e6868ece0ae/14130_kawasaki-shi_city_2022_citygml_4_op.zip'


def download(url, dst, body=None, optional=False):
    dst = Path(dst)
    if dst.exists():
        return True
    if optional and dst.with_suffix(dst.suffix + '.missing').exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, data=body, headers=UA)
            with urllib.request.urlopen(req, timeout=180) as response:
                payload = response.read()
                info = {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                        'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload),
                        'last_modified': response.headers.get('Last-Modified')}
                if body:
                    info['query'] = urllib.parse.parse_qs(body.decode()).get('data', [])
            tmp = dst.with_suffix(dst.suffix + '.tmp')
            tmp.write_bytes(payload)
            tmp.replace(dst)
            dst.with_suffix(dst.suffix + '.source.json').write_text(json.dumps(info, ensure_ascii=False, indent=2))
            return True
        except urllib.error.HTTPError as exc:
            if optional and exc.code == 404:
                dst.with_suffix(dst.suffix + '.missing').write_text(url + '\n')
                return False
            error = exc
        except (OSError, ValueError) as exc:
            error = exc
        if attempt == 0:
            time.sleep(3)
    raise RuntimeError(f'Cannot fetch {url} into {dst}: {error}. Cache is preserved; retry with permitted network.')


def tiles(z):
    s, w, n, e = BOUNDS
    def at(lat, lon):
        return (int((lon + 180) / 360 * 2**z), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 2**z))
    x0, y1 = at(s, w)
    x1, y0 = at(n, e)
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def fetch_osm():
    bbox = ','.join(map(str, BOUNDS))
    queries = {
        'boundary': '[out:json][timeout:120];relation["boundary"="administrative"]["name"="幸区"];out geom;',
        'map': f'''[out:json][timeout:180];(
way["highway"]({bbox});way["railway"]({bbox});nwr["natural"~"^(water|wood|tree|tree_row|scrub)$"]({bbox});
nwr["waterway"]({bbox});nwr["landuse"]({bbox});nwr["leisure"]({bbox});nwr["amenity"]({bbox});
nwr["tourism"]({bbox});nwr["historic"]({bbox});nwr["shop"="mall"]({bbox});nwr["railway"="station"]({bbox});
node["highway"="street_lamp"]({bbox}););out geom;''',
    }
    for kind, query in queries.items():
        out = RAW / f'osm_{kind}.json'
        if out.exists():
            continue
        for host in ('https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter'):
            try:
                download(host, out, urllib.parse.urlencode({'data': query}).encode())
                doc = json.loads(out.read_text())
                if doc.get('remark') or not doc.get('elements'):
                    out.unlink()
                    raise RuntimeError(f'Overpass incomplete/empty response: {doc.get("remark")}')
                break
            except RuntimeError:
                if host.endswith('kumi.systems/api/interpreter'):
                    raise


def fetch_gsi():
    jobs = [('seamlessphoto', 17, x, y, 'jpg') for x, y in tiles(17)]
    # DEM5A is a bare-earth model. DEM10B fills missing cells, never used as canopy/DSM.
    jobs += [(layer, z, x, y, 'txt') for layer, z in [('dem5a', 15), ('dem', 14)] for x, y in tiles(z)]
    def one(job):
        layer, z, x, y, ext = job
        download(f'https://cyberjapandata.gsi.go.jp/xyz/{layer}/{z}/{x}/{y}.{ext}',
                 RAW / 'gsi' / layer / str(z) / str(x) / f'{y}.{ext}', optional=layer == 'dem5a')
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(one, jobs))
    print(f'GSI: checked {len(jobs)} bounded cached tiles')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--group', choices=['osm', 'gsi', 'metadata', 'all'], default='all')
    a = p.parse_args()
    if a.group in ('metadata', 'all'):
        download('https://www.geospatial.jp/ckan/api/3/action/package_show?id=plateau-14130-kawasaki-shi-2022', RAW / 'plateau/metadata.json')
    if a.group in ('osm', 'all'):
        fetch_osm()
    if a.group in ('gsi', 'all'):
        fetch_gsi()
    if a.group == 'all' and not (RAW / 'plateau/kawasaki-2022-v4.zip').exists():
        raise SystemExit(f'PLATEAU archive missing. Download once to data/raw/plateau/kawasaki-2022-v4.zip from {PLATEAU_URL}')


if __name__ == '__main__':
    main()
