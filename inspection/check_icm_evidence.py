#!/usr/bin/env python3
"""Inspect retained ICM records and one frozen AUTOSAR field trace.

Standard library only. Reads files and ZIP members, prints to stdout, and does
not import application modules, contact a service, or write any files.
"""

from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True

DATASET_SHA256 = "d6b4ab4f6b5b29af2dd9007405c4fa626b0b219ca51fed5e720fe0de1a14048d"
RULE_ID = "TPS_SWCT_01519"
RUNNABLE = "RE_Com_Full_Baseline"
EVENT = "TE_Com_Full_Baseline"
TARGET = "/Components/ASW_Com_Full_Baseline/IB_Com_Full_Baseline/" + RUNNABLE
RUNTIME = Path("experiments/vllm/runtime/AI_XmlGenerator/src")
ARCHIVE = Path("experiments/autosar/frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_bytes().decode("utf-8-sig"))


def one(items, message: str):
    items = list(items)
    require(len(items) == 1, f"{message}: expected one item, found {len(items)}")
    return items[0]


def inspect(root: Path) -> dict:
    constraints_path = root / RUNTIME / "kg_builder/doc_constr_parser/v2/constraints_v2.json"
    constraints_bytes = constraints_path.read_bytes()
    require(sha256(constraints_bytes) == DATASET_SHA256, "Unexpected frozen ICM bytes")
    constraints = json.loads(constraints_bytes.decode("utf-8-sig"))
    require(len(constraints) == 1085, "Unexpected constraint count")
    require(len({item["id"] for item in constraints}) == 1085, "Duplicate constraint IDs")

    expected = {
        "semantic_status": {"curated": 473, "provisional": 612},
        "review_status": {"approved": 472, "needs_review": 613},
        "binding_status": {
            "complete": 1052, "not_applicable": 30, "partial": 2, "unresolved": 1
        },
    }
    counts = {}
    for key, expected_counts in expected.items():
        counts[key] = dict(sorted(Counter(item["quality"][key] for item in constraints).items()))
        require(counts[key] == expected_counts, f"Unexpected {key} counts")

    # Recompute the publication rule; this is not an independent human review.
    for item in constraints:
        quality = item["quality"]
        approved = (
            quality["semantic_status"] == "curated"
            and quality["binding_status"] in {"complete", "not_applicable"}
            and "formal_rule_planned" not in quality["issues"]
        )
        require(
            quality["review_status"] == ("approved" if approved else "needs_review"),
            f"Publication status differs from derivation: {item['id']}",
        )

    record = one((r for r in constraints if r["id"] == RULE_ID), "ICM record")
    source = record["source"]["source"]
    require(sha256(source["raw_text"].encode("utf-8")) == source["sha256"], "Source text hash differs")
    excerpt = read_json(root / "supporting/autosar_constraint_preparation/TPS_SWCT_01519_source_excerpt.json")
    require(excerpt["normative_source"]["raw_text"] == source["raw_text"], "Selected source excerpt differs")
    layers = excerpt["preparation_layers"]
    require(layers["source_manifest.jsonl"]["record"] == record["source"], "Selected source record differs")
    semantic = layers["semantic_curation.jsonl"]["record"]
    require(semantic["semantics"] == record["semantics"], "Selected semantic record differs")
    require(semantic["curation"]["status"] == record["quality"]["semantic_status"], "Semantic status differs")
    require(
        layers["binding_decisions.jsonl"]["record"]["binding_status"] == record["quality"]["binding_status"],
        "Selected binding status differs",
    )
    for reference in excerpt["implementation_references"]:
        require(
            sha256((root / reference["release_path"]).read_bytes()) == reference["release_sha256"],
            f"Implementation reference bytes changed: {reference['release_path']}",
        )

    metadata = read_json(root / RUNTIME / "kg_builder/data/unified_metadata_with_inlines.json")
    period_meta = one(
        (e for e in metadata["groups"]["TimingEvent"]["elements"] if e["name"] == "period"),
        "TimingEvent.period metamodel property",
    )
    require(period_meta["xml_tag"] == "PERIOD", "Unexpected period XML mapping")
    retrieval = read_json(root / RUNTIME / "llm_generation/knowledge/v2/retrieval_manifest.json")
    require(retrieval["card_count"] == 1085, "Unexpected retrieval-card count")

    with zipfile.ZipFile(root / ARCHIVE, "r") as archive:
        def member(suffix: str) -> str:
            return one((n for n in archive.namelist() if n.endswith(suffix)), suffix)

        def json_member(name: str):
            return json.loads(archive.read(name).decode("utf-8-sig"))

        evaluation_name = member("ASW-FULL-01/R1/repair-off/attempt-001/independent_evaluation.json")
        run = evaluation_name.removesuffix("independent_evaluation.json")
        schema_name = run + "atlas_output/debug/round2_schema_ASW_Com_Full_Baseline_enhanced_20260902_162833.json"
        design_name = run + "atlas_output/round1_data/round1_20260902_162824.json"
        xml_name = run + "atlas_output/ARXML/Components/ASW_Com_Full_Baseline_8f34364d_1788337723.arxml"
        validation_name = run + "atlas_output/ARXML/validation_8f34364d_1788337723.json"
        plan_name = member("code_snapshot/runtime_assets/src/generate_formal_constraints/v2/validation_plan.json")
        case_name = member("requirements/asw_cases_v3.yaml")
        case_text = archive.read(case_name).decode("utf-8-sig")
        case_block = one(
            (part for part in re.split(r"(?m)^  - case_id: ", case_text) if part.startswith("ASW-FULL-01\n")),
            "Original ASW-FULL-01 case block",
        )
        requested_period = Decimal(one(re.findall(r"period_s:\s*([0-9.]+)", case_block), "Requested period"))

        schema = json_member(schema_name)
        schema_pointer = (
            "properties/APPLICATION-SW-COMPONENT-TYPE/properties/SWC-INTERNAL-BEHAVIOR/"
            "properties/EVENTS/properties/TIMING-EVENT/items/properties/PERIOD"
        )
        period_schema = schema
        for key in schema_pointer.split("/"):
            period_schema = period_schema[key]
        require(period_schema["type"] == "number" and period_schema["x-xml-tag"] == "PERIOD", "Period schema differs")
        annotation = one(period_schema["x-atlas-instance-value-constraints"], "Period annotation")
        require(Decimal(annotation["value"]) == requested_period, "Schema binding differs from requested period")
        require(annotation["anchors"][0]["short_name"] == EVENT, "Schema binds a different event")
        design = json_member(design_name)
        selection = one(
            (s for s in design["design"]["component_plan"][0]["element_design"]["selections"]
             if s["path"][-2:] == ["PERIOD", "#TEXT"]),
            "Processed plan period selection",
        )
        require(Decimal(selection["value"]) == requested_period, "Plan binding differs from requested period")

        xml_bytes = archive.read(xml_name)
        xml = ET.fromstring(xml_bytes)
        runnable = one(
            (r for r in xml.iter() if r.tag.rsplit("}", 1)[-1] == "RUNNABLE-ENTITY"
             and r.findtext("{*}SHORT-NAME") == RUNNABLE), "Runnable declaration"
        )
        event = one(
            (e for e in xml.iter() if e.tag.rsplit("}", 1)[-1] == "TIMING-EVENT"
             and e.findtext("{*}SHORT-NAME") == EVENT), "Timing event"
        )
        reference = event.find("{*}START-ON-EVENT-REF")
        require(reference is not None, "Missing runnable reference")
        require(reference.text == TARGET and reference.get("DEST") == "RUNNABLE-ENTITY", "Unexpected runnable reference")
        require(Decimal(event.findtext("{*}PERIOD")) == requested_period, "Artifact period differs from task")

        plan = json_member(plan_name)
        require(len(plan["rules"]) == 554, "Unexpected configured rule count")
        backends = dict(sorted(Counter(r["backend"] for r in plan["rules"]).items()))
        require(backends == {"python": 400, "dsl": 154}, "Unexpected rule backend counts")
        rule = one((r for r in plan["rules"] if r["constraint_id"] == RULE_ID), "Frozen rule plan")
        require(rule["source_sha256"] == source["sha256"], "Rule source differs from ICM source")
        validation = json_member(validation_name)
        result = one((r for r in validation["rules"] if r["constraint_id"] == RULE_ID), "Executed rule result")
        require(result["status"] == "PASS" and result["applicable_count"] == result["checked_count"] == 1, "Rule result differs")
        evaluation = json_member(evaluation_name)
        obligation = one((o for o in evaluation["structural_obligations"] if o["code"] == "runnable_period"), "Task period obligation")
        require(obligation["status"] == "PASS" and Decimal(str(obligation["expected"])) == requested_period, "Task obligation differs")
        require(all(x["status"] == "PASS" for x in evaluation["xsd"]) and len(evaluation["xsd"]) == 7, "Recorded XSD results differ")
        require(any(x["sha256"] == sha256(xml_bytes) for x in evaluation["xsd"]), "Component bytes differ from recorded XSD input")
        require(evaluation["decision"] == "PASS" and evaluation["full_corpus_decision"] == "INCOMPLETE", "Decision scope differs")
        require(validation["validation_context"]["dataset_sha256"] == retrieval["dataset_sha256"], "Retrieval dataset identities differ")
        require(RULE_ID in validation["validation_context"]["manifest"]["selected_constraint_ids"], "Example not selected in this run")

        return {
            "inspection": "PASS (retained evidence consistency; no generation or validator rerun)",
            "constraint_count": len(constraints), "constraints_file_sha256": DATASET_SHA256,
            "quality_counts": counts, "program_derived_approved_status_matches": True,
            "retrieval_manifest_card_count": retrieval["card_count"],
            "retrieval_policy_source": (RUNTIME / "llm_generation/knowledge/v2/constraint_retriever.py").as_posix(),
            "retrieval_policy_note": "Source inspection: approved adds 5 ranking points; it is not an inclusion gate.",
            "configured_rule_backends": backends,
            "representative_constraint": {
                "id": RULE_ID, "source_document": source["document"],
                "source_line": source["start_line"], "source_text_sha256": source["sha256"],
                "quality": record["quality"], "planned_implementation": rule["implementation"],
                "formal_spec_status": rule["formal_spec"]["status"],
                "executed_status": result["status"], "applicable_count": result["applicable_count"],
                "checked_count": result["checked_count"],
            },
            "field_trace": {
                "case": "ASW-FULL-01", "repetition": 1, "repair": "off",
                "metamodel_property": "groups.TimingEvent.elements[name=period]",
                "requested_period_seconds": str(requested_period),
                "schema_member": schema_name, "schema_pointer": "/" + schema_pointer,
                "period_schema": period_schema, "runnable_declaration": runnable.findtext("{*}SHORT-NAME"),
                "artifact_target": reference.text, "artifact_period": event.findtext("{*}PERIOD"),
                "artifact_member": xml_name, "artifact_sha256": sha256(xml_bytes),
                "recorded_xsd_files_passed": len(evaluation["xsd"]),
                "recorded_task_period_obligation": obligation,
                "task_decision": evaluation["decision"], "full_corpus_decision": evaluation["full_corpus_decision"],
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        report = inspect(args.release_root.resolve())
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, ET.ParseError) as error:
        print(f"ICM evidence inspection failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
