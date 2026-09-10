"""Server-side, frozen allocation of participants to study conditions.

The condition used to be a radio button on the participant's own page.  That
is not an allocation: a participant could read the manual instructions, switch
the control, and see ATLAS proposals, and nothing in the record would show it
happened.  A counterbalanced crossover still needs the arm to be a frozen
property of each participant/task session, so it is looked up here and the page
is built from the answer.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ALLOWED_CONDITIONS = ("manual", "atlas_assisted")
SCHEMA_VERSION = "atlas.workbench.assignment.v1"
_CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class AssignmentError(ValueError):
    """Raised when an arm cannot be established for a participant and task."""


def _identifier(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not _CODE.fullmatch(text):
        raise AssignmentError(f"{label} must be a short pseudonymous code")
    return text


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AssignmentError(f"assignment table repeats JSON key {key!r}")
        result[key] = value
    return result


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class AssignmentTable:
    """An immutable participant/task to condition allocation."""

    def __init__(self, records: dict[tuple[str, str], str], *, source_sha256: str):
        self._records = dict(records)
        self.source_sha256 = source_sha256
        self._participants = frozenset(key[0] for key in records)
        self._tasks = frozenset(key[1] for key in records)

    @classmethod
    def from_file(cls, path: str | Path) -> "AssignmentTable":
        target = Path(path).expanduser().resolve()
        if not target.is_file():
            raise AssignmentError(f"assignment table is missing: {target}")
        raw = target.read_bytes()
        try:
            document = json.loads(
                raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_json_keys
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AssignmentError("assignment table is not valid JSON") from error
        return cls.from_document(
            document, source_sha256=hashlib.sha256(raw).hexdigest()
        )

    @classmethod
    def from_document(
        cls, document: Any, *, source_sha256: str = ""
    ) -> "AssignmentTable":
        if not isinstance(document, dict):
            raise AssignmentError("assignment table root must be an object")
        unexpected_root = sorted(set(document) - {"schema_version", "assignments"})
        if unexpected_root:
            raise AssignmentError(
                f"assignment table has unsupported fields: {unexpected_root!r}"
            )
        if document.get("schema_version") != SCHEMA_VERSION:
            raise AssignmentError("unsupported assignment table schema version")
        rows = document.get("assignments")
        if not isinstance(rows, list) or not rows:
            raise AssignmentError("assignment table declares no assignments")
        records: dict[tuple[str, str], str] = {}
        for position, row in enumerate(rows):
            if not isinstance(row, dict):
                raise AssignmentError(f"assignment[{position}] must be an object")
            unexpected = sorted(set(row) - {"participant", "task", "condition"})
            if unexpected:
                raise AssignmentError(
                    f"assignment[{position}] has unsupported fields: {unexpected!r}"
                )
            participant = _identifier(row.get("participant"), "participant")
            task = _identifier(row.get("task"), "task")
            condition = str(row.get("condition") or "")
            if condition not in ALLOWED_CONDITIONS:
                raise AssignmentError(
                    f"assignment[{position}] has an unsupported condition: "
                    f"{condition!r}"
                )
            key = (participant, task)
            if key in records:
                # Re-allocating a participant mid-study would make their two
                # halves incomparable and is more likely a clerical error than
                # an intention, so it is refused rather than last-one-wins.
                raise AssignmentError(
                    f"{participant}/{task} is allocated more than once"
                )
            records[key] = condition
        participants = {participant for participant, _task in records}
        tasks = {task for _participant, task in records}
        overlap = sorted(participants & tasks)
        if overlap:
            raise AssignmentError(
                "participant and task code namespaces must be disjoint: "
                f"{overlap!r}"
            )
        return cls(records, source_sha256=source_sha256)

    def condition(self, participant: str, task: str) -> str:
        """The allocated arm, or a refusal; there is no default arm."""
        key = (_identifier(participant, "participant"), _identifier(task, "task"))
        if key[0] in self._tasks and key[1] in self._participants:
            raise AssignmentError(
                f"{key[0]}/{key[1]} appears to swap task and participant codes"
            )
        try:
            return self._records[key]
        except KeyError:
            raise AssignmentError(
                f"{key[0]}/{key[1]} has no allocated condition; a session cannot "
                "choose its own arm"
            ) from None

    def allocation_sha256(self, participant: str, task: str) -> str:
        """Stable identity of one allocation, independent of unrelated rows."""
        participant = _identifier(participant, "participant")
        task = _identifier(task, "task")
        condition = self.condition(participant, task)
        return _canonical_sha256(
            {
                "schema_version": SCHEMA_VERSION,
                "participant": participant,
                "task": task,
                "condition": condition,
            }
        )

    def participants(self) -> tuple[str, ...]:
        return tuple(sorted(self._participants))

    def balance(self) -> dict[str, int]:
        counts = {condition: 0 for condition in ALLOWED_CONDITIONS}
        for condition in self._records.values():
            counts[condition] += 1
        return counts

    def __len__(self) -> int:
        return len(self._records)
