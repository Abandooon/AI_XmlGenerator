"""Render and hash every distinct English PIL V4.1 primary prompt.

Repetitions share prompt text and differ only by the frozen provider seed, so
the artifact contains 60 cases x 4 arms = 240 prompt records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pil_v4_arms
import pil_v4_contract as contract
from pil_v4_client import COMMON_SYSTEM_INSTRUCTIONS


ROOT = Path(__file__).resolve().parent
CASES = ROOT / "data" / "inference_dataset_v41_en.jsonl"
KNOWLEDGE = ROOT / "kb" / "authoritative_provisions_v41_en.jsonl"
DEFAULT_OUTPUT = ROOT / "PIL_V41_RENDERED_PROMPTS.jsonl"


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build() -> list[dict[str, Any]]:
    cases = _rows(CASES)
    context = pil_v4_arms.ArmContext.load(knowledge_base=KNOWLEDGE)
    system_sha = hashlib.sha256(COMMON_SYSTEM_INSTRUCTIONS.encode("utf-8")).hexdigest()
    records: list[dict[str, Any]] = []
    for case in cases:
        for arm in contract.ARMS:
            prompt, evidence = pil_v4_arms.render_primary_prompt(
                context, arm=arm, facts=str(case["facts_text"]),
            )
            records.append({
                "schema_version": "atlas.pil.rendered_prompt.v4.1",
                "case_id": case["id"],
                "arm": arm,
                "provider_schema_enforced": arm in {"p2", "p3"},
                "evidence_ids": [str(item["evidence_id"]) for item in evidence],
                "system_instructions_sha256": system_sha,
                "system_instructions": COMMON_SYSTEM_INSTRUCTIONS,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "prompt_characters": len(prompt),
                "prompt_utf8_bytes": len(prompt.encode("utf-8")),
                "language": "en",
                "cjk_characters": len(re.findall(r"[\u3400-\u9fff]", COMMON_SYSTEM_INSTRUCTIONS + prompt)),
                "prompt": prompt,
            })
    if len(records) != 240 or any(row["cjk_characters"] for row in records):
        raise ValueError("rendered prompt qualification failed")
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    records = build()
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in records),
        encoding="utf-8", newline="\n",
    )
    print(json.dumps({
        "output": str(args.output),
        "records": len(records),
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "cjk_characters": sum(int(row["cjk_characters"]) for row in records),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
