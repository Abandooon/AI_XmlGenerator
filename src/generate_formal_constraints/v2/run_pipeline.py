"""Rebuild the deterministic V2 constraint pipeline without calling an LLM."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run(script: Path, *arguments: object) -> None:
    command = [sys.executable, str(script), *(str(item) for item in arguments)]
    subprocess.run(command, check=True)


def run_module(repo: Path, module: str, *arguments: object) -> None:
    command = [sys.executable, "-m", module, *(str(item) for item in arguments)]
    subprocess.run(command, check=True, cwd=repo)


def option(name: str, value: Path) -> tuple[str, Path]:
    return name, value


def main() -> int:
    here = Path(__file__).resolve().parent
    repo = here.parents[2]
    doc = repo / "src" / "kg_builder" / "doc_constr_parser" / "v2"
    tools = doc / "tools"
    work = doc / "work"
    source_input = doc.parent / "input"
    metadata = source_input / "unified_metadata.json"
    retrieval = repo / "src" / "llm_generation" / "knowledge" / "v2"

    run(
        tools / "build_source_manifest.py",
        *option("--input-dir", source_input),
        *option("--metadata", metadata),
        *option("--output-dir", work),
    )
    run(
        tools / "validate_source_manifest.py",
        *option("--manifest", work / "source_manifest.jsonl"),
        *option("--schema", doc / "schema" / "source_constraint.schema.json"),
        *option("--input-dir", source_input),
        *option("--exceptions", doc / "source_exceptions.json"),
    )
    run(
        tools / "apply_source_semantic_overrides.py",
        *option("--input", work / "source_manifest.jsonl"),
        *option("--overrides", doc / "source_semantic_overrides.json"),
        *option("--output", work / "source_manifest_semantic_view.jsonl"),
    )

    source_view = work / "source_manifest_semantic_view.jsonl"
    decision_schema = doc / "schema" / "triage_decision.schema.json"
    curation_schema = doc / "schema" / "semantic_curation.schema.json"
    profiles = doc / "triage_profiles.json"

    batches: list[tuple[str, list[Path]]] = [
        (
            "chapter4",
            [
                *(work / f"triage_chapter4_part{number}.jsonl" for number in range(1, 7)),
                work / "triage_chapter4_part7_canonical.jsonl",
                work / "triage_chapter4_part8.jsonl",
                work / "triage_chapter4_part9.jsonl",
            ],
        ),
        ("chapter5", sorted(work.glob("triage_chapter5_part*.jsonl"))),
        ("chapter6", sorted(work.glob("triage_chapter6_part*.jsonl"))),
        ("chapter7", sorted(work.glob("triage_chapter7_part*.jsonl"))),
        ("chapter8_10", sorted(work.glob("triage_chapter8_10_part*.jsonl"))),
        ("chapter11_13", sorted(work.glob("triage_chapter11_13_part*.jsonl"))),
    ]
    enriched: dict[str, Path] = {}
    for name, decisions in batches:
        raw = work / f"semantic_triage_{name}.jsonl"
        sanitized = work / f"semantic_triage_{name}_sanitized.jsonl"
        bound = work / f"semantic_triage_{name}_bound_hints.jsonl"
        run(
            tools / "expand_triage.py",
            *option("--source", source_view),
            "--decisions",
            *decisions,
            *option("--profiles", profiles),
            *option("--decision-schema", decision_schema),
            *option("--curation-schema", curation_schema),
            *option("--output", raw),
        )
        run(
            tools / "sanitize_curation_targets.py",
            *option("--input", raw),
            *option("--metadata", metadata),
            *option("--output", sanitized),
        )
        run(
            tools / "enrich_target_hints.py",
            *option("--input", sanitized),
            *option("--source", source_view),
            *option("--metadata", metadata),
            *option("--output", bound),
        )
        enriched[name] = bound

    chapter4_correction = work / "semantic_triage_chapter4_corrections.jsonl"
    run(
        tools / "expand_triage.py",
        *option("--source", source_view),
        "--decisions",
        work / "triage_chapter4_corrections.jsonl",
        *option("--profiles", profiles),
        *option("--decision-schema", decision_schema),
        *option("--curation-schema", curation_schema),
        *option("--output", chapter4_correction),
    )
    run(
        tools / "sanitize_curation_targets.py",
        *option("--input", chapter4_correction),
        *option("--metadata", metadata),
        *option("--output", work / "semantic_triage_chapter4_corrections_sanitized.jsonl"),
    )

    curated_inputs = [
        work / "semantic_chapter2.jsonl",
        work / "semantic_chapter2_corrections.jsonl",
        work / "semantic_chapter2_corrections2.jsonl",
        work / "semantic_chapter2_corrections3.jsonl",
        work / "semantic_chapter3_part1.jsonl",
        work / "semantic_chapter3_part2.jsonl",
        work / "semantic_chapter3_part3.jsonl",
        enriched["chapter4"],
        work / "semantic_triage_chapter4_corrections_sanitized.jsonl",
        enriched["chapter5"],
        enriched["chapter6"],
        enriched["chapter7"],
        enriched["chapter8_10"],
        enriched["chapter11_13"],
    ]
    combined = work / "semantic_curation_pre_target_overrides.jsonl"
    run(
        tools / "combine_curation.py",
        *option("--schema", curation_schema),
        *option("--source-manifest", work / "source_manifest.jsonl"),
        "--inputs",
        *curated_inputs,
        *option("--output", combined),
        *option("--audit-output", work / "decision_ledger.json"),
    )

    current = combined
    for number, override_name in enumerate(
        ("chapter4_target_overrides.json", "chapter5_target_overrides.json"), 1
    ):
        target = work / f"semantic_curation_override_{number}.jsonl"
        run(
            tools / "apply_target_overrides.py",
            *option("--input", current),
            *option("--overrides", work / override_name),
            *option("--output", target),
        )
        current = target

    sanitized_bindings = work / "semantic_curation_sanitized_bindings.jsonl"
    run(
        tools / "sanitize_binding_targets.py",
        *option("--input", current),
        *option("--metadata", metadata),
        *option("--output", sanitized_bindings),
    )
    current = sanitized_bindings
    for number, override_name in enumerate(
        (
            "chapter5_target_overrides2.json",
            "chapter6_target_overrides.json",
            "chapter7_target_overrides.json",
            "chapter8_13_target_overrides.json",
        ),
        3,
    ):
        target = work / f"semantic_curation_override_{number}.jsonl"
        run(
            tools / "apply_target_overrides.py",
            *option("--input", current),
            *option("--overrides", work / override_name),
            *option("--output", target),
        )
        current = target
    shutil.copyfile(current, work / "semantic_curation.jsonl")

    run(
        tools / "bind_semantic_targets.py",
        *option("--metadata", metadata),
        "--curation",
        work / "semantic_curation.jsonl",
        *option("--output", work / "binding_decisions.jsonl"),
    )
    run(
        here / "merge_rule_implementations.py",
        "--inputs",
        here / "rule_implementations.json",
        here / "rule_implementations_additional.json",
        *option("--output", here / "rule_implementations_merged.json"),
    )
    run(
        here / "compile_validation_plan.py",
        *option("--curation", work / "semantic_curation.jsonl"),
        *option("--bindings", work / "binding_decisions.jsonl"),
        *option("--implementations", here / "rule_implementations_merged.json"),
        *option("--schema", here / "validation_rule.schema.json"),
        *option("--output", here / "validation_plan_unscoped.json"),
    )
    run(
        here / "scope_planned_rules.py",
        *option("--input", here / "validation_plan_unscoped.json"),
        *option("--output", here / "validation_plan_scoped.json"),
    )
    run(
        here / "compile_constraint_dsl.py",
        *option("--plan", here / "validation_plan_scoped.json"),
        *option("--source", work / "source_manifest.jsonl"),
        *option("--curation", work / "semantic_curation.jsonl"),
        *option("--bindings", work / "binding_decisions.jsonl"),
        *option("--legacy-mapping", repo / "src/validation/data/mapping_smt.json"),
        *option("--schema", here / "validation_rule.schema.json"),
        *option("--output", here / "validation_plan_dsl.json"),
        *option("--audit-output", here / "dsl_compilation_audit.json"),
    )
    run(
        here / "compile_manual_review_plan.py",
        *option("--source", work / "source_manifest.jsonl"),
        *option("--curation", work / "semantic_curation.jsonl"),
        *option("--bindings", work / "binding_decisions.jsonl"),
        *option("--output", here / "manual_review_plan.json"),
    )
    run(
        here / "attach_manual_reviews.py",
        *option("--plan", here / "validation_plan_dsl.json"),
        *option("--manual", here / "manual_review_plan.json"),
        *option("--output", here / "validation_plan.json"),
    )
    run(
        here / "qualify_planned_rules.py",
        *option("--plan", here / "validation_plan.json"),
        *option("--curation", work / "semantic_curation.jsonl"),
        *option("--bindings", work / "binding_decisions.jsonl"),
        *option("--output", here / "planned_rule_qualification.json"),
        *option("--audit-output", here / "planned_rule_qualification_audit.json"),
    )
    run(
        tools / "publish_constraints.py",
        *option("--source", work / "source_manifest.jsonl"),
        *option("--curation", work / "semantic_curation.jsonl"),
        *option("--bindings", work / "binding_decisions.jsonl"),
        *option("--structured-schema", doc / "schema" / "structured_constraint.schema.json"),
        *option("--source-schema", doc / "schema" / "source_constraint.schema.json"),
        *option("--validation-plan", here / "validation_plan.json"),
        *option("--output", doc / "constraints_v2.json"),
        *option("--manifest-output", doc / "publication_manifest.json"),
    )
    run(
        retrieval / "build_retrieval_cards.py",
        *option("--constraints", doc / "constraints_v2.json"),
        *option("--output", retrieval / "retrieval_cards.jsonl"),
        *option("--manifest-output", retrieval / "retrieval_manifest.json"),
    )
    run_module(
        repo,
        "src.validation.v2.implementation_manifest",
        *option("--plan", here / "validation_plan.json"),
        *option("--xsd", repo / "src/validation/data/AUTOSAR_4-2-2.xsd"),
        *option("--dataset-manifest", retrieval / "retrieval_manifest.json"),
        *option(
            "--xsd-serialization-manifest",
            repo / "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json",
        ),
        *option("--output", repo / "src/validation/v2/validator_manifest.json"),
    )
    run_module(
        repo,
        "src.generate_formal_constraints.v2.audit_compiled_rules",
        *option("--plan", here / "validation_plan.json"),
        *option("--constraints", doc / "constraints_v2.json"),
        *option("--validator-manifest", repo / "src/validation/v2/validator_manifest.json"),
        *option("--output", here / "compiled_rule_audit.json"),
    )
    run(
        here / "audit_pipeline.py",
        *option("--source", work / "source_manifest.jsonl"),
        *option("--curation", work / "semantic_curation.jsonl"),
        *option("--bindings", work / "binding_decisions.jsonl"),
        *option("--constraints", doc / "constraints_v2.json"),
        *option("--plan", here / "validation_plan.json"),
        *option("--cards", retrieval / "retrieval_cards.jsonl"),
        *option("--retrieval-manifest", retrieval / "retrieval_manifest.json"),
        *option("--qualification-ledger", here / "planned_rule_qualification.json"),
        *option("--output", here / "pipeline_audit.json"),
    )
    run_module(repo, "src.kg_builder.constraint_v2.cli")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
