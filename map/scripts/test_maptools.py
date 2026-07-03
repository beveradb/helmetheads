from maptools import CAYCE_BBOX, crop_box, deg2num, deg2xy, mercator_aspect, tile_range


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
