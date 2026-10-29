
"""
Convert source-prepped.png into an animated ASCII portrait SVG.

Run:
    python scripts/make_ascii_svg.py
"""

import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

INPUT = os.path.join(ROOT, "source-prepped.png")
OUTPUT = os.path.join(ROOT, "avi-ascii.svg")

COLS = 100
ROWS = 53
RAMP = " .`:-=+*cs#%@"

# Load and resize the prepared grayscale image.
image = Image.open(INPUT).convert("L")
image = image.resize((COLS, ROWS), Image.Resampling.LANCZOS)
pixels = np.asarray(image)

# Map brightness to ASCII characters.
ramp = RAMP
indices = np.clip(
    ((255 - pixels.astype(np.float32)) / 255 * (len(ramp) - 1))
    .astype(int),
    0,
    len(ramp) - 1,
)

lines = ["".join(ramp[index] for index in row) for row in indices]

# Use a monospace font and reveal each row in sequence.
cell_w = 8
cell_h = 12
width = COLS * cell_w
height = ROWS * cell_h + 24

svg_lines = []
for row, line in enumerate(lines):
    y = 18 + (row + 1) * cell_h
    delay = row * 0.025
    svg_lines.append(
        f'<text x="0" y="{y}" class="ascii" '
        f'style="animation-delay:{delay:.3f}s">{line}</text>'
    )

svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
     width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#0d1117"/>
  <style>
    .ascii {{
      font-family: "Courier New", monospace;
      font-size: 10px;
      fill: #39d353;
      white-space: pre;
      opacity: 0;
      animation: reveal 0.35s ease forwards;
    }}
    @keyframes reveal {{
      to {{ opacity: 1; }}
    }}
  </style>
  {''.join(svg_lines)}
</svg>
'''

with open(OUTPUT, "w", encoding="utf-8") as file:
    file.write(svg)

print(f"Wrote {OUTPUT}")
