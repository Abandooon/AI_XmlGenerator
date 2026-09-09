from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import psutil

from experiment_runtime import (
    ORCHESTRATOR_STATE_DIRNAME,
    atomic_write_json,
    child_state_path,
    recover_orphaned_child,
    reserve_attempt,
    run_child_process,
)
from run_asw_v3_experiment import _attempt_layout
from run_asw_v3_full_experiment import run_full_experiment


class FullExperimentRunnerTests(unittest.TestCase):
    def test_formal_timeout_and_repair_rounds_are_not_operator_tunable(self):
        schedule = {"content_sha256": "a" * 64, "models": ["luna"]}
        variants = (
            (60, 1800, 2, "generation timeout"),
            (1800, 60, 2, "repair timeout"),
            (1800, 1800, 3, "repair round"),
        )
        with patch(
            "run_asw_v3_full_experiment.verify_schedule", return_value=schedule
        ):
            for generation_timeout, repair_timeout, rounds, message in variants:
                with self.subTest(message=message), tempfile.TemporaryDirectory() as raw:
                    with self.assertRaisesRegex(ValueError, message):
                        run_full_experiment(
                            schedule,
                            Path(raw),
                            generation_timeout_seconds=generation_timeout,
                            repair_timeout_seconds=repair_timeout,
                            repair_max_rounds=rounds,
                        )

    def test_generation_block_stops_before_repair(self):
        schedule = {"content_sha256": "a" * 64, "models": ["luna"]}
        generation = {
            "experiment_complete": False,
            "record_count": 1,
            "queue_halt_reason": "PROVIDER_RATE_LIMIT",
        }
        with tempfile.TemporaryDirectory() as raw, patch(
            "run_asw_v3_full_experiment.verify_schedule", return_value=schedule
        ), patch(
            "run_asw_v3_full_experiment.run_experiment",
            return_value=generation,
        ) as run_generation, patch(
            "run_asw_v3_full_experiment.build_repair_schedule"
        ) as build_repair:
            result = run_full_experiment(
                schedule,
                Path(raw),
                generation_timeout_seconds=1800,
                repair_timeout_seconds=1800,
                repair_max_rounds=2,
            )
            state = json.loads(
                (Path(raw) / "full_experiment_state.json").read_text("utf-8")
            )
        self.assertFalse(result["experiment_complete"])
        self.assertEqual("GENERATION_BLOCKED", state["stage"])
        self.assertEqual(
            (Path(raw).resolve(),),
            run_generation.call_args.kwargs["additional_operator_stop_roots"],
        )
        build_repair.assert_not_called()

    def test_complete_run_writes_one_hashed_final_manifest(self):
        schedule = {"content_sha256": "a" * 64, "models": ["luna"]}
        generation = {
            "experiment_complete": True,
            "content_sha256": "b" * 64,
            "schedule": {"models": ["luna"]},
            "records": [],
        }
        repair_schedule = {
            "content_sha256": "c" * 64,
            "scheduled_count": 0,
            "controlled_mutations": [],
            "source_generation_run_count": 0,
            "natural_failure_count": 0,
        }
        repair = {
            "experiment_complete": True,
            "content_sha256": "d" * 64,
            "schedule": repair_schedule,
            "records": [],
        }

        def fake_generation(_schedule, root, _timeout, **_kwargs):
            root.mkdir(parents=True, exist_ok=True)
            (root / "experiment_results.json").write_text(
                json.dumps(generation), encoding="utf-8"
            )
            return generation

        def fake_repair(_schedule, root, _rounds, _timeout):
            root.mkdir(parents=True, exist_ok=True)
            (root / "repair_results.json").write_text(
                json.dumps(repair), encoding="utf-8"
            )
            return repair

        with tempfile.TemporaryDirectory() as raw, patch(
            "run_asw_v3_full_experiment.verify_schedule", return_value=schedule
        ), patch(
            "run_asw_v3_full_experiment.run_experiment",
            side_effect=fake_generation,
        ), patch(
            "run_asw_v3_full_experiment.verify_experiment_results"
        ), patch(
            "run_asw_v3_full_experiment.build_repair_schedule",
            return_value=repair_schedule,
        ), patch(
            "run_asw_v3_full_experiment.run_repair_schedule",
            side_effect=fake_repair,
        ), patch(
            "run_asw_v3_full_experiment.verify_repair_results"
        ), patch(
            "evidence_registry_gate.assert_current_autosar_results"
        ):
            root = Path(raw)
            result = run_full_experiment(
                schedule,
                root,
                generation_timeout_seconds=1800,
                repair_timeout_seconds=1800,
                repair_max_rounds=2,
            )
            manifest = json.loads(
                (root / "full_experiment_manifest.json").read_text("utf-8")
            )
            state = json.loads(
                (root / "full_experiment_state.json").read_text("utf-8")
            )
        self.assertTrue(result["experiment_complete"])
        self.assertEqual(result, manifest)
        self.assertEqual("COMPLETE", state["stage"])
        self.assertEqual(6, len(manifest["artifact_hashes"]))


class ChildProcessBoundaryTests(unittest.TestCase):
    """The orchestrator/child boundary, with real processes and no provider.

    The tests above mock ``run_experiment``, so they could not see the defect
    that blocked the first run of the formal experiment: the orchestrator wrote
    its child-liveness file into the child's own run directory immediately after
    spawning, and the child asserts that directory is empty when it starts.  The
    orchestrator always won that race, because the child still has to import the
    generation stack.  These cases drive the real boundary instead.
    """

    RUN_ID = "gpt-5.6-luna__ASW-MIN-01-R1__repair-off"

    def layout(self, root: Path):
        run_base = root / "runs" / "gpt-5.6-luna" / "ASW-MIN-01" / "R1" / "repair-off"
        number, run_root = reserve_attempt(run_base, 3)
        return run_base, number, run_root

    def child_script(self, root: Path) -> Path:
        """A stand-in for run_phase12_case.py's empty-run-root assertion."""
        script = root / "child.py"
        script.write_text(
            "import sys\n"
            "from pathlib import Path\n"
            "run_root = Path(sys.argv[1])\n"
            "if run_root.exists() and any(run_root.iterdir()):\n"
            "    raise SystemExit('run root is not empty: %s' % run_root)\n"
            "(run_root / 'run_summary.json').write_text('{}', encoding='utf-8')\n",
            encoding="utf-8",
        )
        return script

    def test_the_child_starts_with_an_empty_run_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            run_base, number, run_root = self.layout(root)
            result = run_child_process(
                [sys.executable, "-B", str(self.child_script(root)), str(run_root)],
                cwd=root,
                timeout_seconds=60,
                state_path=child_state_path(root, self.RUN_ID, number),
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((run_root / "run_summary.json").is_file())

    def test_the_state_file_lives_outside_the_runs_layout(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            run_base, number, run_root = self.layout(root)
            state_path = child_state_path(root, self.RUN_ID, number)
            run_child_process(
                [sys.executable, "-B", str(self.child_script(root)), str(run_root)],
                cwd=root,
                timeout_seconds=60,
                state_path=state_path,
            )
            self.assertTrue(state_path.is_file())
            self.assertNotIn(run_root, state_path.parents)
            self.assertNotIn(run_base, state_path.parents)
            self.assertIn(root / ORCHESTRATOR_STATE_DIRNAME, state_path.parents)
            # And the runs layout is still walkable, so a resume will not fail
            # on an unexpected entry.
            numbers, roots = _attempt_layout(run_base)
            self.assertEqual([number], numbers)
            self.assertEqual([run_root], roots)

    def test_a_stray_file_in_the_run_base_is_still_refused(self) -> None:
        """The child's invariant was not relaxed to make room for the fix."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            run_base, _, _ = self.layout(root)
            (run_base / "attempt-001.child_process_state.json").write_text(
                "{}", encoding="utf-8"
            )
            with self.assertRaises(ValueError) as caught:
                _attempt_layout(run_base)
            self.assertIn("unexpected entries", str(caught.exception))

    def test_an_orphaned_child_is_found_through_the_same_helper(self) -> None:
        """Launch and recovery must never look in different places."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _, number, _ = self.layout(root)
            state_path = child_state_path(root, self.RUN_ID, number)
            child = subprocess.Popen(
                [sys.executable, "-B", "-c", "import time; time.sleep(120)"]
            )
            self.addCleanup(child.kill)
            atomic_write_json(state_path, {
                "schema_version": "atlas.experiment.child_process.v1",
                "status": "RUNNING",
                "pid": child.pid,
                "parent_pid": os.getpid(),
                "process_create_time": psutil.Process(child.pid).create_time(),
                "started_at_utc": "2026-08-22T00:00:00Z",
            })
            outcome = recover_orphaned_child(state_path)
            self.assertIsNotNone(outcome)
            child.wait(timeout=30)

    def test_no_orphan_is_reported_when_the_state_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _, number, _ = self.layout(root)
            self.assertIsNone(
                recover_orphaned_child(child_state_path(root, self.RUN_ID, number))
            )


if __name__ == "__main__":
    unittest.main()
