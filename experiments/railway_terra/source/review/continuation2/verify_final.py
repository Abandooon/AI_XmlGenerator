#!/usr/bin/env python3
"""Review the second technical continuation offline; preserve the old audit.

Use a NEW output directory, for example:
  delivery/runtime/python/python.exe -I -B review/continuation2/verify_final.py --output review/continuation2/editor_check
No provider, generator, serializer, credential file, or model request is used.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parents[2]
ARMS = ("G0", "GS", "GF")
ACK = "ACKNOWLEDGED_UNKNOWN_OCCUPIED"
UNKNOWN_KEYS = ("BAL-3-07/G0/shared_initial", "CONTINUATION1/BAL-1-03/GS/round_01")
REPLACEMENTS = ("CONTINUATION1/BAL-3-07/G0/shared_initial", "CONTINUATION2/BAL-1-03/GS/round_01")
RESERVATION = 1_093_728_000
PRIOR_REPORT_SHA = "4a062d8e548cb58f50b80bbe8195014d4c834615237a9982388547b633d5baec"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def classify_usage(usage):
    """Unavailable usage is distinct from intact but unitemized cache usage."""
    if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0
                                          for k in ("prompt_tokens", "completion_tokens")):
        return None
    p, c = usage["prompt_tokens"], usage["completion_tokens"]
    details = usage.get("prompt_tokens_details") or {}
    reads = details.get("cached_tokens")
    writes = details.get("cache_write_tokens", details.get("cache_creation_input_tokens"))
    cache_known = (type(reads) is int and type(writes) is int and reads >= 0 and writes >= 0 and reads + writes <= p)
    ordinary = p - reads - writes if cache_known else None
    return {"prompt_tokens": p, "completion_tokens": c, "total_tokens": p + c,
            "reported_total_tokens": usage.get("total_tokens"),
            "reported_total_matches_sum": usage.get("total_tokens") == p + c,
            "cache_breakdown_known": cache_known,
            "ordinary_input_tokens": ordinary, "cache_read_tokens": reads if cache_known else None,
            "cache_write_tokens": writes if cache_known else None,
            "cache_estimate_nano": ordinary * 3000 + reads * 300 + writes * 3750 + c * 18000 if cache_known else None,
            "base_estimate_nano": p * 3000 + c * 18000,
            "conservative_occupied_nano": p * 3750 + c * 18000}


def summarize_usage(calls):
    received = [r for r in calls.values() if r["known"]]
    usage_known = [r for r in received if r["cost"] is not None]
    cache_known = [r for r in usage_known if r["cost"]["cache_breakdown_known"]]
    keys = ("prompt_tokens", "completion_tokens", "total_tokens", "base_estimate_nano", "conservative_occupied_nano")
    sums = {k: sum(r["cost"][k] for r in usage_known) for k in keys}
    for key in ("ordinary_input_tokens", "cache_read_tokens", "cache_write_tokens", "cache_estimate_nano"):
        sums[key] = sum(r["cost"][key] for r in cache_known)
    return received, usage_known, cache_known, sums


def load_review_helpers(base):
    """Reuse only the earlier independent review's sealed pure helpers."""
    import hashlib
    path = base / "review/verify_final.py"
    prior = base / "review/check_003/terra_independent_audit.json"
    need(hashlib.sha256(prior.read_bytes()).hexdigest() == PRIOR_REPORT_SHA, "Historical audit changed")
    prior_report = read(prior)
    need(hashlib.sha256(path.read_bytes()).hexdigest() == prior_report["review_script_sha256"], "Historical review helper changed")
    spec = importlib.util.spec_from_file_location("earlier_independent_offline_review", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay_budget(path, old, approved_cap_nano=5_000_000_000):
    """Replay all three segments in one inherited ledger, exactly once."""
    entries, events, previous, maximum, denials = {}, [], "0" * 64, 0, 0
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        event = json.loads(line)
        need(event["hash"] == old.identity({k: v for k, v in event.items() if k != "hash"})
             and event["previous"] == previous and event["sequence"] == number, "Budget hash chain mismatch")
        previous = event["hash"]
        kind, key = event["kind"], event["key"]
        occupied_before = sum(e["occupied"] for e in entries.values())
        if kind == "RESERVE":
            need(key not in entries, "Existing dispatch key reused")
            need(not any(e["state"] in {"UNKNOWN", "RESERVED", "VIOLATION"} for e in entries.values()),
                 "Request dispatched with an unacknowledged unknown")
            expected_cap = approved_cap_nano if key.startswith("CONTINUATION2/") else 5_000_000_000
            need(event["reserved_nano"] == RESERVATION and event["cap_nano"] == expected_cap,
                 "Unapproved per-request reservation or total cap")
            need(event["occupied_after_nano"] == occupied_before + RESERVATION <= expected_cap,
                 "Pre-dispatch budget exceeded")
            need(event["input_tokens_reserved"] == 272000 and event["output_tokens_reserved"] == 4096,
                 "Changed token reservation")
            if key.startswith("CONTINUATION2/"):
                need(all(entries.get(k, {}).get("state") == ACK and entries[k]["occupied"] == RESERVATION
                         for k in UNKNOWN_KEYS), "Both old unknown reservations must precede new dispatch")
                need(len(entries) < 122, "Physical transmission bound exceeded")
            entries[key] = {"state": "RESERVED", "occupied": RESERVATION, "reserve": event}
            maximum = max(maximum, occupied_before + RESERVATION)
        elif kind in {"SETTLE", "UNKNOWN", "VIOLATION"}:
            need(key in entries and entries[key]["state"] == "RESERVED", "Invalid budget settlement transition")
            if kind == "UNKNOWN":
                need(event["occupied_nano"] == RESERVATION and event.get("usage") is None,
                     "Unknown usage fabricated or unknown reservation released")
            else:
                cost = classify_usage(event["usage"])
                need(cost is not None, "Known usage settlement has no usable token counts")
                need(event["occupied_nano"] == cost["conservative_occupied_nano"]
                     and event["estimated_base_nano"] == cost["base_estimate_nano"], "Known usage arithmetic mismatch")
                cached = event.get("cache_estimate") or {}
                need(cached.get("nano_usd") == cost["cache_estimate_nano"], "Known cache estimate mismatch")
                if cost["cache_breakdown_known"]:
                    for field in ("ordinary_input_tokens", "cache_read_tokens", "cache_write_tokens"):
                        need(cached.get(field) == cost[field], "Known cache component mismatch")
                else:
                    need(cached.get("status") == "CACHE_COMPONENTS_UNAVAILABLE_OR_AMBIGUOUS"
                         and cached.get("usd") is None, "Unavailable cache components priced as known")
                need(cost["prompt_tokens"] <= 272000 and cost["completion_tokens"] <= 4096,
                     "Received usage exceeds approved input/output cap")
                entries[key]["cost"] = cost
            entries[key].update(state=kind, occupied=event["occupied_nano"], terminal=event)
        elif kind == ACK:
            need(key in UNKNOWN_KEYS and entries.get(key, {}).get("state") == "UNKNOWN", "Unapproved unknown acknowledgment")
            need(event["occupied_nano"] == entries[key]["occupied"] == RESERVATION, "Acknowledgment released funds")
            if key == UNKNOWN_KEYS[1]:
                need(event["approved_total_cap_nano"] == approved_cap_nano and event["prior_total_cap_nano"] == 5_000_000_000,
                     "Second acknowledgment does not bind the approved budget")
            entries[key]["state"] = ACK
        elif kind == "DENY":
            need(event.get("network_dispatched") is False, "Denied request dispatched")
            need(key not in entries, "Denied opportunity has a dispatch reservation")
            if event.get("reason") == "INSUFFICIENT_COMBINED_PRE_DISPATCH_RESERVATION":
                expected_cap = approved_cap_nano if key.startswith("CONTINUATION2/") else 5_000_000_000
                need(event.get("occupied_nano") == occupied_before and event.get("required_nano") == RESERVATION
                     and event.get("cap_nano", expected_cap) == expected_cap
                     and occupied_before + RESERVATION > expected_cap, "Budget denial arithmetic differs")
            elif event.get("reason") == "SERIALIZED_REQUEST_TOO_LARGE":
                need(event.get("bytes", 0) > 120000, "Request-size denial does not exceed guard")
            else:
                raise ValueError("Unexpected denial reason")
            denials += 1
        else:
            raise ValueError("Unexpected budget event: " + kind)
        events.append(event)
    need(not any(e["state"] == "RESERVED" for e in entries.values()), "Final ledger contains pending request")
    return entries, events, maximum, denials


def audit_calls(base, stages, entries, old):
    inventory, inherited_copies = {}, 0
    for stage in stages:
        for intent_path in sorted((stage / "tasks").rglob("intent.json")):
            folder = intent_path.parent
            intent, request, wire = read(intent_path), read(folder / "request.json"), read(folder / "http_request_body.json")
            key = intent["logical_key"]
            need(key in entries, "Physical request has no reservation: " + key)
            need(intent.get("automatic_retries") == 0, "Automatic retry setting changed")
            need(old.identity(request) == intent["request_sha256"] and request["wire_body"] == wire,
                 "Request envelope identity mismatch: " + key)
            wire_sha = old.sha(folder / "http_request_body.json")
            need(wire_sha == intent["wire_sha256"] == entries[key]["reserve"]["wire_sha256"] == old.identity(wire),
                 "Actual wire bytes mismatch: " + key)
            expected = {"model": "gpt-5.6-terra", "seed": 104729, "reasoning_effort": "low",
                        "temperature": 1, "max_completion_tokens": 4096, "stream": False}
            need(all(wire.get(k) == v for k, v in expected.items()), "Scientific API setting changed: " + key)
            need(wire.get("response_format", {}).get("json_schema", {}).get("strict") is True,
                 "Strict response schema missing")
            need(len((folder / "http_request_body.json").read_bytes()) <= 120000, "Wire request admission limit exceeded")
            item = {"key": key, "wire_sha256": wire_sha, "request_sha256": old.sha(folder / "request.json"),
                    "source": folder.relative_to(base).as_posix(), "intent_sha256": old.sha(intent_path)}
            response_path, raw_path = folder / "response.json", folder / "http_response_body.json"
            if response_path.exists():
                response, metadata = read(response_path), read(folder / "http_response_metadata.json")
                try:
                    raw = read(raw_path)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    raw = {}
                need(isinstance(raw, dict), "Received JSON is not an object")
                need(response.get("usage") == raw.get("usage"), "Raw/normalized usage mismatch: " + key)
                cost = classify_usage(raw.get("usage"))
                if cost is None:
                    need(entries[key]["state"] == "UNKNOWN" and entries[key]["terminal"].get("usage") is None
                         and entries[key]["occupied"] == RESERVATION and (folder / "unknown.json").exists(),
                         "Missing usage did not retain its technical-unknown reservation")
                    need(read(folder / "unknown.json").get("usage") == raw.get("usage"), "Unknown usage receipt differs")
                else:
                    need(raw["usage"] == entries[key]["terminal"].get("usage") and entries[key]["state"] == "SETTLE",
                         "Raw/ledger settled usage mismatch: " + key)
                raw_sha = old.sha(raw_path)
                need(raw_sha == metadata["stored_raw_sha256"] == response["raw_binding"]["stored_raw_sha256"]
                     == metadata["received_raw_sha256"] and not metadata["credential_redaction_required"],
                     "Raw received response identity differs")
                need(response["request_sha256"] == intent["request_sha256"], "Response bound to another request")
                choice = (raw.get("choices") or [{}])[0]
                message = choice.get("message") or {}
                need(response["finish_reason"] == choice.get("finish_reason")
                     and response["response_model"] == raw.get("model") and response["response_id"] == raw.get("id"),
                     "Raw response metadata differs")
                need(response["text"] == (message.get("content") if isinstance(message.get("content"), str) else ""),
                     "Raw response content differs")
                family_matches = isinstance(raw.get("model"), str) and (
                    raw["model"] == "gpt-5.6-terra" or raw["model"].startswith("gpt-5.6-terra-"))
                expected_kind = ("HTTP_ERROR" if metadata["status"] != 200 else
                                 "TRUNCATED" if choice.get("finish_reason") == "length" else
                                 "REFUSAL" if message.get("refusal") else
                                 "CONTENT" if response["text"] and choice.get("finish_reason") == "stop" else "INVALID_RESPONSE")
                need(response.get("kind") == expected_kind and response.get("refusal") == message.get("refusal")
                     and response.get("output_truncated") == (choice.get("finish_reason") == "length")
                     and response.get("response_model_matches_requested_family") == family_matches,
                     "Raw response classification differs from normalization")
                if cost is not None:
                    need(family_matches, "Received usable response identifies a different model family")
                if cost is None:
                    branch_result = read(folder.parent / "result.json")
                    need(branch_result.get("status", branch_result.get("stop_reason")) == "UNKNOWN_RESPONSE",
                         "Missing-usage response was treated as a completed model opportunity")
                elif expected_kind != "CONTENT":
                    branch_result = read(folder.parent / "result.json")
                    if key.endswith("/G0/shared_initial"):
                        need(branch_result.get("status") == "ASSIGNMENT_REJECTED"
                             and branch_result.get("rejection_kind") == expected_kind
                             and not (folder.parent / "artifact/model.xmi").exists(),
                             "Non-content initial response was applied")
                    else:
                        round_number = int(folder.name.removeprefix("round_"))
                        rejected_rounds = [r for r in branch_result.get("attempts", []) if r["round"] == round_number]
                        need(len(rejected_rounds) == 1 and rejected_rounds[0]["status"] == expected_kind
                             and rejected_rounds[0]["candidate_created"] is False
                             and rejected_rounds[0]["selected"] is False,
                             "Non-content repair response was applied")
                need(metadata["status"] == 200 or cost is None, "Non-successful HTTP status requires separate technical review")
                item.update(known=True, response_sha256=old.sha(response_path), raw_sha256=raw_sha,
                            cost=cost, usage_known=cost is not None,
                            usage_classification="KNOWN" if cost is not None else "TECHNICAL_UNKNOWN_FULL_RESERVATION",
                            response_id=raw.get("id"), response_model=raw.get("model"),
                            finish_reason=choice.get("finish_reason"), refusal=bool(message.get("refusal")),
                            reasoning_tokens=((raw.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens"))
            else:
                need(not raw_path.exists() and (folder / "unknown.json").exists(), "Missing response has no unknown record")
                need(entries[key]["state"] in {"UNKNOWN", ACK} and read(folder / "unknown.json").get("usage") is None,
                     "Missing response classified as known")
                item.update(known=False, usage_known=False, usage_classification="NO_RESPONSE_FULL_RESERVATION",
                            unknown_sha256=old.sha(folder / "unknown.json"))
            if key in inventory:
                need({k: v for k, v in inventory[key].items() if k != "source"}
                     == {k: v for k, v in item.items() if k != "source"}, "Inherited request/receipt changed: " + key)
                inherited_copies += 1
            else:
                inventory[key] = item
    need(set(inventory) == set(entries), "Intent inventory and ledger keys differ")
    known_ids = [r["response_id"] for r in inventory.values() if r["known"] and r["response_id"] is not None]
    need(len(known_ids) == len(set(known_ids)), "Distinct transmissions share a response identity")
    for original, replacement in zip(UNKNOWN_KEYS, REPLACEMENTS):
        need(original in inventory and not inventory[original]["known"], "Old unknown response was fabricated")
        if replacement in inventory:
            need(inventory[replacement]["wire_sha256"] == inventory[original]["wire_sha256"]
                 and inventory[replacement]["request_sha256"] == inventory[original]["request_sha256"],
                 "Manual replacement changed original request bytes")
    opportunities = {}
    for key in inventory:
        normalized = key.split("/", 1)[1] if key.startswith("CONTINUATION") else key
        opportunities.setdefault(normalized, []).append(key)
    need(len(opportunities) <= 120 and len(inventory) <= 122, "Prespecified logical/physical opportunity limit exceeded")
    allowed_duplicates = [set(pair) for pair in zip(UNKNOWN_KEYS, REPLACEMENTS)]
    need(all(len(keys) == 1 or set(keys) in allowed_duplicates for keys in opportunities.values()),
         "A received logical opportunity was resampled")
    return inventory, inherited_copies


def file_map(path, old):
    return {p.relative_to(path).as_posix(): old.sha(p) for p in path.rglob("*") if p.is_file()}


def audit_reuse(base, final_run, design, calls, old):
    previous_run = base / "continuation/run"
    tasks = [r["task_id"] for r in design["tasks"]]
    previous_rows = {(r["task_id"], r["arm"]): r for r in read(previous_run / "RESULTS.json")["rows"]}
    complete = [t for t in tasks if all(previous_rows[t, a]["known_endpoint"] for a in ARMS)]
    need(complete == tasks[:12] and tasks[12] == "BAL-1-03", "Earlier completion prefix differs")
    for task in complete:
        need(file_map(previous_run / "tasks" / task, old) == file_map(final_run / "tasks" / task, old),
             "Previously completed task changed: " + task)
    shared = "tasks/BAL-1-03/shared_generation"
    need(file_map(previous_run / shared, old) == file_map(final_run / shared, old), "Known partial-task G0 changed")
    new_keys = [key for key in calls if key.startswith("CONTINUATION2/")]
    for key in new_keys:
        _, task, arm, opportunity = key.split("/")
        need(task not in complete and not (task == "BAL-1-03" and arm == "G0"), "Known endpoint incurred a new call")
        need(opportunity in ({"shared_initial"} if arm == "G0" else {"round_01", "round_02"}),
             "Request exceeded prespecified logical opportunity bound")
    dispatched = [e for e in read_budget_lines(final_run / "BUDGET.jsonl") if e["kind"] == "RESERVE"
                  and e["key"].startswith("CONTINUATION2/")]
    if dispatched:
        need(dispatched[0]["key"] == REPLACEMENTS[1], "Second continuation did not start at the missing GS opportunity")
    task_positions = [tasks.index(e["key"].split("/")[1]) for e in dispatched]
    need(task_positions == sorted(task_positions), "Original task execution order changed")
    return {"complete_tasks_reused_byte_identically": complete, "partial_task_known_G0_reused_byte_identically": True,
            "new_calls_for_previously_known_endpoints": 0, "new_segment_dispatches": len(dispatched),
            "second_manual_request_byte_identity": REPLACEMENTS[1] in calls,
            "old_unknowns_retained": list(UNKNOWN_KEYS)}


def read_budget_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def audit_denials(base, events, calls, old):
    result = []
    for event in events:
        if event["kind"] != "DENY":
            continue
        key = event["key"]
        need(key not in calls, "Denied request appears in physical dispatch inventory")
        if key.startswith("CONTINUATION2/"):
            stage, normalized = base / "continuation2/run", key.split("/", 1)[1]
        elif key.startswith("CONTINUATION1/"):
            stage, normalized = base / "continuation/run", key.split("/", 1)[1]
        else:
            stage, normalized = base / "run", key
        task, arm, opportunity = normalized.split("/")
        folder = stage / "tasks" / task / ("shared_generation" if arm == "G0" else arm) / opportunity
        need((folder / "request.json").is_file(), "Denied request lacks prepared request evidence")
        forbidden = ("intent.json", "http_request_body.json", "http_response_body.json", "response.json", "unknown.json")
        need(not any((folder / name).exists() for name in forbidden), "Denied request has dispatch or response files")
        request = read(folder / "request.json")
        wire = request["wire_body"]
        expected = {"model": "gpt-5.6-terra", "seed": 104729, "reasoning_effort": "low", "temperature": 1,
                    "max_completion_tokens": 4096, "stream": False}
        need(all(wire.get(k) == v for k, v in expected.items()), "Denied prepared request changed scientific settings")
        item = {"key": key, "task_id": task, "arm": arm, "reason": event["reason"],
                "network_dispatched": False, "counts_as_model_failure": False,
                "prepared_request": (folder / "request.json").relative_to(base).as_posix(),
                "prepared_request_sha256": old.sha(folder / "request.json"), "dispatch_and_response_files_absent": True}
        if event["reason"] == "INSUFFICIENT_COMBINED_PRE_DISPATCH_RESERVATION":
            cap = event.get("cap_nano", 5_000_000_000)
            item.update(occupied_usd=old.usd(event["occupied_nano"]),
                        required_reservation_usd=old.usd(event["required_nano"]),
                        reservation_total_if_dispatched_usd=old.usd(event["occupied_nano"] + event["required_nano"]),
                        cap_usd=old.usd(cap), shortfall_usd=old.usd(event["occupied_nano"] + event["required_nano"] - cap))
        result.append(item)
    return result


def task_progress(tasks, complete, calls, final_run):
    dispatched_tasks = set()
    for key in calls:
        normalized = key.split("/", 1)[1] if key.startswith("CONTINUATION") else key
        dispatched_tasks.add(normalized.split("/")[0])
    partial = [task for task in tasks if task not in complete and task in dispatched_tasks]
    unstarted = [task for task in tasks if task not in complete and task not in dispatched_tasks]
    prepared_not_dispatched = [task for task in unstarted if (final_run / "tasks" / task).exists()]
    return partial, unstarted, prepared_not_dispatched


def rebind(base, value, old):
    retained = value["native_evidence"].replace("\\", "/")
    for suffix in ("/continuation2/run/native_evidence/", "/continuation/run/native_evidence/", "/run/native_evidence/"):
        if suffix in retained:
            return old.local(base, suffix.strip("/") + "/" + retained.split(suffix, 1)[1])
    raise ValueError("Unrecognized package-local native evidence binding")


def compare_results(base, final, rows, tasks, old):
    need(len(final["rows"]) == 72, "Final results omit planned endpoints")
    published = {(r["task_id"], r["arm"]): r for r in final["rows"]}
    need(set(published) == set(rows), "Endpoint identity set differs")
    for key, actual in rows.items():
        expected = published[key]
        for field in ("known_endpoint", "model_failure", "requests", "prompt_tokens", "completion_tokens", "truncations", "refusals", "unknown_usage"):
            need(expected.get(field) == actual.get(field), "Endpoint mismatch: " + str(key) + "/" + field)
        need(expected["strict_success"] == (actual["strict_success"] if actual["known_endpoint"] else False),
             "Published success misclassifies a known or missing endpoint")
        if actual["known_endpoint"]:
            for field in ("failure_type", "task_failures", "frame_failures", "query_failures"):
                need(expected.get(field) == actual.get(field), "Endpoint failure details differ: " + str(key))
    complete = [t for t in tasks if all(rows[t, a]["known_endpoint"] for a in ARMS)]
    all_known = len(complete) == 24
    need(final["all_72_endpoints_known"] == all_known, "Completion flag differs")
    groups = {}
    for arm in ARMS:
        arm_rows = [rows[t, arm] for t in tasks]
        group = {"planned": 24, "known": sum(r["known_endpoint"] for r in arm_rows),
                 "strict_success": sum(r["strict_success"] is True for r in arm_rows),
                 "received_responses": sum(r["requests"] for r in arm_rows),
                 "prompt_tokens": sum(r["prompt_tokens"] for r in arm_rows),
                 "completion_tokens": sum(r["completion_tokens"] for r in arm_rows)}
        for field, value in group.items():
            need(final["groups"][arm][field] == value, "Arm total mismatch: " + arm + "/" + field)
        need(final["groups"][arm]["strict_success_rate_all_planned"] == group["strict_success"] / 24,
             "All-planned success fraction differs")
        group.update(unknown_or_not_run=24 - group["known"],
                     known_model_failures=sum(r["model_failure"] is True for r in arm_rows),
                     all_planned_fraction_is_only_known_success_lower_bound=not all_known)
        groups[arm] = group
    contrasts = old.comparisons(rows, tasks) if all_known else {}
    need(final["exploratory_mcnemar_holm"] == contrasts, "Full McNemar/Holm differs or was run despite missing outcomes")
    baseline = read(base / "historical_luna/BASELINE_ROWS.json")
    lookup = {(r["unit_id"].split(":")[1], r["arm"]): r for r in baseline}
    need(len(baseline) == len(lookup) == 72 and set(lookup) == set(rows), "Luna comparator identity differs")
    need(all(r["unit_id"].split(":")[-2] == "104729" for r in baseline), "Luna comparator seed differs")
    pairs = []
    for task in tasks:
        for arm in ARMS:
            source, new = lookup[task, arm], rows[task, arm]
            state = source["state"]
            success = False if state in {"ASSIGNMENT_REJECTED", "NOT_RUN_SHARED_ASSIGNMENT_REJECTED"} else None if state in {"UNKNOWN_RESPONSE", "NOT_RUN_SHARED_RESPONSE_UNKNOWN"} else source["final_valid"]
            pairs.append({"task_id": task, "arm": arm, "luna_success": success,
                          "luna_trace_artifact_final_valid": source["final_valid"], "luna_state": state,
                          "supplement_success": new["strict_success"] if new["known_endpoint"] else None})
    need(final["luna_same_task_pairs_descriptive_only"] == pairs, "Paired Luna/Terra objects differ")
    comparison = {arm: {"denominator": len(complete), "terra_success": sum(rows[t, arm]["strict_success"] for t in complete),
                       "luna_success": sum(p["luna_success"] is True for p in pairs if p["arm"] == arm and p["task_id"] in complete)} for arm in ARMS}
    return complete, groups, contrasts, pairs, comparison


def review(base, output, java, plan_name, approval_relative):
    old = load_review_helpers(base)
    stage_root = base / "continuation2"
    plan = old.local(stage_root / "plans", plan_name)
    final_run = stage_root / "run"
    stages = [base / "run", base / "continuation/run", final_run]
    need(all((s / "MANIFEST.json").is_file() and not (s / "RUNNING.lock").exists() for s in stages),
         "Final run is absent or still active")
    # Cap 6 must be explicitly approved and bound before this reviewer accepts it.
    need(plan_name == "cap5", "This audit currently accepts only the approved USD 5 protocol")
    cap_nano = 5_000_000_000
    manifests = {"original_code_data": old.verify_manifest(base, "EXECUTION_SEAL.json"),
                 "first_continuation_seal": old.verify_manifest(base / "continuation", "CONTINUATION_SEAL.json")}
    for number, stage in enumerate(stages):
        manifests["run_segment_" + str(number)] = old.verify_manifest(stage, exhaustive=True)
    # The exact second-continuation plan/seal bindings are checked here after preparation.
    manifests["second_continuation_plan"] = verify_second_plan(base, plan, final_run, old, cap_nano, approval_relative)
    for first, second in zip(stages, stages[1:]):
        need((second / "BUDGET.jsonl").read_bytes().startswith((first / "BUDGET.jsonl").read_bytes()),
             "Prior budget is not an exact byte prefix")
    entries, events, maximum, denials = replay_budget(final_run / "BUDGET.jsonl", old, cap_nano)
    original_count = len(read_budget_lines(stages[0] / "BUDGET.jsonl"))
    previous_count = len(read_budget_lines(stages[1] / "BUDGET.jsonl"))
    need(events[original_count]["kind"] == ACK and events[original_count]["key"] == UNKNOWN_KEYS[0], "First acknowledgment differs")
    need(events[previous_count]["kind"] == ACK and events[previous_count]["key"] == UNKNOWN_KEYS[1], "Second acknowledgment differs")
    need(events[previous_count]["amendment_sha256"] == old.sha(plan / "PROTOCOL_AMENDMENT.json"), "Second ACK amendment differs")
    need(all(entries[k]["state"] == ACK and entries[k]["occupied"] == RESERVATION for k in UNKNOWN_KEYS),
         "An old unknown was dropped or its reservation released")
    calls, inherited_copies = audit_calls(base, stages, entries, old)
    denied_requests = audit_denials(base, events, calls, old)
    design = read(base / "DESIGN.json")
    tasks = [r["task_id"] for r in design["tasks"]]
    need(len(tasks) == len(set(tasks)) == 24 and all(r["seed"] == 104729 for r in design["tasks"]), "Fixed task set differs")
    reuse = audit_reuse(base, final_run, design, calls, old)
    final, execution = read(final_run / "RESULTS.json"), read(final_run / "EXECUTION_STATUS.json")
    need(final["status"] == execution["status"], "Result and execution status differ")
    known, usage_known, cache_known, sums = summarize_usage(calls)
    unknown = [calls[key] for key, entry in entries.items() if entry["state"] in {"UNKNOWN", ACK}]
    need(known, "No received responses retained")
    cache_complete = len(cache_known) == len(usage_known)
    unknown_upper = len(unknown) * RESERVATION
    occupied = sum(e["occupied"] for e in entries.values())
    need(occupied == sums["conservative_occupied_nano"] + unknown_upper <= cap_nano, "Combined occupied budget differs")
    budget_expected = {"known_base_price_estimate_usd": old.usd(sums["base_estimate_nano"]),
                       "cache_component_estimate_usd": old.usd(sums["cache_estimate_nano"]),
                       "known_prompt_tokens": sums["prompt_tokens"], "known_completion_tokens": sums["completion_tokens"],
                       "reserved_requests": len(entries), "occupied_upper_usd": old.usd(occupied),
                       "remaining_unoccupied_usd": old.usd(cap_nano - occupied), "cache_component_estimate_responses": len(cache_known),
                       "cache_components_unknown_responses": len(usage_known) - len(cache_known), "denials": denials}
    for summary in (final["monetary"], execution["budget"]):
        for key, value in budget_expected.items():
            need(summary[key] == value, "Published monetary aggregate mismatch: " + key)
    native = old.native_module(base)
    endpoint_path = Path(__file__).with_name("endpoint_review.py")
    endpoint_spec = importlib.util.spec_from_file_location("current_offline_endpoint_review", endpoint_path)
    endpoint_module = importlib.util.module_from_spec(endpoint_spec)
    endpoint_spec.loader.exec_module(endpoint_module)
    rows, native_report = endpoint_module.score_endpoints(base, final_run, output, design, java, native, old,
                                                          lambda package, value: rebind(package, value, old))
    complete, groups, contrasts, pairs, comparison = compare_results(base, final, rows, tasks, old)
    all_known = len(complete) == 24
    need((execution["status"] == "COMPLETE") == all_known, "Overall execution completion status differs")
    partial, unstarted, prepared_not_dispatched = task_progress(tasks, complete, calls, final_run)
    need(final["truncations"] == sum(r["finish_reason"] == "length" for r in known)
         and final["refusals"] == sum(r["refusal"] for r in known), "Response truncation/refusal totals differ")
    need(final["combined_all_segments_dispatch_intents"] == len(calls)
         and final["unknown_usage_transport_attempts_total"] == len(unknown)
         and final["inherited_unknown_transport_attempts"] == 2
         and final["manual_missing_response_replacements_authorized_total"] == 2,
         "Combined transport/replacement totals differ")
    need(final["prior_run_manifest_sha256"] == old.sha(stages[1] / "MANIFEST.json")
         and final["protocol_amendment_sha256"] == old.sha(plan / "PROTOCOL_AMENDMENT.json"),
         "Final results have incorrect prior-state or protocol bindings")
    for stage in stages:
        old.verify_manifest(stage, exhaustive=True)
    old.verify_manifest(base, "EXECUTION_SEAL.json")
    return {"schema_version": "atlas.terra.independent-audit/2", "evidence_integrity": "PASS",
            "study_completion": "COMPLETE" if all_known else "INCOMPLETE", "audited_utc": datetime.now(timezone.utc).isoformat(),
            "source_results": "continuation2/run/RESULTS.json", "source_results_sha256": old.sha(final_run / "RESULTS.json"),
            "review_script_sha256": old.sha(Path(__file__)), "endpoint_review_sha256": old.sha(endpoint_path),
            "historical_review_report_sha256": PRIOR_REPORT_SHA,
            "scope": {"network_calls": 0, "credential_files_read": False, "generation_modules_imported": False,
                      "serializer_modules_imported": False, "source_files_modified": False,
                      "native_scorer": "raw_native_score.py", "java": str(java)},
            "manifests": manifests, "technical_continuation_reuse": reuse,
            "task_completion": {"planned": 24, "complete": len(complete), "partial": len(partial), "unstarted": len(unstarted),
                                "complete_task_ids": complete, "partial_task_ids": partial, "unstarted_task_ids": unstarted,
                                "prepared_but_not_dispatched_task_ids": prepared_not_dispatched,
                                "partial_definition": "Incomplete task with at least one actual model dispatch; preparation alone is unstarted"},
            "denied_pre_dispatch_requests": denied_requests,
            "groups": groups, "endpoints": list(rows.values()), "native_revalidation": native_report,
            "planned_statistics": {"executed": all_known, "contrasts": contrasts,
                                   "reason": "All 72 endpoints independently known" if all_known else "Missing endpoint requirement; no incomplete-subset inference"},
            "matched_luna_terra_descriptive_only": comparison, "paired_luna_terra": pairs,
            "comparison_limitation": "Fixed author tasks and one seed; the historical Luna model is descriptive, and technical missing-response replacements do not establish model superiority.",
            "usage_and_cost": {**{k: (v if cache_complete or k not in {"ordinary_input_tokens", "cache_read_tokens", "cache_write_tokens"} else None)
                                  for k, v in sums.items() if not k.endswith("_nano")},
                "itemized_cache_token_subtotals": {k: sums[k] for k in ("ordinary_input_tokens", "cache_read_tokens", "cache_write_tokens")},
                "received_unique_responses": len(known), "received_responses_with_known_usage": len(usage_known),
                "received_responses_with_unknown_usage": len(known) - len(usage_known),
                "received_responses_with_known_cache_components": len(cache_known),
                "received_responses_with_unknown_cache_components": len(usage_known) - len(cache_known),
                "cache_component_breakdown_complete_for_known_usage": cache_complete,
                "combined_dispatch_intents": len(calls),
                "duplicate_inherited_receipts_counted_once": inherited_copies,
                "all_usable_raw_usage_matches_ledger": True, "unusable_usage_retains_full_reservation": True,
                "all_previous_budget_prefixes_byte_identical": True,
                "known_base_price_estimate_usd": old.usd(sums["base_estimate_nano"]),
                "known_cache_component_price_estimate_usd": old.usd(sums["cache_estimate_nano"]) if cache_complete else None,
                "cache_itemized_responses_price_subtotal_usd": old.usd(sums["cache_estimate_nano"]),
                "cache_estimate_status": "KNOWN_USAGE_ITEMIZED" if cache_complete else "PARTIAL_COMPONENTS_UNAVAILABLE",
                "known_conservative_occupancy_usd": old.usd(sums["conservative_occupied_nano"]),
                "old_two_unknowns_permanent_occupancy_usd": old.usd(2 * RESERVATION),
                "unknown_requests": [r["key"] for r in unknown], "unknown_reserved_upper_usd": old.usd(unknown_upper),
                "known_cache_estimate_plus_unknown_upper_usd": old.usd(sums["cache_estimate_nano"] + unknown_upper) if cache_complete else None,
                "combined_conservative_occupancy_usd": old.usd(occupied), "maximum_predispatch_occupancy_usd": old.usd(maximum),
                "cap_usd": old.usd(cap_nano), "within_client_cap": True, "not_a_provider_invoice": True,
                "price_basis_usd_per_million": {"ordinary_input": "3", "cache_read": "0.3", "cache_write": "3.75", "completion_including_reasoning": "18"},
                "assumptions": "Returned cache read/write counts are disjoint subsets of prompt tokens; price estimates are not authenticated billing.",
                "known_max_prompt_tokens": max((r["cost"]["prompt_tokens"] for r in usage_known), default=None),
                "known_max_completion_tokens": max((r["cost"]["completion_tokens"] for r in usage_known), default=None),
                "known_max_reasoning_tokens": max((r["reasoning_tokens"] for r in known if type(r["reasoning_tokens"]) is int), default=None),
                "received_responses_at_completion_cap": sum(r["cost"]["completion_tokens"] == 4096 for r in usage_known),
                "truncations": final["truncations"], "refusals": final["refusals"],
                "returned_models": sorted({r["response_model"] for r in known if isinstance(r["response_model"], str)})},
            "calls": list(calls.values()), "errors": []}


def verify_second_plan(base, plan, final_run, old, cap_nano, approval_relative):
    stage = base / "continuation2"
    seal_relative = (plan / "CONTINUATION_SEAL.json").relative_to(stage).as_posix()
    summary = old.verify_manifest(stage, seal_relative)
    seal = read(plan / "CONTINUATION_SEAL.json")
    expected_members = {"continue_second.py", "test_second.py", "preflight.py",
                        (plan / "PROTOCOL_AMENDMENT.json").relative_to(stage).as_posix(),
                        (plan / "PREFLIGHT_REPORT.json").relative_to(stage).as_posix()}
    expected_members.update(p.relative_to(stage).as_posix() for p in (plan / "offline").rglob("*")
                            if p.is_file() and "__pycache__" not in p.parts)
    need(set(seal) == expected_members, "Second plan seal membership differs")
    amendment = read(plan / "PROTOCOL_AMENDMENT.json")
    for relative, expected in amendment["prior_file_sha256"].items():
        need(old.sha(old.local(base, relative)) == expected, "Plan prior-state binding differs: " + relative)
    need(amendment["combined_budget_cap_usd"] * 1_000_000_000 == cap_nano
         and amendment["budget_increase_authorized_by_this_plan"] is False,
         "Prepared plan changes budget without approval")
    need(amendment["initial_occupied_nano_usd"] == 3_139_673_250
         and amendment["permanent_historical_unknowns"] == {k: RESERVATION for k in UNKNOWN_KEYS}
         and amendment["permanent_unknown_total_nano_usd"] == 2 * RESERVATION,
         "Prepared plan changes inherited occupancy")
    need(amendment["new_request_reservation_nano_usd"] == RESERVATION
         and amendment["input_tokens_reserved"] == 272000 and amendment["max_completion_tokens"] == 4096
         and amendment["serialized_request_max_bytes"] == 120000 and amendment["smaller_reservation_adopted"] is False,
         "Prepared plan changes admission/scientific limits")
    tasks = [r["task_id"] for r in read(base / "DESIGN.json")["tasks"]]
    need(amendment["reuse_complete_tasks"] == tasks[:12] and amendment["remaining_task_order"] == tasks[12:]
         and amendment["reuse_partial"] == {"task_id": "BAL-1-03", "arm": "G0"}, "Plan changes task reuse or order")
    replacement = amendment["manual_missing_response_replacement"]
    previous_request = base / "continuation/run/tasks/BAL-1-03/GS/round_01"
    need(replacement["task_id"] == "BAL-1-03" and replacement["arm"] == "GS" and replacement["key"] == "round_01"
         and replacement["maximum_new_dispatches"] == 1 and replacement["byte_identical_request_required"] is True
         and replacement["original_request_sha256"] == old.sha(previous_request / "request.json")
         and replacement["original_wire_sha256"] == old.sha(previous_request / "http_request_body.json"),
         "Plan manual replacement differs from missing response")
    need(amendment["logical_response_opportunities_max"] == 120
         and amendment["physical_dispatch_intents_all_segments_max"] == 122, "Plan opportunity limits changed")
    approval_path = old.local(base, approval_relative)
    approval = read(approval_path)
    need(approval.get("parent_confirmed_start") is True and approval.get("budget_usd") * 1_000_000_000 == cap_nano,
         "No matching parent-reviewed start approval")
    for field, filename in (("amendment_sha256", "PROTOCOL_AMENDMENT.json"), ("continuation_seal_sha256", "CONTINUATION_SEAL.json")):
        need(approval.get(field) == old.sha(plan / filename), "Start approval not bound to this exact plan")
    destination_authorization_path = base / "continuation2/review/EXPLICIT_DESTINATION_AUTHORIZATION.json"
    destination_authorization = read(destination_authorization_path)
    need(destination_authorization["record_type"] == "USER_EXPLICIT_DESTINATION_AND_PAYLOAD_AUTHORIZATION"
         and destination_authorization["user_answer_verbatim"] == "\u5141\u8bb8"
         and destination_authorization["combined_budget_cap_usd"] * 1_000_000_000 == cap_nano
         and destination_authorization["budget_6_authorized"] is False
         and destination_authorization["existing_api_credential_authentication_authorized"] is True
         and destination_authorization["credential_value_recorded"] is False,
         "Explicit destination and payload authorization record differs")
    endpoint_hash = old.hashlib.sha256(destination_authorization["endpoint"].encode("utf-8")).hexdigest()
    need(endpoint_hash == destination_authorization["endpoint_sha256"]
         == read(base / "PREPARATION_REPORT.json")["configuration"]["endpoint_sha256"],
         "Destination authorization is bound to a different endpoint")
    inheritance = read(final_run / "INHERITANCE.json")
    need(inheritance["prior_budget_sha256"] == old.sha(base / "continuation/run/BUDGET.jsonl")
         and inheritance["prior_run_manifest_sha256"] == old.sha(base / "continuation/run/MANIFEST.json")
         and inheritance["completed_tasks"] == tasks[:12]
         and inheritance["partially_completed_task_reused_arm"] == {"task_id": "BAL-1-03", "arm": "G0"}
         and inheritance["new_calls_for_reused_evidence"] == 0
         and inheritance["two_historical_unknown_reservations_permanent"] is True
         and inheritance["amendment_sha256"] == old.sha(plan / "PROTOCOL_AMENDMENT.json")
         and inheritance["replaced_missing_request_sha256"] == old.sha(previous_request / "request.json")
         and inheritance["replaced_missing_wire_sha256"] == old.sha(previous_request / "http_request_body.json"),
         "Run inheritance report differs from original bytes or approved plan")
    summary.update(approval_relative=approval_relative, approval_sha256=old.sha(approval_path),
                   plan_relative=plan.relative_to(base).as_posix(), approved_budget_usd=cap_nano // 1_000_000_000,
                   explicit_destination_authorization_sha256=old.sha(destination_authorization_path),
                   authorized_endpoint_sha256=endpoint_hash)
    return summary


def validate_report(report):
    need(report["evidence_integrity"] in {"PASS", "FAIL"}, "Invalid evidence status")
    need(report["study_completion"] in {"COMPLETE", "INCOMPLETE", "NOT_ASSESSED"}, "Invalid completion status")
    if report["evidence_integrity"] == "PASS":
        counts = report["task_completion"]
        need(counts["complete"] + counts["partial"] + counts["unstarted"] == 24, "Task counts differ")
        need(len(report["endpoints"]) == 72, "Missing audit endpoints")
        for row in report["endpoints"]:
            if not row["known_endpoint"]:
                need(row["strict_success"] is None and row["model_failure"] is None, "Unknown marked as model failure")
        need(report["planned_statistics"]["executed"] == (counts["complete"] == 24), "Inference completeness gate differs")
        if counts["complete"] < 24:
            need(report["planned_statistics"]["contrasts"] == {}, "Incomplete study has inference results")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, default=BASE)
    parser.add_argument("--output", type=Path, required=True, help="New output directory; never overwrite")
    parser.add_argument("--java", type=Path)
    parser.add_argument("--plan", default="cap5")
    parser.add_argument("--approval", default="continuation2/plans/cap5/START_AUTHORIZATION.json", help="Exact package-relative authorization record")
    args = parser.parse_args()
    base, output = args.package_root.resolve(), args.output.resolve()
    need(not output.exists(), "Output directory exists; refusing overwrite")
    for protected in ("run", "continuation", "continuation2", "workspace", "inputs", "historical_luna"):
        need(not output.is_relative_to(base / protected), "Output is inside frozen experiment material")
    java = args.java.resolve() if args.java else base / "workspace/native_validation/toolchain/jdk8/jdk8u504-b01/bin/java.exe"
    need(java.is_file(), "Java executable not found")
    def audit_event(event, arguments):
        if event.startswith("socket."):
            raise RuntimeError("Python network operation blocked during offline audit")
    sys.addaudithook(audit_event)
    output.mkdir(parents=True, exist_ok=False)
    try:
        report = review(base, output, java, args.plan, args.approval)
        validate_report(report)
    except Exception as error:
        report = {"schema_version": "atlas.terra.independent-audit/2", "evidence_integrity": "FAIL",
                  "study_completion": "NOT_ASSESSED", "errors": [{"type": type(error).__name__, "message": str(error)}]}
    target = output / "terra_independent_audit.json"
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"report": str(target), "evidence_integrity": report["evidence_integrity"],
                      "study_completion": report["study_completion"], "errors": report["errors"]}, ensure_ascii=False))
    return 0 if report["evidence_integrity"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
