#!/usr/bin/env python3
"""Collect qualifying public Form 4 transactions from official SEC archives.

The collector intentionally uses only Python's standard library, limits request
frequency, identifies itself to the SEC, and writes static JSON for GitHub Pages.
It never places trades or connects to a brokerage.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "signals.json"
STATE_PATH = ROOT / "data" / "state.json"
SEC_BASE = "https://www.sec.gov"
FORM_TYPES = {"4", "4/A"}
COMMON_SECURITY_TERMS = ("common stock", "common shares")
BUY_MINIMUM = Decimal("50000")
SALE_MINIMUM = Decimal("250000")
REQUEST_INTERVAL_SECONDS = 0.26
MAX_HISTORY = 2500
MAX_PROCESSED_ACCESSIONS = 12000
EASTERN = ZoneInfo("America/New_York")


class SecClient:
    def __init__(self, user_agent: str) -> None:
        if "@" not in user_agent:
            raise ValueError("SEC_USER_AGENT must include a contact email address")
        self.user_agent = user_agent
        self._last_request = 0.0

    def get_text(self, url: str, *, allow_not_found: bool = False) -> str | None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < REQUEST_INTERVAL_SECONDS:
            time.sleep(REQUEST_INTERVAL_SECONDS - elapsed)

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/plain, application/xml, text/xml, */*",
            },
        )
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    self._last_request = time.monotonic()
                    return response.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as error:
                self._last_request = time.monotonic()
                if allow_not_found and error.code == 404:
                    return None
                if error.code not in {429, 500, 502, 503, 504}:
                    raise
                last_error = error
            except (urllib.error.URLError, TimeoutError) as error:
                self._last_request = time.monotonic()
                last_error = error
            time.sleep(2**attempt)
        raise RuntimeError(f"SEC request failed after retries: {url}: {last_error}")


def parse_decimal(value: str | None) -> Decimal | None:
    if not value:
        return None
    cleaned = value.replace(",", "").replace("$", "").strip()
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def element_value(parent: ET.Element, path: str) -> str | None:
    element = parent.find(path)
    if element is None or element.text is None:
        return None
    value = element.text.strip()
    return value or None


def parse_master_index(text: str) -> list[dict[str, str]]:
    filings: list[dict[str, str]] = []
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) != 5:
            continue
        cik, company_name, form_type, filed_date, filename = (part.strip() for part in parts)
        if form_type not in FORM_TYPES or not filename.endswith(".txt"):
            continue
        accession = Path(filename).stem
        filings.append(
            {
                "cik": cik,
                "companyName": company_name,
                "form": form_type,
                "filedDate": filed_date,
                "filename": filename,
                "accession": accession,
            }
        )
    return filings


def filing_index_url(filename: str) -> str:
    path = Path(filename.replace("\\", "/"))
    accession = path.stem
    archive_dir = "/".join(path.parts[:-1])
    return f"{SEC_BASE}/Archives/{archive_dir}/{accession.replace('-', '')}/{accession}-index.html"


def complete_submission_url(filename: str) -> str:
    return f"{SEC_BASE}/Archives/{filename.lstrip('/')}"


def extract_ownership_xml(submission: str) -> str | None:
    match = re.search(
        r"(<ownershipDocument(?:\s[^>]*)?>.*?</ownershipDocument>)",
        submission,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1) if match else None


def filing_timestamp(submission: str, fallback_date: str) -> str:
    match = re.search(r"<ACCEPTANCE-DATETIME>(\d{14})", submission, flags=re.IGNORECASE)
    if match:
        parsed = datetime.strptime(match.group(1), "%Y%m%d%H%M%S").replace(tzinfo=EASTERN)
        return parsed.isoformat()
    return datetime.fromisoformat(f"{fallback_date}T00:00:00").replace(tzinfo=EASTERN).isoformat()


def reporting_role(root: ET.Element) -> str:
    relationship = root.find("./reportingOwner/reportingOwnerRelationship")
    if relationship is None:
        return "Reporting person"
    roles: list[str] = []
    if element_value(relationship, "isOfficer") == "1":
        roles.append(element_value(relationship, "officerTitle") or "Officer")
    if element_value(relationship, "isDirector") == "1" and not any("director" in r.lower() for r in roles):
        roles.append("Director")
    if element_value(relationship, "isTenPercentOwner") == "1":
        roles.append("10% owner")
    if element_value(relationship, "isOther") == "1":
        other = element_value(relationship, "otherText")
        if other:
            roles.append(other)
    return " · ".join(roles) if roles else "Reporting person"


def is_common_security(title: str) -> bool:
    normalized = " ".join(title.lower().split())
    return any(term in normalized for term in COMMON_SECURITY_TERMS) and "preferred" not in normalized


def position_change(side: str, shares: Decimal, shares_after: Decimal | None) -> float | None:
    if shares_after is None:
        return None
    prior = shares_after - shares if side == "BUY" else shares_after + shares
    if prior <= 0:
        return None
    change = (shares / prior) * Decimal("100")
    if side == "SELL":
        change = -change
    return round(float(change), 2)


def strength_score(value: Decimal, pct_change: float | None, role: str, side: str) -> int:
    if side != "BUY":
        return 0
    amount = max(float(value), 1.0)
    amount_points = min(55, max(18, round(18 + 12 * math.log10(amount / 50000))))
    pct = abs(pct_change or 0)
    if pct >= 50:
        position_points = 25
    elif pct >= 20:
        position_points = 20
    elif pct >= 10:
        position_points = 15
    elif pct >= 5:
        position_points = 10
    elif pct >= 1:
        position_points = 5
    else:
        position_points = 0
    lowered_role = role.lower()
    role_points = 10 if "chief executive" in lowered_role or "ceo" in lowered_role else 5 if "director" in lowered_role else 0
    return min(100, amount_points + position_points + role_points)


def context_copy(side: str, role: str, value: Decimal, pct_change: float | None) -> tuple[str, str]:
    amount = f"${float(value):,.0f}"
    if side == "BUY":
        if pct_change is None:
            context = f"A reported direct open-market purchase of {amount} by a {role.lower()}; the prior-position change could not be calculated reliably."
        else:
            context = f"A reported direct open-market purchase of {amount} increased the insider's company position by about {pct_change:.1f}%."
        caveat = "The filing reports the transaction, not the insider's reason or total personal portfolio. No market-return history has matured for this automated record."
    else:
        context = f"A reported direct open-market sale of {amount} met the notable-sale threshold."
        caveat = "A sale is not automatically bearish; it may reflect diversification, taxes, liquidity needs, or a prearranged trading plan. Review the filing footnotes."
    return context, caveat


def parse_form4_submission(submission: str, filing: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source = filing_index_url(filing["filename"])
    filed_at = filing_timestamp(submission, filing["filedDate"])
    xml_text = extract_ownership_xml(submission)
    if not xml_text:
        return [], [{"accession": filing["accession"], "form": filing["form"], "filedAt": filed_at, "source": source, "reason": "Ownership XML was not found."}]
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as error:
        return [], [{"accession": filing["accession"], "form": filing["form"], "filedAt": filed_at, "source": source, "reason": f"Ownership XML could not be parsed: {error}."}]

    company = element_value(root, "./issuer/issuerName") or filing["companyName"]
    ticker = element_value(root, "./issuer/issuerTradingSymbol") or "N/A"
    issuer_cik = element_value(root, "./issuer/issuerCik") or ""
    insider = element_value(root, "./reportingOwner/reportingOwnerId/rptOwnerName") or filing["companyName"]
    role = reporting_role(root)

    if filing["form"] == "4/A":
        return [], [{"accession": filing["accession"], "form": filing["form"], "company": company, "ticker": ticker, "insider": insider, "filedAt": filed_at, "source": source, "reason": "Amended Form 4 requires review before it can replace an earlier record."}]

    candidates: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []
    for transaction in root.findall("./nonDerivativeTable/nonDerivativeTransaction"):
        code = element_value(transaction, "./transactionCoding/transactionCode")
        if code not in {"P", "S"}:
            continue
        side = "BUY" if code == "P" else "SELL"
        expected_disposition = "A" if side == "BUY" else "D"
        security_title = element_value(transaction, "./securityTitle/value") or ""
        direct = element_value(transaction, "./ownershipNature/directOrIndirectOwnership/value")
        disposition = element_value(transaction, "./transactionAmounts/transactionAcquiredDisposedCode/value")
        shares = parse_decimal(element_value(transaction, "./transactionAmounts/transactionShares/value"))
        price = parse_decimal(element_value(transaction, "./transactionAmounts/transactionPricePerShare/value"))
        shares_after = parse_decimal(element_value(transaction, "./postTransactionAmounts/sharesOwnedFollowingTransaction/value"))
        trade_date = element_value(transaction, "./transactionDate/value") or filing["filedDate"]

        if not is_common_security(security_title) or direct != "D":
            continue
        if disposition != expected_disposition or shares is None or shares <= 0 or price is None or price <= 0:
            review.append({"accession": filing["accession"], "form": filing["form"], "company": company, "ticker": ticker, "insider": insider, "filedAt": filed_at, "source": source, "reason": "A direct open-market transaction had missing or inconsistent shares, price, or acquisition/disposition data."})
            continue
        value = shares * price
        threshold = BUY_MINIMUM if side == "BUY" else SALE_MINIMUM
        if value < threshold:
            continue
        candidates.append(
            {
                "side": side,
                "code": code,
                "securityTitle": security_title,
                "tradeDate": trade_date,
                "shares": shares,
                "price": price,
                "value": value,
                "sharesAfter": shares_after,
            }
        )

    records: list[dict[str, Any]] = []
    for side in ("BUY", "SELL"):
        grouped = [item for item in candidates if item["side"] == side]
        if not grouped:
            continue
        total_shares = sum((item["shares"] for item in grouped), Decimal("0"))
        total_value = sum((item["value"] for item in grouped), Decimal("0"))
        average_price = total_value / total_shares
        last_transaction = sorted(grouped, key=lambda item: item["tradeDate"])[-1]
        shares_after = last_transaction["sharesAfter"]
        pct_change = position_change(side, total_shares, shares_after)
        score = strength_score(total_value, pct_change, role, side)
        context, caveat = context_copy(side, role, total_value, pct_change)
        records.append(
            {
                "id": f"{filing['accession']}-{side.lower()}",
                "accession": filing["accession"],
                "form": filing["form"],
                "issuerCik": issuer_cik,
                "ticker": ticker.upper(),
                "company": company,
                "insider": insider,
                "role": role,
                "side": side,
                "transactionCode": "P" if side == "BUY" else "S",
                "transactionDate": last_transaction["tradeDate"],
                "filedAt": filed_at,
                "shares": round(float(total_shares), 6),
                "price": round(float(average_price), 6),
                "value": round(float(total_value), 2),
                "sharesAfter": round(float(shares_after), 6) if shares_after is not None else None,
                "positionChange": pct_change,
                "securityTitle": last_transaction["securityTitle"],
                "directOwnership": True,
                "strength": score,
                "trust": None,
                "trustN": 0,
                "move5d": None,
                "source": source,
                "context": context,
                "caveat": caveat,
                "dataStatus": "automated-public-filing",
            }
        )
    return records, review


def daily_index_url(day: date) -> str:
    quarter = (day.month - 1) // 3 + 1
    return f"{SEC_BASE}/Archives/edgar/daily-index/{day.year}/QTR{quarter}/master.{day:%Y%m%d}.idx"


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def date_sequence(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", help="Override the collection end date (YYYY-MM-DD).")
    parser.add_argument("--lookback-days", type=int, default=4, help="Days to overlap before the last successful run.")
    parser.add_argument("--user-agent", default=os.environ.get("SEC_USER_AGENT", "PlainSight public filing research mohammedborhan0480@gmail.com"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    as_of = date.fromisoformat(args.as_of) if args.as_of else datetime.now(EASTERN).date()
    state = load_json(STATE_PATH, {"lastSuccessfulDate": as_of.isoformat(), "processedAccessions": []})
    data = load_json(DATA_PATH, {"transactions": [], "reviewNeeded": []})
    last_success = date.fromisoformat(state.get("lastSuccessfulDate", as_of.isoformat()))
    start = min(as_of, last_success) - timedelta(days=max(1, args.lookback_days))
    prior_processed = state.get("processedAccessions", [])
    processed = set(prior_processed)
    client = SecClient(args.user_agent)

    new_records: list[dict[str, Any]] = []
    new_review: list[dict[str, Any]] = []
    encountered: list[str] = []
    encountered_set: set[str] = set()
    index_days_found = 0
    submission_failures = 0

    for day in date_sequence(start, as_of):
        index_text = client.get_text(daily_index_url(day), allow_not_found=True)
        if index_text is None:
            continue
        index_days_found += 1
        for filing in parse_master_index(index_text):
            accession = filing["accession"]
            if accession in processed or accession in encountered_set:
                continue
            try:
                submission = client.get_text(complete_submission_url(filing["filename"]))
                if submission is None:
                    raise RuntimeError("complete submission was not returned")
                records, warnings = parse_form4_submission(submission, filing)
                new_records.extend(records)
                new_review.extend(warnings)
                encountered.append(accession)
                encountered_set.add(accession)
            except Exception as error:  # retain for a later retry instead of losing the filing
                submission_failures += 1
                print(f"warning: {accession} could not be processed: {error}", file=sys.stderr)

    if submission_failures and not encountered:
        raise RuntimeError("No Form 4 submissions were processed successfully; state was not advanced.")

    existing_records = data.get("transactions", [])
    replaced_accessions = {record["accession"] for record in new_records}
    merged = [record for record in existing_records if record.get("accession") not in replaced_accessions]
    merged.extend(new_records)
    merged.sort(key=lambda item: item.get("filedAt", ""), reverse=True)
    unique_records: dict[str, dict[str, Any]] = {}
    for record in merged:
        unique_records.setdefault(record["id"], record)
    merged = list(unique_records.values())[:MAX_HISTORY]

    existing_review = data.get("reviewNeeded", [])
    warning_accessions = {item["accession"] for item in new_review}
    merged_review = [item for item in existing_review if item.get("accession") not in warning_accessions]
    merged_review.extend(new_review)
    merged_review.sort(key=lambda item: item.get("filedAt", ""), reverse=True)
    unique_review: dict[str, dict[str, Any]] = {}
    for warning in merged_review:
        unique_review.setdefault(warning["accession"], warning)
    merged_review = list(unique_review.values())[:200]

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    buys = [record for record in merged if record.get("side") == "BUY"]
    sales = [record for record in merged if record.get("side") == "SELL"]
    payload = {
        "schemaVersion": 1,
        "generatedAt": now,
        "lastCheckedDate": as_of.isoformat(),
        "automation": {
            "stage": 1,
            "status": "active",
            "source": "SEC EDGAR public filings",
            "schedule": "Weekdays after 10:00 p.m. America/New_York",
            "emailDelivery": False,
            "note": "Automated SEC collection began August 16, 2026; earlier records are an archived research seed.",
        },
        "filters": {
            "purchaseMinimumUsd": float(BUY_MINIMUM),
            "saleMinimumUsd": float(SALE_MINIMUM),
            "transactionCodes": ["P", "S"],
            "directOwnershipOnly": True,
            "nonDerivativeOnly": True,
        },
        "stats": {
            "totalRecords": len(merged),
            "purchases": len(buys),
            "sales": len(sales),
            "reviewNeeded": len(merged_review),
            "newThisRun": len(new_records),
            "indexDaysChecked": index_days_found,
        },
        "transactions": merged,
        "reviewNeeded": merged_review,
        "notice": "Public filing research only. Filings may be delayed or amended. This is not financial advice and no orders are executed.",
    }
    write_json(DATA_PATH, payload)

    ordered_processed = list(dict.fromkeys([*prior_processed, *encountered]))[-MAX_PROCESSED_ACCESSIONS:]
    write_json(
        STATE_PATH,
        {
            "schemaVersion": 1,
            "lastSuccessfulDate": as_of.isoformat(),
            "lastSuccessfulAt": now,
            "processedAccessions": ordered_processed,
        },
    )
    print(json.dumps(payload["stats"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
