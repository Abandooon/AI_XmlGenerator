"""Build deterministic counterbalanced ATLAS U/G/A schedules."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

ARM_PERMUTATIONS = (
    ("U", "G", "A"),
    ("U", "A", "G"),
    ("G", "U", "A"),
    ("G", "A", "U"),
    ("A", "U", "G"),
    ("A", "G", "U"),
)
QUALIFICATION_CASES = ("ASW-MIN-04", "ASW-STD-04", "ASW-FULL-03")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_content_hash(document: dict[str, Any], label: str) -> str:
    claimed = document.get("content_sha256")
    body = {key: value for key, value in document.items() if key != "content_sha256"}
    actual = canonical_sha256(body)
    if claimed != actual:
        raise RuntimeError(f"{label}_content_hash_mismatch")
    return actual


def atomic_write_json(path: Path, value: Any) -> None:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, path)


def build_schedule(
    *,
    assets_manifest_path: Path,
    kind: str,
    experiment_id: str,
) -> dict[str, Any]:
    assets_manifest_path = assets_manifest_path.resolve()
    assets = json.loads(assets_manifest_path.read_text(encoding="utf-8"))
    assets_content_sha256 = verify_content_hash(assets, "assets_manifest")
    if assets.get("schema_version") != "atlas.vllm.uga.compiled_assets.v3":
        raise RuntimeError("compiled_assets_schema_version_mismatch")
    if assets.get("decision") != "PASS" or assets.get("case_count") != 20:
        raise RuntimeError("compiled_assets_not_admitted")
    asset_by_case = {item["case_id"]: item for item in assets["records"]}
    if len(asset_by_case) != 20:
        raise RuntimeError("compiled_asset_case_ids_are_not_unique")

    if kind == "qualification":
        blocks = [
            {
                "case_id": case_id,
                "tier": asset_by_case[case_id]["tier"],
                "repetition": 1,
                "seed": 104729,
            }
            for case_id in QUALIFICATION_CASES
        ]
    elif kind == "formal":
        seeds = (104729, 130363, 155921)
        blocks = [
            {
                "case_id": item["case_id"],
                "tier": item["tier"],
                "case_ordinal": case_ordinal,
                "repetition": repetition,
                "seed": seeds[repetition - 1],
            }
            for case_ordinal, item in enumerate(assets["records"], start=1)
            for repetition in (1, 2, 3)
        ]
    else:
        raise ValueError("schedule_kind_must_be_qualification_or_formal")

    records: list[dict[str, Any]] = []
    for block_ordinal, block in enumerate(blocks, start=1):
        if kind == "formal":
            permutation_index = (
                int(block["case_ordinal"])
                - 1
                + 2 * (int(block["repetition"]) - 1)
            ) % len(ARM_PERMUTATIONS)
        else:
            permutation_index = (block_ordinal - 1) % len(ARM_PERMUTATIONS)
        permutation = ARM_PERMUTATIONS[permutation_index]
        for within_block_ordinal, arm in enumerate(permutation, start=1):
            schedule_ordinal = len(records) + 1
            request_id = (
                f"{experiment_id}-{kind[:4]}-{schedule_ordinal:03d}-"
                f"{block['case_id']}-r{block['repetition']}-{arm.lower()}"
            )
            if len(request_id) > 128:
                raise RuntimeError("generated_request_id_is_too_long")
            records.append(
                {
                    "schedule_ordinal": schedule_ordinal,
                    "block_ordinal": block_ordinal,
                    "within_block_ordinal": within_block_ordinal,
                    "arm_order": "".join(permutation),
                    "request_id": request_id,
                    "audit_request_id": f"cmpl-{request_id}-0",
                    "arm": arm,
                    **block,
                    "asset_file_sha256": asset_by_case[block["case_id"]][
                        "file_sha256"
                    ],
                    "asset_content_sha256": asset_by_case[block["case_id"]][
                        "content_sha256"
                    ],
                    "prompt_sha256": asset_by_case[block["case_id"]][
                        "prompt_sha256"
                    ],
                    "prompt_token_count": asset_by_case[block["case_id"]][
                        "prompt_token_count"
                    ],
                    "prompt_token_ids_sha256": asset_by_case[block["case_id"]][
                        "prompt_token_ids_sha256"
                    ],
                    "schema_sha256": asset_by_case[block["case_id"]][
                        "schema_sha256"
                    ],
                }
            )

    expected_count = 9 if kind == "qualification" else 180
    if len(records) != expected_count:
        raise RuntimeError("schedule_request_count_mismatch")
    arm_counts = {arm: sum(item["arm"] == arm for item in records) for arm in "UGA"}
    if len(set(arm_counts.values())) != 1:
        raise RuntimeError("schedule_arms_are_not_balanced")
    manifest: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.schedule.v1",
        "experiment_id": experiment_id,
        "kind": kind,
        "model_path": assets["model_path"],
        "max_model_len": assets["max_model_len"],
        "max_output_tokens": assets["max_output_tokens"],
        "enable_thinking": assets["enable_thinking"],
        "assets_manifest_path": str(assets_manifest_path),
        "assets_manifest_file_sha256": sha256_file(assets_manifest_path),
        "assets_manifest_content_sha256": assets_content_sha256,
        "block_count": len(blocks),
        "request_count": len(records),
        "arm_counts": arm_counts,
        "counterbalancing": (
            "six_permutations_balanced_with_per_case_compilation_order_control"
            if kind == "formal"
            else "six_permutations_cycled_by_block_ordinal"
        ),
        "records": records,
    }
    manifest["content_sha256"] = canonical_sha256(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-manifest", type=Path, required=True)
    parser.add_argument(
        "--kind", choices=("qualification", "formal"), required=True
    )
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    schedule = build_schedule(
        assets_manifest_path=args.assets_manifest,
        kind=args.kind,
        experiment_id=args.experiment_id,
    )
    atomic_write_json(args.output.resolve(), schedule)
    print(
        json.dumps(
            {
                "kind": schedule["kind"],
                "request_count": schedule["request_count"],
                "content_sha256": schedule["content_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
