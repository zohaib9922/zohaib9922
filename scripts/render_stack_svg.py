#!/usr/bin/env python3
"""
render_stack_svg.py

Reads data/languages.json and renders a terminal-style horizontal bar
chart of your top languages by bytes across public repos -- ASCII-bar
look ([####....]) with a neon green fill, each bar sweeping in
left-to-right, staggered top to bottom, then freezing (no looping).

Usage:
    python scripts/render_stack_svg.py [languages.json] [output.svg]
"""

import json
import sys
from pathlib import Path

BAR_COLOR = "#39d353"
TRACK_COLOR = "#21262d"
TEXT_COLOR = "#c9d1d9"
LABEL_COLOR = "#8b949e"
PANEL_BG = "#0d1117"
BORDER_COLOR = "#30363d"

TOP_N = 6
FONT_SIZE = 13
ROW_H = 30
BAR_H = 10
LABEL_W = 110
PCT_W = 50
PAD = 20
CHART_W = 420

BAR_STAGGER = 0.1
BAR_DURATION = 0.6


def xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(data: dict) -> str:
    langs = data.get("languages", [])[:TOP_N]
    max_pct = max((l["pct"] for l in langs), default=1) or 1

    width = PAD * 2 + LABEL_W + CHART_W + PCT_W
    height = PAD * 2 + 34 + len(langs) * ROW_H + 10

    style_rules = [
        "@keyframes barIn { from { transform: scaleX(0); } to { transform: scaleX(1); } }",
        "@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }",
    ]
    body = []

    header_y = PAD + 16
    body.append(
        f'<text x="{PAD}" y="{header_y}" font-family="Menlo, Consolas, monospace" '
        f'font-size="14" font-weight="600" fill="{TEXT_COLOR}">avi@github ~ $ ./stack.sh</text>'
    )

    top = PAD + 34
    for i, lang in enumerate(langs):
        y = top + i * ROW_H
        begin = round(i * BAR_STAGGER, 3)
        bar_id = f"stackbar-{i}"
        label = xml_escape(lang["language"])
        pct = lang["pct"]
        bar_full_w = CHART_W * (pct / max_pct)

        style_rules.append(
            f'#{bar_id} {{ opacity: 0; animation: fadeIn 0.2s ease-out {begin}s forwards; }}'
        )
        style_rules.append(
            f'#{bar_id} .fill {{ transform-origin: left center; transform: scaleX(0); '
            f'animation: barIn {BAR_DURATION}s cubic-bezier(0.2,0.8,0.2,1) {begin}s forwards; }}'
        )

        label_x = PAD
        track_x = PAD + LABEL_W
        track_y = y - BAR_H / 2

        body.append(
            f'<g id="{bar_id}">'
            f'<text x="{label_x}" y="{y + 4}" font-family="Menlo, Consolas, monospace" '
            f'font-size="{FONT_SIZE}" fill="{TEXT_COLOR}">{label}</text>'
            f'<rect x="{track_x}" y="{track_y}" width="{CHART_W}" height="{BAR_H}" rx="{BAR_H/2}" '
            f'fill="{TRACK_COLOR}"/>'
            f'<rect class="fill" x="{track_x}" y="{track_y}" width="{bar_full_w:.1f}" height="{BAR_H}" '
            f'rx="{BAR_H/2}" fill="{BAR_COLOR}"/>'
            f'<text x="{track_x + CHART_W + 10}" y="{y + 4}" font-family="Menlo, Consolas, monospace" '
            f'font-size="{FONT_SIZE}" fill="{LABEL_COLOR}">{pct:.1f}%</text>'
            f'</g>'
        )

    style_block = f'<style>{"".join(style_rules)}</style>'

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">'
        f'{style_block}'
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="8" '
        f'fill="{PANEL_BG}" stroke="{BORDER_COLOR}" stroke-width="1"/>'
        f'{"".join(body)}'
        f'</svg>'
    )
    return svg


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/languages.json")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("stack-chart.svg")

    if not input_path.exists():
        print(f"Error: {input_path} not found. Run fetch_languages.py first.")
        sys.exit(1)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    svg = build_svg(data)
    output_path.write_text(svg, encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
