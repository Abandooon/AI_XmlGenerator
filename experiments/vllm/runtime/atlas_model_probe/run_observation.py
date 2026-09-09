"""Observe a paid run without being able to break it.

Two observation defects showed up while the V16 pilot ran.  A liveness check
built on ``pgrep -f`` could not see Windows-native command lines and reported a
healthy runner as dead, which is the kind of false alarm that gets a working
paid experiment killed.  A watcher that greps only for progress markers has the
opposite failure: it stays silent through a crash, and silence is
indistinguishable from work.

So an observer here does two things and no more: it identifies the process by
recorded identity rather than by name matching, and it reports.  It never stops
anything.  Stopping is an operator decision expressed through the stop
sentinel, because an observer that can halt a run on an uncertain signal is a
new way to lose money.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import psutil


OBSERVER_VERSION = "atlas.v17.run_observation.v1"

_FORMAL_CONTRACT = json.loads(
    (Path(__file__).resolve().parent / "FORMAL_EXPERIMENT_CONTRACT.json").read_text(
        encoding="utf-8"
    )
)
_GENERATION_CONTRACT = _FORMAL_CONTRACT["generation"]
_ORCHESTRATION_CONTRACT = _GENERATION_CONTRACT["orchestration"]

# A stall threshold must exceed the frozen provider timeout plus the time a run
# legitimately spends after its last provider call: validation, rendering,
# independent evaluation and manifest writing.  Below that, a slow-but-healthy
# run is reported as stalled.
DEFAULT_PROVIDER_TIMEOUT_SECONDS = float(
    _GENERATION_CONTRACT["provider_registration"]["request_timeout_seconds"]
)
DEFAULT_CHILD_HARD_TIMEOUT_SECONDS = float(
    _ORCHESTRATION_CONTRACT["generation_child_hard_timeout_seconds"]
)
DEFAULT_POST_CALL_WINDOW_SECONDS = 600.0
STALL_SAFETY_FACTOR = 1.1


def stall_threshold_seconds(
    provider_timeout_seconds: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS,
    post_call_window_seconds: float = DEFAULT_POST_CALL_WINDOW_SECONDS,
    child_hard_timeout_seconds: float = DEFAULT_CHILD_HARD_TIMEOUT_SECONDS,
) -> float:
    """A conservative advisory threshold derived from frozen runtime bounds."""
    legitimate_window = max(
        provider_timeout_seconds + post_call_window_seconds,
        child_hard_timeout_seconds,
    )
    return legitimate_window * STALL_SAFETY_FACTOR


def process_identity(pid: int) -> dict[str, Any]:
    """Identity that survives PID reuse.

    A PID alone is not an identity: the operating system reissues it, and a
    watcher comparing PIDs alone will eventually call an unrelated process the
    experiment runner.  The creation time makes the pair unique.
    """
    process = psutil.Process(pid)
    return {"pid": int(pid), "create_time": float(process.create_time())}


def is_same_process(identity: dict[str, Any]) -> bool:
    """Whether the recorded process is still the one running under that PID."""
    try:
        process = psutil.Process(int(identity["pid"]))
        return abs(process.create_time() - float(identity["create_time"])) < 1e-6
    except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError, ValueError):
        return False


def newest_mtime(root: Path) -> float | None:
    latest: float | None = None
    for path in root.rglob("*"):
        try:
            if path.is_file():
                stamp = path.stat().st_mtime
                latest = stamp if latest is None else max(latest, stamp)
        except OSError:
            continue
    return latest


def observe(
    experiment_root: Path,
    runner_identity: dict[str, Any] | None,
    *,
    expected_runs: int,
    provider_timeout_seconds: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS,
    now: float | None = None,
) -> dict[str, Any]:
    """One observation across all four dimensions.  Reports; never acts."""
    now = time.time() if now is None else now
    completed = len(list(experiment_root.rglob("completion_manifest.json")))
    failures: list[str] = []
    for path in experiment_root.rglob("completion_manifest.json"):
        try:
            body = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        kind = str(body.get("completion_kind") or "")
        if kind and kind != "SUCCESSFUL_ARTIFACT":
            failures.append(f"{body.get('run_id')}: {kind}")

    latest = newest_mtime(experiment_root)
    idle_seconds = None if latest is None else max(0.0, now - latest)
    threshold = stall_threshold_seconds(provider_timeout_seconds)

    process_alive = (
        None if runner_identity is None else is_same_process(runner_identity)
    )

    signals: list[str] = []
    if process_alive is False:
        signals.append("RUNNER_PROCESS_IDENTITY_NO_LONGER_PRESENT")
    if idle_seconds is not None and idle_seconds > threshold:
        signals.append("NO_DISK_ACTIVITY_BEYOND_STALL_THRESHOLD")
    if failures:
        signals.append("NON_SUCCESS_COMPLETION_PRESENT")
    if completed >= expected_runs:
        signals.append("ALL_SCHEDULED_RUNS_HAVE_COMPLETION_MANIFESTS")

    return {
        "schema_version": OBSERVER_VERSION,
        "observed_at_epoch": now,
        "progress": {"completed": completed, "expected": expected_runs},
        "non_success_runs": failures,
        "process_identity_present": process_alive,
        "idle_seconds": idle_seconds,
        "stall_threshold_seconds": threshold,
        "signals": signals,
        # An observer reports.  Ending a paid run is an operator decision made
        # through the stop sentinel, never an inference from an uncertain
        # signal.
        "action_taken": "none",
        "may_stop_the_runner": False,
    }
