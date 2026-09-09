"""Latest-only AUTOSAR evidence gate shared by paper and promotion paths."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ATLAS_ROOT = Path(r"E:\git projects\AI_XmlGenerator")


def assert_current_autosar_results(
    results: dict[str, Any], *, purpose: str
) -> dict[str, Any]:
    if str(ATLAS_ROOT) not in sys.path:
        sys.path.insert(0, str(ATLAS_ROOT))
    from src.workbench.artifacts import assert_latest_autosar_identity

    schedule = results.get("schedule") or {}
    schedule_sha256 = schedule.get("content_sha256")
    if not isinstance(schedule_sha256, str) or len(schedule_sha256) != 64:
        raise ValueError("AUTOSAR results have no frozen schedule identity")
    return assert_latest_autosar_identity(
        {"schedule_content_sha256": schedule_sha256}, purpose=purpose
    )
