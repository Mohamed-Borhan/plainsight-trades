from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from update_sec import filing_index_url, parse_form4_submission, parse_master_index  # noqa: E402


class Form4CollectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_dir = ROOT / "tests" / "fixtures"
        self.filing = {
            "cik": "123456",
            "companyName": "Fallback name",
            "form": "4",
            "filedDate": "2026-08-14",
            "filename": "edgar/data/123456/0000123456-26-000001.txt",
            "accession": "0000123456-26-000001",
        }

    def test_master_index_keeps_only_form_4(self) -> None:
        text = "Header\n-----\n123|One|4|2026-08-14|edgar/data/123/a.txt\n456|Two|10-K|2026-08-14|edgar/data/456/b.txt\n789|Three|4/A|2026-08-14|edgar/data/789/c.txt\n"
        result = parse_master_index(text)
        self.assertEqual([item["form"] for item in result], ["4", "4/A"])

    def test_same_accession_can_be_identified_across_duplicate_index_rows(self) -> None:
        text = "123|One|4|2026-08-14|edgar/data/123/0000123456-26-000001.txt\n123|One joint filer|4|2026-08-14|edgar/data/123/0000123456-26-000001.txt\n"
        result = parse_master_index(text)
        self.assertEqual(result[0]["accession"], result[1]["accession"])

    def test_purchase_is_aggregated_and_position_change_is_calculated(self) -> None:
        submission = (self.fixture_dir / "purchase-form4.txt").read_text(encoding="utf-8")
        records, warnings = parse_form4_submission(submission, self.filing)
        self.assertEqual(warnings, [])
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["ticker"], "EXMP")
        self.assertEqual(record["side"], "BUY")
        self.assertEqual(record["value"], 100000.0)
        self.assertEqual(record["positionChange"], 50.0)
        self.assertIn("Chief Executive Officer", record["role"])

    def test_indirect_and_preferred_transactions_are_excluded(self) -> None:
        filing = dict(self.filing, filename="edgar/data/123456/0000123456-26-000002.txt", accession="0000123456-26-000002")
        submission = (self.fixture_dir / "excluded-form4.txt").read_text(encoding="utf-8")
        records, warnings = parse_form4_submission(submission, filing)
        self.assertEqual(records, [])
        self.assertEqual(warnings, [])

    def test_amendment_is_sent_to_review(self) -> None:
        filing = dict(self.filing, form="4/A")
        submission = (self.fixture_dir / "purchase-form4.txt").read_text(encoding="utf-8")
        records, warnings = parse_form4_submission(submission, filing)
        self.assertEqual(records, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("Amended Form 4", warnings[0]["reason"])

    def test_official_index_url_has_accession_directory(self) -> None:
        self.assertEqual(
            filing_index_url(self.filing["filename"]),
            "https://www.sec.gov/Archives/edgar/data/123456/000012345626000001/0000123456-26-000001-index.html",
        )


if __name__ == "__main__":
    unittest.main()
