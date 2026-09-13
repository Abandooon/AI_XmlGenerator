#!/usr/bin/env python3
"""Offline replay from raw PIL answers to repair prompts, selection and release.

Uses the standard library only. No generation module is imported. A named
allowlist of pure functions is read from the frozen contract, prompt and scorer
sources. The finite schema used by this experiment is checked independently;
an unknown schema keyword is an error, not silently ignored. This is a record
consistency check, not a new legal judgment or provider authentication.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys
import types
from typing import Any, Iterable, Mapping

sys.dont_write_bytecode = True


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding="utf-8-sig").splitlines() if s.strip()]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def schema_errors(value, schema, path="$", *, vocabulary_check=True):
    allowed = {"$id", "$schema", "description", "type", "enum", "properties", "required",
               "additionalProperties", "items", "uniqueItems", "minLength", "pattern"}
    require(not (set(schema) - allowed), "Unsupported schema keywords: " + str(set(schema) - allowed))
    result = []
    typ = schema.get("type")
    types_ = {"object": dict, "array": list, "string": str, "boolean": bool}
    if typ:
        require(typ in types_, "Unsupported schema type " + typ)
        if type(value) is not types_[typ]:
            return [path + ": wrong type"]
    if "enum" in schema and value not in schema["enum"]:
        result.append(path + ": outside enumeration")
    if typ == "object":
        props = schema.get("properties", {})
        result += [path + ": missing " + k for k in schema.get("required", []) if k not in value]
        if schema.get("additionalProperties") is False and set(value) - set(props):
            result.append(path + ": additional properties")
        for k, v in value.items():
            if k in props:
                result += schema_errors(v, props[k], path + "." + k)
    if typ == "array":
        if schema.get("uniqueItems") and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            result.append(path + ": duplicate items")
        for i, v in enumerate(value):
            result += schema_errors(v, schema.get("items", {}), path + "[" + str(i) + "]")
    if typ == "string":
        if len(value) < schema.get("minLength", 0):
            result.append(path + ": too short")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            result.append(path + ": pattern mismatch")
    return result


def schema_findings(value, schema):
    return [{"code": "schema_invalid", "stage": "schema", "message": s} for s in schema_errors(value, schema)]


def pure_source(path, functions, constants=(), bindings=None):
    """Load named, inspectable pure definitions, never module import side effects."""
    source = Path(path).read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    module = types.ModuleType("pil_review_" + hashlib.sha256(str(path).encode()).hexdigest()[:12])
    sys.modules[module.__name__] = module
    module.__dict__.update(dict(json=json, re=re, math=math, random=random, hashlib=hashlib,
                                dataclass=dataclass, defaultdict=defaultdict, Mapping=Mapping,
                                Any=Any, Iterable=Iterable, Path=Path))
    module.__dict__.update(bindings or {})
    selected = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    found = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in functions:
            selected.append(node)
            found.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in constants:
                    module.__dict__[target.id] = ast.literal_eval(node.value)
                    found.add(target.id)
    require(set(functions) | set(constants) == found, "Missing frozen pure definitions in " + str(path))
    exec(compile(ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[])), str(path), "exec"), module.__dict__)
    return module


def load_context(root):
    folder = root / "experiments/pil/frozen/prepaid_freeze"
    contract = pure_source(folder / "pil_v4_contract.py",
        {"contains_cjk", "strict_json_parse", "provision_set", "evidence_set", "_has_prefix",
         "audit_decision", "fail_closed_decision", "GoldCompatibility", "score_against_gold", "seed_for_replicate"},
        {"ABSTAIN", "ATOMIC_FORUM_TYPES", "ARMS", "PROVIDER_PROTOCOL"}, {"schema_findings": schema_findings})
    arms = pure_source(folder / "pil_v4_arms.py",
        {"_norm", "_terms", "_affirmative_match", "FrozenRetriever", "_evidence_text", "_redact_cjk_for_prompt"},
        {"COMMON_PROMPT", "REPAIR_PROMPT", "TOP_K"}, {"contract": contract})
    scorer = pure_source(folder / "pil_v4_rescore.py",
        {"_percentile", "_bootstrap_difference", "_sign_test", "_validate_balanced_entries", "_citation_metrics",
         "score_row", "_mean", "summarize"},
        {"BOOTSTRAP_DRAWS", "BOOTSTRAP_SEED", "CONTRASTS"}, {"contract": contract})
    return folder, contract, arms, scorer


def replay(root, *, entries=None, statistics=False):
    folder, contract, arms, scorer = load_context(root)
    schema, rules = read(folder / "schema/decision_schema_v4.json"), read(folder / "rules/delivery_rules_v4.json")
    facts = {r["id"]: r for r in jsonl(folder / "data/inference_dataset_v41_en.jsonl")}
    gold = {r["id"]: r for r in jsonl(root / "experiments/pil/corrections/data/consensus_gold_v41_erratum1.jsonl")}
    rows = entries if entries is not None else jsonl(root / "experiments/pil/frozen/formal/PIL_V41_RUN_LEDGER.jsonl")
    scorer._validate_balanced_entries(rows, set(gold))
    retriever = arms.FrozenRetriever(jsonl(folder / "kb/authoritative_provisions_v41_en.jsonl"))
    checked, metrics, rebuilt = [], defaultdict(Counter), []
    repair_count = 0
    for entry in rows:
        row = entry["row"]
        uid, arm = row["unit_id"], row["mode"]
        initial, parse_error = contract.strict_json_parse(row["raw_text"])
        require(initial == row["parsed_decision"], uid + ": initial parse differs")
        initial_ok = isinstance(initial, dict) and not schema_errors(initial, schema)
        evidence = retriever.retrieve(facts[entry["case_id"]]["facts_text"]) if arm != "p0" else []
        evidence_ids = [e["evidence_id"] for e in evidence]
        require(evidence_ids == row["retrieved_evidence"], uid + ": retrieval differs")
        final, release, structural = initial, bool(initial_ok), bool(initial_ok)
        if arm == "p3":
            audit = contract.audit_decision(initial or {}, schema=schema, rules=rules, allowed_evidence=evidence_ids)
            require(audit == row["internal_audit"], uid + ": initial audit differs")
            needs_repair = audit["status"] != "PASS"
            require(needs_repair == row["repair"]["attempted"], uid + ": repair trigger differs")
            if needs_repair:
                repair_count += 1
                repaired, error = contract.strict_json_parse(row["repair"]["raw_text"])
                require(repaired == row["repair"]["decision"], uid + ": repair parse differs")
                ra = contract.audit_decision(repaired or {}, schema=schema, rules=rules, allowed_evidence=evidence_ids)
                require(ra == row["repair"]["audit"], uid + ": repair audit differs")
                release = ra["status"] == "PASS"
                final = repaired if release else contract.fail_closed_decision(r["code"] for r in ra["findings"])
                structural = not schema_errors(final, schema)
                prompt = arms.REPAIR_PROMPT.format(
                    facts=facts[entry["case_id"]]["facts_text"], evidence=arms._evidence_text(evidence),
                    schema=json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                    prior=json.dumps(arms._redact_cjk_for_prompt(initial), ensure_ascii=False, sort_keys=True),
                    findings=json.dumps(arms._redact_cjk_for_prompt(audit["findings"]), ensure_ascii=False, sort_keys=True))
                require(prompt == row["repair"]["prompt"], uid + ": reconstructed repair prompt differs")
        require(final == row["final_decision"], uid + ": final selection differs")
        require(release == row["system_release"], uid + ": release flag differs")
        require(structural == (row["schema_status"] == "PASS"), uid + ": schema status differs")
        fresh = copy.deepcopy(entry)
        fresh["row"].update(final_decision=final, system_release=release, schema_status="PASS" if structural else "FAIL")
        scored = scorer.score_row(fresh, gold[entry["case_id"]], schema, rules)
        checked.append(scored)
        rebuilt.append(fresh)
        m = metrics[arm]
        m["units"] += 1
        for key in ["structure_valid", "common_delivery_valid", "system_release", "gold_correct", "endpoint_success"]:
            m[key] += scored[key]
        for response in row["provider_responses"]:
            m["responses"] += 1
            m["tokens"] += response["usage"]["total_tokens"]
    expected = read(root / "experiments/pil/corrections/expected/PIL_V41_ERRATUM1_ANALYSIS.json")
    for fresh, saved in zip(checked, expected["scored_units"]):
        require({k: v for k, v in fresh.items() if k != "common_audit"} ==
                {k: v for k, v in saved.items() if k != "common_audit"},
                fresh["unit_id"] + ": raw-answer-derived scientific score differs")
        require(fresh["common_audit"]["status"] == saved["common_audit"]["status"],
                fresh["unit_id"] + ": common audit status differs")
        require([(v["code"], v["stage"]) for v in fresh["common_audit"]["findings"]] ==
                [(v["code"], v["stage"]) for v in saved["common_audit"]["findings"]],
                fresh["unit_id"] + ": common audit finding codes differ")
    result = {"status": "PASS", "raw_initial_answers_replayed": len(rows), "raw_repair_answers_and_prompts_replayed": repair_count,
              "schema_checker": "Independent finite-schema checker; only the frozen schema vocabulary is accepted",
              "source_loading": "Named pure-function AST allowlists; generation modules and API clients are not imported",
              "new_model_calls": 0, "full_legal_accuracy": "NOT_ESTIMATED", "arms": dict(metrics), "scored_units": checked}
    if statistics:
        result["summary"] = scorer.summarize(checked)
        require(result["summary"] == expected["summary"], "Fresh paired statistics differ from comparison target")
    return result


def self_test(root):
    original = jsonl(root / "experiments/pil/frozen/formal/PIL_V41_RUN_LEDGER.jsonl")
    cases = []
    for field in ["final_decision", "system_release", "schema_status", "repair_prompt"]:
        changed = copy.deepcopy(original)
        row = next(e["row"] for e in changed if e["row"]["repair"]["attempted"])
        if field == "final_decision": row[field]["forum"] = "MUTATED"
        elif field == "system_release": row[field] = not row[field]
        elif field == "schema_status": row[field] = "FAIL" if row[field] == "PASS" else "PASS"
        else: row["repair"]["prompt"] += " MUTATED"
        try:
            replay(root, entries=changed)
        except ValueError as error:
            cases.append({"mutation": field, "rejected": True, "diagnostic": str(error)})
        else:
            raise ValueError("Negative control was not rejected: " + field)
    return cases


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--output", type=Path, help="Optional external JSON file; default stdout")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    try:
        report = replay(args.root.resolve())
        report.pop("scored_units")
        if args.self_test: report["negative_controls"] = self_test(args.root.resolve())
    except Exception as error:
        report = {"status": "FAIL", "error": type(error).__name__ + ": " + str(error)}
    content = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        target = args.output.resolve()
        require(not target.is_relative_to(args.root.resolve()), "Output must be outside the release")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content + "\n", encoding="utf-8")
    print(content)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
