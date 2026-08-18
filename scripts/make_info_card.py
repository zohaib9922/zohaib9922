#!/usr/bin/env python3
"""
make_info_card.py

Hand-authors info-card.svg: a neofetch-style panel (title bar + colored
key/value rows) that fades and slides in line by line, staggered, so it
looks like it's printing next to the ASCII portrait.

This card is for the story numbers can't tell -- role, stack, highlights.
The contribution heatmap already covers the GitHub stats, so don't
duplicate those here.

Usage:
    python scripts/make_info_card.py [output.svg]

    STATIC=1 python scripts/make_info_card.py   # emits a frozen frame,
                                                  # useful for local Quick
                                                  # Look previews on macOS.

Edit the CONFIG dict below with your own info.
"""

import os
import sys
from pathlib import Path

CONFIG = {
    "user": "zohaib",
    "host": "github",
    "role": "Senior Full Stack Developer",
    "now": "RootsByGA (remote)",
    "prev": "Texas Digital Hub, KodeInn Technologies",
    "stack": "PHP - Laravel - WordPress - React - MySQL",
    "highlights": "5+ yrs shipping full-stack products",
    "location": "Lahore, PK",
}

TITLE_BAR_COLOR = "#161b22"
PANEL_BG = "#0d1117"
BORDER_COLOR = "#30363d"
LABEL_COLOR = "#39d353"     # green, like a shell prompt
VALUE_COLOR = "#c9d1d9"
DIM_COLOR = "#6e7681"

FONT_SIZE = 14
LINE_H = 26
PAD_X = 22
PAD_TOP = 64

ROW_STAGGER = 0.12   # seconds between each line starting to fade in
ROW_DURATION = 0.45  # seconds for a single line's fade/slide


def xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_rows(cfg: dict) -> list[tuple[str, str]]:
    return [
        ("role", cfg["role"]),
        ("now", cfg["now"]),
        ("prev", cfg["prev"]),
        ("stack", cfg["stack"]),
        ("highlights", cfg["highlights"]),
        ("location", cfg["location"]),
    ]


def build_svg(cfg: dict, static: bool) -> str:
    rows = build_rows(cfg)
    width = 490
    height = PAD_TOP + len(rows) * LINE_H + 30

    style_rules = []
    body = []

    prompt_line = f"{cfg['user']}@{cfg['host']}"
    header_y = 40

    for i, (label, value) in enumerate(rows):
        y = PAD_TOP + i * LINE_H
        row_class = f"row-{i}"
        begin = round(i * ROW_STAGGER, 3)

        if not static:
            style_rules.append(
                f'.{row_class} {{'
                f'opacity: 0; transform: translateX(-8px);'
                f'animation: fadeSlideIn {ROW_DURATION}s ease-out {begin}s forwards;'
                f'}}'
            )

        label_txt = xml_escape(label.ljust(12))
        value_txt = xml_escape(value)

        body.append(
            f'<g class="{row_class}">'
            f'<text x="{PAD_X}" y="{y}" font-family="Menlo, Consolas, monospace" '
            f'font-size="{FONT_SIZE}" fill="{LABEL_COLOR}">{label_txt}</text>'
            f'<text x="{PAD_X + 118}" y="{y}" font-family="Menlo, Consolas, monospace" '
            f'font-size="{FONT_SIZE}" fill="{VALUE_COLOR}">{value_txt}</text>'
            f'</g>'
        )

    keyframes = (
        '@keyframes fadeSlideIn {'
        'from { opacity: 0; transform: translateX(-8px); } '
        'to { opacity: 1; transform: translateX(0); }'
        '}'
    ) if not static else ""

    style_block = f'<style>{keyframes}{"".join(style_rules)}</style>'

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">'
        f'{style_block}'
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="8" '
        f'fill="{PANEL_BG}" stroke="{BORDER_COLOR}" stroke-width="1" />'
        f'<rect x="1" y="1" width="{width-2}" height="30" rx="8" fill="{TITLE_BAR_COLOR}" />'
        f'<rect x="1" y="20" width="{width-2}" height="12" fill="{TITLE_BAR_COLOR}" />'
        f'<circle cx="18" cy="16" r="5" fill="#ff5f56" />'
        f'<circle cx="34" cy="16" r="5" fill="#ffbd2e" />'
        f'<circle cx="50" cy="16" r="5" fill="#27c93f" />'
        f'<text x="{width/2}" y="20" text-anchor="middle" '
        f'font-family="Menlo, Consolas, monospace" font-size="12" fill="{DIM_COLOR}">'
        f'neofetch</text>'
        f'<text x="{PAD_X}" y="{header_y}" font-family="Menlo, Consolas, monospace" '
        f'font-size="{FONT_SIZE}" fill="{LABEL_COLOR}">{xml_escape(prompt_line)}</text>'
        f'<line x1="{PAD_X}" y1="{header_y+10}" x2="{width-PAD_X}" y2="{header_y+10}" '
        f'stroke="{BORDER_COLOR}" stroke-width="1" />'
        f'{"".join(body)}'
        f'</svg>'
    )
    return svg


def main():
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("info-card.svg")
    static = os.environ.get("STATIC") == "1"

    svg = build_svg(CONFIG, static)
    output_path.write_text(svg, encoding="utf-8")
    print(f"Wrote {output_path} (static={static})")


if __name__ == "__main__":
    main()
