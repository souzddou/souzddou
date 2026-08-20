#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "contrib-heatmap.svg"
DEFAULT_JSON = REPO_ROOT / "data" / "contributions.json"
PALETTE = ["#0d1117", "#0e4429", "#006d32", "#26a641", "#39d353"]


@dataclass
class Cell:
    x: int
    y: int
    level: int
    date: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch GitHub contribution graph and render local SVG")
    parser.add_argument("--username", default="souzddou", help="GitHub username")
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT), help=f"Output SVG path (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--json", default=str(DEFAULT_JSON), help=f"Output JSON cache path (default: {DEFAULT_JSON})")
    return parser.parse_args()


def fetch_cells(username: str) -> list[Cell]:
    url = f"https://github.com/users/{username}/contributions"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    nodes = soup.select("rect[data-date][data-level], td[data-date][data-level]")
    raw_cells: list[tuple[int, int, int, str]] = []
    for node in nodes:
        try:
            date = node.get("data-date", "")
            x_raw = node.get("x")
            y_raw = node.get("y")
            ix_raw = node.get("data-ix")
            if x_raw is not None:
                x_val = int(float(x_raw))
            elif ix_raw is not None:
                x_val = int(ix_raw)
            else:
                x_val = 0

            if y_raw is not None:
                y_val = int(float(y_raw))
            elif date:
                dt = datetime.fromisoformat(date)
                y_val = (dt.weekday() + 1) % 7
            else:
                y_val = 0

            raw_cells.append(
                (
                    x_val,
                    y_val,
                    int(node.get("data-level", "0")),
                    date,
                )
            )
        except ValueError:
            continue
    if not raw_cells:
        raise RuntimeError("No contribution cells found in fetched HTML.")

    x_values = sorted({x for x, _, _, _ in raw_cells})
    y_values = sorted({y for _, y, _, _ in raw_cells})
    x_index = {x: i for i, x in enumerate(x_values)}
    y_index = {y: i for i, y in enumerate(y_values)}

    cells = [
        Cell(
            x=x_index[x],
            y=y_index[y],
            level=level,
            date=date,
        )
        for x, y, level, date in raw_cells
    ]
    return cells


def build_svg(cells: list[Cell], static_mode: bool) -> str:
    cell = 11
    gap = 2
    left_pad = 20
    top_pad = 24

    max_week = max(c.x for c in cells)
    max_day = max(c.y for c in cells)
    width = left_pad * 2 + (max_week + 1) * (cell + gap)
    height = top_pad + 28 + (max_day + 1) * (cell + gap)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        ".bg{fill:#050607;stroke:#1f2937;stroke-width:1.2}",
        ".title{fill:#9aff9a;font:700 13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}",
        "</style>",
        f'<rect class="bg" x="0.6" y="0.6" width="{width-1.2}" height="{height-1.2}" rx="8"/>',
        '<text class="title" x="20" y="18">$ github contributions --last-year</text>',
    ]

    if static_mode:
        for c in cells:
            color = PALETTE[max(0, min(c.level, len(PALETTE) - 1))]
            x = left_pad + c.x * (cell + gap)
            y = top_pad + c.y * (cell + gap)
            lines.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{color}"/>')
    else:
        for c in cells:
            color = PALETTE[max(0, min(c.level, len(PALETTE) - 1))]
            x = left_pad + c.x * (cell + gap)
            y = top_pad + c.y * (cell + gap)
            delay = round(c.x * 0.015 + c.y * 0.01, 3)
            lines.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{color}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" begin="{delay}s" dur="0.2s" fill="freeze"/>'
                "</rect>"
            )

    lines.append("</svg>")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    json_path = Path(args.json).expanduser().resolve()
    static_mode = os.getenv("STATIC", "0") == "1"

    cells = fetch_cells(args.username)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            {
                "username": args.username,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "cells": [c.__dict__ for c in cells],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_svg(cells, static_mode), encoding="utf-8")
    print(f"Saved contribution heatmap: {output_path} ({'static' if static_mode else 'animated'})")
    print(f"Saved contribution cache: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
