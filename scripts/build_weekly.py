#!/usr/bin/env python3
"""Generate the Stage 1 on-site weekly PlainSight preview."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
SIGNALS_PATH = ROOT / "data" / "signals.json"
WEEKLY_DIR = ROOT / "data" / "weekly"
LATEST_PATH = WEEKLY_DIR / "latest.json"
ARCHIVE_INDEX_PATH = WEEKLY_DIR / "archive-index.json"
EASTERN = ZoneInfo("America/New_York")


def read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def filed_date(record: dict[str, Any]) -> date | None:
    value = record.get("filedAt") or record.get("filed")
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def compact_record(record: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "accession",
        "ticker",
        "company",
        "insider",
        "role",
        "side",
        "transactionDate",
        "filedAt",
        "shares",
        "price",
        "value",
        "sharesAfter",
        "positionChange",
        "strength",
        "source",
        "context",
        "caveat",
    )
    return {key: record.get(key) for key in keys}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", help="Edition date in YYYY-MM-DD format.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    as_of = date.fromisoformat(args.as_of) if args.as_of else datetime.now(EASTERN).date()
    period_start = as_of - timedelta(days=6)
    data = read_json(SIGNALS_PATH, {"transactions": [], "reviewNeeded": []})
    records = [record for record in data.get("transactions", []) if (record_date := filed_date(record)) and period_start <= record_date <= as_of]
    warnings = [warning for warning in data.get("reviewNeeded", []) if (warning_date := filed_date(warning)) and period_start <= warning_date <= as_of]
    purchases = sorted((record for record in records if record.get("side") == "BUY"), key=lambda item: (item.get("strength") or 0, item.get("value") or 0), reverse=True)
    sales = sorted((record for record in records if record.get("side") == "SELL"), key=lambda item: item.get("value") or 0, reverse=True)

    by_ticker: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for purchase in purchases:
        by_ticker[purchase.get("ticker", "N/A")].append(purchase)
    clusters = []
    for ticker, items in by_ticker.items():
        insiders = sorted({item.get("insider", "Unknown") for item in items})
        if len(insiders) < 2:
            continue
        clusters.append(
            {
                "ticker": ticker,
                "company": items[0].get("company"),
                "insiderCount": len(insiders),
                "insiders": insiders,
                "combinedValue": round(sum(float(item.get("value") or 0) for item in items), 2),
            }
        )
    clusters.sort(key=lambda item: item["combinedValue"], reverse=True)

    strongest = [compact_record(record) for record in purchases[:5]]
    notable_sales = [compact_record(record) for record in sales[:5]]
    status = "published" if records else "no-qualifying-trades"
    if purchases:
        leader = purchases[0]
        lead = f"{leader.get('ticker', 'N/A')} led the week's qualifying purchases with a reported value of ${float(leader.get('value') or 0):,.0f}."
    elif sales:
        lead = "No qualifying purchases were recorded; the edition contains notable direct sales and review notes only."
    else:
        lead = "No qualifying new direct open-market transactions were recorded for this edition."

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    edition = {
        "schemaVersion": 1,
        "editionDate": as_of.isoformat(),
        "periodStart": period_start.isoformat(),
        "periodEnd": as_of.isoformat(),
        "generatedAt": generated_at,
        "stage": 1,
        "status": status,
        "workInProgress": True,
        "maturity": "collecting-history",
        "emailSent": False,
        "headline": "The week's public Form 4 activity, with the filing context intact.",
        "lead": lead,
        "counts": {
            "qualifyingPurchases": len(purchases),
            "notableSales": len(sales),
            "clusters": len(clusters),
            "reviewNeeded": len(warnings),
        },
        "strongestBuys": strongest,
        "notableSales": notable_sales,
        "clusters": clusters[:5],
        "reviewNeeded": warnings[:10],
        "methodology": "Ranks direct, non-derivative common-stock open-market purchases using reported value, estimated change in the insider's company position, and seniority. Amendments and ambiguous records remain outside the ranking.",
        "riskNote": "Filings are delayed and may be amended. A disclosed transaction is not a recommendation, and past outcomes do not predict future returns.",
        "developmentNote": "The weekly newsletter is a work in progress. Rankings and historical grades will become more informative only after PlainSight collects a larger validated filing history.",
    }
    write_json(LATEST_PATH, edition)
    write_json(WEEKLY_DIR / f"{as_of.isoformat()}.json", edition)

    archive = read_json(ARCHIVE_INDEX_PATH, {"editions": []})
    entries = [entry for entry in archive.get("editions", []) if entry.get("editionDate") != as_of.isoformat()]
    entries.append(
        {
            "editionDate": as_of.isoformat(),
            "periodStart": period_start.isoformat(),
            "periodEnd": as_of.isoformat(),
            "status": status,
            "path": f"data/weekly/{as_of.isoformat()}.json",
            "counts": edition["counts"],
        }
    )
    entries.sort(key=lambda entry: entry["editionDate"], reverse=True)
    write_json(ARCHIVE_INDEX_PATH, {"schemaVersion": 1, "generatedAt": generated_at, "editions": entries[:104]})
    print(json.dumps(edition["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
