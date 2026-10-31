#!/usr/bin/env python3
"""Build PlainSight's historical purchase-follow-through score snapshot.

The input is the point-in-time qualified-signals export produced by the
historical backtest. This script does not download prices. It turns already
calculated, matured 60-session outcomes into a small static JSON file for the
GitHub Pages site.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "trust-scores.json"
MINIMUM_PUBLISHED_SAMPLE = 3
SHRINKAGE_PRIOR = 20.0
OUTCOME_CAP = 0.25

NAME_OVERRIDES = {
    "0001065416": "Frank B. Holding Jr.",
    "0001065425": "Douglas A. Pertz",
    "0001613438": "Anthony Noto",
    "0001007772": "Morris Goldfarb",
    "0001137443": "Gary G. Friedman",
    "0001233163": "Joseph M. Hogan",
}


def canonical_cik(value: str | None) -> str:
    digits = "".join(character for character in str(value or "") if character.isdigit())
    return digits.zfill(10) if digits else ""


def display_name(raw: str, owner_cik: str) -> str:
    if owner_cik in NAME_OVERRIDES:
        return NAME_OVERRIDES[owner_cik]
    if raw and raw == raw.upper():
        return " ".join(part.capitalize() for part in raw.split())
    return raw or "Reporting person"


def confidence_band(sample_size: int) -> str:
    if sample_size < 3:
        return "Insufficient"
    if sample_size < 6:
        return "Provisional"
    if sample_size < 12:
        return "Developing"
    return "Established"


def score_band(score: float) -> str:
    if score >= 60:
        return "Strong"
    if score >= 55:
        return "Positive"
    if score >= 45:
        return "Neutral"
    return "Weak"


def bounded(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def aggregate_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, Any]]:
    """Aggregate one outcome per owner/issuer/entry-session purchase episode."""
    episodes: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        if str(row.get("direction", "BUY")).upper() != "BUY":
            continue
        if str(row.get("mature", "")).lower() != "true":
            continue
        try:
            excess = float(row.get("follower_excess_return", ""))
        except (TypeError, ValueError):
            continue
        owner_cik = canonical_cik(row.get("RPTOWNERCIK"))
        if not owner_cik:
            continue
        key = (owner_cik, canonical_cik(row.get("ISSUERCIK")), row.get("entry_date", ""))
        episode = episodes.setdefault(
            key,
            {
                "ownerCik": owner_cik,
                "name": row.get("RPTOWNERNAME", ""),
                "role": row.get("RPTOWNER_TITLE", "") or "Reporting person",
                "filingDate": row.get("filing_date", ""),
                "entryDate": row.get("entry_date", ""),
                "outcomes": [],
            },
        )
        episode["outcomes"].append(excess)

    by_owner: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for episode in episodes.values():
        episode_outcomes = episode.pop("outcomes")
        episode["excess"] = sum(episode_outcomes) / len(episode_outcomes)
        by_owner[episode["ownerCik"]].append(episode)

    insiders: list[dict[str, Any]] = []
    for owner_cik, owner_episodes in by_owner.items():
        if len(owner_episodes) < MINIMUM_PUBLISHED_SAMPLE:
            continue
        outcomes = [float(item["excess"]) for item in owner_episodes]
        capped_average = sum(bounded(value, -OUTCOME_CAP, OUTCOME_CAP) for value in outcomes) / len(outcomes)
        hit_rate = sum(value > 0 for value in outcomes) / len(outcomes)
        performance_component = bounded(50.0 + capped_average * 500.0, 0.0, 100.0)
        raw_score = 0.65 * performance_component + 0.35 * (hit_rate * 100.0)
        confidence_weight = len(outcomes) / (len(outcomes) + SHRINKAGE_PRIOR)
        score = 50.0 + confidence_weight * (raw_score - 50.0)
        latest = max(owner_episodes, key=lambda item: (item.get("entryDate", ""), item.get("filingDate", "")))
        insiders.append(
            {
                "reportingOwnerCik": owner_cik,
                "name": display_name(str(latest.get("name") or ""), owner_cik),
                "role": latest.get("role") or "Reporting person",
                "score": round(score, 1),
                "scoreBand": score_band(score),
                "sampleSize": len(outcomes),
                "confidence": confidence_band(len(outcomes)),
                "cappedAverageExcessReturnPct": round(capped_average * 100.0, 1),
                "hitRatePct": round(hit_rate * 100.0),
                "firstEntryDate": min(item.get("entryDate", "") for item in owner_episodes),
                "lastEntryDate": max(item.get("entryDate", "") for item in owner_episodes),
            }
        )
    return sorted(insiders, key=lambda item: (item["score"], item["sampleSize"]), reverse=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signals-csv", required=True, type=Path, help="Qualified historical signal export.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--as-of", default="2026-06-30", help="Last date included in the historical research window.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.signals_csv.open(encoding="utf-8-sig", newline="") as source:
        insiders = aggregate_rows(csv.DictReader(source))
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload = {
        "schemaVersion": 1,
        "methodologyVersion": "trust-meter-v1",
        "generatedAt": generated_at,
        "asOf": args.as_of,
        "status": "archived-research-snapshot",
        "label": "Historical purchase follow-through",
        "benchmark": "SPY",
        "holdingPeriodSessions": 60,
        "entryRule": "Adjusted opening price of the next trading session after the filing date.",
        "eligibility": "Validated direct, non-derivative, open-market common-stock purchases only.",
        "formula": {
            "performanceWeight": 0.65,
            "hitRateWeight": 0.35,
            "outcomeCapPct": 25,
            "shrinkage": "50 + n/(n+20) * (raw score - 50)",
            "minimumPublishedSample": MINIMUM_PUBLISHED_SAMPLE,
        },
        "confidenceBands": {
            "insufficient": "0-2 mature purchase episodes",
            "provisional": "3-5 mature purchase episodes",
            "developing": "6-11 mature purchase episodes",
            "established": "12+ mature purchase episodes",
        },
        "limitations": "Historical research output, not a prediction or a measure of honesty. Outcomes include a 0.2% modeled round-trip cost and are not independently validated.",
        "insiders": insiders,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(insiders)} scored insiders to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
