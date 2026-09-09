"""Crash-safe process and filesystem primitives for paper experiments.

The helpers in this module are deliberately provider-agnostic.  They never
load credentials and are safe to exercise in offline regression tests.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

import psutil


LOCK_NAME = ".atlas-experiment.lock"


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def atomic_write_text(path: Path, text: str) -> None:
    """Replace *path* atomically with UTF-8 text on the same filesystem."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(
        f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    )
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        synchronize = 0x00100000
        wait_timeout = 0x00000102
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(synchronize, False, pid)
        if not handle:
            # Access denied means a process exists but cannot be queried;
            # invalid-parameter means the PID no longer exists.
            return ctypes.get_last_error() == 5
        try:
            return kernel32.WaitForSingleObject(handle, 0) == wait_timeout
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


@contextmanager
def exclusive_experiment_lock(
    experiment_root: Path,
    *,
    schedule_sha256: str,
    lock_name: str = LOCK_NAME,
) -> Iterator[Path]:
    """Allow one orchestrator per experiment root and retain stale-lock audit."""

    experiment_root.mkdir(parents=True, exist_ok=True)
    lock_path = experiment_root / lock_name
    token = uuid.uuid4().hex
    body = {
        "schema_version": "atlas.experiment.lock.v1",
        "pid": os.getpid(),
        "token": token,
        "schedule_sha256": schedule_sha256,
        "acquired_at_utc": utc_now(),
    }

    while True:
        try:
            descriptor = os.open(
                lock_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError:
            try:
                existing = json.loads(lock_path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                continue
            except (OSError, json.JSONDecodeError) as error:
                raise RuntimeError(
                    f"experiment lock exists but is not auditable: {lock_path}"
                ) from error
            existing_pid = int(existing.get("pid") or 0)
            if _process_is_alive(existing_pid):
                raise RuntimeError(
                    "another experiment orchestrator is active for this root: "
                    f"pid={existing_pid}"
                )
            stale_path = experiment_root / (
                f"{lock_name}.stale.{int(time.time())}."
                f"{existing_pid or 'unknown'}.{uuid.uuid4().hex}.json"
            )
            try:
                os.replace(lock_path, stale_path)
            except FileNotFoundError:
                continue
            continue
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(body, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        break

    try:
        yield lock_path
    finally:
        try:
            existing = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = {}
        if existing.get("token") == token:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def reserve_attempt(attempt_base: Path, max_attempts: int) -> tuple[int, Path]:
    """Atomically reserve the first unused contiguous attempt directory."""

    attempt_base.mkdir(parents=True, exist_ok=True)
    for number in range(1, max_attempts + 1):
        path = attempt_base / f"attempt-{number:03d}"
        try:
            path.mkdir(exist_ok=False)
        except FileExistsError:
            continue
        return number, path
    raise RuntimeError(f"attempt budget exhausted: {attempt_base}")


@dataclass(frozen=True)
class ChildProcessResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    termination: str | None = None


def _terminate_process_tree(process: subprocess.Popen[str]) -> str:
    if process.poll() is not None:
        return "already_exited"
    if os.name == "nt":
        completed = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            return "windows_taskkill_tree"
        process.kill()
        return "windows_parent_kill_fallback"
    try:
        os.killpg(process.pid, signal.SIGKILL)
        return "posix_process_group_kill"
    except ProcessLookupError:
        return "already_exited"


ORCHESTRATOR_STATE_DIRNAME = "orchestrator_state"


def child_state_path(
    experiment_root: Path, run_identity: str, attempt_number: int
) -> Path:
    """Where the orchestrator records one child's liveness.

    Deliberately outside the runs layout.  The child asserts that its own run
    directory is empty when it starts, and the orchestrator writes this file
    immediately after ``Popen`` -- a race the orchestrator wins, because the
    child still has to import the generation stack.  Keeping both in one
    directory blocked the very first run of the experiment.

    It cannot live in the attempt's parent either: that directory admits only
    contiguous ``attempt-NNN`` subdirectories, so a stray file there would make
    the *next* resume fail instead.  Launch and recovery both call this
    function, so the two can never look in different places.
    """
    return (
        experiment_root
        / ORCHESTRATOR_STATE_DIRNAME
        / run_identity
        / f"attempt-{attempt_number:03d}.child_process_state.json"
    )


def recover_orphaned_child(state_path: Path) -> str | None:
    """Terminate a still-running child whose owning orchestrator disappeared."""

    if not state_path.is_file():
        return None
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"child process state is not auditable: {state_path}") from error
    if state.get("status") != "RUNNING":
        return None
    pid = int(state.get("pid") or 0)
    expected_create_time = state.get("process_create_time")
    try:
        process = psutil.Process(pid)
        observed_create_time = process.create_time()
    except psutil.NoSuchProcess:
        outcome = "ORPHAN_ALREADY_EXITED"
    else:
        if (
            expected_create_time is None
            or abs(float(expected_create_time) - observed_create_time) > 0.01
        ):
            raise RuntimeError(
                f"child PID was reused; refusing to terminate unrelated process: {pid}"
            )
        if os.name == "nt":
            completed = subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                # taskkill can fail in restricted Windows sessions even for a
                # create-time-verified direct child.  Kill that exact process
                # through its existing psutil handle, then wait for confirmed
                # termination; never fall back to an unverified PID.
                try:
                    process.kill()
                except psutil.NoSuchProcess:
                    pass
            try:
                process.wait(timeout=10)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired) as error:
                if isinstance(error, psutil.TimeoutExpired):
                    raise RuntimeError(
                        f"failed to terminate orphaned child tree: {pid}"
                    ) from error
        else:
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        outcome = "ORPHAN_TREE_TERMINATED"
    atomic_write_json(
        state_path,
        {
            **state,
            "status": outcome,
            "recovered_at_utc": utc_now(),
        },
    )
    return outcome


def tee_stream(source: Any, target: Path, sink: list[str]) -> None:
    """Tee one child stream to disk line by line, flushed on every line."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        for line in iter(source.readline, ""):
            sink.append(line)
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
    try:
        source.close()
    except OSError:
        pass


def run_child_process(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    state_path: Path | None = None,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
) -> ChildProcessResult:
    """Run one child and guarantee tree termination on timeout or interruption.

    When ``stdout_path``/``stderr_path`` are supplied the streams are teed to
    disk as they arrive.  ``communicate()`` alone holds everything in the pipe
    until the child exits, so a run that hangs, or one stopped by an operator,
    leaves no readable output at all: during the V16 pilot the runner's own log
    stayed empty for its whole execution and the only observable progress was
    per-run artifacts appearing on disk.
    """

    kwargs: dict[str, Any] = {
        "cwd": str(cwd),
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    process = subprocess.Popen(list(command), **kwargs)
    state = {
        "schema_version": "atlas.experiment.child_process.v1",
        "status": "RUNNING",
        "pid": process.pid,
        "parent_pid": os.getpid(),
        "process_create_time": psutil.Process(process.pid).create_time(),
        "started_at_utc": utc_now(),
    }
    if state_path is not None:
        atomic_write_json(state_path, state)
    teed: dict[str, list[str]] = {"stdout": [], "stderr": []}
    threads: list[threading.Thread] = []
    if stdout_path is not None or stderr_path is not None:
        for name, path in (("stdout", stdout_path), ("stderr", stderr_path)):
            if path is None:
                continue
            thread = threading.Thread(
                target=tee_stream,
                args=(getattr(process, name), Path(path), teed[name]),
                daemon=True,
            )
            thread.start()
            threads.append(thread)

    def _collected(fallback: tuple[str, str]) -> tuple[str, str]:
        if not threads:
            return fallback
        for thread in threads:
            thread.join(timeout=5)
        return "".join(teed["stdout"]), "".join(teed["stderr"])

    try:
        if threads:
            process.wait(timeout=timeout_seconds)
            stdout, stderr = _collected(("", ""))
        else:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
        if state_path is not None:
            atomic_write_json(
                state_path,
                {
                    **state,
                    "status": "FINISHED",
                    "returncode": int(process.returncode or 0),
                    "finished_at_utc": utc_now(),
                },
            )
        return ChildProcessResult(
            returncode=int(process.returncode or 0),
            stdout=stdout,
            stderr=stderr,
            timed_out=False,
        )
    except subprocess.TimeoutExpired:
        termination = _terminate_process_tree(process)
        stdout, stderr = _collected(process.communicate() if not threads else ("", ""))
        if state_path is not None:
            atomic_write_json(
                state_path,
                {
                    **state,
                    "status": "TIMED_OUT",
                    "returncode": int(process.returncode or -1),
                    "termination": termination,
                    "finished_at_utc": utc_now(),
                },
            )
        return ChildProcessResult(
            returncode=int(process.returncode or -1),
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
            termination=termination,
        )
    except BaseException:
        termination = _terminate_process_tree(process)
        process.communicate()
        if state_path is not None:
            atomic_write_json(
                state_path,
                {
                    **state,
                    "status": "INTERRUPTED",
                    "returncode": int(process.returncode or -1),
                    "termination": termination,
                    "finished_at_utc": utc_now(),
                },
            )
        raise
