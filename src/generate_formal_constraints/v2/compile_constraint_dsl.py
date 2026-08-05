"""Compile high-confidence structured constraints into the typed native DSL.

Every planned rule receives a formalization record, but only rules whose full
assertion can be deterministically recovered are promoted to implemented.  A
partial necessary condition remains a draft and cannot yield a false PASS.
Legacy SMT mappings are used only as path/formula evidence, never as an
execution backend or authority.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

try:
    from .reviewed_dsl_specs import reviewed_specs
except ImportError:  # direct script execution in the deterministic pipeline
    from reviewed_dsl_specs import reviewed_specs


NUMBER = r"-?\d+(?:\.\d+)?"
# These five specifications were individually compared with the complete source
# assertion and bound XML paths.  Pattern-derived candidates outside this set
# remain drafts until they receive the same rule-level review.
REVIEWED_DSL_IDS = {
    "constr_1169", "constr_1011", "constr_1382", "constr_1243",
    "constr_1393",
}


STOP_ENUMS = {
    "A", "AN", "AND", "ARXML", "AUTOSAR", "BE", "BY", "DATA", "FALSE",
    "FOR", "FROM", "IF", "IN", "IS", "IT", "MAY", "MUST", "NOT", "OF",
    "ON", "ONE", "ONLY", "OR", "RTE", "SHALL", "SHOULD", "THAN", "THE",
    "THEN", "TO", "TRUE", "VALUE", "VALUES", "WHEN", "WITH",
}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def load_constraints(source_path: Path, curation_path: Path, bindings_path: Path) -> dict[str, dict]:
    sources = {item["id"]: item for item in load_jsonl(source_path)}
    bindings = {item["id"]: item for item in load_jsonl(bindings_path)}
    result: dict[str, dict] = {}
    for curated in load_jsonl(curation_path):
        cid = curated["id"]
        result[cid] = {
            "id": cid,
            "source": sources[cid],
            "semantics": curated["semantics"],
            "verification": curated["verification"],
            "targets": bindings[cid]["targets"],
        }
    return result


def load_mapping(path: Path) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in json.loads(path.read_text(encoding="utf-8-sig")):
        grouped.setdefault(str(row.get("constraint_id") or "").casefold(), []).append(row)
    return grouped


def clean_path(value: Any) -> str:
    return "/".join(part for part in str(value or "").strip().split("/") if part)


def mapping_evidence(rows: list[dict]) -> tuple[list[str], list[dict], str]:
    targets: list[str] = []
    properties: list[dict] = []
    descriptions: list[str] = []
    for row in rows:
        target = ((row.get("target") or {}).get("target_xml") or {}).get("xml_tag")
        if target and target not in targets:
            targets.append(str(target))
        for item in row.get("properties") or []:
            path = clean_path(item.get("xpath") or item.get("xml_tag"))
            if path:
                properties.append({
                    "path": path,
                    "role": str(item.get("role") or ""),
                    "xml_tag": str(item.get("xml_tag") or ""),
                    "sort": str(item.get("smt_sort") or ""),
                    "is_reference": bool(item.get("is_cross_file_ref"))
                        or str(item.get("xml_tag") or "").endswith(("-REF", "-TREF", "-IREF")),
                })
        description = str((row.get("logical_pattern") or {}).get("description") or "").strip()
        if description and description not in descriptions:
            descriptions.append(description)
    unique = {
        (item["path"], item["role"], item["xml_tag"], item["sort"], item["is_reference"]): item
        for item in properties
    }
    return targets, list(unique.values()), " ".join(descriptions)


def property_for(properties: list[dict], *, numeric: bool = False, reference: bool = False) -> dict | None:
    candidates = properties
    if numeric:
        typed = [item for item in candidates if item["sort"].casefold() in {"int", "real", "integer", "decimal"}]
        if typed:
            candidates = typed
    if reference:
        typed = [item for item in candidates if item["is_reference"]]
        if typed:
            candidates = typed
    return candidates[0] if candidates else None


def numeric_bounds(text: str) -> tuple[str | None, str | None, bool, bool] | None:
    patterns = [
        rf"({NUMBER})\s*<=\s*[^.;]{{0,100}}?\s*<=\s*({NUMBER})",
        rf"(?:between|from)\s+({NUMBER})\s+(?:and|to)\s+({NUMBER})",
        rf"\[\s*({NUMBER})\s*,\s*({NUMBER})\s*\]",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2), False, False
    at_least = re.search(rf"(?:at least|>=|greater than or equal to)\s*({NUMBER})", text, re.IGNORECASE)
    greater = re.search(rf"(?:strictly greater than|greater than|>)\s*({NUMBER})", text, re.IGNORECASE)
    at_most = re.search(rf"(?:at most|<=|less than or equal to)\s*({NUMBER})", text, re.IGNORECASE)
    less = re.search(rf"(?:strictly less than|less than|<)\s*({NUMBER})", text, re.IGNORECASE)
    minimum = (at_least or greater).group(1) if at_least or greater else None
    maximum = (at_most or less).group(1) if at_most or less else None
    if minimum is not None or maximum is not None:
        return minimum, maximum, bool(greater and not at_least), bool(less and not at_most)
    return None


def cardinality_bounds(text: str) -> tuple[int | None, int | None] | None:
    lower = text.casefold()
    if re.search(r"\b(exactly|one and only) one\b", lower):
        return 1, 1
    if re.search(r"\b(at most one|no more than one|shall not .* multiple)\b", lower):
        return None, 1
    if re.search(r"\b(at least one|one or more|one or several)\b", lower):
        return 1, None
    if re.search(r"\bmust not (?:have|contain|own)|\bshall not (?:have|contain|own)", lower):
        return 0, 0
    return None


def enum_values(text: str) -> list[str]:
    quoted = re.findall(r"[\"']([A-Z][A-Z0-9_-]{1,})[\"']", text)
    if len(set(quoted)) >= 2:
        return sorted(set(quoted))
    marker = re.search(
        r"(?:either|one of|values? (?:must|shall) be|value must be|allowed values?\s*(?:are|:))([^.;]+)",
        text,
        re.IGNORECASE,
    )
    if not marker:
        return []
    values = [
        item for item in re.findall(r"\b[A-Z][A-Z0-9_-]{1,}\b", marker.group(1))
        if item not in STOP_ENUMS
    ]
    return sorted(set(values)) if 2 <= len(set(values)) <= 20 else []


def base_spec(rule: dict, family: str, evidence: dict[str, Any]) -> dict:
    return {
        "language": "autosar-constraint-ir/1.0",
        "status": "draft",
        "coverage": "none",
        "rule_family": family,
        "checks": [],
        "evidence": evidence,
    }


def compile_rule(rule: dict, constraint: dict, legacy_rows: list[dict]) -> tuple[dict, list[str]]:
    family = constraint["semantics"]["rule_family"]
    targets, properties, legacy_description = mapping_evidence(legacy_rows)
    source_text = " ".join((
        rule["title"],
        str(constraint["source"].get("expression") or ""),
        legacy_description,
    ))
    evidence = {
        "source_sha256": rule["source_sha256"],
        "legacy_mapping_count": len(legacy_rows),
        "legacy_description": legacy_description,
    }
    spec = base_spec(rule, family, evidence)
    reasons: list[str] = []
    reviewed = reviewed_specs(rule["title"]).get(rule["constraint_id"])
    if reviewed is not None:
        reviewed["evidence"] = evidence
        return reviewed, reasons

    def promote(checks: list[dict], reason: str) -> None:
        spec["checks"] = checks
        spec["coverage"] = "full"
        spec["status"] = "reviewed"
        spec["qualification_reason"] = reason

    if family == "value_range":
        prop = property_for(properties, numeric=True)
        bounds = numeric_bounds(source_text)
        if prop and bounds:
            minimum, maximum, min_exclusive, max_exclusive = bounds
            promote([{
                "op": "numeric_range", "path": prop["path"],
                "min": minimum, "max": maximum,
                "min_exclusive": min_exclusive, "max_exclusive": max_exclusive,
                "message": rule["title"],
            }], "Explicit numeric bounds and a typed XML value binding were recovered.")
        else:
            reasons.append("numeric bound or typed value path is not explicit")
    elif family == "value_domain":
        prop = property_for(properties)
        allowed = enum_values(source_text)
        if prop and allowed:
            promote([{
                "op": "value_domain", "path": prop["path"], "allowed": allowed,
                "message": rule["title"],
            }], "A closed enum domain and XML value binding were recovered.")
        else:
            reasons.append("closed value domain or XML value path is not explicit")
    elif family == "cardinality":
        prop = property_for(properties)
        bounds = cardinality_bounds(source_text)
        if prop and bounds:
            minimum, maximum = bounds
            promote([{
                "op": "count", "path": prop["path"], "min": minimum, "max": maximum,
                "message": rule["title"],
            }], "Explicit cardinality and counted XML path were recovered.")
        else:
            reasons.append("cardinality or counted XML path is not explicit")
    elif family == "mutual_exclusion":
        paths = sorted({item["path"] for item in properties})
        if len(paths) >= 2 and re.search(r"mutual|exclusive| versus | vs\.? |not both", source_text, re.I):
            promote([{
                "op": "mutually_exclusive", "paths": paths, "max_present": 1,
                "message": rule["title"],
            }], "Explicit alternative XML paths and mutual-exclusion wording were recovered.")
        else:
            reasons.append("mutually exclusive alternatives are not explicit")
    elif family == "required_existence":
        prop = property_for(properties)
        if prop and re.search(r"\b(must|shall|required)\b.*\b(exist|present|contain|have|define|provide|map)", source_text, re.I):
            promote([{"op": "exists", "path": prop["path"], "message": rule["title"]}],
                    "An unconditional existence obligation and XML path were recovered.")
        else:
            reasons.append("unconditional required path is not explicit")
    elif family == "forbidden_existence":
        prop = property_for(properties)
        if prop and re.search(r"\b(must not|shall not|forbidden|not allowed)\b", source_text, re.I):
            promote([{"op": "forbidden", "path": prop["path"], "message": rule["title"]}],
                    "An unconditional forbidden XML path was recovered.")
        else:
            reasons.append("unconditional forbidden path is not explicit")
    elif family == "reference_integrity":
        refs = sorted({item["path"] for item in properties if item["is_reference"]})
        if refs and re.search(r"\b(reference|refers|referenced)\b", source_text, re.I) and not re.search(
            r"same|owner|correspond|compatible|mapping", source_text, re.I
        ):
            promote([
                {"op": "reference_resolves", "path": path, "message": rule["title"]}
                for path in refs
            ], "The complete assertion is reference existence/resolution.")
        else:
            reasons.append("reference resolution is only part of the assertion")
    elif family == "uniqueness":
        prop = property_for(properties)
        if prop and re.search(r"\b(unique|uniquely|only once|no duplicate|unambiguous)\b", source_text, re.I):
            promote([{"op": "unique", "path": prop["path"], "message": rule["title"]}],
                    "An explicit uniqueness key path was recovered.")
        else:
            reasons.append("uniqueness key is not explicit")
    else:
        reasons.append(f"{family} requires a reviewed relational or conditional formalization")

    # Pattern recovery creates candidates, not trust.  Promotion requires an
    # explicit rule-level review of the complete source assertion.
    if spec["status"] == "reviewed" and rule["constraint_id"] not in REVIEWED_DSL_IDS:
        reasons.append("pattern-derived candidate has not completed rule-level semantic review")
        spec["status"] = "draft"
        spec["coverage"] = "candidate_only"
    if rule["constraint_id"] == "constr_1243":
        spec = {
            **spec,
            "status": "reviewed", "coverage": "full",
            "checks": [{
                "op": "mutually_exclusive", "paths": ["VF", "VT"],
                "min_present": 1, "max_present": 1, "message": rule["title"],
            }],
            "qualification_reason": "The source explicitly requires exactly one of VF and VT.",
        }
    if spec["status"] != "reviewed":
        # Preserve useful candidate paths without making them executable.
        spec["candidate_paths"] = sorted({item["path"] for item in properties})
        spec["candidate_targets"] = targets
        spec["qualification_reason"] = "; ".join(reasons)
    else:
        spec["reviewed_selector_tags"] = targets or list(rule.get("selector", {}).get("tags") or [])
    return spec, reasons


def compile_plan(plan: dict, constraints: dict[str, dict], mappings: dict[str, list[dict]]) -> tuple[dict, dict]:
    counts = Counter()
    family_counts = Counter()
    for rule in plan.get("rules", []):
        if rule.get("implementation", {}).get("status") != "planned":
            counts["existing_implemented"] += 1
            continue
        constraint = constraints[rule["constraint_id"]]
        spec, _ = compile_rule(rule, constraint, mappings.get(rule["constraint_id"].casefold(), []))
        rule["formal_spec"] = spec
        family_counts[(constraint["semantics"]["rule_family"], spec["status"])] += 1
        if spec["status"] == "reviewed" and spec["coverage"] == "full":
            rule["backend"] = "dsl"
            rule["implementation"] = {
                "status": "implemented",
                "plugin": "constraint_dsl",
                "reason": spec["qualification_reason"],
            }
            targets = spec.get("reviewed_selector_tags") or []
            if targets:
                rule["selector"] = {"tags": targets, "mode": "any"}
            if spec.get("activation"):
                required = rule.setdefault("completeness", {}).setdefault("requires", [])
                for capability in ("validation_context", "generation_intent"):
                    if capability not in required:
                        required.append(capability)
                required.sort()
            counts["dsl_implemented"] += 1
        else:
            counts["dsl_draft"] += 1
    plan["coverage"]["implemented_rule_count"] = sum(
        rule["implementation"]["status"] == "implemented" for rule in plan["rules"]
    )
    plan["coverage"]["planned_rule_count"] = sum(
        rule["implementation"]["status"] == "planned" for rule in plan["rules"]
    )
    audit = {
        "schema_version": "1.0",
        "counts": dict(counts),
        "family_status": {
            f"{family}:{status}": count
            for (family, status), count in sorted(family_counts.items())
        },
        "policy": "Only full, statically recoverable assertions are promoted; partial necessary conditions remain planned.",
    }
    return plan, audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--curation", required=True, type=Path)
    parser.add_argument("--bindings", required=True, type=Path)
    parser.add_argument("--legacy-mapping", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--audit-output", required=True, type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
    compiled, audit = compile_plan(
        plan, load_constraints(args.source, args.curation, args.bindings),
        load_mapping(args.legacy_mapping),
    )
    validator = Draft202012Validator(json.loads(args.schema.read_text(encoding="utf-8-sig")))
    errors = [
        f"{rule['rule_id']}:{list(error.path)}:{error.message}"
        for rule in compiled["rules"] for error in validator.iter_errors(rule)
    ]
    if errors:
        raise ValueError("\n".join(errors))
    args.output.write_text(json.dumps(compiled, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.audit_output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
