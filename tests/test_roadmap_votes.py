from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_roadmap_votes import aggregate_votes, parse_vote  # noqa: E402


class RoadmapVoteTests(unittest.TestCase):
    def test_issue_form_selection_is_parsed(self) -> None:
        body = "### What should PlainSight build next?\n\nValidated Trust Meter\n\n### Optional note\n\nMore confidence context."
        self.assertEqual(parse_vote(body), "trust-meter")

    def test_latest_vote_per_account_wins(self) -> None:
        issues = [
            {
                "title": "[Roadmap vote] first",
                "body": "### What should PlainSight build next?\n\nValidated Trust Meter",
                "user": {"login": "student"},
                "updated_at": "2026-10-01T00:00:00Z",
            },
            {
                "title": "[Roadmap vote] changed",
                "body": "### What should PlainSight build next?\n\nClean and explain the review queue",
                "user": {"login": "Student"},
                "updated_at": "2026-10-02T00:00:00Z",
            },
        ]
        payload = aggregate_votes(issues)
        self.assertEqual(payload["totalVotes"], 1)
        counts = {option["id"]: option["votes"] for option in payload["options"]}
        self.assertEqual(counts["review-queue"], 1)
        self.assertEqual(counts["trust-meter"], 0)


if __name__ == "__main__":
    unittest.main()
