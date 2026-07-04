"""Crop a US-letter-printable section (8 x 10.5 in @ 300 dpi) from the full-size
composite, centered on the school, for a true-scale home test print."""

from pathlib import Path

from PIL import Image

from maptools import CAYCE_BBOX, deg2xy

Image.MAX_IMAGE_PIXELS = None

SCHOOL_LAT, SCHOOL_LON = 33.981738, -81.056747
CROP_W, CROP_H = 2400, 3150  # 8 x 10.5 in at 300 dpi

OUT = Path(__file__).resolve().parent.parent / "render" / "out"
im = Image.open(OUT / "full-composite.png")

# School's fractional position within the bbox, in mercator space (zoom cancels out).
x_w, y_n = deg2xy(CAYCE_BBOX.north, CAYCE_BBOX.west, 0)
x_e, y_s = deg2xy(CAYCE_BBOX.south, CAYCE_BBOX.east, 0)
x_school, y_school = deg2xy(SCHOOL_LAT, SCHOOL_LON, 0)
fx = (x_school - x_w) / (x_e - x_w)
fy = (y_school - y_n) / (y_s - y_n)

cx, cy = round(im.width * fx), round(im.height * fy)
left = min(max(cx - CROP_W // 2, 0), im.width - CROP_W)
top = min(max(cy - CROP_H // 2, 0), im.height - CROP_H)
crop = im.crop((left, top, left + CROP_W, top + CROP_H))
crop.save(OUT / "letter-test.png", dpi=(300, 300))
print("saved", OUT / "letter-test.png", crop.size, "school at fraction", (round(fx, 3), round(fy, 3)))
