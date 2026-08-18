#!/usr/bin/env python3
"""
make_ascii_svg.py

Converts source-prepped.png into ascii-portrait.svg: a monochrome ASCII
portrait that "types" itself in, row by row, then freezes (no looping).

Usage:
    python scripts/make_ascii_svg.py [source-prepped.png] [ascii-portrait.svg]

Design choices (see the writeup this is based on):
    - Monochrome fill. Per-character rainbow coloring makes ASCII art look
      like static; one light-gray fill reads as a clean terminal render.
    - High contrast in the source image means a busy background washes out
      to the space glyph, so only the subject actually prints.
    - Each row wipes left-to-right via an animated clip-path rect, with a
      small "cursor" block riding the wipe edge. Rows are staggered top to
      bottom. The whole thing prints once and freezes (fill="freeze").
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

# bright (sparse) -> dark (dense); leading space clears background to nothing
RAMP = " .`:-=+*cs#%@"

GRID_COLS = 100
GRID_ROWS = 53

FONT_SIZE = 8
CHAR_W = FONT_SIZE * 0.6   # approximate monospace advance width
LINE_H = FONT_SIZE * 1.05

FILL_COLOR = "#c9d1d9"     # light gray, monochrome
CURSOR_COLOR = "#39d353"   # small green cursor block riding the wipe edge
BG_COLOR = "none"

ROW_STAGGER = 0.045        # seconds between each row starting to type
ROW_DURATION = 0.5         # seconds for a single row to fully wipe in


def image_to_grid(img: Image.Image, cols: int, rows: int) -> np.ndarray:
    """Downsample a grayscale image to a cols x rows brightness grid (0-255)."""
    resized = img.convert("L").resize((cols, rows), Image.LANCZOS)
    return np.array(resized)


def brightness_to_char(value: int) -> str:
    """Map a 0-255 brightness value to a RAMP glyph. Bright -> sparse."""
    idx = int((255 - value) / 255 * (len(RAMP) - 1))
    idx = max(0, min(len(RAMP) - 1, idx))
    return RAMP[idx]


def grid_to_ascii_rows(grid: np.ndarray) -> list[str]:
    rows = []
    for r in range(grid.shape[0]):
        line = "".join(brightness_to_char(int(v)) for v in grid[r])
        rows.append(line.rstrip())  # trailing spaces add nothing visually
    return rows


def xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(rows: list[str]) -> str:
    width = int(GRID_COLS * CHAR_W) + 20
    height = int(len(rows) * LINE_H) + 20

    defs = []
    body = []

    for i, row_text in enumerate(rows):
        if not row_text:
            continue

        row_width_px = len(row_text) * CHAR_W
        y = 10 + (i + 1) * LINE_H
        begin = round(i * ROW_STAGGER, 3)
        clip_id = f"clip-row-{i}"

        # Clip rect that wipes left -> right, then freezes at full width.
        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{y - LINE_H}" width="0" height="{LINE_H + 2}">'
            f'<animate attributeName="width" from="0" to="{row_width_px:.1f}" '
            f'begin="{begin}s" dur="{ROW_DURATION}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.2 0 0.2 1" />'
            f'</rect>'
            f'</clipPath>'
        )

        escaped = xml_escape(row_text)
        body.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="10" y="{y}" font-family="Menlo, Consolas, monospace" '
            f'font-size="{FONT_SIZE}" fill="{FILL_COLOR}" '
            f'xml:space="preserve">{escaped}</text>'
            f'</g>'
        )

        # Cursor block riding the wipe edge, fades out once the row is done.
        cursor_id = f"cursor-{i}"
        body.append(
            f'<rect id="{cursor_id}" x="10" y="{y - LINE_H + 1}" '
            f'width="{CHAR_W:.1f}" height="{LINE_H - 1}" fill="{CURSOR_COLOR}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;1;0" '
            f'keyTimes="0;0.01;0.9;1" begin="{begin}s" dur="{ROW_DURATION}s" fill="freeze" />'
            f'<animate attributeName="x" from="10" to="{10 + row_width_px:.1f}" '
            f'begin="{begin}s" dur="{ROW_DURATION}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.2 0 0.2 1" />'
            f'</rect>'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">'
        f'<defs>{"".join(defs)}</defs>'
        f'<rect width="100%" height="100%" fill="{BG_COLOR}" />'
        f'{"".join(body)}'
        f'</svg>'
    )
    return svg


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("source-prepped.png")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("ascii-portrait.svg")

    if not input_path.exists():
        print(f"Error: {input_path} not found. Run prep_photo.py first.")
        sys.exit(1)

    img = Image.open(input_path)
    grid = image_to_grid(img, GRID_COLS, GRID_ROWS)
    rows = grid_to_ascii_rows(grid)
    svg = build_svg(rows)

    output_path.write_text(svg, encoding="utf-8")
    print(f"Wrote {output_path} ({len(rows)} rows x {GRID_COLS} cols)")


if __name__ == "__main__":
    main()
