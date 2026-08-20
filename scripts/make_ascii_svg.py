#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import os
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "source-prepped.png"
DEFAULT_OUTPUT = REPO_ROOT / "avi-ascii.svg"
RAMP = " .`:-=+*cs#%@"
FONT_SIZE = 10
LINE_HEIGHT = 12
CHAR_WIDTH = 6.2
PADDING = 14
COLUMNS = 100
CHAR_ASPECT_CORRECTION = 0.53


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert preprocessed image to animated ASCII SVG")
    parser.add_argument("-i", "--input", default=str(DEFAULT_INPUT), help=f"Input image (default: {DEFAULT_INPUT})")
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT), help=f"Output SVG (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--columns", type=int, default=COLUMNS, help="Target ASCII columns")
    parser.add_argument(
        "--char-aspect",
        type=float,
        default=CHAR_ASPECT_CORRECTION,
        help="Character aspect correction factor",
    )
    return parser.parse_args()


def to_ascii_grid(image_path: Path, columns: int, char_aspect: float) -> list[str]:
    img = Image.open(image_path).convert("L")
    w, h = img.size
    rows = max(1, int((h / w) * columns / char_aspect))
    resized = img.resize((columns, rows), Image.Resampling.BICUBIC)
    arr = np.array(resized)

    idx = np.clip((arr / 255.0 * (len(RAMP) - 1)).astype(int), 0, len(RAMP) - 1)
    ascii_rows = ["".join(RAMP[val] for val in row) for row in idx]
    return ascii_rows


def build_svg(rows: list[str], static_mode: bool) -> str:
    width = int(PADDING * 2 + len(rows[0]) * CHAR_WIDTH)
    height = int(PADDING * 2 + len(rows) * LINE_HEIGHT)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        "<style>",
        ".frame{fill:#050607;stroke:#1f2937;stroke-width:1.2}",
        ".txt{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,Liberation Mono,monospace;font-size:10px;fill:#9aff9a;white-space:pre}",
        "</style>",
        "</defs>",
        f'<rect class="frame" x="0.6" y="0.6" width="{width-1.2}" height="{height-1.2}" rx="8"/>',
    ]

    if not static_mode:
        lines.append("<defs>")
        for i, _ in enumerate(rows):
            y = PADDING + i * LINE_HEIGHT - FONT_SIZE + 2
            full_w = len(rows[0]) * CHAR_WIDTH
            begin = round(i * 0.045, 3)
            lines.append(f'<clipPath id="rowclip-{i}"><rect x="{PADDING}" y="{y}" width="0" height="{LINE_HEIGHT+3}"><animate attributeName="width" from="0" to="{full_w}" dur="0.35s" begin="{begin}s" fill="freeze" /></rect></clipPath>')
        lines.append("</defs>")

    for i, row in enumerate(rows):
        y = PADDING + i * LINE_HEIGHT
        text = html.escape(row)
        if static_mode:
            lines.append(f'<text class="txt" x="{PADDING}" y="{y}">{text}</text>')
        else:
            lines.append(f'<text class="txt" x="{PADDING}" y="{y}" clip-path="url(#rowclip-{i})">{text}</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_path}")

    static_mode = os.getenv("STATIC", "0") == "1"
    rows = to_ascii_grid(input_path, args.columns, args.char_aspect)
    svg = build_svg(rows, static_mode)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    print(f"Saved ASCII SVG: {output_path} ({'static' if static_mode else 'animated'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
