from __future__ import annotations

import copy
import unittest

from summarize_heldout_v3 import source_cases, summarize


def results_fixture() -> dict:
    cases = source_cases()
    runs = []
    records = []
    model = "gpt-5.6-luna"
    for case_id in cases:
        for repetition, seed in enumerate((104729, 130363, 155921), start=1):
            run_id = f"{model}__{case_id}-R{repetition}__repair-off"
            runs.append(
                {
                    "run_id": run_id,
                    "model": model,
                    "case_id": case_id,
                    "repetition": repetition,
                    "seed": seed,
                }
            )
            records.append(
                {
                    "run_id": run_id,
                    "status": "COMPLETE",
                    "independent_decision": "PASS",
                }
            )
    return {
        "content_sha256": "a" * 64,
        "schedule": {
            "cohort": "prospective_internally_authored_heldout_v3",
            "heldout_source_sha256": "78dc6d65672d896af3c19b50a5efbf5ca18d8237de9f32f2b7234cd6ff226945",
            "models": [model],
            "runs": runs,
        },
        "records": records,
    }


class HeldoutV3SummaryTests(unittest.TestCase):
    def test_all_pass_summary_keeps_strata_cells_and_pooling_labels(self) -> None:
        summary = summarize(results_fixture())
        row = summary["models"]["gpt-5.6-luna"]
        self.assertEqual(6, row["structural_strata"]["REPLICATION"]["case_count"])
        self.assertEqual(6, row["structural_strata"]["EXTENSION"]["case_count"])
        self.assertEqual(6, len(row["tier_by_structural_role_cells"]))
        self.assertTrue(all(item["case_count"] == 2 for item in row["tier_by_structural_role_cells"].values()))
        self.assertTrue(row["run_level_interval_prohibited"])
        self.assertNotIn("run_pass_rate_wilson_95", row)
        self.assertEqual(12, row["pooled_balanced_mixture_descriptive"]["strict_3_of_3_pass_cases"])

    def test_one_failed_seed_changes_one_case_not_three_independent_units(self) -> None:
        fixture = results_fixture()
        fixture["records"][0]["independent_decision"] = "FAIL"
        summary = summarize(fixture)
        row = summary["models"]["gpt-5.6-luna"]
        self.assertEqual(35, row["run_pass_count_diagnostic"])
        self.assertEqual(11, row["pooled_balanced_mixture_descriptive"]["strict_3_of_3_pass_cases"])
        self.assertEqual(5, row["structural_strata"]["REPLICATION"]["strict_3_of_3_pass_cases"])

    def test_duplicate_seed_is_refused(self) -> None:
        fixture = results_fixture()
        fixture["schedule"]["runs"][1]["seed"] = 104729
        with self.assertRaisesRegex(ValueError, "repetitions/seeds"):
            summarize(fixture)

    def test_unknown_case_is_refused(self) -> None:
        fixture = results_fixture()
        fixture["schedule"]["runs"][0]["case_id"] = "ASW-HO-UNKNOWN"
        with self.assertRaisesRegex(ValueError, "unknown case"):
            summarize(fixture)

    def test_missing_record_is_refused(self) -> None:
        fixture = results_fixture()
        fixture["records"].pop()
        with self.assertRaisesRegex(ValueError, "exactly cover"):
            summarize(fixture)

    def test_wrong_cohort_identity_is_refused(self) -> None:
        fixture = results_fixture()
        fixture["schedule"]["cohort"] = "primary"
        with self.assertRaisesRegex(ValueError, "not bound"):
            summarize(fixture)


if __name__ == "__main__":
    unittest.main()
