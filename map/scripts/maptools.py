"""Slippy-tile and Web-Mercator math shared by the preview renderers."""

import math
from typing import NamedTuple

TILE_SIZE = 256


class BBox(NamedTuple):
    west: float
    south: float
    east: float
    north: float


# From map-area-corners.txt — the club riding area around BCHS, Cayce, SC.
CAYCE_BBOX = BBox(west=-81.100988, south=33.943360, east=-81.035242, north=33.998016)


def deg2xy(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    n = 2**zoom
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def deg2num(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    x, y = deg2xy(lat, lon, zoom)
    return int(x), int(y)


def tile_range(bbox: BBox, zoom: int) -> tuple[range, range]:
    x_min, y_min = deg2num(bbox.north, bbox.west, zoom)
    x_max, y_max = deg2num(bbox.south, bbox.east, zoom)
    return range(x_min, x_max + 1), range(y_min, y_max + 1)


def crop_box(bbox: BBox, zoom: int) -> tuple[int, int, int, int]:
    """Pixel crop (left, top, right, bottom) of the bbox within the stitched tile grid."""
    xs, ys = tile_range(bbox, zoom)
    x_w, y_n = deg2xy(bbox.north, bbox.west, zoom)
    x_e, y_s = deg2xy(bbox.south, bbox.east, zoom)
    return (
        round((x_w - xs.start) * TILE_SIZE),
        round((y_n - ys.start) * TILE_SIZE),
        round((x_e - xs.start) * TILE_SIZE),
        round((y_s - ys.start) * TILE_SIZE),
    )


def mercator_aspect(bbox: BBox) -> float:
    """Height/width ratio of the bbox in Web-Mercator units (for render viewports)."""
    x_w, y_n = deg2xy(bbox.north, bbox.west, 0)
    x_e, y_s = deg2xy(bbox.south, bbox.east, 0)
    return (y_s - y_n) / (x_e - x_w)


def y_to_lat(y: float) -> float:
    """Inverse of deg2xy's y at zoom 0: Web-Mercator y-fraction → latitude degrees."""
    return math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * y))))


def fit_bbox_to_aspect(bbox: BBox, aspect: float) -> BBox:
    """Return a new BBox with same west/east and same center latitude,
    adjusting N-S extent symmetrically."""
    x_w, _ = deg2xy(0.0, bbox.west, 0)
    x_e, _ = deg2xy(0.0, bbox.east, 0)
    _, y_n = deg2xy(bbox.north, 0.0, 0)
    _, y_s = deg2xy(bbox.south, 0.0, 0)
    y_center = (y_n + y_s) / 2.0
    dy = aspect * (x_e - x_w)  # desired mercator height
    north = y_to_lat(y_center - dy / 2.0)
    south = y_to_lat(y_center + dy / 2.0)  # y increases southward
    return BBox(west=bbox.west, south=south, east=bbox.east, north=north)


def mile_to_lon(miles: float, lat: float) -> float:
    """Longitude degrees spanning `miles` at latitude `lat`."""
    return miles * 1609.344 / (111319.49 * math.cos(math.radians(lat)))


def anchored_bbox(bbox: BBox, trim_west_miles: float, aspect: float) -> BBox:
    """Anchor the NE corner (keep east + north); move the west edge east by
    `trim_west_miles`; set the south edge so mercator_aspect == `aspect`.
    Trims the west and (via the fixed north + aspect) the south, zooming in
    on the NE while filling the same slot."""
    lat_ref = (bbox.north + bbox.south) / 2.0
    west = bbox.west + mile_to_lon(trim_west_miles, lat_ref)
    x_w, _ = deg2xy(0.0, west, 0)
    x_e, _ = deg2xy(0.0, bbox.east, 0)
    _, y_n = deg2xy(bbox.north, 0.0, 0)
    south = y_to_lat(y_n + aspect * (x_e - x_w))  # y increases southward
    return BBox(west=west, south=south, east=bbox.east, north=bbox.north)
