from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_trust_scores import aggregate_rows, confidence_band  # noqa: E402


class TrustScoreTests(unittest.TestCase):
    def test_duplicate_same_session_filings_count_as_one_episode(self) -> None:
        base = {
            "direction": "BUY",
            "mature": "True",
            "RPTOWNERCIK": "123",
            "ISSUERCIK": "456",
            "RPTOWNERNAME": "TEST PERSON",
            "RPTOWNER_TITLE": "CEO",
            "filing_date": "2020-01-01",
        }
        rows = []
        for entry_date, excess in (("2020-01-02", ".10"), ("2020-01-02", ".10"), ("2020-05-02", ".05"), ("2020-09-02", "-.02")):
            rows.append({**base, "entry_date": entry_date, "follower_excess_return": excess})
        result = aggregate_rows(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sampleSize"], 3)
        self.assertEqual(result[0]["confidence"], "Provisional")

    def test_small_samples_are_not_published(self) -> None:
        rows = [
            {
                "direction": "BUY",
                "mature": "True",
                "RPTOWNERCIK": "123",
                "ISSUERCIK": "456",
                "RPTOWNERNAME": "TEST PERSON",
                "RPTOWNER_TITLE": "CEO",
                "filing_date": "2020-01-01",
                "entry_date": f"2020-01-0{index + 2}",
                "follower_excess_return": ".10",
            }
            for index in range(2)
        ]
        self.assertEqual(aggregate_rows(rows), [])

    def test_confidence_depends_on_sample_not_score(self) -> None:
        self.assertEqual(confidence_band(3), "Provisional")
        self.assertEqual(confidence_band(7), "Developing")
        self.assertEqual(confidence_band(12), "Established")


if __name__ == "__main__":
    unittest.main()
