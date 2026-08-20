#!/usr/bin/env python3
from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "source-prepped.png"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Remove photo background, composite on white, convert to grayscale, "
            "and apply CLAHE contrast enhancement."
        )
    )
    parser.add_argument("source", nargs="?", help="Path to source photo")
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output PNG path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    if not args.source:
        parser.print_help()
        parser.exit(1, "\nError: missing source photo path.\n")
    return args


def main() -> int:
    args = parse_args()
    source_path = Path(args.source).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not source_path.exists():
        raise FileNotFoundError(f"Source photo not found: {source_path}")

    with source_path.open("rb") as f:
        removed = remove(f.read())

    fg_rgba = Image.open(BytesIO(removed)).convert("RGBA")
    white_bg = Image.new("RGBA", fg_rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, fg_rgba).convert("RGB")

    rgb_array = np.array(composited)
    gray = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(enhanced).save(output_path)
    print(f"Saved preprocessed photo: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
