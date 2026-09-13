#!/usr/bin/env python3
"""Check Figures 7 and 8 against original archived events and endpoint records.

Uses the Python standard library, reads archives in memory, and writes only to
stdout. No model calls, extraction, plotting, database access or validator runs.
Optional data-file arguments allow checking an external edited plotting input.
"""

from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from contextlib import ExitStack
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import zipfile
import zlib

sys.dont_write_bytecode = True

FIGURE7 = Path("paper/figure_sources/data/Fig7_vllm_intervention_data.json")
FIGURE8 = Path("paper/figure_sources/data/Fig8_railway_results_data.json")
VLLM_ARCHIVE = Path("experiments/vllm/archives/atlas-vllm-uga-v6-3-4-paper-evidence-20260829.tar.gz")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def decode(data):
    return json.loads(data.decode("utf-8-sig"))


def read_json(path):
    return decode(path.read_bytes())


def equal(actual, expected, location):
    require(actual == expected, f"{location}: recomputed {actual!r}; plotting input has {expected!r}")


def check_figure7(root, plot_path):
    plot = read_json(plot_path)
    source = plot["sources"]["formal_paper_evidence"]
    archive_bytes = (root / VLLM_ARCHIVE).read_bytes()
    equal(sha256(archive_bytes), source["archive_sha256"], "Figure 7 original archive hash")
    equal(len(archive_bytes), source["archive_size_bytes"], "Figure 7 original archive size")
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
        def read_member(name):
            stream = archive.extractfile(name)
            require(stream is not None, f"Missing original vLLM member: {name}")
            return stream.read()

        def referenced(ref):
            data = read_member(ref["member"])
            equal(sha256(data), ref["sha256"], f"Original member hash {ref['member']}")
            return decode(data)

        referenced(source["formal_result"])
        audit_bytes = read_member(source["audit_member"])
        equal(sha256(audit_bytes), source["audit_member_sha256"], "Figure 7 original event-file hash")
        states = {}
        line_count = 0
        for line_count, line in enumerate(audit_bytes.splitlines(), 1):
            event = decode(line)
            rid = event["request_id"]
            state = states.setdefault(rid, {"sequence": 0, "chain": "0" * 64,
                                           "types": Counter(), "bindings": [], "bound": [],
                                           "lines": [], "evaluable": 0})
            equal(event["sequence"], state["sequence"], f"Event sequence at line {line_count}")
            equal(event["previous_chain_sha256"], state["chain"], f"Previous hash at line {line_count}")
            core = {k: event[k] for k in ("schema_version", "record_type", "timestamp_ns",
                                        "request_id", "sequence", "event")}
            digest = sha256(bytes.fromhex(state["chain"]) + canonical(core))
            equal(digest, event["chain_sha256"], f"Event hash at line {line_count}")
            state["sequence"] += 1
            state["chain"] = digest
            kind = event["event"]["event_type"]
            state["types"][kind] += 1
            if kind == "request_start":
                state["metadata"] = event["event"]["metadata"]
            if kind == "binding_step":
                payload = event["event"]["payload"]
                ordinal = payload["sample_ordinal"]
                state["bindings"].append(ordinal)
                require(payload["mask_applied"] is True, f"Mask not applied at line {line_count}")
                state["evaluable"] += payload["evaluable"] is True
                if payload["bound"]:
                    require(payload["evaluable"] is True, f"Unevaluable bound step at line {line_count}")
                    state["bound"].append(ordinal)
                    state["lines"].append(line_count)
        equal(line_count, source["audit_ndjson_lines"], "Original event count")
        rows = plot["audit_requests"]
        equal(set(states), {row["internal_request_id"] for row in rows}, "Audited request identities")
        equal(len(rows), len(states), "Audited request uniqueness")
        originals, traces = {}, defaultdict(list)

        def original_pair(request_ref, post_ref, case, repeat, arm):
            request, post = referenced(request_ref), referenced(post_ref)
            schedule = request["schedule"]
            for key, value in (("case_id", case), ("repetition", repeat), ("arm", arm)):
                equal(schedule[key], value, f"Original request {key}")
            equal(post["schedule_ordinal"], schedule["schedule_ordinal"], "Postprocess request ordinal")
            equal(post["case_id"], case, "Postprocess case")
            equal(post["arm"], arm, "Postprocess arm")
            equal(post["source_result_content_sha256"], request["content_sha256"], "Postprocess input identity")
            equal(sha256(request["output"].encode("utf-8")), request["output_sha256"], "Original output hash")
            token_evidence = request["output_token_ids_evidence"]
            tokens_bytes = zlib.decompress(base64.b64decode(token_evidence["data"]))
            tokens = decode(tokens_bytes)
            equal(sha256(canonical(tokens)), request["output_token_ids_sha256"], "Original output token hash")
            equal(len(tokens), request["usage"]["completion_tokens"], "Original completion token count")
            originals[(case, repeat, arm)] = request
            return request, post

        for row in rows:
            location = f"Figure 7 {row['case_id']} repetition {row['repeat']}"
            state = states[row["internal_request_id"]]
            count = len(state["bindings"])
            equal(state["types"]["request_start"], 1, location + " request start")
            equal(state["types"]["request_end"], 1, location + " request end")
            equal(state["bindings"], list(range(count)), location + " contiguous output ordinals")
            equal(state["evaluable"], count, location + " evaluable steps")
            equal(row["source"]["audit_member"], source["audit_member"], location + " audit member")
            values = {"case": row["case_id"], "arm": "A", "total_steps": count,
                      "evaluable_steps": state["evaluable"], "bound_steps": len(state["bound"]),
                      "bound_sample_ordinals": state["bound"],
                      "bound_event_source_lines_1based": state["lines"],
                      "sample_ordinal_base": 0, "last_sample_ordinal": count - 1,
                      "external_request_id": state["metadata"]["external_request_id"]}
            request, post = original_pair(row["source"]["request_result"], row["source"]["postprocess_result"],
                                          row["case_id"], row["repeat"], "A")
            for target, key in (("tier", "tier"), ("formal_case_ordinal", "case_ordinal"),
                                ("seed", "seed"), ("schedule_ordinal", "schedule_ordinal")):
                values[target] = request["schedule"][key]
            values["completion_tokens"] = request["usage"]["completion_tokens"]
            values["end_to_end_structural_decision"] = post["end_to_end_structural_decision"]
            equal(values["completion_tokens"], count, location + " binding count versus completion")
            for key, value in values.items():
                equal(value, row[key], location + " " + key)
            traces[row["case_id"]].append((count, tuple(state["bound"])))
        for case, repetitions in traces.items():
            equal(len(repetitions), 3, case + " trace repetitions")
            equal(len(set(repetitions)), 1, case + " overlaid trace identity")

        passes, outcomes, identity_pairs = Counter(), Counter(), 0
        equal({p["case_id"] for p in plot["case_pairs"]}, set(traces), "Figure 7 case sets")
        equal(len(plot["case_pairs"]), len(traces), "Figure 7 case uniqueness")
        for pair in plot["case_pairs"]:
            case = pair["case_id"]
            equal(pair["case"], case, "Figure 7 case label")
            equal([r["repeat"] for r in pair["per_repetition"]], [1, 2, 3], case + " paired repetitions")
            case_pass = Counter()
            for repetition in pair["per_repetition"]:
                for arm in ("U", "G"):
                    record = repetition[arm]
                    request, post = original_pair(record["source_request_result"], record["source_postprocess_result"],
                                                  case, repetition["repeat"], arm)
                    values = {"decision": post["end_to_end_structural_decision"],
                              "schema_decision": request["schema_decision"],
                              "schedule_ordinal": request["schedule"]["schedule_ordinal"],
                              "output_sha256": request["output_sha256"],
                              "output_token_ids_sha256": request["output_token_ids_sha256"],
                              "completion_tokens": request["usage"]["completion_tokens"]}
                    for key, value in values.items():
                        equal(value, record[key], f"Figure 7 {case} {arm} r{repetition['repeat']} {key}")
                    case_pass[arm] += values["decision"] == "PASS"
                g = originals[(case, repetition["repeat"], "G")]
                a = originals[(case, repetition["repeat"], "A")]
                identity_pairs += all(g[k] == a[k] for k in ("output_sha256", "output_token_ids_sha256"))
            passes.update(case_pass)
            equal(pair["repetitions"], 3, case + " repetition denominator")
            for arm in ("U", "G"):
                equal(case_pass[arm], pair[arm.lower() + "_pass_count"], case + " pass count " + arm)
                equal(case_pass[arm] == 3, pair[arm.lower() + "_case_all_repetitions_pass"], case + " all-pass " + arm)
            outcome = "improved" if case_pass["G"] > case_pass["U"] else "worsened" if case_pass["G"] < case_pass["U"] else "tied"
            equal(outcome, pair["paired_outcome"], case + " paired outcome")
            outcomes[outcome] += 1
        bound = sum(len(s["bound"]) for s in states.values())
        evaluable = sum(s["evaluable"] for s in states.values())
        summary = {"audit_requests": len(states), "requests_with_binding": sum(bool(s["bound"]) for s in states.values()),
                   "evaluable_steps": evaluable, "bound_steps": bound, "binding_rate": bound / evaluable,
                   "bound_steps_min": min(len(s["bound"]) for s in states.values()),
                   "bound_steps_max": max(len(s["bound"]) for s in states.values()),
                   "case_count": len(traces), "repetitions_per_case": 3,
                   "u_pass_runs": passes["U"], "g_pass_runs": passes["G"],
                   "cases_improved": outcomes["improved"], "cases_worsened": outcomes["worsened"],
                   "cases_tied": outcomes["tied"], "ga_output_and_token_identity_equal_pairs": identity_pairs}
        for key, value in summary.items():
            equal(value, plot["summary"][key], "Figure 7 summary " + key)
        return {"status": "PASS", "original_archive": VLLM_ARCHIVE.as_posix(),
                "event_lines_and_hashes_recomputed": line_count, "all_plotted_positions_and_source_lines_match": True,
                "identical_repetitions_per_case": 3, "request_postprocess_pairs_read": len(originals),
                "summary": summary,
                "scope": "Re-extraction of recorded binding flags, event hash chains and structural acceptance records. Historical logits and masks are not reconstructed."}


def check_figure8(root, plot_path):
    plot = read_json(plot_path)
    rail_root = root / "experiments/railway"
    manifest = read_json(rail_root / "PAYLOAD_MANIFEST.json")
    with ExitStack() as stack:
        members = {}
        for entry in manifest["archives"]:
            data = (rail_root / entry["path"]).read_bytes()
            equal(len(data), entry["bytes"], "Railway original archive size")
            equal(sha256(data), entry["sha256"], "Railway original archive hash")
            archive = stack.enter_context(zipfile.ZipFile(io.BytesIO(data)))
            for name in archive.namelist():
                require(name not in members, f"Duplicate railway archive member: {name}")
                members[name] = archive

        def original(name):
            data = members[name].read(name)
            equal(sha256(data), manifest["files"][name]["sha256"], f"Railway original member {name}")
            return decode(data)

        plan = original("frozen/release/EXECUTION_PLAN.json")
        units = {u["unit_id"]: u for u in plan["units"]}
        stage_counts, luna = {}, {}
        original_scores_read = 0
        for stage, arms, denominator, plot_key in (("G", ["G0", "GS", "GF"], 72, "historical_G_counts"),
                                                  ("R", ["S", "V", "F"], 144, "controlled_R_counts")):
            rows = original(f"frozen/release/formal_export/paired/{stage}.json")["records"]
            equal({r["unit_id"] for r in rows}, {u["unit_id"] for u in units.values() if u["stage"] == stage},
                  stage + " scheduled unit set")
            equal(len(rows), denominator * len(arms), stage + " original row denominator")
            counts, denominators = Counter(), Counter()
            for row in rows:
                unit = units[row["unit_id"]]
                prefix = "frozen/release/paid_formal/" + unit["directory"] + "/"
                arm = unit["arm"]
                denominators[arm] += 1
                if "independent_score" in row:
                    score_name = prefix + ("independent.json" if arm == "G0" else "independent_final.json")
                    score = original(score_name)["value"]
                    # The paired export reran native checks. Process IDs, timing,
                    # temporary paths and diagnostic object addresses can differ.
                    for key in ("artifact_sha256", "frame_errors", "independent_query_matches",
                                "task_results", "strict_success"):
                        equal(score[key], row["independent_score"][key],
                              "Original score versus paired row " + row["unit_id"] + " " + key)
                    for key in ("eobject_projection", "query_tuples", "pass", "loaded", "identity_checks"):
                        equal(score["native_receipt"][key], row["independent_score"]["native_receipt"][key],
                              "Original native result versus paired row " + row["unit_id"] + " " + key)
                    original_scores_read += 1
                    native = score["native_receipt"]
                    success = (native["pass"] is True and not any(score["independent_query_matches"].values())
                               and all(t["pass"] is True for t in score["task_results"])
                               and not score["frame_errors"])
                    equal(success, score["strict_success"], "Recombined recorded checks " + row["unit_id"])
                else:
                    result = original(prefix + "result.json")
                    require(result["status"] in {"ASSIGNMENT_REJECTED", "NOT_RUN_SHARED_ASSIGNMENT_REJECTED"},
                            "Unexpected unmaterialized original unit status")
                    require(result.get("model") is None and result.get("final_model") is None,
                            "Rejected original unit unexpectedly has a model")
                    success = False
                equal(success, row["outcome"], "Original endpoint versus paired row " + row["unit_id"])
                counts[arm] += success
                if stage == "G" and unit["seed"] == 104729:
                    luna[(unit["base_scenario_id"], arm)] = success
            equal(dict(denominators), {arm: denominator for arm in arms}, stage + " arm denominators")
            values = [counts[arm] for arm in arms]
            equal(values, plot[plot_key], "Figure 8 " + plot_key)
            stage_counts[stage] = values
        equal(plot["historical_G_denominator"], 72, "Figure 8 generation denominator")
        equal(plot["controlled_R_denominator"], 144, "Figure 8 controlled-damage denominator")
        equal(plot["natural_arms"], ["G0", "GS", "GF"], "Figure 8 generation arm order")
        equal(plot["controlled_arms"], ["S", "V", "F"], "Figure 8 damage arm order")

    terra_root = root / "experiments/railway_terra"
    parts = read_json(terra_root / "PARTS_MANIFEST.json")
    buffer = io.BytesIO()
    for index, part in enumerate(parts["parts"], 1):
        equal(part["index"], index, "Terra part index")
        equal(buffer.tell(), part["offset"], "Terra part offset")
        data = (terra_root / part["path"]).read_bytes()
        equal(len(data), part["bytes"], "Terra part size")
        equal(sha256(data), part["sha256"], "Terra part hash")
        buffer.write(data)
    equal(buffer.tell(), parts["archive"]["bytes"], "Terra original archive size")
    equal(sha256(buffer.getbuffer()), parts["archive"]["sha256"], "Terra original archive hash")
    result_member = "ATLAS_TERRA_SUPPLEMENT/continuation3/run/RESULTS.json"
    with zipfile.ZipFile(buffer) as archive:
        result_bytes = archive.read(result_member)
        equal(sha256(result_bytes), plot["supplement_source_sha256"], "Figure 8 original Terra results hash")
        results = decode(result_bytes)
    rows = results["rows"]
    terra = {(r["task_id"], r["arm"]): r["strict_success"] for r in rows}
    equal(len(terra), len(rows), "Terra original endpoint uniqueness")
    equal(set(terra), set(luna), "Original Luna/Terra task-arm pairing")
    equal(len(terra), 72, "Terra original endpoint count")
    require(all(r["known_endpoint"] is True for r in rows), "Terra has unknown endpoints")
    equal(plot["supplement_all_72_known"], True, "Figure 8 endpoint coverage")
    paired_bytes = (terra_root / "reports/paired_tasks.csv").read_bytes()
    paired = list(csv.DictReader(io.StringIO(paired_bytes.decode("utf-8-sig"))))
    equal(len(paired), 24, "Paired CSV task count")
    equal({r["task_id"] for r in paired}, {key[0] for key in terra}, "Paired CSV task set")
    for row in paired:
        for arm in ("G0", "GS", "GF"):
            key = (row["task_id"], arm)
            equal(row["Terra_" + arm], str(int(terra[key])), "Original Terra endpoint versus paired CSV " + str(key))
            equal(row["Luna_" + arm], str(luna[key]), "Original Luna endpoint versus paired CSV " + str(key))
    luna_counts = [sum(v for (task, arm), v in luna.items() if arm == a) for a in ("G0", "GS", "GF")]
    terra_counts = [sum(v for (task, arm), v in terra.items() if arm == a) for a in ("G0", "GS", "GF")]
    equal(luna_counts, plot["same_task_Luna_counts"], "Figure 8 same_task_Luna_counts")
    equal(terra_counts, plot["Terra_counts"], "Figure 8 Terra_counts")
    equal(plot["supplement_denominator"], 24, "Figure 8 supplement denominator")
    return {"status": "PASS", "railway_archive_count": len(manifest["archives"]),
            "original_railway_scores_read": original_scores_read,
            "historical_generation_counts": stage_counts["G"], "generation_denominator": 72,
            "controlled_damage_counts": stage_counts["R"], "damage_denominator": 144,
            "original_Terra_result_member": result_member, "original_Terra_endpoints": len(rows),
            "paired_CSV_sha256": sha256(paired_bytes), "paired_CSV_tasks": len(paired),
            "same_task_Luna_seed": 104729, "same_task_Luna_counts": luna_counts,
            "Terra_counts": terra_counts, "supplement_denominator": 24,
            "scope": "Counts recomputed from original per-unit scores and endpoint rows, cross-checked against paired CSV and plotting data. Recorded check outcomes are recombined; EMF/VIATRA validators are not rerun."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--figure", choices=("7", "8", "all"), default="all")
    parser.add_argument("--figure7-data", type=Path, help="Optional external Figure 7 plotting JSON to check")
    parser.add_argument("--figure8-data", type=Path, help="Optional external Figure 8 plotting JSON to check")
    args = parser.parse_args()
    root = args.release_root.resolve()
    try:
        report = {"inspection": "PASS", "mode": "read-only original-evidence comparison"}
        if args.figure in ("7", "all"):
            report["figure7"] = check_figure7(root, args.figure7_data or root / FIGURE7)
        if args.figure in ("8", "all"):
            report["figure8"] = check_figure8(root, args.figure8_data or root / FIGURE8)
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError, zipfile.BadZipFile, zlib.error) as error:
        print(f"Figure evidence inspection failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
