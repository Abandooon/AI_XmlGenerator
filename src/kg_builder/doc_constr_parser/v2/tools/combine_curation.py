"""Combine curated JSONL batches; later files explicitly supersede earlier IDs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    args = parse_args()
    validator = Draft202012Validator(json.loads(args.schema.read_text(encoding="utf-8")))
    source = {item["id"]: item for item in load_jsonl(args.source_manifest)}
    combined: dict[str, dict] = {}
    order: list[str] = []
    audit: list[dict] = []
    errors: list[str] = []

    for path in args.inputs:
        for line_number, record in enumerate(load_jsonl(path), 1):
            for error in validator.iter_errors(record):
                errors.append(
                    f"{path.name}:{line_number}:{record.get('id')}:{list(error.path)}:{error.message}"
                )
            constraint_id = record.get("id")
            source_record = source.get(constraint_id)
            if source_record is None:
                errors.append(f"{path.name}:{line_number}:unknown source id {constraint_id}")
                continue
            if record.get("source_sha256") != source_record["source"]["sha256"]:
                errors.append(f"{path.name}:{line_number}:{constraint_id}:source hash mismatch")
            if constraint_id not in combined:
                order.append(constraint_id)
            else:
                audit.append(
                    {
                        "id": constraint_id,
                        "superseded_by": path.name,
                        "previous_record_sha256": __import__("hashlib").sha256(
                            json.dumps(combined[constraint_id], sort_keys=True).encode("utf-8")
                        ).hexdigest(),
                    }
                )
            combined[constraint_id] = record

    if errors:
        print("\n".join(errors))
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for constraint_id in order:
            handle.write(json.dumps(combined[constraint_id], ensure_ascii=False, separators=(",", ":")) + "\n")
    args.audit_output.write_text(
        json.dumps({"overrides": audit}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"record_count": len(combined), "override_count": len(audit)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

