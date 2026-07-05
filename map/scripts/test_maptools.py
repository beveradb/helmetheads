from maptools import (
    CAYCE_BBOX, deg2xy, fit_bbox_to_aspect, mercator_aspect, y_to_lat,
)
from maptools import crop_box, deg2num, tile_range


def test_deg2xy_origin_is_center_of_world():
    assert deg2xy(0.0, 0.0, 0) == (0.5, 0.5)


def test_deg2num_london_z10():
    # Known slippy tile for central London at z10.
    assert deg2num(51.5074, -0.1278, 10) == (511, 340)


def test_tile_range_cayce_z16():
    xs, ys = tile_range(CAYCE_BBOX, 16)
    assert (xs.start, xs.stop - 1) == (18004, 18015)
    assert (ys.start, ys.stop - 1) == (26180, 26191)


def test_crop_box_lies_within_stitched_image():
    xs, ys = tile_range(CAYCE_BBOX, 16)
    left, top, right, bottom = crop_box(CAYCE_BBOX, 16)
    assert 0 <= left < right <= len(xs) * 256
    assert 0 <= top < bottom <= len(ys) * 256


def test_cayce_bbox_is_nearly_square_in_mercator():
    assert abs(mercator_aspect(CAYCE_BBOX) - 1.0) < 0.02


def test_y_to_lat_inverts_deg2xy():
    for lat in (33.94, 33.97, 33.998, 0.0, 51.5):
        _, y = deg2xy(lat, 0.0, 0)
        assert abs(y_to_lat(y) - lat) < 1e-9


def test_fit_bbox_to_aspect_hits_target_aspect():
    fitted = fit_bbox_to_aspect(CAYCE_BBOX, 0.9375)
    assert abs(mercator_aspect(fitted) - 0.9375) < 1e-6


def test_fit_bbox_preserves_west_east_and_center_lat():
    fitted = fit_bbox_to_aspect(CAYCE_BBOX, 0.9375)
    assert fitted.west == CAYCE_BBOX.west
    assert fitted.east == CAYCE_BBOX.east
    orig_center = (CAYCE_BBOX.north + CAYCE_BBOX.south) / 2.0
    fitted_center = (fitted.north + fitted.south) / 2.0
    assert abs(fitted_center - orig_center) < 0.001


def test_fit_bbox_expands_ns_for_wide_aspect():
    wide = fit_bbox_to_aspect(CAYCE_BBOX, 1.5)
    assert wide.north > CAYCE_BBOX.north
    assert wide.south < CAYCE_BBOX.south
