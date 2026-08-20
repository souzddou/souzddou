#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = REPO_ROOT / "info-card.svg"

NAME = "Smaail Ouzddou"
ROLE = "Software Engineer Student @ 1337"
STACK = "C/C++, Python, TypeScript, FastAPI, Docker"
HIGHLIGHTS = [
    "AI matchmaking + LLM integrations",
    "RAG pipelines and semantic retrieval",
    "Systems programming and backend architecture",
]


def build_rows() -> list[tuple[str, str]]:
    return [
        ("name", NAME),
        ("role", ROLE),
        ("stack", STACK),
        ("focus", " | ".join(HIGHLIGHTS)),
        ("github", "github.com/souzddou"),
        ("linkedin", "linkedin.com/in/smaail-ouzddou"),
    ]


def build_svg(static_mode: bool) -> str:
    rows = build_rows()
    width = 860
    height = 60 + len(rows) * 32

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        "<style>",
        ".bg{fill:#07090d;stroke:#253046;stroke-width:1.2}",
        ".title{fill:#9aff9a;font:700 16px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}",
        ".k{fill:#6ee7ff;font:600 14px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}",
        ".v{fill:#d2ffe0;font:400 14px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}",
        "</style>",
        "</defs>",
        f'<rect class="bg" x="0.6" y="0.6" width="{width-1.2}" height="{height-1.2}" rx="10"/>',
        '<text class="title" x="20" y="30">$ neofetch --profile</text>',
    ]

    for i, (k, v) in enumerate(rows):
        y = 60 + i * 30
        if static_mode:
            out.append(f'<text class="k" x="24" y="{y}">{k:>8}</text>')
            out.append(f'<text class="v" x="136" y="{y}">: {v}</text>')
        else:
            begin = round(0.2 + i * 0.14, 3)
            out.append(
                f'<g opacity="0" transform="translate(-8,0)">'
                f'<animate attributeName="opacity" from="0" to="1" begin="{begin}s" dur="0.25s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" from="-8 0" to="0 0" begin="{begin}s" dur="0.25s" fill="freeze"/>'
                f'<text class="k" x="24" y="{y}">{k:>8}</text>'
                f'<text class="v" x="136" y="{y}">: {v}</text>'
                "</g>"
            )

    out.append("</svg>")
    return "\n".join(out)


def main() -> int:
    static_mode = os.getenv("STATIC", "0") == "1"
    OUTPUT.write_text(build_svg(static_mode), encoding="utf-8")
    print(f"Saved info card: {OUTPUT} ({'static' if static_mode else 'animated'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
