"""Offline, reproducible revalidation of one saved Phase 1/Phase 2 run.

The script never calls a model API.  It rebuilds the production Phase 1
selection plan from the saved raw response, applies the current deterministic
compilation/augmentation rules, then reruns the pinned V2 bundle validator and
parsed selection obligations against the immutable generated ARXML files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROBE_ROOT = Path(__file__).resolve().parent
ATLAS_ROOT = Path(r"E:\git projects\AI_XmlGenerator")


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected an object in {path}")
    return value


def _single_file(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {pattern!r} below {directory}, found {len(matches)}"
        )
    return matches[0]


def _short_name(root: Any, payload_tags: set[str]) -> str:
    from lxml import etree

    def local_name(tag: Any) -> str:
        return etree.QName(tag).localname if isinstance(tag, str) else ""

    for node in root.iter():
        if local_name(node.tag) not in payload_tags:
            continue
        for child in node:
            if local_name(child.tag) == "SHORT-NAME" and (child.text or "").strip():
                return (child.text or "").strip()
    raise RuntimeError(f"no payload SHORT-NAME found for {sorted(payload_tags)}")


def _load_bundle(run_root: Path) -> dict[str, dict[str, str]]:
    from lxml import etree

    parser = etree.XMLParser(
        resolve_entities=False, no_network=True, recover=False, huge_tree=True
    )
    arxml_root = run_root / "atlas_output" / "ARXML"
    component_tags = {
        "APPLICATION-SW-COMPONENT-TYPE",
        "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE",
        "SERVICE-SW-COMPONENT-TYPE",
    }
    interface_tags = {
        "SENDER-RECEIVER-INTERFACE",
        "CLIENT-SERVER-INTERFACE",
        "MODE-SWITCH-INTERFACE",
        "PARAMETER-INTERFACE",
    }
    bundle: dict[str, dict[str, str]] = {"components": {}, "interfaces": {}}
    for category, directory, tags in (
        ("components", arxml_root / "Components", component_tags),
        ("interfaces", arxml_root / "Interfaces", interface_tags),
    ):
        for path in sorted(directory.glob("*.arxml")):
            xml_text = path.read_text(encoding="utf-8")
            root = etree.fromstring(xml_text.encode("utf-8"), parser)
            name = _short_name(root, tags)
            if name in bundle[category]:
                raise RuntimeError(f"duplicate {category} payload {name!r}")
            bundle[category][name] = xml_text
    if not bundle["components"]:
        raise RuntimeError("saved run contains no component ARXML")
    return bundle


def _rebuild_component_plans(
    run_root: Path, *, case_id: str, generation_seed: int
) -> list[dict[str, Any]]:
    from run_phase12_case import _requirement
    from src.llm_generation.core.round2_generator import round2_generator
    from src.llm_generation.knowledge.element_selection import (
        augment_declared_value_selections,
        augment_required_existence_selections,
        compile_architecture_selection_paths,
        normalize_component_reference_values,
    )

    round1_path = _single_file(run_root / "atlas_output" / "round1_data", "*.json")
    round1 = _load_json(round1_path)
    response = round1.get("response_data") or {}
    raw_plans = response.get("component_plan") if isinstance(response, dict) else None
    if not isinstance(raw_plans, list) or not raw_plans:
        raise RuntimeError("saved Phase 1 response has no component_plan")

    compiled, _ = compile_architecture_selection_paths(
        {"component_plan": deepcopy(raw_plans)},
        xsd_path_index=round2_generator.selection_path_index,
    )
    plans = compiled["component_plan"]
    for plan in plans:
        component_name = str(plan.get("name") or "").strip()
        plan["element_design"] = normalize_component_reference_values(
            plan.get("element_design") or {}, component_name=component_name
        )

    requirements = _requirement(case_id, generation_seed=generation_seed)
    declared_values = requirements.get("generation_value_obligations") or []
    requirement_contracts = requirements.get("generation_requirement_contracts") or []
    rebuilt: list[dict[str, Any]] = []
    for plan in plans:
        augmented, value_audit = augment_declared_value_selections(
            plan,
            declared_values,
            xsd_path_index=round2_generator.selection_path_index,
            requirement_contracts=requirement_contracts,
        )
        if round2_generator.validation_service is not None:
            augmented, existence_audit = augment_required_existence_selections(
                augmented,
                round2_generator.validation_service.engine.plan,
                xsd_path_index=round2_generator.selection_path_index,
            )
        else:
            existence_audit = {
                "derived_selection_count": 0,
                "promoted_selection_count": 0,
            }
        if (
            value_audit.get("applied_count")
            or existence_audit.get("derived_selection_count")
            or existence_audit.get("promoted_selection_count")
        ):
            recompiled, _ = compile_architecture_selection_paths(
                {"component_plan": [augmented]},
                xsd_path_index=round2_generator.selection_path_index,
            )
            augmented = recompiled["component_plan"][0]
        component_name = str(augmented.get("name") or "").strip()
        augmented["element_design"] = normalize_component_reference_values(
            augmented.get("element_design") or {}, component_name=component_name
        )
        rebuilt.append(augmented)
    return rebuilt


def revalidate(run_root: Path) -> dict[str, Any]:
    os.environ["LLM_API_KEY"] = "offline-revalidation-placeholder"
    if str(PROBE_ROOT) not in sys.path:
        sys.path.insert(0, str(PROBE_ROOT))
    if str(ATLAS_ROOT) not in sys.path:
        sys.path.insert(0, str(ATLAS_ROOT))

    from src.llm_generation.core.round2_generator import round2_generator
    from src.validation.v2.selection_obligations import (
        generation_status_from_validation,
        merge_selection_obligations,
        validate_selection_obligations,
    )

    summary = _load_json(run_root / "run_summary.json")
    case_id = str(summary.get("case_id") or "").strip()
    generation_seed = int(summary.get("seed"))
    plans = _rebuild_component_plans(
        run_root, case_id=case_id, generation_seed=generation_seed
    )
    bundle = _load_bundle(run_root)
    context_path = _single_file(
        run_root / "atlas_output" / "ARXML", "validation_context_*.json"
    )
    source_validation_context = _load_json(context_path)
    service = round2_generator.validation_service
    if service is None:
        raise RuntimeError("V2 validation service is disabled")
    # Revalidation intentionally uses the current hash-pinned validator.  Build
    # a new context from the saved immutable retrieval scopes and declarations;
    # never mutate the historical context or pretend its old validator hash is
    # current.
    validation_context = service.build_validation_context(
        source_validation_context.get("selection_scopes") or {},
        declared_use_cases=source_validation_context.get("declared_use_cases") or [],
        declared_constraint_ids=source_validation_context.get(
            "declared_constraint_ids"
        )
        or [],
        declared_targets=source_validation_context.get("declared_targets") or {},
        declared_parameters=source_validation_context.get("declared_parameters") or {},
        intent_scope=str(source_validation_context.get("intent_scope") or "partial"),
        declared_capability_scopes=source_validation_context.get(
            "declared_capability_scopes"
        )
        or [],
        manual_evidence_scope=source_validation_context.get("manual_evidence_scope"),
    )
    v2_report = service.validate_bundle(bundle, validation_context=validation_context)
    obligations = validate_selection_obligations(bundle, plans)
    merged = merge_selection_obligations(v2_report, obligations)
    artifact_profile = merged.get("artifact_profile") or {}
    result = {
        "schema_version": "atlas.autosar.saved-run-revalidation.v1",
        "created_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "source_run_summary_sha256": hashlib.sha256(
            (run_root / "run_summary.json").read_bytes()
        ).hexdigest(),
        "source_validation_context_sha256": hashlib.sha256(
            context_path.read_bytes()
        ).hexdigest(),
        "source_validation_context_manifest_sha256": source_validation_context.get(
            "manifest_sha256"
        ),
        "revalidation_context_manifest_sha256": validation_context.get(
            "manifest_sha256"
        ),
        "source_artifact_hashes": summary.get("artifact_hashes") or {},
        "case_id": case_id,
        "model": summary.get("model"),
        "repetition": summary.get("repetition"),
        "validation_decision": merged.get("decision"),
        "generation_status": generation_status_from_validation(merged.get("decision")),
        "validation_summary": merged.get("summary") or {},
        "selection_obligations": obligations,
        "artifact_profile": artifact_profile,
        "xsd": merged.get("xsd") or {},
        "report": merged,
    }
    result["revalidation_fingerprint_sha256"] = _canonical_hash(result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    run_root = args.run_root.resolve()
    output = args.output or (run_root / "offline_revalidation.json")
    result = revalidate(run_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "validation_decision": result["validation_decision"],
                "selection_obligation_decision": result["selection_obligations"].get(
                    "decision"
                ),
                "artifact_profile_decision": result["artifact_profile"].get(
                    "decision"
                ),
                "output": str(output.resolve()),
                "revalidation_fingerprint_sha256": result[
                    "revalidation_fingerprint_sha256"
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
