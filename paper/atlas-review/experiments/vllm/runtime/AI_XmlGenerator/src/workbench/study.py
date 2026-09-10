"""Append-only interaction telemetry for a counterbalanced repair user study."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ALLOWED_CONDITIONS = frozenset({"manual", "atlas_assisted"})
ALLOWED_EVENTS = frozenset(
    {
        "START",
        "VALIDATE",
        "EDIT",
        "ATLAS_SUGGESTION_VIEWED",
        "ATLAS_PROPOSAL_APPLIED",
        "ATLAS_PROPOSAL_REJECTED",
        "COMPLETE",
        "ABANDON",
        "NOTE",
    }
)

# Events a participant may declare about their own session.  Everything else is
# emitted by the action that caused it: a hand-picked "I viewed a suggestion"
# is a self-report, and a manual-versus-assisted effort comparison cannot rest
# on participants remembering to log their own interactions.
SELF_DECLARED_EVENTS = frozenset({"COMPLETE", "ABANDON", "NOTE"})

# Events that only exist because the assisted intervention was present.  The
# condition was previously validated on its own and the event on its own, so a
# manual-condition log could legally contain a suggestion view: the condition
# was a label on the telemetry rather than a property of the session it
# describes, and a manual-versus-assisted comparison cannot rest on that.
ASSISTED_ONLY_EVENTS = frozenset(
    {
        "ATLAS_SUGGESTION_VIEWED",
        "ATLAS_PROPOSAL_APPLIED",
        "ATLAS_PROPOSAL_REJECTED",
    }
)
_CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class StudyLogError(ValueError):
    """Raised for invalid identifiers, chain damage, or illegal study events."""


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _identifier(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not _CODE.fullmatch(text):
        raise StudyLogError(f"{label} must be a short pseudonymous code")
    return text


class StudyEventStore:
    """Store one hash-chained JSONL event stream per participant/task/condition."""

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, participant: str, task: str, condition: str) -> Path:
        participant = _identifier(participant, "participant")
        task = _identifier(task, "task")
        if condition not in ALLOWED_CONDITIONS:
            raise StudyLogError(f"unsupported study condition: {condition}")
        folder = self.root / participant
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{task}.{condition}.events.jsonl"

    @contextmanager
    def _lock(self, path: Path) -> Iterator[None]:
        lock_path = path.with_suffix(path.suffix + ".lock")
        descriptor: int | None = None
        for _ in range(100):
            try:
                descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(descriptor, str(os.getpid()).encode("ascii"))
                break
            except FileExistsError:
                time.sleep(0.02)
        if descriptor is None:
            raise StudyLogError(f"study log is busy: {path.name}")
        try:
            yield
        finally:
            os.close(descriptor)
            lock_path.unlink(missing_ok=True)

    def load(self, participant: str, task: str, condition: str) -> list[dict[str, Any]]:
        path = self.path_for(participant, task, condition)
        if not path.is_file():
            return []
        records: list[dict[str, Any]] = []
        previous = "0" * 64
        for position, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                item = json.loads(line)
            except json.JSONDecodeError as error:
                raise StudyLogError(f"study log line {position} is invalid JSON") from error
            claimed = item.get("event_sha256")
            unsigned = {key: value for key, value in item.items() if key != "event_sha256"}
            if item.get("sequence") != position:
                raise StudyLogError(f"study log sequence breaks at line {position}")
            if item.get("previous_event_sha256") != previous:
                raise StudyLogError(f"study log chain breaks at line {position}")
            if claimed != _canonical_sha256(unsigned):
                raise StudyLogError(f"study log line {position} was edited")
            previous = claimed
            records.append(item)
        return records

    def record(
        self,
        participant: str,
        task: str,
        condition: str,
        event: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        participant = _identifier(participant, "participant")
        task = _identifier(task, "task")
        if condition not in ALLOWED_CONDITIONS:
            raise StudyLogError(f"unsupported study condition: {condition}")
        if event not in ALLOWED_EVENTS:
            raise StudyLogError(f"unsupported study event: {event}")
        if condition == "manual" and event in ASSISTED_ONLY_EVENTS:
            raise StudyLogError(
                f"the manual condition cannot record {event}; a session that saw "
                "an ATLAS proposal is not a manual session"
            )
        if payload is not None and not isinstance(payload, dict):
            raise StudyLogError("event payload must be an object")
        path = self.path_for(participant, task, condition)
        with self._lock(path):
            records = self.load(participant, task, condition)
            if records and records[-1]["event"] in {"COMPLETE", "ABANDON"}:
                raise StudyLogError("the task already has a terminal event")
            if not records and event != "START":
                raise StudyLogError("the first study event must be START")
            if records and event == "START":
                raise StudyLogError("the task already has a START event")
            previous = records[-1]["event_sha256"] if records else "0" * 64
            unsigned = {
                "schema_version": "atlas.user_study.event.v2",
                "sequence": len(records) + 1,
                "previous_event_sha256": previous,
                "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "participant_code": participant,
                "task_id": task,
                "condition": condition,
                "event": event,
                "payload": payload or {},
            }
            record = {**unsigned, "event_sha256": _canonical_sha256(unsigned)}
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        return record

    def metrics(self, participant: str, task: str, condition: str) -> dict[str, Any]:
        records = self.load(participant, task, condition)
        if not records:
            return {"event_count": 0, "terminal": False}
        timestamps = [datetime.fromisoformat(item["recorded_at_utc"]) for item in records]
        terminal = records[-1]["event"] in {"COMPLETE", "ABANDON"}
        counts = {event: 0 for event in ALLOWED_EVENTS}
        for item in records:
            counts[item["event"]] += 1
        return {
            "event_count": len(records),
            "terminal": terminal,
            "outcome": records[-1]["event"] if terminal else "IN_PROGRESS",
            "elapsed_seconds": (timestamps[-1] - timestamps[0]).total_seconds(),
            "validation_cycles": counts["VALIDATE"],
            # An edit the participant typed and an edit a proposal wrote are
            # different measurements; pooling them would let assisted effort be
            # counted as manual effort.
            "edit_actions": counts["EDIT"],
            "atlas_suggestions_viewed": counts["ATLAS_SUGGESTION_VIEWED"],
            "atlas_proposals_applied": counts["ATLAS_PROPOSAL_APPLIED"],
            "atlas_proposals_rejected": counts["ATLAS_PROPOSAL_REJECTED"],
            "chain_head_sha256": records[-1]["event_sha256"],
        }
