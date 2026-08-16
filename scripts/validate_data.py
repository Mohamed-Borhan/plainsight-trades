#!/usr/bin/env python3
"""Validate generated PlainSight data before publishing it."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    if not path.exists():
        raise AssertionError(f"Missing generated file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def official_sec_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.hostname in {"www.sec.gov", "sec.gov"}


def main() -> int:
    signals = load(ROOT / "data" / "signals.json")
    state = load(ROOT / "data" / "state.json")
    weekly = load(ROOT / "data" / "weekly" / "latest.json")
    archive = load(ROOT / "data" / "weekly" / "archive-index.json")

    assert signals.get("schemaVersion") == 1
    assert state.get("schemaVersion") == 1
    assert weekly.get("schemaVersion") == 1
    assert archive.get("schemaVersion") == 1
    assert signals.get("automation", {}).get("emailDelivery") is False
    assert weekly.get("emailSent") is False
    assert weekly.get("workInProgress") is True
    assert weekly.get("maturity") == "collecting-history"

    seen_ids: set[str] = set()
    for record in signals.get("transactions", []):
        required = {"id", "accession", "ticker", "company", "insider", "side", "filedAt", "value", "source"}
        missing = required - record.keys()
        assert not missing, f"{record.get('id', 'record')} is missing {sorted(missing)}"
        assert record["id"] not in seen_ids, f"duplicate record id: {record['id']}"
        seen_ids.add(record["id"])
        assert record["side"] in {"BUY", "SELL"}
        assert float(record["value"]) > 0
        assert official_sec_url(record["source"]), f"non-SEC source: {record['source']}"
        if record["side"] == "BUY":
            assert float(record["value"]) >= float(signals["filters"]["purchaseMinimumUsd"])
        else:
            assert float(record["value"]) >= float(signals["filters"]["saleMinimumUsd"])

    for warning in signals.get("reviewNeeded", []):
        assert official_sec_url(warning["source"])
        assert warning.get("reason")

    assert weekly.get("periodStart") <= weekly.get("periodEnd")
    assert isinstance(weekly.get("strongestBuys"), list)
    assert isinstance(weekly.get("notableSales"), list)
    assert isinstance(weekly.get("reviewNeeded"), list)
    print(f"validated {len(seen_ids)} transaction records and {len(signals.get('reviewNeeded', []))} review warnings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
