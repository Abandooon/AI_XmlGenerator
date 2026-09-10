#!/usr/bin/env python3
"""Offline review of the sealed Terra continuation; never imports a provider.

Run with Python 3.12 and a NEW output directory:
  python review/verify_final.py --output /path/to/new-review-directory
The package root defaults to this script's parent directory. The bundled Java
8 runtime is used unless --java is supplied. No generation, serialization,
credential-file access, model request, or modification of sealed inputs occurs.

The report separates evidence integrity from study completion. An intact,
incomplete run can pass evidence checks but never receives COMPLETE status or
the planned all-task significance tests. All output files are newly created.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ARMS = ("G0", "GS", "GF")
RESERVATION = 1_093_728_000
CAP = 5_000_000_000
ORIGINAL_UNKNOWN = "BAL-3-07/G0/shared_initial"
ACK = "ACKNOWLEDGED_UNKNOWN_OCCUPIED"
SCORE_FIELDS = ("strict_success", "status", "oracle_agreement", "task_results",
                "frame_errors", "independent_query_matches")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def identity(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def usd(nano):
    return format(Decimal(nano) / Decimal(1_000_000_000), ".9f")


def need(condition, message):
    if not condition:
        raise ValueError(message)


def local(base, relative):
    """Accept portable relative evidence paths only; never use author sources."""
    relative = str(relative).replace("\\", "/")
    need(not relative.startswith("/") and ":" not in relative, "Absolute evidence path: " + relative)
    path = (base / relative).resolve()
    need(path.is_relative_to(base.resolve()), "Evidence path escapes package: " + relative)
    return path


def verify_manifest(directory, name="MANIFEST.json", exhaustive=False):
    manifest = read(directory / name)
    need(isinstance(manifest, dict), "Manifest is not a mapping")
    for relative, expected in manifest.items():
        path = local(directory, relative)
        need(path.is_file() and sha(path) == expected, "Manifest mismatch: " + relative)
    if exhaustive:
        actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*")
                  if p.is_file() and p.name not in {name, "RUNNING.lock"}}
        need(actual == set(manifest), "Run manifest membership differs")
    return {"files": len(manifest), "manifest_sha256": sha(directory / name), "all_match": True}


def prices(usage):
    """Independent integer arithmetic using the user-supplied USD/M prices."""
    need(isinstance(usage, dict), "Missing usage")
    p, c = usage.get("prompt_tokens"), usage.get("completion_tokens")
    need(type(p) is int and type(c) is int and p >= 0 and c >= 0, "Invalid token counts")
    need(usage.get("total_tokens") == p + c, "Usage total does not equal input + completion")
    details = usage.get("prompt_tokens_details") or {}
    reads = details.get("cached_tokens")
    writes = details.get("cache_write_tokens", details.get("cache_creation_input_tokens"))
    need(type(reads) is int and type(writes) is int and reads >= 0 and writes >= 0
         and reads + writes <= p, "Cache components unavailable, overlapping, or invalid")
    ordinary = p - reads - writes
    return {"prompt_tokens": p, "completion_tokens": c, "total_tokens": p + c,
            "ordinary_input_tokens": ordinary, "cache_read_tokens": reads, "cache_write_tokens": writes,
            "cache_estimate_nano": ordinary * 3000 + reads * 300 + writes * 3750 + c * 18000,
            "base_estimate_nano": p * 3000 + c * 18000,
            "conservative_occupied_nano": p * 3750 + c * 18000}


def budget_replay(path):
    entries, events, previous, denials, maximum = {}, [], "0" * 64, 0, 0
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        event = json.loads(line)
        payload = {k: v for k, v in event.items() if k != "hash"}
        need(event["hash"] == identity(payload) and event["previous"] == previous
             and event["sequence"] == number, "Budget chain/sequence mismatch")
        previous = event["hash"]
        kind, key = event["kind"], event["key"]
        occupied_before = sum(e["occupied"] for e in entries.values())
        if kind == "RESERVE":
            need(key not in entries, "Duplicate reservation: " + key)
            need(not any(e["state"] in {"UNKNOWN", "RESERVED", "VIOLATION"} for e in entries.values()),
                 "Dispatch after unresolved request: " + key)
            need(event["reserved_nano"] == RESERVATION and event["cap_nano"] == CAP,
                 "Changed reservation or cap")
            need(event["occupied_after_nano"] == occupied_before + RESERVATION <= CAP,
                 "Pre-dispatch ceiling failure")
            entries[key] = {"state": "RESERVED", "occupied": RESERVATION, "reserve": event}
            maximum = max(maximum, occupied_before + RESERVATION)
        elif kind in {"SETTLE", "UNKNOWN", "VIOLATION"}:
            need(key in entries and entries[key]["state"] == "RESERVED", "Invalid budget transition")
            if kind == "UNKNOWN":
                need(event["occupied_nano"] == RESERVATION and event.get("usage") is None,
                     "Unknown request reservation was released")
            else:
                cost = prices(event["usage"])
                need(event["occupied_nano"] == cost["conservative_occupied_nano"], "Settlement mismatch")
                need(event["estimated_base_nano"] == cost["base_estimate_nano"], "Base estimate mismatch")
                cached = event.get("cache_estimate") or {}
                need(cached.get("nano_usd") == cost["cache_estimate_nano"], "Cached estimate mismatch")
                for field in ("ordinary_input_tokens", "cache_read_tokens", "cache_write_tokens"):
                    need(cached.get(field) == cost[field], "Cache component mismatch: " + field)
                need(cost["prompt_tokens"] <= 272000 and cost["completion_tokens"] <= 4096,
                     "Reported usage exceeded the protocol limit")
                entries[key]["cost"] = cost
            entries[key].update(state=kind, occupied=event["occupied_nano"], terminal=event)
        elif kind == ACK:
            need(key == ORIGINAL_UNKNOWN and entries[key]["state"] == "UNKNOWN"
                 and event["occupied_nano"] == entries[key]["occupied"] == RESERVATION,
                 "Acknowledgment changed the unknown occupancy")
            entries[key]["state"] = ACK
        elif kind == "DENY":
            need(event.get("network_dispatched") is False, "Budget denial marked dispatched")
            denials += 1
        else:
            raise ValueError("Unexpected budget event " + kind)
        events.append(event)
    need(not any(e["state"] == "RESERVED" for e in entries.values()), "Unsettled reservation in final ledger")
    return entries, events, maximum, denials


def raw_calls(base, run, entries):
    """Union by logical key, proving copied receipts are identical before dedup."""
    inventory, copied = {}, 0
    for directory in (base / "run", run):
        for intent_path in sorted((directory / "tasks").rglob("intent.json")):
            folder = intent_path.parent
            intent, request, wire = read(intent_path), read(folder / "request.json"), read(folder / "http_request_body.json")
            key = intent["logical_key"]
            need(key in entries, "Intent has no reservation: " + key)
            need(identity(request) == intent["request_sha256"] and request["wire_body"] == wire,
                 "Request identity mismatch: " + key)
            wire_sha = sha(folder / "http_request_body.json")
            need(wire_sha == intent["wire_sha256"] == entries[key]["reserve"]["wire_sha256"],
                 "Wire identity mismatch: " + key)
            need(wire_sha == identity(wire), "Noncanonical request bytes")
            expected = {"model": "gpt-5.6-terra", "seed": 104729, "reasoning_effort": "low",
                        "temperature": 1, "max_completion_tokens": 4096, "stream": False}
            need(all(wire.get(k) == v for k, v in expected.items()), "Request configuration changed: " + key)
            need(wire.get("response_format", {}).get("json_schema", {}).get("strict") is True,
                 "Strict schema missing: " + key)
            item = {"key": key, "wire_sha256": wire_sha,
                    "source": folder.relative_to(base).as_posix(), "intent_sha256": sha(intent_path)}
            response_path, raw_path = folder / "response.json", folder / "http_response_body.json"
            if response_path.exists():
                response, raw, metadata = read(response_path), read(raw_path), read(folder / "http_response_metadata.json")
                need(response.get("usage") == raw.get("usage") == entries[key]["terminal"].get("usage"),
                     "Raw HTTP usage differs from copied usage: " + key)
                raw_sha = sha(raw_path)
                need(raw_sha == metadata["stored_raw_sha256"] == response["raw_binding"]["stored_raw_sha256"],
                     "Raw HTTP byte hash mismatch: " + key)
                need(not metadata["credential_redaction_required"] and raw_sha == metadata["received_raw_sha256"],
                     "Received raw response identity cannot be verified")
                need(response["request_sha256"] == intent["request_sha256"], "Response/request binding mismatch")
                choice = (raw.get("choices") or [{}])[0]
                message = choice.get("message") or {}
                need(response["finish_reason"] == choice.get("finish_reason") and
                     response["response_model"] == raw.get("model") and response["response_id"] == raw.get("id"),
                     "Response fields disagree with raw HTTP")
                need(response["text"] == (message.get("content") if isinstance(message.get("content"), str) else ""),
                     "Normalized response text differs from raw HTTP")
                need(metadata["status"] == 200 and entries[key]["state"] == "SETTLE", "Non-successful received call")
                item.update(response_sha256=sha(response_path), raw_sha256=raw_sha, known=True,
                            cost=prices(raw["usage"]), finish_reason=choice.get("finish_reason"),
                            refusal=bool(message.get("refusal")), response_id=raw.get("id"))
            else:
                need(not raw_path.exists() and (folder / "unknown.json").exists(), "Missing response lacks unknown record")
                need(entries[key]["state"] in {"UNKNOWN", ACK}, "No-body request is not recorded unknown")
                need(read(folder / "unknown.json").get("usage") is None, "Unknown has fabricated usage")
                item.update(known=False, unknown_sha256=sha(folder / "unknown.json"))
            if key in inventory:
                old = {k: v for k, v in inventory[key].items() if k != "source"}
                new = {k: v for k, v in item.items() if k != "source"}
                need(old == new, "Reused request/response changed: " + key)
                copied += 1
            else:
                inventory[key] = item
    need(set(inventory) == set(entries), "Reservation and physical intent sets differ")
    response_ids = [i["response_id"] for i in inventory.values() if i["known"]]
    need(len(response_ids) == len(set(response_ids)), "Duplicate response ID across distinct calls")
    replacement = "CONTINUATION1/" + ORIGINAL_UNKNOWN
    need(ORIGINAL_UNKNOWN in inventory and not inventory[ORIGINAL_UNKNOWN]["known"], "Original unknown lost")
    need(replacement in inventory and inventory[replacement]["wire_sha256"] == inventory[ORIGINAL_UNKNOWN]["wire_sha256"],
         "Manual replacement changed the request")
    return inventory, copied


def exact_comparison(first, second):
    both = sum(x and y for x, y in zip(first, second))
    only_first = sum(x and not y for x, y in zip(first, second))
    only_second = sum(y and not x for x, y in zip(first, second))
    discordant = only_first + only_second
    p = min(1.0, 2 * sum(math.comb(discordant, k) for k in range(min(only_first, only_second) + 1))
            / (2 ** discordant)) if discordant else 1.0
    return {"both_success": both, "only_first_success": only_first, "only_second_success": only_second,
            "neither_success": len(first) - both - only_first - only_second,
            "second_minus_first_pp": 100 * (sum(second) - sum(first)) / len(first), "exact_two_sided_p": p}


def comparisons(rows, tasks):
    result, running = {}, 0.0
    for first in ("G0", "GS"):
        result[first + "_vs_GF"] = exact_comparison([rows[t, first]["strict_success"] for t in tasks],
                                                    [rows[t, "GF"]["strict_success"] for t in tasks])
    for rank, key in enumerate(sorted(result, key=lambda k: result[k]["exact_two_sided_p"])):
        running = max(running, min(1.0, result[key]["exact_two_sided_p"] * (2 - rank)))
        result[key]["holm_p"] = running
    return result


def native_module(base):
    path = base / "raw_native_score.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(n.name.split(".")[0] for n in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module.split(".")[0])
    need(imports <= {"pathlib", "copy", "hashlib", "json", "os", "subprocess"}, "Unexpected native scorer import")
    spec = importlib.util.spec_from_file_location("frozen_raw_native_score", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rebind_native_evidence(base, value):
    historical = value["native_evidence"].replace("\\", "/")
    for suffix in ("/continuation/run/native_evidence/", "/run/native_evidence/"):
        if suffix in historical:
            relative = suffix.strip("/") + "/" + historical.split(suffix, 1)[1]
            return local(base, relative)
    raise ValueError("Unrecognized retained native evidence path")


def score_endpoints(base, run, output, design, java, native):
    library = base / "workspace/native_validation/legacy_build/native-verifier/build/native-dist/lib"
    rows, cache, replays, artifact_count = {}, {}, [], 0
    for entry in design["tasks"]:
        task_id = entry["task_id"]
        public_path = local(base, entry["task_file"])
        need(sha(public_path) == entry["task_file_sha256"], "Fixed task changed: " + task_id)
        public = read(public_path)
        for arm in ARMS:
            branch = run / "tasks" / task_id / ("shared_generation" if arm == "G0" else arm)
            result_path = branch / "result.json"
            result = read(result_path) if result_path.exists() else None
            state = result.get("status", result.get("stop_reason")) if result else "NOT_RUN"
            row = {"task_id": task_id, "arm": arm, "state": state, "known_endpoint": False,
                   "strict_success": None, "model_failure": None, "artifact_valid": None,
                   "failure_type": state, "requests": 0, "prompt_tokens": 0, "completion_tokens": 0}
            responses = [read(p) for p in branch.glob("*/response.json")]
            row.update(requests=len(responses),
                       prompt_tokens=sum(r["usage"]["prompt_tokens"] for r in responses),
                       completion_tokens=sum(r["usage"]["completion_tokens"] for r in responses),
                       truncations=sum(r.get("finish_reason") == "length" for r in responses),
                       refusals=sum(bool(r.get("refusal")) for r in responses),
                       unknown_usage=sum(r.get("usage") is None for r in responses))
            artifact = branch / ("artifact" if arm == "G0" else "final_artifact")
            xmi, identities = artifact / "model.xmi", artifact / "identity.json"
            retained_path = branch / ("independent.json" if arm == "G0" else "independent_final.json")
            if xmi.exists():
                artifact_count += 1
                need(identities.exists() and retained_path.exists(), "Artifact lacks identity/score")
                need(read(branch / "task_spec.json") == public, "Branch task differs from fixed public input")
                envelope = read(retained_path)
                value = envelope["value"]
                need(envelope["sha256"] == identity(value), "Score envelope hash mismatch")
                xmi_sha, identity_sha = sha(xmi), sha(identities)
                need(value["artifact_sha256"] == xmi_sha and value["identity_sha256"] == identity_sha,
                     "Retained score uses other artifact bytes")
                evidence = rebind_native_evidence(base, value)
                need(read(evidence / "score.json") == value, "Retained score/native evidence mismatch")
                need(read(evidence / "native.json") == value["native_receipt"], "Retained native receipt mismatch")
                cache_key = (xmi_sha, identity_sha, sha(public_path))
                if cache_key not in cache:
                    receipt_path = output / "native" / ("group_%03d.json" % (len(cache) + 1))
                    receipt = native.run_native(xmi, identities, receipt_path, java, library)
                    rescored = native.score_native_receipt(receipt, public)
                    cache[cache_key] = (rescored, receipt_path)
                rescored, receipt_path = cache[cache_key]
                for field in SCORE_FIELDS:
                    need(rescored.get(field) == value.get(field), "Native scientific field mismatch: " + task_id + "/" + arm + "/" + field)
                need(sha(xmi) == xmi_sha and sha(identities) == identity_sha, "Native input modified")
                row.update(artifact_valid=rescored["strict_success"], xmi_sha256=xmi_sha, identity_sha256=identity_sha,
                           native_output=receipt_path.relative_to(output).as_posix(),
                           task_failures=[r["id"] for r in rescored.get("task_results", []) if not r["pass"]],
                           frame_failures=rescored.get("frame_errors", []),
                           query_failures={k: len(v) for k, v in rescored.get("independent_query_matches", {}).items() if v})
                if state not in {"UNKNOWN_RESPONSE", "NOT_RUN_SHARED_RESPONSE_UNKNOWN", "NOT_RUN"}:
                    row["known_endpoint"] = rescored["status"] == "EVALUATED" and rescored["oracle_agreement"] is True
                    if row["known_endpoint"]:
                        row["strict_success"] = rescored["strict_success"]
                        row["model_failure"] = not rescored["strict_success"]
                        if row["strict_success"]:
                            row["failure_type"] = "NONE_FINAL_ARTIFACT_VALID"
                replays.append({"task_id": task_id, "arm": arm, "xmi": xmi.relative_to(base).as_posix(),
                                "known_endpoint": row["known_endpoint"], "artifact_valid": row["artifact_valid"],
                                "native_output": row["native_output"], "score_fields_match": True})
            elif result:
                if state in {"ASSIGNMENT_REJECTED", "NOT_RUN_SHARED_ASSIGNMENT_REJECTED"}:
                    if arm != "G0":
                        shared = read(run / "tasks" / task_id / "shared_generation/result.json")
                        need(shared.get("status") == "ASSIGNMENT_REJECTED", "Derived failure lacks rejected shared assignment")
                    row.update(known_endpoint=True, strict_success=False, model_failure=True)
                else:
                    need(state in {"UNKNOWN_RESPONSE", "NOT_RUN_SHARED_RESPONSE_UNKNOWN"}, "Unclassified no-artifact result: " + state)
            rows[task_id, arm] = row
    return rows, {"final_artifacts_checked": artifact_count, "unique_native_groups": len(cache),
                  "grouping": "Identical XMI bytes, identity bytes, and fixed task bytes", "score_mismatches": 0,
                  "rows": replays}


def validate_schema(report):
    need(report["evidence_integrity"] in {"PASS", "FAIL"}, "Invalid evidence status")
    need(report["study_completion"] in {"COMPLETE", "INCOMPLETE", "NOT_ASSESSED"}, "Invalid completion status")
    if report["evidence_integrity"] == "PASS":
        need(report["scope"]["network_calls"] == 0 and report["scope"]["generation_modules_imported"] is False,
             "Offline review scope violated")
        counts = report["task_completion"]
        need(counts["complete"] + counts["partial"] + counts["unstarted"] == 24, "Task count mismatch")
        if report["study_completion"] == "INCOMPLETE":
            need(report["planned_statistics"]["executed"] is False and report["planned_statistics"]["contrasts"] == {},
                 "Inferential statistics executed on incomplete study")


def review(base, output, java):
    run = base / "continuation/run"
    need((run / "RESULTS.json").is_file() and (run / "EXECUTION_STATUS.json").is_file(), "No sealed final result")
    need(not (base / "run/RUNNING.lock").exists() and not (run / "RUNNING.lock").exists(), "Run is still active")
    result, execution, design = read(run / "RESULTS.json"), read(run / "EXECUTION_STATUS.json"), read(base / "DESIGN.json")
    need(result["status"] == execution["status"], "Final status differs between records")
    tasks = [e["task_id"] for e in design["tasks"]]
    need(len(tasks) == len(set(tasks)) == 24 and all(e["seed"] == 104729 for e in design["tasks"]), "Wrong task set/seed")
    manifests = {"original_code_data": verify_manifest(base, "EXECUTION_SEAL.json"),
                 "original_run": verify_manifest(base / "run", exhaustive=True),
                 "continuation_seal": verify_manifest(base / "continuation", "CONTINUATION_SEAL.json"),
                 "continuation_run": verify_manifest(run, exhaustive=True)}
    amendment = read(base / "continuation/PROTOCOL_AMENDMENT.json")
    bindings = {"original_design_sha256": "DESIGN.json", "original_execution_seal_sha256": "EXECUTION_SEAL.json",
                "original_run_manifest_sha256": "run/MANIFEST.json", "original_budget_sha256": "run/BUDGET.jsonl",
                "original_results_sha256": "run/RESULTS.json"}
    for key, relative in bindings.items():
        need(amendment[key] == sha(base / relative), "Original amendment binding mismatch: " + key)
    source = read(base / "SOURCE_MANIFEST.json")
    preparation = read(base / "PREPARATION_REPORT.json")
    declared_adaptations = {r["path"]: r for r in preparation["changed_historical_source_files"]}
    need(len(declared_adaptations) == len(preparation["changed_historical_source_files"]),
         "Duplicate historical source adaptation")
    actual_adaptations = []
    execution_seal = read(base / "EXECUTION_SEAL.json")
    for relative, record in source["files"].items():
        source_path = local(base, "workspace/" + relative)
        actual = sha(source_path)
        need(execution_seal[source_path.relative_to(base).as_posix()] == actual,
             "Workspace not bound by execution seal")
        if actual != record["sha256"]:
            adaptation = declared_adaptations.get(relative)
            need(adaptation is not None and adaptation["historical_sha256"] == record["sha256"]
                 and adaptation["supplement_sha256"] == actual, "Undeclared historical source adaptation: " + relative)
            actual_adaptations.append(adaptation)
        else:
            need(relative not in declared_adaptations, "Declared source adaptation did not change bytes")
    need({r["path"] for r in actual_adaptations} == set(declared_adaptations), "Unbound source adaptation")
    original_bytes, combined_bytes = (base / "run/BUDGET.jsonl").read_bytes(), (run / "BUDGET.jsonl").read_bytes()
    need(combined_bytes.startswith(original_bytes), "Original budget is not an exact inherited byte prefix")
    original_entries, original_events, _, _ = budget_replay(base / "run/BUDGET.jsonl")
    entries, events, maximum, denials = budget_replay(run / "BUDGET.jsonl")
    need(events[len(original_events)]["kind"] == ACK, "Original unknown was not preserved at continuation start")
    need(sum(e["occupied"] for e in original_entries.values()) == 1_210_467_000, "Original budget starting amount differs")
    need(entries[ORIGINAL_UNKNOWN]["state"] == ACK and entries[ORIGINAL_UNKNOWN]["occupied"] == RESERVATION,
         "Original unknown lost permanent occupancy")
    for task in amendment["reuse_completed_tasks"]:
        old, new = base / "run/tasks" / task, run / "tasks" / task
        old_files = {p.relative_to(old).as_posix(): sha(p) for p in old.rglob("*") if p.is_file()}
        new_files = {p.relative_to(new).as_posix(): sha(p) for p in new.rglob("*") if p.is_file()}
        need(old_files == new_files, "Completed original task was changed during reuse")
    calls, copied = raw_calls(base, run, entries)
    known = [r for r in calls.values() if r["known"]]
    unknown = [r for r in calls.values() if not r["known"]]
    sums = {k: sum(r["cost"][k] for r in known) for k in known[0]["cost"]}
    unknown_upper = len(unknown) * RESERVATION
    occupied = sum(e["occupied"] for e in entries.values())
    need(occupied == sums["conservative_occupied_nano"] + unknown_upper, "Known plus unknown occupancy mismatch")
    summary_expected = {"known_base_price_estimate_usd": usd(sums["base_estimate_nano"]),
                        "cache_component_estimate_usd": usd(sums["cache_estimate_nano"]),
                        "known_prompt_tokens": sums["prompt_tokens"], "known_completion_tokens": sums["completion_tokens"],
                        "reserved_requests": len(entries), "occupied_upper_usd": usd(occupied),
                        "remaining_unoccupied_usd": usd(CAP - occupied), "cache_component_estimate_responses": len(known),
                        "cache_components_unknown_responses": 0, "denials": denials}
    for source_summary in (result["monetary"], execution["budget"]):
        for key, expected in summary_expected.items():
            need(source_summary[key] == expected, "Budget summary mismatch: " + key)
    native = native_module(base)
    rows, native_report = score_endpoints(base, run, output, design, java, native)
    need(len(result["rows"]) == 72, "Final results dropped planned endpoints")
    published = {(r["task_id"], r["arm"]): r for r in result["rows"]}
    need(set(published) == set(rows), "Published endpoint identities differ")
    for key, actual in rows.items():
        old = published[key]
        for field in ("known_endpoint", "model_failure", "requests", "prompt_tokens", "completion_tokens", "truncations", "refusals", "unknown_usage"):
            need(old.get(field) == actual.get(field), "Endpoint mismatch: " + str(key) + "/" + field)
        need(old["strict_success"] == (actual["strict_success"] if actual["known_endpoint"] else False),
             "Published success differs from independent classification")
        if actual["known_endpoint"]:
            need(old["failure_type"] == actual["failure_type"], "Failure classification mismatch")
            for field in ("task_failures", "frame_failures", "query_failures"):
                need(old.get(field) == actual.get(field), "Failure detail mismatch: " + field)
    complete = [t for t in tasks if all(rows[t, a]["known_endpoint"] for a in ARMS)]
    partial = [t for t in tasks if t not in complete and (run / "tasks" / t).exists()]
    unstarted = [t for t in tasks if t not in complete and t not in partial]
    groups = {}
    for arm in ARMS:
        arm_rows = [rows[t, arm] for t in tasks]
        expected = {"planned": 24, "known": sum(r["known_endpoint"] for r in arm_rows),
                    "strict_success": sum(r["strict_success"] is True for r in arm_rows),
                    "received_responses": sum(r["requests"] for r in arm_rows),
                    "prompt_tokens": sum(r["prompt_tokens"] for r in arm_rows),
                    "completion_tokens": sum(r["completion_tokens"] for r in arm_rows)}
        for key, value in expected.items():
            need(result["groups"][arm][key] == value, "Group total mismatch: " + arm + "/" + key)
        need(result["groups"][arm]["strict_success_rate_all_planned"] == expected["strict_success"] / 24,
             "Published all-planned fraction mismatch")
        groups[arm] = {**expected, "unknown_or_not_run": 24 - expected["known"],
                       "known_model_failures": sum(r["model_failure"] is True for r in arm_rows),
                       "all_planned_fraction_is_only_known_success_lower_bound": len(complete) != 24}
    all_known = len(complete) == 24
    need(result["all_72_endpoints_known"] == all_known, "Completion flag mismatch")
    need((execution["status"] == "COMPLETE") == all_known, "Overall completion status mismatch")
    inferential = comparisons(rows, tasks) if all_known else {}
    need(result["exploratory_mcnemar_holm"] == inferential, "Planned McNemar/Holm mismatch or improperly executed")
    baseline = read(base / "historical_luna/BASELINE_ROWS.json")
    lookup = {(r["unit_id"].split(":")[1], r["arm"]): r for r in baseline}
    need(len(baseline) == len(lookup) == 72 and set(lookup) == set(rows), "Luna matched subset differs")
    pairs = []
    for task in tasks:
        for arm in ARMS:
            old, new = lookup[task, arm], rows[task, arm]
            state = old["state"]
            success = False if state in {"ASSIGNMENT_REJECTED", "NOT_RUN_SHARED_ASSIGNMENT_REJECTED"} else None if state in {"UNKNOWN_RESPONSE", "NOT_RUN_SHARED_RESPONSE_UNKNOWN"} else old["final_valid"]
            pairs.append({"task_id": task, "arm": arm, "luna_success": success,
                          "luna_trace_artifact_final_valid": old["final_valid"], "luna_state": state,
                          "supplement_success": new["strict_success"] if new["known_endpoint"] else None})
    need(result["luna_same_task_pairs_descriptive_only"] == pairs, "Luna/Terra paired objects differ")
    truncations = sum(r["finish_reason"] == "length" for r in known)
    refusals = sum(r["refusal"] for r in known)
    need(result["truncations"] == truncations and result["refusals"] == refusals, "Truncation/refusal total differs")
    need(result["combined_original_and_continuation_dispatch_intents"] == len(calls)
         and result["unknown_usage_transport_attempts_total"] == len(unknown), "Combined transport count differs")
    for row in native_report["rows"]:
        if not row["known_endpoint"]:
            row["endpoint_note"] = "Retained candidate may be valid; incomplete response prevents a known completed endpoint."
    subset = {a: {"denominator": len(complete), "terra_success": sum(rows[t, a]["strict_success"] for t in complete),
                  "luna_success": sum(p["luna_success"] is True for p in pairs if p["task_id"] in complete and p["arm"] == a)} for a in ARMS}
    # Verify input identities once more after native execution, including native evidence and budgets.
    verify_manifest(base / "run", exhaustive=True)
    verify_manifest(run, exhaustive=True)
    return {"schema_version": "atlas.terra.independent-audit/1", "evidence_integrity": "PASS",
            "study_completion": "COMPLETE" if all_known else "INCOMPLETE", "audited_utc": datetime.now(timezone.utc).isoformat(),
            "source_results_sha256": sha(run / "RESULTS.json"), "review_script_sha256": sha(Path(__file__)),
            "scope": {"network_calls": 0, "credential_files_read": False, "generation_modules_imported": False,
                      "serializer_modules_imported": False, "native_scorer": "raw_native_score.py",
                      "java": str(java), "source_files_modified": False},
            "manifests": manifests,
            "historical_source_adaptations": {"count": len(actual_adaptations), "records": actual_adaptations,
                "meaning": "SOURCE_MANIFEST identifies historical inputs; PREPARATION_REPORT declares these adaptations and EXECUTION_SEAL binds the exact supplement files."},
            "task_completion": {"planned": 24, "complete": len(complete), "partial": len(partial), "unstarted": len(unstarted),
                                "complete_task_ids": complete, "partial_task_ids": partial, "unstarted_task_ids": unstarted,
                                "complete_tasks_form_execution_prefix": complete == tasks[:len(complete)]},
            "groups": groups, "endpoints": list(rows.values()), "native_revalidation": native_report,
            "completed_task_subset_descriptive_only": subset,
            "subset_limitation": "Completed tasks are a post-hoc execution-order subset, not the planned complete study or an independently selected evaluation sample.",
            "planned_statistics": {"executed": all_known, "contrasts": inferential,
                                   "reason": "All 24 tasks completed" if all_known else "Prespecified completeness requirement not met; no subset McNemar/Holm tests performed"},
            "paired_luna_terra": pairs,
            "usage_and_cost": {**{k: v for k, v in sums.items() if not k.endswith("_nano")},
                "received_unique_responses": len(known), "combined_dispatch_intents": len(calls),
                "duplicate_inherited_receipts_counted_once": copied,
                "raw_http_usage_matches_ledger": True, "original_budget_prefix_bytes_identical": True,
                "known_base_price_estimate_usd": usd(sums["base_estimate_nano"]),
                "known_cache_component_price_estimate_usd": usd(sums["cache_estimate_nano"]),
                "known_conservative_occupancy_usd": usd(sums["conservative_occupied_nano"]),
                "original_unknown_occupied_usd": usd(RESERVATION), "unknown_requests": [r["key"] for r in unknown],
                "unknown_reserved_upper_usd": usd(unknown_upper),
                "known_cache_estimate_plus_unknown_upper_usd": usd(sums["cache_estimate_nano"] + unknown_upper),
                "combined_conservative_occupancy_usd": usd(occupied), "maximum_predispatch_occupancy_usd": usd(maximum),
                "cap_usd": usd(CAP), "within_client_cap": occupied <= CAP, "not_a_provider_invoice": True,
                "price_basis_usd_per_million": {"ordinary_input": "3", "cache_read": "0.3", "cache_write": "3.75", "completion_including_reasoning": "18"},
                "assumptions": "Returned cache read/write counts are disjoint subsets of prompt tokens; estimates use supplied rates and are not independently authenticated billing.",
                "known_max_completion_tokens": max(r["cost"]["completion_tokens"] for r in known),
                "received_responses_at_completion_cap": sum(r["cost"]["completion_tokens"] == 4096 for r in known),
                "truncations": truncations, "refusals": refusals},
            "calls": list(calls.values()), "errors": []}


def self_test():
    usage = {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120,
             "prompt_tokens_details": {"cached_tokens": 40, "cache_write_tokens": 50}}
    p = prices(usage)
    need(p["cache_estimate_nano"] == 589500 and p["conservative_occupied_nano"] == 735000, "Price test failed")
    try:
        prices({**usage, "prompt_tokens_details": {"cached_tokens": 60, "cache_write_tokens": 50}})
    except ValueError:
        pass
    else:
        raise ValueError("Overlapping cache components were accepted")
    x = exact_comparison([False] * 5, [True] * 5)
    need(x["exact_two_sided_p"] == 0.0625 and x["only_second_success"] == 5, "Exact test failed")
    need(exact_comparison([True, False], [True, False])["exact_two_sided_p"] == 1, "Zero-discordance test failed")
    print(json.dumps({"self_test": "PASS", "checks": 4, "network_calls": 0}))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="New output directory; existing directories are rejected")
    parser.add_argument("--java", type=Path, help="Optional Java 8 executable")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    need(args.output is not None, "--output is required")
    base, output = args.package_root.resolve(), args.output.resolve()
    need(not output.exists(), "Output must be a new directory; refusing overwrite")
    for protected in (base / "run", base / "continuation", base / "workspace", base / "inputs", base / "historical_luna"):
        need(not output.is_relative_to(protected), "Output is inside sealed evidence")
    java = args.java.resolve() if args.java else base / "workspace/native_validation/toolchain/jdk8/jdk8u504-b01/bin/java.exe"
    need(java.is_file(), "Java executable not found")
    # Python networking is forbidden for the review process; no provider is imported.
    def audit_event(event, arguments):
        if event.startswith("socket."):
            raise RuntimeError("Network operation blocked during offline review")
    sys.addaudithook(audit_event)
    output.mkdir(parents=True, exist_ok=False)
    try:
        report = review(base, output, java)
        validate_schema(report)
    except Exception as error:
        report = {"schema_version": "atlas.terra.independent-audit/1", "evidence_integrity": "FAIL",
                  "study_completion": "NOT_ASSESSED", "errors": [{"type": type(error).__name__, "message": str(error)}]}
    destination = output / "terra_independent_audit.json"
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"report": str(destination), "evidence_integrity": report["evidence_integrity"],
                      "study_completion": report["study_completion"], "errors": report["errors"]}, ensure_ascii=False))
    return 0 if report["evidence_integrity"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
