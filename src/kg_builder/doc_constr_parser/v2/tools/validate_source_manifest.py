"""Validate source_manifest.jsonl and its provenance invariants."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--exceptions", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    exceptions = json.loads(args.exceptions.read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in args.manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    errors: list[str] = []
    seen: set[str] = set()
    document_cache: dict[str, str] = {}
    for index, record in enumerate(records, 1):
        for error in validator.iter_errors(record):
            path = ".".join(str(item) for item in error.absolute_path)
            errors.append(f"record {index} {record.get('id')} {path}: {error.message}")

        constraint_id = record["id"]
        if constraint_id in seen:
            errors.append(f"duplicate id: {constraint_id}")
        seen.add(constraint_id)

        source = record["source"]
        raw = source["raw_text"]
        if hashlib.sha256(raw.encode("utf-8")).hexdigest() != source["sha256"]:
            errors.append(f"raw sha mismatch: {constraint_id}")

        document_name = source["document"]
        if document_name not in document_cache:
            document_cache[document_name] = (args.input_dir / document_name).read_text(encoding="utf-8")
        if raw not in document_cache[document_name]:
            errors.append(f"raw evidence not found in document: {constraint_id}")

        if record["parse"]["status"] == "malformed" and constraint_id not in exceptions:
            errors.append(f"unapproved malformed source record: {constraint_id}")

    stale_exceptions = sorted(set(exceptions) - seen)
    if stale_exceptions:
        errors.append(f"stale source exceptions: {stale_exceptions}")

    if errors:
        print("\n".join(errors))
        return 1

    print(
        json.dumps(
            {
                "valid": True,
                "record_count": len(records),
                "unique_id_count": len(seen),
                "approved_malformed_count": sum(
                    record["parse"]["status"] == "malformed" for record in records
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

