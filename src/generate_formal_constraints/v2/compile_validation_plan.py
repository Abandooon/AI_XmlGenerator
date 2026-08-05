"""Compile all must-validate curation decisions into a fail-closed rule plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--curation", type=Path, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--implementations", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    curation = load_jsonl(args.curation)
    bindings = {item["id"]: item for item in load_jsonl(args.bindings)}
    implementations = json.loads(args.implementations.read_text(encoding="utf-8"))
    validator = Draft202012Validator(json.loads(args.schema.read_text(encoding="utf-8")))
    required = [item for item in curation if item["verification"]["must_validate"]]
    rules: list[dict] = []
    errors: list[str] = []

    for item in required:
        constraint_id = item["id"]
        specs = implementations.get(constraint_id) or [{
            "plugin": None,
            "selector": [],
            "requires": ["well_formed_xml"],
            "reason": "No implementation decision has been recorded.",
        }]
        binding = bindings.get(constraint_id)
        if binding is None:
            errors.append(f"{constraint_id}: missing binding decision")
            continue
        if binding["binding_status"] in {"unresolved", "partial"}:
            errors.append(f"{constraint_id}: binding status is {binding['binding_status']}")
            continue
        for number, spec in enumerate(specs, 1):
            plugin = spec.get("plugin")
            rule = {
                "schema_version": "2.0",
                "rule_id": f"{constraint_id}#r{number}",
                "constraint_id": constraint_id,
                "source_sha256": item["source_sha256"],
                "title": item["semantics"]["summary"],
                "severity": item["verification"]["severity"],
                "policy": item["verification"]["policy"],
                "backend": "python" if plugin else item["verification"]["preferred_backend"],
                "implementation": {
                    "status": "implemented" if plugin else "planned",
                    "plugin": plugin,
                    "reason": spec.get("reason", ""),
                },
                "selector": {
                    "tags": spec.get("selector", []),
                    "mode": "any" if spec.get("selector") else "global",
                },
                "parameters": spec.get("parameters", {}),
                "completeness": {
                    "requires": spec.get("requires", ["well_formed_xml"]),
                    "on_missing": "not_evaluated",
                },
                "dependencies": spec.get("dependencies", []),
                "bindings": [
                    {"role": target["role"], "path_variants": target["path_variants"]}
                    for target in binding["targets"]
                    if target["binding_status"] != "not_applicable"
                ],
            }
            if spec.get("activation"):
                rule["formal_spec"] = {
                    "language": "autosar-constraint-ir/1.0",
                    "status": "reviewed",
                    "coverage": "full",
                    "rule_family": spec.get("rule_family", "cross_object_consistency"),
                    "checks": [],
                    "qualification_reason": spec.get("reason", "Reviewed Python graph validator."),
                    "reviewed_selector_tags": list(spec.get("selector") or []),
                    "review_basis": spec.get(
                        "review_basis",
                        "complete_normative_assertion_and_resolved_arxml_paths",
                    ),
                    "activation": spec["activation"],
                    "evidence": {
                        "source_sha256": item["source_sha256"],
                        "implementation_map": args.implementations.name,
                    },
                }
            for error in validator.iter_errors(rule):
                errors.append(f"{rule['rule_id']}:{list(error.path)}:{error.message}")
            rules.append(rule)

    published_ids = {rule["constraint_id"] for rule in rules}
    missing_ids = sorted({item["id"] for item in required} - published_ids)
    if missing_ids:
        errors.append("must-validate rules missing from plan: " + ", ".join(missing_ids))
    if errors:
        print("\n".join(errors))
        return 1

    payload = {
        "schema_version": "2.0",
        "policy": {
            "fail_on_rule_failure": True,
            "fail_on_must_not_evaluated": True,
            "fail_on_engine_error": True,
        },
        "coverage": {
            "must_validate_constraints": len(required),
            "published_constraints": len(published_ids),
            "rule_count": len(rules),
            "implemented_rule_count": sum(rule["implementation"]["status"] == "implemented" for rule in rules),
            "planned_rule_count": sum(rule["implementation"]["status"] == "planned" for rule in rules),
        },
        "rules": rules,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["coverage"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
