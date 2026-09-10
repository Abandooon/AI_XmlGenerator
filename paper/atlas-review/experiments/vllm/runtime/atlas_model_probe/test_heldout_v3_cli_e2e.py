from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evaluate_asw_v3_run import evaluate


ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "run_phase12_case.py"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class HeldoutV3RealCliE2ETests(unittest.TestCase):
    def test_reviewed_full_case_runs_with_exact_types_and_zero_external_calls(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            run_root = Path(raw) / "heldout-full"
            environment = os.environ.copy()
            environment["LLM_API_KEY"] = "offline-local-placeholder"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(RUNNER),
                    "--cohort",
                    "heldout",
                    "--case-id",
                    "ASW-HO-FULL-02",
                    "--model",
                    "gpt-5.6-luna",
                    "--repetition",
                    "3",
                    "--repair-mode",
                    "off",
                    "--offline-scripted",
                    "--run-root",
                    str(run_root),
                ],
                cwd=ROOT,
                env=environment,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=180,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)

            summary = json.loads(
                (run_root / "run_summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual("heldout", summary["cohort"])
            self.assertEqual("EXTENSION", summary["structural_role"])
            self.assertEqual(0, summary["external_model_api_calls"])
            self.assertEqual(3, summary["offline_scripted_provider_call_count"])
            self.assertEqual("PASS", summary["phase2"]["raw_provider_schema_status"])
            self.assertEqual(
                "NOT_APPLICABLE", summary["phase2"]["normalization_status"]
            )
            self.assertEqual("PASS", summary["phase2"]["artifact_profile_decision"])
            self.assertEqual(0, summary["phase2"]["validation_summary"]["FAIL"])
            self.assertEqual(0, summary["phase2"]["validation_summary"]["ERROR"])
            self.assertGreater(
                summary["phase2"]["validation_summary"]["NOT_EVALUATED"], 0
            )

            provenance = summary["phase2"]["provider_payload_provenance"]
            self.assertEqual({"component", "interfaces"}, {p["scope"] for p in provenance})
            for item in provenance:
                self.assertEqual("PASS", item["raw_provider_schema_status"])
                self.assertEqual("NOT_APPLICABLE", item["normalization_status"])
                self.assertEqual("PASS", item["final_atlas_status"])
                raw_payload = Path(item["raw_provider_payload"]["path"])
                self.assertTrue(raw_payload.is_file())
                self.assertEqual(
                    item["raw_provider_payload"]["file_sha256"], _sha256(raw_payload)
                )

            for response in summary["phase2"]["provider_responses"]:
                self.assertFalse(response["actual_paid_provider_call"])
                self.assertEqual(1, response["max_attempts"])
                self.assertEqual(180.0, response["request_timeout_seconds"])
                self.assertEqual("gpt-5.6-luna", response["requested_model"])
                self.assertEqual(64, len(response["provider_endpoint_sha256"]))

            outputs = [Path(path) for path in summary["phase2"]["output_files"]]
            component = next(
                path for path in outputs if path.suffix == ".arxml" and "Components" in path.parts
            )
            interfaces = [
                path for path in outputs if path.suffix == ".arxml" and "Interfaces" in path.parts
            ]
            validation = next(
                path
                for path in outputs
                if path.name.startswith("validation_")
                and not path.name.startswith("validation_context_")
            )
            independent = evaluate(
                case_id="ASW-HO-FULL-02",
                component_path=component,
                interface_paths=interfaces,
                validation_path=validation,
                cohort="heldout",
            )
            self.assertEqual("PASS", independent["decision"])
            self.assertTrue(independent["promotable"])
            self.assertEqual(0, independent["structural_failure_count"])
            self.assertEqual(0, independent["local_reference_failure_count"])
            self.assertEqual(0, independent["external_reference_not_evaluated_count"])
            self.assertTrue(all(item["status"] == "PASS" for item in independent["xsd"]))

            type_refs = {
                tuple(item["actual"])
                for item in independent["structural_obligations"]
                if item["code"] == "interface_data_type_ref"
            }
            self.assertEqual(
                {("/DataTypes/Impl_Float32",), ("/DataTypes/Impl_UInt8",)},
                type_refs,
            )
            self.assertTrue(
                all(
                    item["target"].startswith("/ComponentInterfaces/")
                    for item in independent["reference_integrity"]
                    if item["tag"] != "TYPE-TREF"
                    and item["target"].startswith("/ComponentInterfaces/")
                )
            )


if __name__ == "__main__":
    unittest.main()
