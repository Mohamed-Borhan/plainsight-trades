#!/usr/bin/env python3
"""Build the latest daily PlainSight brief from two SEC data snapshots."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SIGNALS_PATH = ROOT / "data" / "signals.json"
DAILY_DIR = ROOT / "data" / "daily"
LATEST_PATH = DAILY_DIR / "latest.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def previous_snapshot(ref: str) -> dict[str, Any]:
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{ref}:data/signals.json"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
        return json.loads(raw)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {"transactions": [], "reviewNeeded": []}


def record_key(record: dict[str, Any]) -> str:
    return str(record.get("id") or f"{record.get('accession')}:{record.get('side')}")


def distinct_insiders(records: list[dict[str, Any]]) -> set[str]:
    return {str(record.get("insider") or "Unknown") for record in records}


def build_clusters(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        ticker = str(record.get("ticker") or "N/A")
        grouped[(ticker, str(record.get("side") or "N/A"))].append(record)

    clusters: list[dict[str, Any]] = []
    for (ticker, side), members in grouped.items():
        insiders = sorted(distinct_insiders(members))
        if len(insiders) < 2:
            continue
        clusters.append(
            {
                "ticker": ticker,
                "company": members[0].get("company") or "N/A",
                "side": side,
                "insiderCount": len(insiders),
                "insiders": insiders,
                "combinedValue": round(sum(float(item.get("value") or 0) for item in members), 2),
                "accessions": sorted({str(item.get("accession")) for item in members}),
            }
        )
    clusters.sort(key=lambda item: item["combinedValue"], reverse=True)
    return clusters


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--previous-ref",
        default="HEAD",
        help="Git ref containing the data snapshot from before the current collection.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current = load_json(SIGNALS_PATH)
    previous = previous_snapshot(args.previous_ref)

    prior_ids = {record_key(record) for record in previous.get("transactions", [])}
    records = [
        record
        for record in current.get("transactions", [])
        if record_key(record) not in prior_ids
    ]
    prior_warnings = {
        warning.get("accession") for warning in previous.get("reviewNeeded", [])
    }
    warnings = [
        warning
        for warning in current.get("reviewNeeded", [])
        if warning.get("accession") not in prior_warnings
    ]

    buys = [record for record in records if record.get("side") == "BUY"]
    sales = [record for record in records if record.get("side") == "SELL"]
    clusters = build_clusters(records)
    clustered_buy_tickers = {
        cluster["ticker"] for cluster in clusters if cluster.get("side") == "BUY"
    }

    for record in buys:
        base = int(record.get("strength") or 0)
        record["dailyConviction"] = min(
            100,
            base + (10 if record.get("ticker") in clustered_buy_tickers else 0),
        )
    buys.sort(
        key=lambda record: (
            int(record.get("dailyConviction") or 0),
            float(record.get("value") or 0),
        ),
        reverse=True,
    )
    sales.sort(key=lambda record: float(record.get("value") or 0), reverse=True)
    warnings.sort(key=lambda warning: warning.get("filedAt", ""), reverse=True)

    edition = current.get("lastCheckedDate") or current.get("generatedAt", "")[:10]
    payload = {
        "schemaVersion": 1,
        "editionDate": edition,
        "generatedAt": current.get("generatedAt"),
        "source": "SEC EDGAR public Forms 4 and 4/A",
        "counts": {
            "qualifyingPurchases": len(buys),
            "notableSales": len(sales),
            "clusters": len(clusters),
            "reviewNeeded": len(warnings),
        },
        "strongestBuys": buys,
        "notableSales": sales,
        "clusters": clusters,
        "reviewNeeded": warnings,
        "methodology": {
            "purchaseMinimumUsd": current.get("filters", {}).get("purchaseMinimumUsd", 50000),
            "saleMinimumUsd": current.get("filters", {}).get("saleMinimumUsd", 250000),
            "directOwnershipOnly": True,
            "nonDerivativeOnly": True,
            "transactionCodes": ["P", "S"],
        },
        "notice": "Public-filing research only. SEC filings may be delayed, amended, incomplete, or corrected later. This is not financial advice, and PlainSight never places broker orders.",
    }

    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    LATEST_PATH.write_text(serialized, encoding="utf-8")
    (DAILY_DIR / f"{edition}.json").write_text(serialized, encoding="utf-8")
    print(json.dumps(payload["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
