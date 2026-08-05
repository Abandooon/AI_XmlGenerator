from __future__ import annotations

import json
import unittest
from pathlib import Path


class ManualReviewPlanTests(unittest.TestCase):
    def test_all_manual_constraints_have_a_reviewed_disposition(self) -> None:
        root = Path(__file__).resolve().parents[1]
        review = json.loads(
            (root / "src/generate_formal_constraints/v2/manual_review_plan.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(51, review["count"])
        self.assertEqual(51, len(review["reviews"]))
        self.assertTrue(all(item["decision"] == "retain_manual" for item in review["reviews"]))
        partial = {item["constraint_id"] for item in review["reviews"] if item["partial_arxml_guard"]}
        self.assertEqual({
            "TPS_SWCT_01000", "TPS_SWCT_01001", "TPS_SWCT_01040",
            "TPS_SWCT_01511", "TPS_SWCT_01512", "TPS_SWCT_01513",
        }, partial)

    def test_validation_plan_embeds_same_manual_review(self) -> None:
        root = Path(__file__).resolve().parents[1]
        v2 = root / "src/generate_formal_constraints/v2"
        review = json.loads((v2 / "manual_review_plan.json").read_text(encoding="utf-8"))
        plan = json.loads((v2 / "validation_plan.json").read_text(encoding="utf-8"))
        self.assertEqual(review, plan["manual_review"])


if __name__ == "__main__":
    unittest.main()
