#!/usr/bin/env python3
"""
prep_photo.py

Turns a normal photo into a clean, high-contrast grayscale image that's
ready to be converted into ASCII art. Run this once per photo, locally
(not part of the daily GitHub Actions workflow).

Usage:
    python scripts/prep_photo.py source-photo.jpg [output-prepped.png]

Pipeline:
    1. Remove the background with rembg, so only the subject remains.
    2. Composite the cutout onto pure white (so background pixels map to
       the blank end of the ASCII ramp -> spaces, not noise).
    3. Convert to grayscale and boost local contrast with CLAHE
       (contrast-limited adaptive histogram equalization). This is what
       gives a flatly-lit face real highlights and shadows.
"""

import sys
from pathlib import Path

import numpy as np
import cv2
from PIL import Image
from rembg import remove


def remove_background(input_path: Path) -> Image.Image:
    """Return an RGBA PIL image with the background removed."""
    with open(input_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    from io import BytesIO
    return Image.open(BytesIO(output_bytes)).convert("RGBA")


def composite_on_white(rgba: Image.Image) -> Image.Image:
    """Flatten an RGBA cutout onto a solid white background."""
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    flattened = Image.alpha_composite(white_bg, rgba)
    return flattened.convert("RGB")


def boost_contrast_clahe(rgb: Image.Image) -> Image.Image:
    """Apply CLAHE to bring out highlights/shadows, return grayscale PIL image."""
    arr = np.array(rgb)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return Image.fromarray(enhanced)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py source-photo.jpg [output-prepped.png]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("source-prepped.png")

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    print(f"Removing background from {input_path} ...")
    cutout = remove_background(input_path)

    print("Compositing onto white ...")
    flattened = composite_on_white(cutout)

    print("Boosting local contrast (CLAHE) ...")
    prepped = boost_contrast_clahe(flattened)

    prepped.save(output_path)
    print(f"Wrote {output_path} ({prepped.size[0]}x{prepped.size[1]})")


if __name__ == "__main__":
    main()
