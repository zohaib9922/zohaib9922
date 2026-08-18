#!/usr/bin/env python3
"""
fetch_languages.py

Pulls your public, non-fork repos via GitHub's REST API (no token needed
for public data, though an unauthenticated IP is rate-limited to 60
req/hour) and sums each repo's per-language byte counts into an overall
language breakdown. Writes data/languages.json.

Usage:
    GITHUB_USERNAME=yourusername python scripts/fetch_languages.py
    # or:
    python scripts/fetch_languages.py yourusername
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

USER_AGENT = "Mozilla/5.0 (compatible; profile-readme-bot/1.0)"
API_ROOT = "https://api.github.com"


def get_username() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    env_user = os.environ.get("GITHUB_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER")
    if env_user:
        return env_user
    print("Usage: python scripts/fetch_languages.py <username>")
    sys.exit(1)


def api_get(path: str) -> object:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(f"{API_ROOT}{path}", headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def list_owned_repos(username: str) -> list[dict]:
    repos = []
    page = 1
    while True:
        batch = api_get(f"/users/{username}/repos?per_page=100&type=owner&page={page}")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return [r for r in repos if not r.get("fork") and not r.get("archived")]


def sum_languages(username: str, repos: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for repo in repos:
        name = repo["name"]
        try:
            langs = api_get(f"/repos/{username}/{name}/languages")
        except requests.HTTPError as e:
            print(f"  skip {name}: {e}")
            continue
        for lang, bytes_count in langs.items():
            totals[lang] = totals.get(lang, 0) + bytes_count
        time.sleep(0.05)
    return totals


def main():
    username = get_username()
    print(f"Listing repos for {username} ...")
    repos = list_owned_repos(username)
    print(f"Found {len(repos)} owned, non-fork repos. Fetching languages ...")

    totals = sum_languages(username, repos)
    grand_total = sum(totals.values()) or 1

    breakdown = sorted(
        (
            {"language": lang, "bytes": count, "pct": round(count / grand_total * 100, 1)}
            for lang, count in totals.items()
        ),
        key=lambda x: x["bytes"],
        reverse=True,
    )

    output = {
        "username": username,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "repo_count": len(repos),
        "languages": breakdown,
    }

    out_path = Path("data/languages.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    top = ", ".join(f"{d['language']} {d['pct']}%" for d in breakdown[:5])
    print(f"Wrote {out_path}: {len(breakdown)} languages across {len(repos)} repos")
    print(f"Top: {top}")


if __name__ == "__main__":
    main()
