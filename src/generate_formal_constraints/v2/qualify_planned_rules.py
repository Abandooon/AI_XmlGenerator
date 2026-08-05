"""Build a rule-by-rule, fail-closed qualification ledger for planned rules.

This step is deliberately separate from compilation.  It assigns every
unimplemented must rule to a concrete backend and review track, but it never
promotes a rule merely because a pattern or legacy mapping looks plausible.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

LOCAL_DSL = {
    "value_range", "value_domain", "format_pattern", "ordering", "cardinality",
    "required_existence", "forbidden_existence", "mutual_exclusion", "uniqueness",
}
CONDITIONAL_DSL = {"conditional_existence"}
GRAPH_PLUGIN = {"cross_object_consistency", "type_compatibility", "reference_integrity"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def backend_track(family: str) -> tuple[str, str]:
    if family in LOCAL_DSL:
        return "typed_dsl", "local_xml_assertion"
    if family in CONDITIONAL_DSL:
        return "typed_dsl", "conditional_xml_assertion"
    if family in GRAPH_PLUGIN:
        return "python", "resolved_arxml_graph"
    if family == "generation_procedure":
        return "manual", "generated_artifact_evidence"
    return "python", "reviewed_specialist_plugin"


def priority_score(semantic: dict[str, Any], verification: dict[str, Any]) -> int:
    score = 0
    if semantic.get("is_core"):
        score += 100
    score += {"critical": 60, "major": 40, "minor": 20}.get(str(semantic.get("importance")), 0)
    if "repair_guidance" in set(semantic.get("usages") or []):
        score += 15
    if verification.get("observability") == "full":
        score += 10
    if verification.get("severity") == "error":
        score += 5
    return score


def qualification_record(
    rule: dict[str, Any],
    curated: dict[str, Any],
    binding: dict[str, Any],
) -> dict[str, Any]:
    semantic = curated["semantics"]
    verification = curated["verification"]
    curation = curated.get("curation") or {}
    formal = rule.get("formal_spec") or {}
    family = str(semantic.get("rule_family") or formal.get("rule_family") or "unknown")
    backend, execution_model = backend_track(family)
    candidate_paths = sorted(set(formal.get("candidate_paths") or []))
    blockers: list[str] = []
    if curation.get("status") != "curated":
        blockers.append("semantic_curation_not_final")
    blockers.extend(f"curation_issue:{item}" for item in sorted(set(curation.get("issues") or [])))
    if formal.get("coverage") == "candidate_only":
        blockers.append("candidate_does_not_prove_full_assertion")
    if not formal.get("checks"):
        blockers.append("formal_atoms_not_compiled")
    if not candidate_paths:
        blockers.append("xml_path_evidence_missing")
    if not int((formal.get("evidence") or {}).get("legacy_mapping_count") or 0):
        blockers.append("legacy_mapping_evidence_missing")
    declared_capabilities = set((rule.get("completeness") or {}).get("requires") or [])
    requires_complete_scope = family in GRAPH_PLUGIN or "complete_reference_scope" in declared_capabilities
    if requires_complete_scope:
        blockers.append("complete_reference_scope_required")
    if family in GRAPH_PLUGIN:
        if "complete_reference_scope" not in declared_capabilities:
            blockers.append("completeness_metadata_upgrade_required")
        blockers.append("resolved_graph_semantics_required")
    elif family in CONDITIONAL_DSL:
        blockers.append("antecedent_and_exception_atomization_required")
    elif family == "generation_procedure":
        blockers.append("generated_c_code_evidence_required")
        blockers.append("policy_reclassification_required")

    if formal.get("coverage") == "candidate_only":
        state = "candidate_rejected_incomplete_assertion"
        wave = 1
    elif family in LOCAL_DSL:
        state = "local_atomization_required"
        wave = 2
    elif family in CONDITIONAL_DSL:
        state = "conditional_atomization_required"
        wave = 3
    elif family in GRAPH_PLUGIN:
        state = "graph_plugin_spec_required"
        wave = 4
    elif family == "generation_procedure":
        state = "manual_reclassification_required"
        wave = 5
    else:
        state = "specialist_spec_required"
        wave = 5

    acceptance_gates = [
        "complete_antecedent_consequence_exceptions_reviewed",
        "selector_and_every_xml_binding_reviewed",
        "positive_negative_boundary_tests_added",
        "missing_evidence_returns_not_evaluated",
        "source_sha256_and_dataset_sha256_pinned",
    ]
    if backend == "python":
        acceptance_gates.append("plugin_has_no_arbitrary_code_or_query_from_data")
    elif backend == "typed_dsl":
        acceptance_gates.append("typed_dsl_schema_validation_passes")
    else:
        acceptance_gates.append("external_artifact_and_trace_are_attached")

    return {
        "rule_id": rule["rule_id"],
        "constraint_id": rule["constraint_id"],
        "source_sha256": rule["source_sha256"],
        "title": rule["title"],
        "family": family,
        "scope": semantic.get("scope"),
        "importance": semantic.get("importance"),
        "is_core": bool(semantic.get("is_core")),
        "usages": list(semantic.get("usages") or []),
        "priority_score": priority_score(semantic, verification),
        "wave": wave,
        "qualification_state": state,
        "qualification_decision": "not_qualified",
        "decision_reason": "One or more explicit blockers prevent trustworthy execution.",
        "current_disposition": "remain_not_evaluated",
        "recommended_backend": backend,
        "execution_model": execution_model,
        "reference_scope": "complete" if requires_complete_scope else "partial_ok",
        "selector_tags": list((rule.get("selector") or {}).get("tags") or []),
        "binding_status": binding.get("binding_status"),
        "candidate_paths": candidate_paths,
        "candidate_check_count": len(formal.get("checks") or []),
        "blockers": blockers,
        "acceptance_gates": acceptance_gates,
        "next_artifacts": [
            f"qualification/{rule['constraint_id']}.json",
            f"tests/validation/{rule['constraint_id']}_positive.arxml",
            f"tests/validation/{rule['constraint_id']}_negative.arxml",
        ],
    }


def build_ledger(plan: dict[str, Any], curation_rows: list[dict], binding_rows: list[dict]) -> tuple[dict, dict]:
    curation = {row["id"]: row for row in curation_rows}
    bindings = {row["id"]: row for row in binding_rows}
    planned = [rule for rule in plan.get("rules", []) if (rule.get("implementation") or {}).get("status") == "planned"]
    records = [qualification_record(rule, curation[rule["constraint_id"]], bindings[rule["constraint_id"]]) for rule in planned]
    records.sort(key=lambda item: (-item["priority_score"], item["wave"], item["constraint_id"], item["rule_id"]))
    family_counts = Counter(item["family"] for item in records)
    state_counts = Counter(item["qualification_state"] for item in records)
    backend_counts = Counter(item["recommended_backend"] for item in records)
    wave_counts = Counter(str(item["wave"]) for item in records)
    ledger = {
        "schema_version": "1.0",
        "policy": "Qualification is not implementation. Every record remains NOT_EVALUATED until all acceptance gates pass.",
        "planned_rule_count": len(records),
        "summary": {
            "families": dict(sorted(family_counts.items())),
            "states": dict(sorted(state_counts.items())),
            "recommended_backends": dict(sorted(backend_counts.items())),
            "waves": dict(sorted(wave_counts.items())),
        },
        "records": records,
    }
    expected = {rule["rule_id"] for rule in planned}
    actual = {item["rule_id"] for item in records}
    errors: list[str] = []
    if expected != actual:
        errors.append(f"qualification coverage mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    if len(actual) != len(records):
        errors.append("qualification ledger contains duplicate rule ids")
    if any(item["current_disposition"] != "remain_not_evaluated" for item in records):
        errors.append("an unreviewed qualification record was promoted")
    if any(item["qualification_decision"] != "not_qualified" for item in records):
        errors.append("a rule without completed acceptance gates was qualified")
    audit = {
        "schema_version": "1.0",
        "valid": not errors,
        "planned_rule_count": len(planned),
        "qualified_rule_count": len(records),
        "errors": errors,
    }
    return ledger, audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--curation", type=Path, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    args = parser.parse_args()
    ledger, audit = build_ledger(
        json.loads(args.plan.read_text(encoding="utf-8-sig")),
        load_jsonl(args.curation),
        load_jsonl(args.bindings),
    )
    args.output.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.audit_output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if audit["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
