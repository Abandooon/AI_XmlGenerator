from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from offline_v17_e2e import DEFAULT_REFERENCE_MANIFEST
from run_asw_v3_repair_experiment import sha256_file


ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "offline_v17_e2e.py"


class OfflineV17FullContextE2ETests(unittest.TestCase):
    def test_real_cli_failure_repair_interrupt_resume_and_registry(self):
        self.assertTrue(DEFAULT_REFERENCE_MANIFEST.is_file())
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            e2e_root = Path(raw) / "e2e"
            command = [
                sys.executable,
                "-B",
                str(RUNNER),
                "--root",
                str(e2e_root),
                "--controlled-reference-manifest",
                str(DEFAULT_REFERENCE_MANIFEST),
            ]
            interrupted = subprocess.run(
                [*command, "--stop-after-upstream"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=180,
                check=False,
            )
            self.assertEqual(75, interrupted.returncode, interrupted.stderr)
            state = json.loads(
                (e2e_root / "e2e_state.json").read_text(encoding="utf-8")
            )
            self.assertEqual("UPSTREAM_REPAIRED_DURABLE", state["stage"])
            upstream_audit = (
                Path(state["upstream_repaired"]["run_root"])
                / "provider_calls.jsonl"
            )
            audit_before_resume = sha256_file(upstream_audit)
            self.assertEqual(3, state["upstream_repaired"]["provider_call_count"])

            resumed = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=180,
                check=False,
            )
            self.assertEqual(0, resumed.returncode, resumed.stderr)
            manifest = json.loads(
                (e2e_root / "offline_v17_e2e_manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual("PASS", manifest["decision"])
            self.assertEqual(0, manifest["external_model_api_calls"])
            self.assertTrue(manifest["generation_failure_preserved"])
            self.assertTrue(manifest["upstream_repair_strict_pass"])
            self.assertTrue(manifest["artifact_repair_strict_pass"])
            self.assertTrue(manifest["interrupt_resume_verified"])
            self.assertEqual(0, manifest["duplicate_upstream_provider_calls"])
            self.assertEqual(audit_before_resume, sha256_file(upstream_audit))
            self.assertEqual("PASS", manifest["raw_provider_schema_status"])
            self.assertEqual(
                "NOT_APPLICABLE", manifest["normalization_status"]
            )
            self.assertEqual("PASS", manifest["payload_final_atlas_status"])
            self.assertEqual(2, manifest["raw_provider_payload_count"])
            self.assertEqual(
                {"component", "interfaces"},
                set(manifest["raw_provider_payload_sha256_by_scope"]),
            )
            self.assertTrue(
                manifest["registry_gate"]["stale_schedule_refused"]
            )
            registration = manifest["formal_provider_registration"]
            self.assertEqual("gpt-5.6-luna", registration["requested_model"])
            self.assertEqual(180.0, registration["request_timeout_seconds"])
            self.assertEqual(1, registration["max_attempts_per_call"])
            self.assertEqual(64, len(registration["provider_endpoint_sha256"]))
            self.assertEqual(
                "direct_no_environment_proxy",
                registration["transport_route_policy"],
            )


if __name__ == "__main__":
    unittest.main()
