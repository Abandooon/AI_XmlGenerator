"""Observation must not raise false alarms, miss crashes, or stop a paid run."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import run_observation as obs


class ProcessIdentityTests(unittest.TestCase):
    def test_the_current_process_is_recognised(self):
        identity = obs.process_identity(os.getpid())
        self.assertTrue(obs.is_same_process(identity))

    def test_pid_reuse_does_not_pass_as_the_same_process(self):
        """A PID alone is not an identity; the OS reissues them."""
        identity = obs.process_identity(os.getpid())
        impostor = {**identity, "create_time": identity["create_time"] - 500.0}
        self.assertFalse(obs.is_same_process(impostor))

    def test_a_missing_process_is_reported_not_raised(self):
        self.assertFalse(
            obs.is_same_process({"pid": 2 ** 30, "create_time": 1.0})
        )

    def test_a_malformed_identity_is_not_alive(self):
        for bad in ({}, {"pid": "x", "create_time": 1.0}, {"pid": 1}):
            with self.subTest(bad=bad):
                self.assertFalse(obs.is_same_process(bad))


class StallThresholdTests(unittest.TestCase):
    def test_defaults_are_derived_from_the_frozen_contract(self):
        contract = json.loads(
            (Path(obs.__file__).parent / "FORMAL_EXPERIMENT_CONTRACT.json").read_text(
                encoding="utf-8"
            )
        )
        generation = contract["generation"]
        self.assertEqual(
            generation["provider_registration"]["request_timeout_seconds"],
            obs.DEFAULT_PROVIDER_TIMEOUT_SECONDS,
        )
        self.assertEqual(
            generation["orchestration"][
                "generation_child_hard_timeout_seconds"
            ],
            obs.DEFAULT_CHILD_HARD_TIMEOUT_SECONDS,
        )

    def test_the_threshold_exceeds_the_provider_timeout_and_wrap_up(self):
        threshold = obs.stall_threshold_seconds(180.0, 600.0)
        self.assertGreater(threshold, 180.0)
        self.assertGreater(threshold, 780.0)
        self.assertGreater(threshold, obs.DEFAULT_CHILD_HARD_TIMEOUT_SECONDS)

    def test_a_slow_but_healthy_run_is_not_called_stalled(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "artifact.txt").write_text("x", encoding="utf-8")
            # Nine minutes idle: longer than one provider timeout, still healthy.
            report = obs.observe(
                root, None, expected_runs=60,
                now=(root / "artifact.txt").stat().st_mtime + 540,
            )
            self.assertNotIn(
                "NO_DISK_ACTIVITY_BEYOND_STALL_THRESHOLD", report["signals"]
            )

    def test_a_genuine_stall_is_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "artifact.txt").write_text("x", encoding="utf-8")
            report = obs.observe(
                root, None, expected_runs=60,
                now=(root / "artifact.txt").stat().st_mtime + 10_000,
            )
            self.assertIn(
                "NO_DISK_ACTIVITY_BEYOND_STALL_THRESHOLD", report["signals"]
            )


class CoverageTests(unittest.TestCase):
    """Silence must not be able to mean either 'fine' or 'crashed'."""

    def _root(self, kinds):
        raw = tempfile.mkdtemp()
        root = Path(raw)
        for index, kind in enumerate(kinds):
            run = root / f"run-{index}"
            run.mkdir(parents=True)
            (run / "completion_manifest.json").write_text(
                json.dumps({"run_id": f"run-{index}", "completion_kind": kind}),
                encoding="utf-8",
            )
        return root

    def test_a_crashed_runner_is_signalled_even_while_progress_looks_fine(self):
        root = self._root(["SUCCESSFUL_ARTIFACT"] * 3)
        report = obs.observe(
            root, {"pid": 2 ** 30, "create_time": 1.0}, expected_runs=60
        )
        self.assertIn(
            "RUNNER_PROCESS_IDENTITY_NO_LONGER_PRESENT", report["signals"]
        )

    def test_non_success_runs_are_surfaced_immediately(self):
        root = self._root(
            ["SUCCESSFUL_ARTIFACT", "AMBIGUOUS_PROVIDER_DELIVERY"]
        )
        report = obs.observe(root, None, expected_runs=60)
        self.assertIn("NON_SUCCESS_COMPLETION_PRESENT", report["signals"])
        self.assertEqual(1, len(report["non_success_runs"]))
        self.assertIn("AMBIGUOUS_PROVIDER_DELIVERY", report["non_success_runs"][0])

    def test_all_four_dimensions_are_present_in_every_report(self):
        root = self._root(["SUCCESSFUL_ARTIFACT"])
        report = obs.observe(root, obs.process_identity(os.getpid()),
                             expected_runs=60)
        self.assertIn("progress", report)
        self.assertIn("non_success_runs", report)
        self.assertIn("process_identity_present", report)
        self.assertIn("idle_seconds", report)

    def test_completion_is_signalled(self):
        root = self._root(["SUCCESSFUL_ARTIFACT"] * 2)
        report = obs.observe(root, None, expected_runs=2)
        self.assertIn(
            "ALL_SCHEDULED_RUNS_HAVE_COMPLETION_MANIFESTS", report["signals"]
        )


class ObserverAuthorityTests(unittest.TestCase):
    def test_an_observer_never_stops_the_runner(self):
        """A false alarm must not be able to end a paid experiment."""
        with tempfile.TemporaryDirectory() as raw:
            report = obs.observe(
                Path(raw), {"pid": 2 ** 30, "create_time": 1.0},
                expected_runs=60,
            )
            self.assertTrue(report["signals"])          # it did raise an alarm
            self.assertEqual("none", report["action_taken"])
            self.assertFalse(report["may_stop_the_runner"])

    def test_liveness_uses_process_identity_not_a_name_match(self):
        """``pgrep -f`` cannot see Windows-native command lines.

        The pilot's watcher used it, reported a healthy runner as dead, and
        stopped itself on that false signal.  Liveness is now a recorded
        pid/create_time pair resolved through psutil.
        """
        source = Path(obs.__file__).read_text(encoding="utf-8")
        code = "\n".join(
            line for line in source.splitlines()
            if not line.strip().startswith("#")
        )
        # No shelling out of any kind in the observation path.
        for shell_api in ("subprocess", "os.system", "os.popen", "shell=True"):
            self.assertNotIn(shell_api, code, shell_api)
        self.assertIn("psutil.Process", code)
        self.assertIn("create_time", code)


if __name__ == "__main__":
    unittest.main()
