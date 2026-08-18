#!/usr/bin/env python3
"""
render_heatmap_svg.py

Reads data/contributions.json and renders the classic 53-week x 7-day
contribution calendar as rounded, colored boxes, using a GitHub-ish green
ramp. Boxes reveal once with a diagonal line-after-line slide-down (CSS
keyframes that play on load, then freeze -- no looping), plus a
Less -> More legend and a stats footer.

Usage:
    python scripts/render_heatmap_svg.py [contributions.json] [output.svg]
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# none -> brightest (level 5 is a neon top end, beyond GitHub's own scale,
# used only if a day's count is unusually high relative to the rest)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

BOX = 11
GAP = 3
CELL = BOX + GAP
LEFT_PAD = 30
TOP_PAD = 20
MONTH_LABEL_H = 18

STAGGER_UNIT = 0.012   # seconds per (week + weekday) diagonal step
BOX_DURATION = 0.35

MONTH_ABBR = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def load_data(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def level_for_count(count: int, max_count: int) -> int:
    """Bucket a raw count into a 0-4 palette level (5 reserved for standout days)."""
    if count <= 0:
        return 0
    if max_count <= 0:
        return 1
    ratio = count / max_count
    if ratio > 0.9:
        return 5 if count >= 10 else 4
    if ratio > 0.6:
        return 4
    if ratio > 0.3:
        return 3
    if ratio > 0.1:
        return 2
    return 1


def layout_weeks(days: list[dict]) -> list[list[dict | None]]:
    """
    Arrange sequential day dicts into GitHub's column-per-week grid.
    Each column is a week; row 0 = Sunday .. row 6 = Saturday.
    Returns a list of weeks, each a list of 7 entries (day dict or None).
    """
    if not days:
        return []

    parsed = []
    for d in days:
        dt = datetime.strptime(d["date"][:10], "%Y-%m-%d")
        parsed.append((dt, d))
    parsed.sort(key=lambda x: x[0])

    first_dt = parsed[0][0]
    # Python: Monday=0 .. Sunday=6. GitHub calendar row 0 = Sunday.
    first_weekday_sun0 = (first_dt.weekday() + 1) % 7  # Sun=0 .. Sat=6

    weeks: list[list[dict | None]] = [[None] * 7]
    col = 0
    row = first_weekday_sun0

    for dt, d in parsed:
        if row == 7:
            row = 0
            col += 1
            weeks.append([None] * 7)
        weeks[col][row] = {**d, "_dt": dt}
        row += 1

    return weeks


def month_label_positions(weeks: list[list[dict | None]]) -> list[tuple[int, str]]:
    """Return (week_index, label) pairs where a new month starts."""
    labels = []
    seen_months = set()
    for week_idx, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            month_key = day["_dt"].strftime("%Y-%m")
            if month_key not in seen_months:
                seen_months.add(month_key)
                labels.append((week_idx, MONTH_ABBR[day["_dt"].month - 1]))
            break
    return labels


def xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(data: dict) -> str:
    days = data.get("days", [])
    stats = data.get("stats", {})
    username = data.get("username", "")

    weeks = layout_weeks(days)
    num_weeks = max(len(weeks), 1)
    max_count = max((d["count"] for d in days), default=0)

    grid_w = num_weeks * CELL
    grid_h = 7 * CELL
    legend_h = 26
    footer_h = 24

    width = LEFT_PAD + grid_w + 20
    height = TOP_PAD + MONTH_LABEL_H + grid_h + legend_h + footer_h + 20

    style_rules = [
        "@keyframes boxIn { from { opacity: 0; transform: translateY(-6px); } "
        "to { opacity: 1; transform: translateY(0); } }"
    ]
    body = []

    # Month labels
    for week_idx, label in month_label_positions(weeks):
        x = LEFT_PAD + week_idx * CELL
        body.append(
            f'<text x="{x}" y="{TOP_PAD + 10}" font-family="Menlo, Consolas, monospace" '
            f'font-size="10" fill="#8b949e">{label}</text>'
        )

    # Day boxes, diagonal stagger by (week + weekday)
    grid_top = TOP_PAD + MONTH_LABEL_H
    for week_idx, week in enumerate(weeks):
        for row_idx, day in enumerate(week):
            x = LEFT_PAD + week_idx * CELL
            y = grid_top + row_idx * CELL

            if day is None:
                color = PALETTE[0]
                level = 0
            else:
                level = level_for_count(day["count"], max_count)
                color = PALETTE[min(level, len(PALETTE) - 1)]

            box_id = f"box-{week_idx}-{row_idx}"
            delay = round((week_idx + row_idx) * STAGGER_UNIT, 3)
            style_rules.append(
                f'#{box_id} {{ opacity: 0; '
                f'animation: boxIn {BOX_DURATION}s ease-out {delay}s forwards; }}'
            )

            title = ""
            if day is not None:
                count = day["count"]
                date_str = day["date"][:10]
                title = f'{count} contribution{"s" if count != 1 else ""} on {date_str}'

            body.append(
                f'<rect id="{box_id}" x="{x}" y="{y}" width="{BOX}" height="{BOX}" '
                f'rx="2" ry="2" fill="{color}">'
                + (f'<title>{xml_escape(title)}</title>' if title else "")
                + '</rect>'
            )

    # Legend: Less -> boxes -> More
    legend_y = grid_top + grid_h + 20
    legend_x = LEFT_PAD
    body.append(
        f'<text x="{legend_x}" y="{legend_y + 9}" font-family="Menlo, Consolas, monospace" '
        f'font-size="10" fill="#8b949e">Less</text>'
    )
    lx = legend_x + 36
    for lvl, color in enumerate(PALETTE[:5]):
        body.append(
            f'<rect x="{lx}" y="{legend_y}" width="{BOX}" height="{BOX}" rx="2" ry="2" '
            f'fill="{color}" />'
        )
        lx += CELL
    body.append(
        f'<text x="{lx + 4}" y="{legend_y + 9}" font-family="Menlo, Consolas, monospace" '
        f'font-size="10" fill="#8b949e">More</text>'
    )

    # Stats footer
    total = stats.get("total", 0)
    current_streak = stats.get("current_streak", 0)
    longest_streak = stats.get("longest_streak", 0)
    footer_y = legend_y + footer_h
    footer_text = (
        f"{total:,} contributions in the last year   |   "
        f"current streak: {current_streak}d   |   longest streak: {longest_streak}d"
    )
    body.append(
        f'<text x="{LEFT_PAD}" y="{footer_y}" font-family="Menlo, Consolas, monospace" '
        f'font-size="11" fill="#c9d1d9">{xml_escape(footer_text)}</text>'
    )

    style_block = f'<style>{"".join(style_rules)}</style>'

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">'
        f'{style_block}'
        f'<rect width="100%" height="100%" fill="none" />'
        f'{"".join(body)}'
        f'</svg>'
    )
    return svg


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/contributions.json")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("contrib-heatmap.svg")

    if not input_path.exists():
        print(f"Error: {input_path} not found. Run fetch_contributions.py first.")
        sys.exit(1)

    data = load_data(input_path)
    svg = build_svg(data)
    output_path.write_text(svg, encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
