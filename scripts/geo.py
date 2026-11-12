"""Japan UTM54N <-> WGS84 (PROJ) and map projections."""

import math

from config import CX, CY, XMAX, XMIN, YMAX, YMIN

HX, HZ = (XMAX - XMIN) / 2, (YMAX - YMIN) / 2


# Historical function names kept for upstream callers; these now use Japan UTM54N.
from pyproj import Transformer
_TO_METRIC = Transformer.from_crs(4326, 32654, always_xy=True)
_TO_WGS = Transformer.from_crs(32654, 4326, always_xy=True)

def wgs_to_rd(lat, lon):
    return _TO_METRIC.transform(lon, lat)

def rd_to_wgs(x, y):
    lon, lat = _TO_WGS.transform(x, y)
    return lat, lon


def screen(x, z, h=0.0, look=45):
    """Local meters (x east, z south, h up) to the render's screen meters (u right, v up) for a camera looking `look`
    degrees from north, 30 degrees down (render/scene.js). Works on numbers and numpy arrays alike."""
    a = math.radians(look)
    return x * math.cos(a) + z * math.sin(a), (x * math.sin(a) - z * math.cos(a)) * 0.5 + h * math.cos(math.radians(30))


def rd_to_image(x, y, scale=4, height_m=0.0):
    """Pixel position in the full isometric render of an RD point at a height above ground (see render/scene.js)."""
    width = round(2 * (HX + HZ) / math.sqrt(2) * scale)
    lx, lz = x - CX, CY - y
    u = (lx + lz) / math.sqrt(2)
    v = (lx - lz) / (2 * math.sqrt(2)) + height_m * math.cos(math.radians(30))
    top = (HX + HZ) / math.sqrt(2) * 0.5 + 220
    return u * scale + width / 2, (top - v) * scale
