from __future__ import annotations

import unittest

from tests_v2.test_constraint_neo4j_model import ConstraintNeo4jModelTests


class ManualReviewNeo4jProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ConstraintNeo4jModelTests.setUpClass()
        cls.projection = ConstraintNeo4jModelTests.projection

    def test_manual_review_decision_is_published_on_constraint_node(self) -> None:
        record = next(
            item for item in self.projection["constraints"]
            if item["constraint_id"] == "TPS_SWCT_01000"
        )
        props = record["props"]
        self.assertEqual("retain_manual", props["manual_review_decision"])
        self.assertEqual("generated_artifact", props["manual_required_capability"])
        self.assertTrue(props["partial_arxml_guard"])
        self.assertTrue(props["manual_review_reason"])
        self.assertEqual(51, self.projection["dataset"]["props"]["manual_review_count"])


if __name__ == "__main__":
    unittest.main()
