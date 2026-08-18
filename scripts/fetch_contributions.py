#!/usr/bin/env python3
"""
fetch_contributions.py

Pulls your real contribution calendar with no GraphQL API and no personal
access token. GitHub serves the calendar as public HTML at:

    https://github.com/users/<username>/contributions

(the same fragment the profile page itself embeds). This script fetches
it, parses the day cells with BeautifulSoup, and writes
data/contributions.json with the raw days plus derived stats.

Usage:
    GITHUB_USERNAME=yourusername python scripts/fetch_contributions.py
    # or:
    python scripts/fetch_contributions.py yourusername
"""

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (compatible; profile-readme-bot/1.0)"


def get_username() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    env_user = os.environ.get("GITHUB_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER")
    if env_user:
        return env_user
    print("Usage: python scripts/fetch_contributions.py <username>")
    print("   or: GITHUB_USERNAME=<username> python scripts/fetch_contributions.py")
    sys.exit(1)


def fetch_contribution_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    """Parse the calendar cells into a list of {date, count, level} dicts."""
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # GitHub has used both <td class="ContributionCalendar-day"> and
    # <table>-free <tool-tip>/<td> layouts over the years; handle the
    # common attributes defensively.
    cells = soup.select("td.ContributionCalendar-day") or soup.select("[data-date]")

    for cell in cells:
        d = cell.get("data-date")
        if not d:
            continue
        level_attr = cell.get("data-level")
        level = int(level_attr) if level_attr is not None else 0

        count = 0
        tooltip_id = cell.get("id")
        if tooltip_id:
            tip = soup.select_one(f'[for="{tooltip_id}"]') or soup.select_one(
                f'tool-tip[for="{tooltip_id}"]'
            )
            if tip and tip.text:
                text = tip.text.strip()
                first_token = text.split(" ")[0].replace(",", "")
                if first_token.isdigit():
                    count = int(first_token)
                elif text.lower().startswith("no contributions"):
                    count = 0

        days.append({"date": d, "count": count, "level": level})

    days.sort(key=lambda x: x["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    if not days:
        return {
            "total": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "best_day": None,
            "monthly_totals": {},
        }

    total = sum(d["count"] for d in days)

    # Longest streak of consecutive days with count > 0.
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    # Current streak: walk backwards from the most recent day.
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    best_day = max(days, key=lambda x: x["count"])

    monthly_totals: dict[str, int] = {}
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + d["count"]

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": {"date": best_day["date"], "count": best_day["count"]},
        "monthly_totals": monthly_totals,
    }


def main():
    username = get_username()
    print(f"Fetching contribution calendar for {username} ...")
    html = fetch_contribution_html(username)

    days = parse_days(html)
    if not days:
        print("Warning: no day cells parsed. GitHub may have changed its markup.")

    stats = compute_stats(days)

    output = {
        "username": username,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "days": days,
        "stats": stats,
    }

    out_path = Path("data/contributions.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"Wrote {out_path}: {len(days)} days, {stats['total']} total contributions")


if __name__ == "__main__":
    main()
