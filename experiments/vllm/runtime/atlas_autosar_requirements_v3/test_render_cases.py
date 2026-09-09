from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from render_cases import (
    DEFAULT_SOURCE,
    ManifestError,
    load_manifest,
    render_all,
    render_prompt,
    validate_manifest,
)


class ManifestValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_manifest(DEFAULT_SOURCE)

    def test_source_manifest_is_consistent(self) -> None:
        result = validate_manifest(self.manifest)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["case_count"], 20)
        self.assertEqual(result["run_count"], 60)
        self.assertEqual(
            result["tier_counts"],
            {"minimal": 6, "standard": 7, "full": 7},
        )

    def test_duplicate_case_id_fails_closed(self) -> None:
        broken = copy.deepcopy(self.manifest)
        broken["cases"][1]["case_id"] = broken["cases"][0]["case_id"]
        with self.assertRaisesRegex(ManifestError, "duplicate_or_empty_case_id"):
            validate_manifest(broken)

    def test_read_without_required_port_fails_closed(self) -> None:
        broken = copy.deepcopy(self.manifest)
        standard = next(case for case in broken["cases"] if case["tier"] == "standard")
        standard["internal_behavior"]["runnables"][0]["reads"] = ["HCU02_Poweroff"]
        with self.assertRaisesRegex(ManifestError, "read_without_r_port"):
            validate_manifest(broken)

    def test_expected_count_mismatch_fails_closed(self) -> None:
        broken = copy.deepcopy(self.manifest)
        broken["cases"][0]["expected_counts"]["p_ports"] = 2
        with self.assertRaisesRegex(ManifestError, "expected_count_mismatch"):
            validate_manifest(broken)

    def test_missing_authoritative_init_value_fails_closed(self) -> None:
        broken = copy.deepcopy(self.manifest)
        del broken["authoritative_context"]["unconnected_required_port_init_value"]
        with self.assertRaisesRegex(
            ManifestError, "invalid_unconnected_required_port_init_value"
        ):
            validate_manifest(broken)


class RenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_manifest(DEFAULT_SOURCE)

    def test_prompt_is_deterministic(self) -> None:
        case = self.manifest["cases"][13]
        self.assertEqual(
            render_prompt(self.manifest, case),
            render_prompt(copy.deepcopy(self.manifest), copy.deepcopy(case)),
        )

    def test_minimal_prompt_forbids_internal_behavior(self) -> None:
        prompt = render_prompt(self.manifest, self.manifest["cases"][0])
        self.assertIn("Do not create an SWC-INTERNAL-BEHAVIOR", prompt)
        self.assertIn("Exactly 1 P ports, 0 R ports", prompt)
        self.assertNotIn("INIT-VALUE", prompt)
        self.assertNotIn("NONQUEUED-RECEIVER-COM-SPEC", prompt)

    def test_standard_prompt_distinguishes_read_and_write_access(self) -> None:
        prompt = render_prompt(self.manifest, self.manifest["cases"][6])
        self.assertIn("DATA-RECEIVE-POINT-BY-ARGUMENTS VARIABLE-ACCESS", prompt)
        self.assertIn("DATA-SEND-POINTS VARIABLE-ACCESS", prompt)
        self.assertIn("NONQUEUED-RECEIVER-COM-SPEC", prompt)
        self.assertIn(
            "INIT-VALUE/NUMERICAL-VALUE-SPECIFICATION/VALUE=0", prompt
        )
        self.assertIn("every listed R-PORT-PROTOTYPE is unconnected", prompt)

    def test_full_prompt_assigns_reproducible_event_and_access_identities(self) -> None:
        case = next(
            item for item in self.manifest["cases"] if item["case_id"] == "ASW-FULL-06"
        )
        prompt = render_prompt(self.manifest, case)
        self.assertIn("TIMING-EVENT TE_Com_Torque", prompt)
        self.assertIn(
            "VARIABLE-ACCESS VA_Com_Torque_Read_HCU01_TqCmd", prompt
        )
        self.assertIn(
            "VARIABLE-ACCESS VA_Com_Torque_Write_MCU02_MaxTor", prompt
        )

    def test_minimal_required_port_carries_numeric_init_value(self) -> None:
        case = next(
            item
            for item in self.manifest["cases"]
            if item["case_id"] == "ASW-MIN-04"
        )
        prompt = render_prompt(self.manifest, case)
        self.assertIn(
            "INIT-VALUE/NUMERICAL-VALUE-SPECIFICATION/VALUE=0", prompt
        )

    def test_render_all_writes_twenty_prompts_and_sixty_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = render_all(DEFAULT_SOURCE, Path(temp_dir))
            self.assertEqual(result["prompt_count"], 20)
            self.assertEqual(result["run_count"], 60)
            self.assertEqual(len(list((Path(temp_dir) / "prompts").glob("*.txt"))), 20)
            self.assertTrue((Path(temp_dir) / "run_manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
