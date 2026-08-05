"""Produce a per-rule qualification ledger for every executable must rule."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
from typing import Any

import src.validation.v2  # noqa: F401 - register every executable plugin
from src.validation.v2.implementation_manifest import validate_manifest
from src.validation.v2.plugins import REGISTRY

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PLAN = Path(__file__).resolve().parent / "validation_plan.json"
DEFAULT_CONSTRAINTS = PROJECT_ROOT / "src/kg_builder/doc_constr_parser/v2/constraints_v2.json"
DEFAULT_VALIDATOR = PROJECT_ROOT / "src/validation/v2/validator_manifest.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "compiled_rule_audit.json"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_audit(plan_path: Path, constraints_path: Path, validator_path: Path) -> dict[str, Any]:
    plan = _load(plan_path)
    constraints_payload = _load(constraints_path)
    constraints = constraints_payload if isinstance(constraints_payload, list) else constraints_payload.get("constraints") or []
    validator = validate_manifest(validator_path, plan_path=plan_path)
    manifest_files = {str(item["path"]): str(item["sha256"]) for item in validator["source_files"]}
    constraint_by_id = {str(item["id"]): item for item in constraints}
    must_ids = {
        constraint_id for constraint_id, item in constraint_by_id.items()
        if bool((item.get("verification") or {}).get("must_validate"))
    }
    rules = list(plan.get("rules") or [])
    errors: list[str] = []
    if len(constraint_by_id) != len(constraints):
        errors.append("structured constraints contain duplicate ids")
    rule_ids = [str(rule.get("rule_id") or "") for rule in rules]
    if len(set(rule_ids)) != len(rule_ids):
        errors.append("validation plan contains duplicate rule ids")
    rules_by_constraint: dict[str, list[dict]] = {}
    for rule in rules:
        rules_by_constraint.setdefault(str(rule.get("constraint_id") or ""), []).append(rule)
    if set(rules_by_constraint) != must_ids:
        errors.append(
            f"must/rule id set mismatch: missing={sorted(must_ids - set(rules_by_constraint))[:20]}, "
            f"extra={sorted(set(rules_by_constraint) - must_ids)[:20]}"
        )

    records: list[dict[str, Any]] = []
    for rule in sorted(rules, key=lambda item: str(item.get("constraint_id") or "")):
        cid = str(rule.get("constraint_id") or "")
        rule_errors: list[str] = []
        constraint = constraint_by_id.get(cid)
        if constraint is None:
            rule_errors.append("structured constraint is missing")
            source_sha256 = ""
        else:
            source_sha256 = str(((constraint.get("source") or {}).get("source") or {}).get("sha256") or "")
            if str(rule.get("source_sha256") or "") != source_sha256:
                rule_errors.append("rule source_sha256 differs from structured source evidence")
        implementation = rule.get("implementation") or {}
        plugin_name = str(implementation.get("plugin") or "")
        if implementation.get("status") != "implemented":
            rule_errors.append("implementation status is not implemented")
        plugin_function = REGISTRY.get(plugin_name)
        module_path = ""
        module_sha256 = ""
        if plugin_function is None:
            rule_errors.append(f"plugin {plugin_name!r} is not registered")
        else:
            source_file = Path(inspect.getsourcefile(plugin_function) or "").resolve()
            try:
                module_path = source_file.relative_to(PROJECT_ROOT).as_posix()
            except ValueError:
                rule_errors.append("plugin source is outside the project")
            module_sha256 = manifest_files.get(module_path, "")
            if not module_sha256:
                rule_errors.append("plugin source is not covered by validator manifest")
        selector = rule.get("selector") or {}
        selector_tags = list(selector.get("tags") or [])
        selector_mode = selector.get("mode")
        if selector_mode not in {"any", "all", "global"} or (
            selector_mode != "global" and not selector_tags
        ):
            rule_errors.append("selector is empty or malformed")
        completeness = rule.get("completeness") or {}
        requires = sorted({str(item) for item in completeness.get("requires") or []})
        if "well_formed_xml" not in requires:
            rule_errors.append("well_formed_xml is not a declared prerequisite")
        if completeness.get("on_missing") != "not_evaluated":
            rule_errors.append("missing prerequisites are not fail-closed")
        backend = str(rule.get("backend") or "")
        formal_spec = rule.get("formal_spec") or {}
        qualification = "python_plugin"
        if backend == "dsl":
            qualification = "reviewed_full_dsl"
            if plugin_name != "constraint_dsl":
                rule_errors.append("DSL backend does not use constraint_dsl")
            if formal_spec.get("status") != "reviewed" or formal_spec.get("coverage") != "full":
                rule_errors.append("DSL formal_spec is not reviewed/full")
            if not list(formal_spec.get("checks") or []):
                rule_errors.append("DSL formal_spec has no executable checks")
        elif backend == "python":
            if plugin_name == "constraint_dsl":
                rule_errors.append("Python backend unexpectedly uses constraint_dsl")
        else:
            rule_errors.append(f"unsupported backend {backend!r}")
        record = {
            "constraint_id": cid,
            "rule_id": str(rule.get("rule_id") or ""),
            "source_sha256": source_sha256,
            "backend": backend,
            "plugin": plugin_name,
            "plugin_module": module_path,
            "plugin_module_sha256": module_sha256,
            "validator_sha256": str(validator["validator_sha256"]),
            "selector_tags": selector_tags,
            "requires": requires,
            "qualification": qualification,
            "qualified": not rule_errors,
            "errors": rule_errors,
        }
        records.append(record)
        errors.extend(f"{cid}: {message}" for message in rule_errors)

    counts = {
        "structured_constraints": len(constraints),
        "must_validate": len(must_ids),
        "validation_rules": len(rules),
        "qualified_rules": sum(bool(item["qualified"]) for item in records),
        "python_rules": sum(item["backend"] == "python" for item in records),
        "dsl_rules": sum(item["backend"] == "dsl" for item in records),
    }
    return {
        "schema_version": "1.0",
        "valid": not errors and counts["qualified_rules"] == counts["must_validate"],
        "dataset_sha256": str(validator["dataset_sha256"]),
        "validator_sha256": str(validator["validator_sha256"]),
        "counts": counts,
        "errors": errors,
        "rules": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit every compiled must validation rule")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--constraints", type=Path, default=DEFAULT_CONSTRAINTS)
    parser.add_argument("--validator-manifest", type=Path, default=DEFAULT_VALIDATOR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    audit = build_audit(args.plan, args.constraints, args.validator_manifest)
    args.output.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid": audit["valid"], "counts": audit["counts"], "error_count": len(audit["errors"])}, indent=2))
    return 0 if audit["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
