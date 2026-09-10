#!/usr/bin/env python3
"""Offline last-task budget-extension audit; requires an explicit USD 6 approval.

Reuses the unchanged earlier review's pricing, raw HTTP, score comparison,
native endpoint, and exact-statistics helpers. Does not import paid code.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parents[2]
TASK = "BAL-3-01"
CAP_EVENT = "BUDGET_CAP_EXTENSION_AUTHORIZED"
PRIOR_REPORT_SHA = "d6b48ebac19099c87a41cfdfac95a46b5f3f4bf4f7841ccbf35c3146e057df22"
ALLOWED = {"CONTINUATION3/" + TASK + "/" + arm + "/" + key
           for arm, keys in (("G0", ["shared_initial"]), ("GS", ["round_01", "round_02"]), ("GF", ["round_01", "round_02"])) for key in keys}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def helpers(base):
    report_path = base / "review/continuation2/check_002/terra_independent_audit.json"
    need(hashlib.sha256(report_path.read_bytes()).hexdigest() == PRIOR_REPORT_SHA, "Prior independent audit changed")
    prior = read(report_path)
    path = base / "review/continuation2/verify_final.py"
    need(hashlib.sha256(path.read_bytes()).hexdigest() == prior["review_script_sha256"], "Prior review source changed")
    endpoint_path = path.with_name("endpoint_review.py")
    need(hashlib.sha256(endpoint_path.read_bytes()).hexdigest() == prior["endpoint_review_sha256"], "Prior endpoint reviewer changed")
    previous = module_at("preserved_second_continuation_review", path)
    return previous, previous.load_review_helpers(base), module_at("preserved_endpoint_review", endpoint_path)


def replay_extension(path, prior_path, previous, old, approval_sha, amendment_sha):
    """Replay the old ledger unchanged, then validate only the new suffix."""
    prior_bytes = prior_path.read_bytes()
    need(path.read_bytes().startswith(prior_bytes), "Old cap-5 budget byte prefix changed")
    entries, events, maximum, denial_count = previous.replay_budget(prior_path, old)
    need(sum(e["occupied"] for e in entries.values()) == 3_916_463_250 and len(entries) == 60,
         "Extension starts from a different monetary state")
    all_events = previous.read_budget_lines(path)
    prefix_count = len(events)
    need(all_events[:prefix_count] == events, "Inherited ledger event prefix differs")
    extension_recorded = False
    new_keys = []
    for number, event in enumerate(all_events[prefix_count:], prefix_count + 1):
        need(event["sequence"] == number and event["previous"] == events[-1]["hash"]
             and event["hash"] == old.identity({k: v for k, v in event.items() if k != "hash"}), "Extension budget chain differs")
        kind, key = event["kind"], event["key"]
        occupied = sum(e["occupied"] for e in entries.values())
        if kind == CAP_EVENT:
            need(not extension_recorded and number == prefix_count + 1 and key == "GLOBAL_BUDGET_CAP",
                 "Budget increase is repeated or not at the boundary")
            need(event["old_cap_nano"] == 5_000_000_000 and event["new_cap_nano"] == 6_000_000_000
                 and event["occupied_nano"] == occupied == 3_916_463_250
                 and event["user_explicit_total_cap_usd"] == 6
                 and event["approval_sha256"] == approval_sha and event["amendment_sha256"] == amendment_sha
                 and event["historical_unknown_occupied_nano"] == 2_187_456_000
                 and event["missing_response_replacements_added"] == 0, "Budget-extension authorization or amount differs")
            extension_recorded = True
        else:
            need(extension_recorded and key in ALLOWED, "Unapproved task/opportunity after budget extension")
            if kind == "RESERVE":
                need(key not in entries and len(new_keys) < 5, "Last-task request duplicated or bound exceeded")
                need(not any(e["state"] in {"UNKNOWN", "RESERVED", "VIOLATION"} for e in entries.values()),
                     "Dispatch after new unresolved request")
                need(event["cap_nano"] == 6_000_000_000 and event["reserved_nano"] == previous.RESERVATION
                     and event["input_tokens_reserved"] == 272000 and event["output_tokens_reserved"] == 4096
                     and event["occupied_after_nano"] == occupied + previous.RESERVATION <= 6_000_000_000,
                     "Unapproved reservation or cap exceeded")
                entries[key] = {"state": "RESERVED", "occupied": previous.RESERVATION, "reserve": event}
                new_keys.append(key)
                maximum = max(maximum, occupied + previous.RESERVATION)
            elif kind in {"SETTLE", "UNKNOWN"}:
                need(entries.get(key, {}).get("state") == "RESERVED", "Settlement without a new reservation")
                if kind == "UNKNOWN":
                    need(event["occupied_nano"] == previous.RESERVATION and event.get("usage") is None,
                         "New unknown reservation released")
                else:
                    cost = previous.classify_usage(event["usage"])
                    need(cost is not None and cost["prompt_tokens"] <= 272000 and cost["completion_tokens"] <= 4096,
                         "Received usage outside supported fixed limits")
                    need(event["occupied_nano"] == cost["conservative_occupied_nano"]
                         and event["estimated_base_nano"] == cost["base_estimate_nano"], "Settlement arithmetic differs")
                    cached = event.get("cache_estimate") or {}
                    need(cached.get("nano_usd") == cost["cache_estimate_nano"], "Cache arithmetic differs")
                    if cost["cache_breakdown_known"]:
                        need(all(cached.get(k) == cost[k] for k in ("ordinary_input_tokens", "cache_read_tokens", "cache_write_tokens")),
                             "Cache component allocation differs")
                    else:
                        need(cached.get("status") == "CACHE_COMPONENTS_UNAVAILABLE_OR_AMBIGUOUS" and cached.get("usd") is None,
                             "Unavailable cache components priced as known")
                    entries[key]["cost"] = cost
                entries[key].update(state=kind, occupied=event["occupied_nano"], terminal=event)
            elif kind == "DENY":
                need(key not in entries and event.get("network_dispatched") is False, "Denied request already dispatched")
                if event["reason"] == "INSUFFICIENT_COMBINED_PRE_DISPATCH_RESERVATION":
                    need(event["occupied_nano"] == occupied and event["required_nano"] == previous.RESERVATION
                         and event["cap_nano"] == 6_000_000_000 and occupied + previous.RESERVATION > 6_000_000_000,
                         "Extension denial arithmetic differs")
                else:
                    need(event["reason"] == "SERIALIZED_REQUEST_TOO_LARGE" and event.get("bytes", 0) > 120000,
                         "Unsupported extension denial")
                denial_count += 1
            else:
                raise ValueError("Unexpected extension event: " + kind)
        events.append(event)
    need(extension_recorded and not any(e["state"] == "RESERVED" for e in entries.values()), "Extension incomplete at ledger level")
    need(all(entries[k]["state"] == previous.ACK and entries[k]["occupied"] == previous.RESERVATION
             for k in previous.UNKNOWN_KEYS), "Permanent historical unknowns changed")
    order = ["CONTINUATION3/" + TASK + "/" + item for item in ("G0/shared_initial", "GS/round_01", "GS/round_02", "GF/round_01", "GF/round_02")]
    need(new_keys == sorted(new_keys, key=order.index), "Fixed G0, GS, GF opportunity order changed")
    return entries, events, maximum, denial_count, new_keys


def verify_plan(base, previous, old, require_approval=True):
    root, plan = base / "continuation3", base / "continuation3/plans/cap6"
    seal = read(plan / "CONTINUATION_SEAL.json")
    for relative, expected in seal.items():
        need(old.sha(old.local(root, relative)) == expected, "Extension seal mismatch: " + relative)
    expected_files = {"budget_extension.py", "preflight_extension.py", "test_extension.py", "plans/cap6/PROTOCOL_AMENDMENT.json", "plans/cap6/PREFLIGHT_REPORT.json"}
    expected_files.update(p.relative_to(root).as_posix() for p in (plan / "offline").rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    need(set(seal) == expected_files, "Extension seal membership differs")
    amendment = read(plan / "PROTOCOL_AMENDMENT.json")
    for relative, expected in amendment["prior_file_sha256"].items():
        need(old.sha(old.local(base, relative)) == expected, "Prior-state binding differs: " + relative)
    tasks = [e["task_id"] for e in read(base / "DESIGN.json")["tasks"]]
    need(amendment["prior_combined_cap_usd"] == 5 and amendment["new_combined_cap_usd"] == 6
         and amendment["user_budget_extension_authorized_by_this_plan"] is False
         and amendment["explicit_user_total_cap6_required_before_execution"] is True
         and amendment["prior_occupied_nano_usd"] == 3_916_463_250
         and amendment["two_unknown_occupied_nano_usd"] == 2_187_456_000, "Plan budget context differs")
    need(amendment["reuse_complete_task_ids"] == tasks[:-1] and tasks[-1] == TASK
         and amendment["only_new_task"] == TASK and set(amendment["allowed_new_logical_keys"]) == ALLOWED
         and amendment["maximum_new_dispatches"] == 5 and amendment["missing_response_replacements_added"] == 0
         and amendment["historical_missing_response_replacements_total"] == 2
         and amendment["previous_G0_status"] == "DENIED_BEFORE_DISPATCH", "Extension changes task scope or response opportunities")
    need(amendment["request_reservation_nano_usd"] == previous.RESERVATION and amendment["input_tokens_reserved"] == 272000
         and amendment["completion_tokens_cap"] == 4096 and amendment["model"] == "gpt-5.6-terra"
         and amendment["reasoning_effort"] == "low" and amendment["seed"] == 104729
         and amendment["temperature"] == 1 and amendment["strict_schema"] is True, "Scientific settings changed")
    old_request = base / "continuation2/run/tasks" / TASK / "shared_generation/shared_initial/request.json"
    need(amendment["generation_request_sha256"] == old.sha(old_request), "Unsent request identity differs")
    result = {"files": len(seal), "manifest_sha256": old.sha(plan / "CONTINUATION_SEAL.json"),
              "all_match": True, "amendment_sha256": old.sha(plan / "PROTOCOL_AMENDMENT.json"), "approval_checked": False}
    if require_approval:
        approval_path = plan / "START_AUTHORIZATION.json"
        approval = read(approval_path)
        need(approval.get("parent_confirmed_start") is True and approval.get("budget_usd") == 6
             and approval.get("user_explicitly_authorized_total_cap_usd") == 6, "No explicit user USD 6 approval")
        need(approval.get("amendment_sha256") == result["amendment_sha256"]
             and approval.get("continuation_seal_sha256") == result["manifest_sha256"], "Budget approval is not bound to this plan")
        result.update(approval_checked=True, approval_sha256=old.sha(approval_path))
    return result


def review(base, output, java):
    previous, old, endpoint = helpers(base)
    stages = [base / p for p in ("run", "continuation/run", "continuation2/run", "continuation3/run")]
    need(all((p / "MANIFEST.json").exists() and not (p / "RUNNING.lock").exists() for p in stages), "Final run absent or active")
    manifests = {"original_code_data": old.verify_manifest(base, "EXECUTION_SEAL.json"),
                 "continuation1": old.verify_manifest(base / "continuation", "CONTINUATION_SEAL.json"),
                 "continuation2": previous.verify_second_plan(base, base / "continuation2/plans/cap5", stages[2], old,
                                                               5_000_000_000, "continuation2/plans/cap5/START_AUTHORIZATION.json"),
                 "extension": verify_plan(base, previous, old)}
    for i, stage in enumerate(stages):
        manifests["run_segment_" + str(i)] = old.verify_manifest(stage, exhaustive=True)
    for first, second in zip(stages, stages[1:]):
        need((second / "BUDGET.jsonl").read_bytes().startswith((first / "BUDGET.jsonl").read_bytes()), "Prior budget prefix changed")
    final_run = stages[-1]
    entries, events, maximum, denials, new_keys = replay_extension(final_run / "BUDGET.jsonl", stages[2] / "BUDGET.jsonl", previous, old,
                                                               manifests["extension"]["approval_sha256"], manifests["extension"]["amendment_sha256"])
    calls, copies = previous.audit_calls(base, stages, entries, old)
    need(set(k for k in calls if k.startswith("CONTINUATION3/")) == set(new_keys), "New intent set differs")
    tasks = [e["task_id"] for e in read(base / "DESIGN.json")["tasks"]]
    for task in tasks[:-1]:
        need(previous.file_map(stages[2] / "tasks" / task, old) == previous.file_map(final_run / "tasks" / task, old),
             "Previously complete task changed: " + task)
    old_denials = previous.audit_denials(base, previous.read_budget_lines(stages[2] / "BUDGET.jsonl"), calls, old)
    need(len(old_denials) == 1 and old_denials[0]["task_id"] == TASK, "Prior last-task denial differs")
    new_denials = []
    for event in events:
        if event["kind"] == "DENY" and event["key"].startswith("CONTINUATION3/"):
            _, task, arm, opportunity = event["key"].split("/")
            denied_folder = final_run / "tasks" / task / ("shared_generation" if arm == "G0" else arm) / opportunity
            need((denied_folder / "request.json").is_file() and event["key"] not in calls
                 and not any((denied_folder / name).exists() for name in ("intent.json", "http_request_body.json", "http_response_body.json", "response.json", "unknown.json")),
                 "Extension denial has dispatch/response evidence")
            new_denials.append({"key": event["key"], "reason": event["reason"], "network_dispatched": False, "counts_as_model_failure": False})
    generation = final_run / "tasks" / TASK / "shared_generation/shared_initial"
    if new_keys:
        need(new_keys[0] == "CONTINUATION3/" + TASK + "/G0/shared_initial", "Extension did not begin with the unsent G0")
        need(old.sha(generation / "request.json") == old.sha(stages[2] / "tasks" / TASK / "shared_generation/shared_initial/request.json"),
             "New generation differs from the never-dispatched request")
    inheritance = read(final_run / "INHERITANCE.json")
    need(inheritance["prior_budget_sha256"] == old.sha(stages[2] / "BUDGET.jsonl")
         and inheritance["prior_run_manifest_sha256"] == old.sha(stages[2] / "MANIFEST.json")
         and inheritance["reused_complete_task_ids"] == tasks[:-1] and inheritance["new_calls_on_reused_tasks"] == 0
         and inheritance["only_new_task"] == TASK and inheritance["previous_generation_request_was_not_dispatched"] is True
         and inheritance["missing_response_replacements_added"] == 0
         and inheritance["permanent_historical_unknown_occupied_usd"] == "2.187456000"
         and inheritance["amendment_sha256"] == manifests["extension"]["amendment_sha256"], "Inheritance differs")
    received, usable, itemized, sums = previous.summarize_usage(calls)
    unknown = [key for key, e in entries.items() if e["state"] in {"UNKNOWN", previous.ACK}]
    unknown_upper = len(unknown) * previous.RESERVATION
    occupied = sum(e["occupied"] for e in entries.values())
    need(occupied == sums["conservative_occupied_nano"] + unknown_upper <= 6_000_000_000, "Final occupied budget differs")
    final, execution = read(final_run / "RESULTS.json"), read(final_run / "EXECUTION_STATUS.json")
    budget_expected = {"cap_usd": "6.000000000", "occupied_upper_usd": old.usd(occupied),
                       "remaining_unoccupied_usd": old.usd(6_000_000_000 - occupied),
                       "known_base_price_estimate_usd": old.usd(sums["base_estimate_nano"]),
                       "cache_component_estimate_usd": old.usd(sums["cache_estimate_nano"]),
                       "known_prompt_tokens": sums["prompt_tokens"], "known_completion_tokens": sums["completion_tokens"],
                       "reserved_requests": len(entries), "cache_component_estimate_responses": len(itemized),
                       "cache_components_unknown_responses": len(usable) - len(itemized), "denials": denials}
    for summary in (final["monetary"], execution["budget"]):
        need(all(summary[k] == v for k, v in budget_expected.items()), "Published monetary aggregate differs")
        need(summary["budget_extension_recorded"] is True and summary["explicit_extended_total_cap_usd"] == 6
             and summary["new_missing_response_replacements"] == 0, "Published extension classification differs")
    def rebind(package, value):
        path = value["native_evidence"].replace("\\", "/")
        suffix = "/continuation3/run/native_evidence/"
        if suffix in path:
            return old.local(package, suffix.strip("/") + "/" + path.split(suffix, 1)[1])
        return previous.rebind(package, value, old)
    rows, native = endpoint.score_endpoints(base, final_run, output, read(base / "DESIGN.json"), java,
                                            old.native_module(base), old, rebind)
    complete, groups, contrasts, pairs, comparison = previous.compare_results(base, final, rows, tasks, old)
    all_known = len(complete) == 24
    need(final["status"] == execution["status"] and (final["status"] == "COMPLETE") == all_known, "Overall completion differs")
    need(final["combined_all_segments_dispatch_intents"] == len(calls)
         and final["unknown_usage_transport_attempts_total"] == len(unknown)
         and final["inherited_unknown_transport_attempts"] == 2
         and final["manual_missing_response_replacements_authorized_total"] == 2
         and final["new_missing_response_replacements_added"] == 0, "Transport/replacement totals differ")
    need(final["prior_run_manifest_sha256"] == old.sha(stages[2] / "MANIFEST.json")
         and final["protocol_amendment_sha256"] == manifests["extension"]["amendment_sha256"], "Final source bindings differ")
    need(final["truncations"] == sum(r["finish_reason"] == "length" for r in received)
         and final["refusals"] == sum(r["refusal"] for r in received), "Truncation/refusal totals differ")
    partial, unstarted, prepared = previous.task_progress(tasks, complete, calls, final_run)
    for stage in stages:
        old.verify_manifest(stage, exhaustive=True)
    itemization_complete = len(usable) == len(itemized)
    return {"schema_version": "atlas.terra.independent-audit/3", "evidence_integrity": "PASS",
            "study_completion": "COMPLETE" if all_known else "INCOMPLETE", "audited_utc": datetime.now(timezone.utc).isoformat(),
            "source_results": "continuation3/run/RESULTS.json", "source_results_sha256": old.sha(final_run / "RESULTS.json"),
            "review_script_sha256": old.sha(Path(__file__)), "preserved_prior_audit_sha256": PRIOR_REPORT_SHA,
            "scope": {"network_calls": 0, "credential_files_read": False, "generation_modules_imported": False,
                      "serializer_modules_imported": False, "source_files_modified": False, "native_scorer": "raw_native_score.py"},
            "manifests": manifests,
            "extension": {"prior_cap_usd": 5, "approved_cap_usd": 6, "old_budget_prefix_unchanged": True,
                          "complete_tasks_reused_byte_identically": tasks[:-1], "only_new_task": TASK,
                          "new_dispatches": len(new_keys), "maximum_new_dispatches": 5,
                          "prior_denial": old_denials[0], "new_denied_requests": new_denials, "new_missing_response_replacements": 0},
            "task_completion": {"planned": 24, "complete": len(complete), "partial": len(partial), "unstarted": len(unstarted),
                                "complete_task_ids": complete, "partial_task_ids": partial, "unstarted_task_ids": unstarted,
                                "prepared_but_not_dispatched_task_ids": prepared},
            "groups": groups, "endpoints": list(rows.values()), "native_revalidation": native,
            "planned_statistics": {"executed": all_known, "contrasts": contrasts,
                                   "reason": "All 72 endpoints known" if all_known else "Missing endpoints; no incomplete-subset tests"},
            "matched_luna_terra_descriptive_only": comparison, "paired_luna_terra": pairs,
            "comparison_limitation": "Fixed author tasks and one seed; model-to-model comparison is descriptive, not a population or superiority claim.",
            "usage_and_cost": {"prompt_tokens": sums["prompt_tokens"], "completion_tokens": sums["completion_tokens"],
                "total_tokens": sums["total_tokens"], "received_unique_responses": len(received),
                "received_responses_with_known_usage": len(usable), "received_responses_with_unknown_usage": len(received) - len(usable),
                "received_responses_with_known_cache_components": len(itemized),
                "received_responses_with_unknown_cache_components": len(usable) - len(itemized),
                "combined_dispatch_intents": len(calls), "duplicate_inherited_receipts_counted_once": copies,
                "known_base_price_estimate_usd": old.usd(sums["base_estimate_nano"]),
                "known_cache_component_price_estimate_usd": old.usd(sums["cache_estimate_nano"]) if itemization_complete else None,
                "cache_itemized_responses_price_subtotal_usd": old.usd(sums["cache_estimate_nano"]),
                "cache_component_breakdown_complete_for_known_usage": itemization_complete,
                "known_conservative_occupancy_usd": old.usd(sums["conservative_occupied_nano"]),
                "old_two_unknowns_permanent_occupancy_usd": "2.187456000", "unknown_requests": unknown,
                "unknown_reserved_upper_usd": old.usd(unknown_upper),
                "known_cache_estimate_plus_unknown_upper_usd": old.usd(sums["cache_estimate_nano"] + unknown_upper) if itemization_complete else None,
                "combined_conservative_occupancy_usd": old.usd(occupied), "maximum_predispatch_occupancy_usd": old.usd(maximum),
                "cap_usd": "6.000000000", "within_client_cap": True, "not_a_provider_invoice": True,
                "price_basis_usd_per_million": {"ordinary_input": "3", "cache_read": "0.3", "cache_write": "3.75", "completion_including_reasoning": "18"},
                "known_max_prompt_tokens": max((r["cost"]["prompt_tokens"] for r in usable), default=None),
                "known_max_completion_tokens": max((r["cost"]["completion_tokens"] for r in usable), default=None),
                "received_responses_at_completion_cap": sum(r["cost"]["completion_tokens"] == 4096 for r in usable),
                "truncations": final["truncations"], "refusals": final["refusals"]},
            "calls": list(calls.values()), "errors": []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, default=BASE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--java", type=Path)
    args = parser.parse_args()
    base, output = args.package_root.resolve(), args.output.resolve()
    need(not output.exists(), "Output must be new; refusing overwrite")
    for directory in ("run", "continuation", "continuation2", "continuation3", "workspace", "inputs", "historical_luna"):
        need(not output.is_relative_to(base / directory), "Output lies in experiment evidence")
    java = args.java.resolve() if args.java else base / "workspace/native_validation/toolchain/jdk8/jdk8u504-b01/bin/java.exe"
    need(java.is_file(), "Java executable missing")
    def no_network(event, args):
        if event.startswith("socket."):
            raise RuntimeError("Python network operation blocked by offline reviewer")
    sys.addaudithook(no_network)
    output.mkdir(parents=True, exist_ok=False)
    try:
        report = review(base, output, java)
        previous, _, _ = helpers(base)
        previous.validate_report(report)
    except Exception as error:
        report = {"schema_version": "atlas.terra.independent-audit/3", "evidence_integrity": "FAIL",
                  "study_completion": "NOT_ASSESSED", "errors": [{"type": type(error).__name__, "message": str(error)}]}
    target = output / "terra_independent_audit.json"
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"report": str(target), "evidence_integrity": report["evidence_integrity"],
                      "study_completion": report["study_completion"], "errors": report["errors"]}, ensure_ascii=True))
    return 0 if report["evidence_integrity"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
