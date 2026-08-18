#!/usr/bin/env python3
"""
make_link_buttons.py

Hand-authors a set of modern pill-shaped SVG buttons for external links
(Portfolio, LinkedIn, Instagram, ...) that match the terminal/neofetch
look of the rest of the profile. Each button is its own small SVG so it
can be wrapped in a markdown link in the README -- GitHub strips
inline <a>/onclick from SVGs, so the click target has to be the
surrounding markdown link, not something inside the SVG itself.

A short entrance animation (fade + slight rise, staggered per button)
plays once on load via CSS keyframes, then freezes.

Usage:
    python scripts/make_link_buttons.py   # writes buttons/*.svg

Edit the LINKS list below to add/remove/reorder buttons.
"""

import re
from pathlib import Path

LINKS = [
    {
        "id": "portfolio",
        "label": "Portfolio",
        "url": "https://zohaib9922.github.io/portfolio",
        "accent": "#39d353",
        "icon": "globe",
    },
    {
        "id": "linkedin",
        "label": "LinkedIn",
        "url": "https://linkedin.com/in/zohaibhasann",
        "accent": "#0a66c2",
        "icon": "linkedin",
    },
    {
        "id": "instagram",
        "label": "Instagram",
        "url": "https://www.instagram.com/idk_zabii/",
        "accent": "#e1306c",
        "icon": "instagram",
    },
]

PANEL_BG = "#0d1117"
BORDER_COLOR = "#30363d"
TEXT_COLOR = "#c9d1d9"

FONT_SIZE = 14
HEIGHT = 42
PAD_X = 18
ICON_SIZE = 16
ICON_GAP = 10

ENTRANCE_STAGGER = 0.08
ENTRANCE_DURATION = 0.4


def xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def icon_path(kind: str, accent: str) -> str:
    """Return SVG markup for a 16x16 icon, positioned at (0,0), stroke/fill in accent."""
    if kind == "globe":
        return (
            f'<circle cx="8" cy="8" r="7" fill="none" stroke="{accent}" stroke-width="1.4"/>'
            f'<ellipse cx="8" cy="8" rx="3" ry="7" fill="none" stroke="{accent}" stroke-width="1.2"/>'
            f'<line x1="1" y1="8" x2="15" y2="8" stroke="{accent}" stroke-width="1.2"/>'
        )
    if kind == "linkedin":
        return (
            f'<rect x="0.5" y="0.5" width="15" height="15" rx="3" fill="{accent}"/>'
            f'<rect x="3.3" y="6.2" width="2.2" height="7" fill="#0d1117"/>'
            f'<circle cx="4.4" cy="3.6" r="1.4" fill="#0d1117"/>'
            f'<path d="M7.6 6.2h2.1v1.1c0.4-0.7 1.2-1.3 2.4-1.3 2.1 0 2.7 1.2 2.7 3.3v4h-2.2V9.7c0-0.9-0.3-1.6-1.2-1.6-0.9 0-1.4 0.6-1.4 1.6v3.5H7.6V6.2z" fill="#0d1117"/>'
        )
    if kind == "instagram":
        return (
            f'<rect x="0.5" y="0.5" width="15" height="15" rx="4.5" fill="none" '
            f'stroke="{accent}" stroke-width="1.4"/>'
            f'<circle cx="8" cy="8" r="3.3" fill="none" stroke="{accent}" stroke-width="1.4"/>'
            f'<circle cx="12.1" cy="3.9" r="1" fill="{accent}"/>'
        )
    return ""


def build_button_svg(link: dict, index: int) -> str:
    label = link["label"]
    accent = link["accent"]
    icon = icon_path(link["icon"], accent)

    text_width = len(label) * (FONT_SIZE * 0.62)
    width = int(PAD_X + ICON_SIZE + ICON_GAP + text_width + PAD_X)

    begin = round(index * ENTRANCE_STAGGER, 3)

    icon_y = (HEIGHT - ICON_SIZE) / 2
    text_x = PAD_X + ICON_SIZE + ICON_GAP
    text_y = HEIGHT / 2 + FONT_SIZE * 0.35

    style = (
        f'<style>'
        f'.btn {{ opacity: 0; transform: translateY(4px); '
        f'animation: btnIn {ENTRANCE_DURATION}s ease-out {begin}s forwards; }}'
        f'@keyframes btnIn {{ to {{ opacity: 1; transform: translateY(0); }} }}'
        f'.pill {{ transition: stroke 0.15s ease; }}'
        f'</style>'
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {HEIGHT}" '
        f'width="{width}" height="{HEIGHT}">'
        f'{style}'
        f'<g class="btn">'
        f'<rect class="pill" x="1" y="1" width="{width-2}" height="{HEIGHT-2}" '
        f'rx="{(HEIGHT-2)/2:.1f}" fill="{PANEL_BG}" stroke="{BORDER_COLOR}" stroke-width="1.4"/>'
        f'<g transform="translate({PAD_X},{icon_y:.1f})">{icon}</g>'
        f'<text x="{text_x:.1f}" y="{text_y:.1f}" font-family="Menlo, Consolas, monospace" '
        f'font-size="{FONT_SIZE}" font-weight="600" fill="{TEXT_COLOR}">{xml_escape(label)}</text>'
        f'</g>'
        f'</svg>'
    )
    return svg


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9-]", "", s.lower().replace(" ", "-"))


def main():
    out_dir = Path("buttons")
    out_dir.mkdir(exist_ok=True)

    for i, link in enumerate(LINKS):
        svg = build_button_svg(link, i)
        out_path = out_dir / f"{link['id']}.svg"
        out_path.write_text(svg, encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
