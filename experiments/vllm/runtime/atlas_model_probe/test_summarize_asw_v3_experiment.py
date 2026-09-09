from __future__ import annotations

import unittest

from summarize_asw_v3_experiment import markdown, summarize, wilson


def record(model: str, case_id: str, repetition: int, *, passed: bool = True, status: str = "COMPLETE") -> dict:
    return {
        "model": model,
        "case_id": case_id,
        "repetition": repetition,
        "tier": "minimal",
        "status": status,
        "independent_decision": "PASS" if passed else "FAIL",
        "xsd_all_pass": passed,
        "artifact_profile_decision": "PASS" if passed else "FAIL",
        "full_corpus_decision": "INCOMPLETE",
        "total_tokens": 100,
        "total_duration_seconds": 2.0,
    }


class AswV3SummaryTests(unittest.TestCase):
    def test_rates_stability_and_hash_are_reproducible(self):
        records = []
        for case_id in ("C1", "C2"):
            for repetition in (1, 2, 3):
                records.append(record("luna", case_id, repetition))
        source = {
            "content_sha256": "a" * 64,
            "schedule": {"models": ["luna"]},
            "records": records,
        }
        first = summarize(source)
        second = summarize(source)
        self.assertEqual(first, second)
        self.assertEqual(
            2, first["models"]["luna"]["case_all_repetitions_pass_count"]
        )
        self.assertEqual(
            1.0, first["models"]["luna"]["case_all_repetitions_pass_rate"]
        )
        self.assertFalse(first["study_design"]["cross_model_comparison_performed"])
        self.assertEqual(64, len(first["content_sha256"]))
        self.assertIn("Stable cases", markdown(first))

    def test_partial_luna_cohort_is_not_complete(self):
        source = {
            "content_sha256": "b" * 64,
            "schedule": {"models": ["luna"]},
            "records": [
                record("luna", "C1", 1),
                record("luna", "C1", 2, status="PIPELINE_TIMEOUT"),
                record("luna", "C1", 3),
            ],
        }
        summary = summarize(source)
        self.assertFalse(summary["models"]["luna"]["cohort_complete"])
        self.assertFalse(summary["study_design"]["cross_model_comparison_performed"])

    def test_terminal_generation_failure_remains_in_pass_rate_denominator(self):
        failed = record(
            "luna", "C1", 2, passed=False, status="TERMINAL_FAILURE"
        )
        failed["independent_decision"] = None
        failed["xsd_all_pass"] = None
        source = {
            "content_sha256": "b" * 64,
            "schedule": {"models": ["luna"]},
            "records": [
                record("luna", "C1", 1),
                failed,
                record("luna", "C1", 3),
            ],
        }
        row = summarize(source)["models"]["luna"]
        self.assertTrue(row["cohort_complete"])
        self.assertEqual(3, row["terminal_observations"])
        self.assertEqual(1, row["terminal_generation_failures"])
        self.assertAlmostEqual(2 / 3, row["run_pass_rate"])
        self.assertEqual(0, row["case_all_repetitions_pass_count"])
        self.assertEqual(
            {"PASS": 2, "FAIL": 0, "NOT_EVALUATED": 1},
            row["xsd_status_counts"],
        )

    def test_xsd_counters_explicitly_cover_pass_fail_and_not_evaluated(self):
        passed = record("luna", "C1", 1)
        failed = record("luna", "C1", 2, passed=False)
        not_evaluated = record(
            "luna", "C1", 3, passed=False, status="TERMINAL_FAILURE"
        )
        not_evaluated["independent_decision"] = None
        not_evaluated["xsd_all_pass"] = None
        source = {
            "content_sha256": "c" * 64,
            "schedule": {"models": ["luna"]},
            "records": [passed, failed, not_evaluated],
        }
        row = summarize(source)["models"]["luna"]
        self.assertEqual(
            {"PASS": 1, "FAIL": 1, "NOT_EVALUATED": 1},
            row["xsd_status_counts"],
        )
        self.assertEqual(1, row["xsd_all_pass_runs"])
        self.assertEqual(1, row["xsd_fail_runs"])
        self.assertEqual(1, row["xsd_not_evaluated_runs"])

    def test_interval_and_exact_test_boundaries(self):
        self.assertIsNone(wilson(0, 0))
        low, high = wilson(5, 10)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)


if __name__ == "__main__":
    unittest.main()
