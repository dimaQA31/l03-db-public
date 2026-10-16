"""Offline regression checks for the assembled set and its cheapest assertions."""

import unittest
from pathlib import Path
from unittest.mock import patch

from assertions import NAME_TO_LEVEL
from generate_golden import golden_cases
from loader import load
from runner import evaluate

HERE = Path(__file__).resolve().parent


def passes(case, answer):
    return evaluate(case, [{"answer": answer, "trace": {}}]).passed


class GoldenTests(unittest.TestCase):
    def setUp(self):
        self.rows = list(golden_cases())
        self.cases = {c["id"]: c for c in self.rows}

    def test_saved_set_and_every_level_explained(self):
        self.assertEqual(self.rows, load(HERE / "golden.jsonl"))
        self.assertGreaterEqual(len(self.rows), 30)
        self.assertLessEqual(len(self.rows), 40)
        own = [c for c in self.rows if c["additional_metadata"]["added_in"] == "hw2"]
        self.assertGreaterEqual(len(own), 15)
        self.assertLessEqual(sum(c["additional_metadata"]["oracle"] == "human" for c in own), 5)
        self.assertEqual(len(self.cases), len(self.rows))
        for case in self.rows:
            meta = case["additional_metadata"]
            self.assertTrue(meta["why_this_level"])
            self.assertEqual(meta["check_level"], NAME_TO_LEVEL[meta["assertion"]])
            self.assertIn(meta["severity"], ("low", "medium", "high", "critical"))
        self.assertTrue({1, 2, 3, 4, 7} <= {c["additional_metadata"]["check_level"] for c in self.rows})
        self.assertTrue({"FX-006", "FX-007", "FX-008", "FX-009", "FX-010", "FX-011"} <= self.cases.keys())

    def test_eligibility_negation_and_wrong_spread_fail(self):
        case = self.cases["DIS2-001-inside"]
        self.assertTrue(passes(case, "ELIGIBLE"))
        self.assertFalse(passes(case, "not eligible"))
        self.assertFalse(passes(case, "INELIGIBLE"))
        case = self.cases["DIS2-001-outside"]
        self.assertTrue(passes(case, "INELIGIBLE"))
        self.assertFalse(passes(case, "ELIGIBLE"))
        for cid in ("FX-007-S", "FX2-004-above-S"):
            self.assertTrue(passes(self.cases[cid], "0.9%"))
            self.assertFalse(passes(self.cases[cid], "10.9%"))
        self.assertTrue(passes(self.cases["FX-006-S"], "0%"))

    def test_negative_guards_allow_negation_and_reject_affirmative_promises(self):
        case = self.cases["DIS-002-N"]
        self.assertTrue(passes(case, "You cannot dispute it; it is not eligible."))
        self.assertFalse(passes(case, "You can still dispute it."))

    def test_monthly_remainder_uses_seed_spending(self):
        case = self.cases["LIM-002"]
        self.assertEqual(case["additional_metadata"]["expected_number"], 48745.10)
        self.assertTrue(passes(case, "Your monthly remainder is EUR 48,745.10."))
        self.assertFalse(passes(case, "Your monthly remainder is EUR 50,000."))
        self.assertFalse(passes(case, "Your monthly remainder is EUR 5,000."))

    def test_four_semantic_human_rubrics_use_judge_without_live_calls(self):
        cases = [c for c in self.rows if c["id"].startswith("HUM-") and c["additional_metadata"]["assertion"] == "judge"]
        self.assertEqual(len(cases), 4)
        for case in cases:
            meta = case["additional_metadata"]
            self.assertEqual(meta["oracle"], "human")
            self.assertEqual(meta["human_review_status"], "pending")
            self.assertIn("PASS", meta["rubric"])
            self.assertIn("FAIL", meta["rubric"])
            with patch("runner._judge", return_value=(False, "rubric failed")) as fake:
                self.assertFalse(passes(case, "Dismissive response."))
                fake.assert_called_once_with(case["input"], "Dismissive response.", meta["rubric"])


if __name__ == "__main__":
    unittest.main()
