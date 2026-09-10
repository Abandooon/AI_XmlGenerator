"""Read-only raw-XMI review, retaining unknown-usage response classification.

Missing usage contributes no known token sum; unknown_usage remains explicit.
This is not an assignment of zero token usage or zero price to that request.
"""
def score_endpoints(base, run, output, design, java, native, old, rebind):
    local, sha, identity, read, need = old.local, old.sha, old.identity, old.read, old.need
    ARMS, SCORE_FIELDS = old.ARMS, old.SCORE_FIELDS
    rebind_native_evidence = rebind
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
                       prompt_tokens=sum((r.get("usage") or {}).get("prompt_tokens", 0) for r in responses),
                       completion_tokens=sum((r.get("usage") or {}).get("completion_tokens", 0) for r in responses),
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
