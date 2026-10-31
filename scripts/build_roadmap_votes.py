#!/usr/bin/env python3
"""Aggregate one active public PlainSight roadmap vote per GitHub user."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "roadmap-votes.json"
VOTE_HEADING = "What should PlainSight build next?"
OPTIONS = [
    {
        "id": "review-queue",
        "label": "Clean and explain the review queue",
        "description": "Reconcile amendments and show resolved, superseded, or still-needs-review status.",
    },
    {
        "id": "trust-meter",
        "label": "Validated Trust Meter",
        "description": "Add benchmark-relative history, sample size, and confidence to insider records.",
    },
    {
        "id": "benchmark-outcomes",
        "label": "Benchmark outcome charts",
        "description": "Compare 30-, 90-, and 180-session follow-through with SPY.",
    },
    {
        "id": "advanced-filters",
        "label": "Advanced filing filters and export",
        "description": "Filter by role, size, date, cluster, confidence, and review status.",
    },
    {
        "id": "congressional-automation",
        "label": "Automated congressional disclosures",
        "description": "Import official House and Senate disclosures into a separate tracker.",
    },
    {
        "id": "newsletter-watchlists",
        "label": "Weekly delivery and watchlists",
        "description": "Offer an optional weekly email and issuer watchlists without order execution.",
    },
]
OPTION_BY_LABEL = {option["label"]: option for option in OPTIONS}


def parse_vote(body: str | None) -> str | None:
    if not body:
        return None
    pattern = rf"###\s+{re.escape(VOTE_HEADING)}\s*\n+\s*(.+?)\s*(?=\n+###|\Z)"
    match = re.search(pattern, body, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    selected = " ".join(match.group(1).strip().split())
    option = OPTION_BY_LABEL.get(selected)
    return option["id"] if option else None


def fetch_open_issues(repository: str, token: str | None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repository}/issues?state=open&per_page=100&page={page}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "PlainSight-roadmap-vote-aggregator",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.loads(response.read().decode("utf-8"))
        issues.extend(batch)
        if len(batch) < 100:
            return issues
        page += 1


def aggregate_votes(issues: list[dict[str, Any]]) -> dict[str, Any]:
    latest_by_user: dict[str, tuple[str, str]] = {}
    for issue in issues:
        if issue.get("pull_request") or not str(issue.get("title", "")).startswith("[Roadmap vote]"):
            continue
        vote_id = parse_vote(issue.get("body"))
        login = str((issue.get("user") or {}).get("login") or "").lower()
        if not vote_id or not login:
            continue
        updated_at = str(issue.get("updated_at") or issue.get("created_at") or "")
        previous = latest_by_user.get(login)
        if previous is None or updated_at >= previous[0]:
            latest_by_user[login] = (updated_at, vote_id)

    counts = {option["id"]: 0 for option in OPTIONS}
    for _updated_at, vote_id in latest_by_user.values():
        counts[vote_id] += 1
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "method": "One active public GitHub issue-form vote per GitHub account; the latest edited vote wins.",
        "totalVotes": len(latest_by_user),
        "options": [{**option, "votes": counts[option["id"]]} for option in OPTIONS],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "Mohamed-Borhan/plainsight-trades"))
    parser.add_argument("--issues-json", type=Path, help="Optional local GitHub issues response for testing.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.issues_json:
        issues = json.loads(args.issues_json.read_text(encoding="utf-8"))
    else:
        issues = fetch_open_issues(args.repository, os.environ.get("GITHUB_TOKEN"))
    payload = aggregate_votes(issues)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {payload['totalVotes']} public roadmap votes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
