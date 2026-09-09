from __future__ import annotations

import unittest

from build_requirement_contract_smoke_manifest import build_manifest


class RequirementContractSmokeManifestTests(unittest.TestCase):
    def test_manifest_is_deterministic_and_never_ranks_partial_cohort(self):
        first = build_manifest()
        second = build_manifest()
        self.assertEqual(first, second)
        self.assertFalse(first["ranking"]["permitted"])
        self.assertEqual("PASS", first["models"]["gpt-5.6-terra"]["model_quality_decision"])
        self.assertEqual(
            "NOT_EVALUATED",
            first["models"]["gpt-5.6-sol"]["model_quality_decision"],
        )
        self.assertEqual(
            61,
            first["models"]["gpt-5.6-sol"]["phase1_machine_contract"][
                "applied_obligation_count"
            ],
        )


if __name__ == "__main__":
    unittest.main()
