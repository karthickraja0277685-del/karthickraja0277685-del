
"""
Prepare the photo for clean ASCII conversion:
  1. Remove the background using rembg.
  2. Smooth texture while preserving edges.
  3. Stretch tones for better contrast.
  4. Darken fine details.
  5. Composite onto white and crop around the subject.

Output: source-prepped.png

Usage:
    python scripts/prep_photo.py [input.png] [output.png]
"""

import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    HERE, "..", "source-photo.png"
)
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    HERE, "..", "source-prepped.png"
)

LINE_WEIGHT = 0.6

# 1. Remove the background.
cut = remove(Image.open(INP).convert("RGBA"))
rgb = np.array(cut.convert("RGB"))
alpha = np.array(cut.split()[-1])
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

# 2. Smooth texture while preserving edges.
smooth = gray
for _ in range(3):
    smooth = cv2.bilateralFilter(smooth, 9, 40, 9)

# 3. Stretch tones over the subject.
lo, hi = np.percentile(smooth[alpha > 128], [2, 92])
tone = np.clip(
    (smooth.astype(np.float32) - lo) / (hi - lo), 0, 1
)

# 4. Darken fine details.
fine = cv2.GaussianBlur(smooth, (0, 0), 1.5).astype(np.float32)
coarse = cv2.GaussianBlur(smooth, (0, 0), 6).astype(np.float32)
lines = np.clip((coarse - fine) / 40.0, 0, 1)
out = np.clip(tone - LINE_WEIGHT * lines, 0, 1) * 255

# 5. Composite onto white and crop around the subject.
mask = cv2.GaussianBlur(
    alpha.astype(np.float32) / 255.0, (0, 0), 1.0
)
out = out * mask + 255.0 * (1.0 - mask)

ys, xs = np.where(alpha > 20)
side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 60
cx = (xs.min() + xs.max()) // 2
cy = (ys.min() + ys.max()) // 2

canvas = np.full((side, side), 255, np.uint8)
x0, y0 = cx - side // 2, cy - side // 2
sx0, sy0 = max(x0, 0), max(y0, 0)
sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])

canvas[
    sy0 - y0:sy1 - y0,
    sx0 - x0:sx1 - x0
] = out[sy0:sy1, sx0:sx1].astype(np.uint8)

Image.fromarray(canvas, mode="L").save(OUT)
print("wrote", OUT, canvas.shape)
