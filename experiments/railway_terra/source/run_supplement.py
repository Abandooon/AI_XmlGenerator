"""Offline preparation/replay and explicitly gated paid supplement entry point."""
from pathlib import Path
import argparse,hashlib,json,math,os,sys,time
from contextlib import contextmanager

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"workspace"))
from supplement_runtime import Budget,MonetaryStop,BudgetIntegrityError,SupplementProvider,LunaReplayProvider,read,identity,configuration,now,canonical
from railway_method_v5.task_compiler import compile_task
from railway_method_v5.pipeline import generation_branches
from railway_method_v5.bounded_native import NativeValidator
import supplement_native

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(value,ensure_ascii=False,indent=2)+"\n"
    if path.exists():
        if path.read_text(encoding="utf-8")!=text: raise BudgetIntegrityError("Refusing to overwrite different retained evidence: "+str(path))
    else:
        with path.open("x",encoding="utf-8",newline="") as stream:
            stream.write(text);stream.flush();os.fsync(stream.fileno())

@contextmanager
def exclusive_lock(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    path=directory/"RUNNING.lock";owner={"pid":os.getpid(),"nonce":os.urandom(16).hex(),"utc":now()}
    with path.open("x",encoding="utf-8",newline="") as stream:
        stream.write(canonical(owner));stream.flush();os.fsync(stream.fileno())
    try: yield
    finally:
        if path.exists() and read(path)==owner:path.unlink()

def compiled(entry):
    path=HERE/entry["task_file"]
    if digest(path)!=entry["task_file_sha256"]:raise BudgetIntegrityError("Task bytes changed")
    task=compile_task(read(path))
    if task.contract_hash!=entry["contract_sha256"]:raise BudgetIntegrityError("Compiled task differs from the frozen Luna contract")
    return task

def terminal(directory,arm,task_id,run_stop):
    branch=directory/("shared_generation" if arm=="G0" else arm)
    file=branch/"result.json"
    base={"task_id":task_id,"arm":arm,"known_endpoint":False,"strict_success":False,
          "failure_type":"NOT_RUN_"+run_stop,"model_failure":None,"requests":0,"prompt_tokens":0,"completion_tokens":0}
    responses=[read(p) for p in branch.glob("*/response.json")]
    base.update(requests=len(responses),prompt_tokens=sum((r.get("usage") or {}).get("prompt_tokens",0) for r in responses),
                completion_tokens=sum((r.get("usage") or {}).get("completion_tokens",0) for r in responses),
                truncations=sum(bool(r.get("output_truncated") or r.get("finish_reason")=="length") for r in responses),
                refusals=sum(r.get("kind")=="REFUSAL" for r in responses),
                unknown_usage=sum(r.get("usage") is None for r in responses))
    if not file.exists():return base
    result=read(file);state=result.get("status",result.get("stop_reason"))
    base["failure_type"]=state
    if state in {"UNKNOWN_RESPONSE","NOT_RUN_SHARED_RESPONSE_UNKNOWN"}:return base
    if result.get("stage")=="generation_terminal" or state=="ASSIGNMENT_REJECTED" or state=="NOT_RUN_SHARED_ASSIGNMENT_REJECTED":
        base.update(known_endpoint=True,strict_success=False,model_failure=True)
        return base
    scorefile=branch/("independent.json" if arm=="G0" else "independent_final.json")
    if not scorefile.exists():return base
    score=read(scorefile)["value"]
    known=score.get("status")=="EVALUATED" and score.get("oracle_agreement") is True
    base.update(known_endpoint=known,strict_success=known and bool(score.get("strict_success")),
                model_failure=(not bool(score.get("strict_success"))) if known else None,
                task_failures=[r["id"] for r in score.get("task_results",[]) if not r["pass"]],
                frame_failures=score.get("frame_errors",[]),
                query_failures={k:len(v) for k,v in score.get("independent_query_matches",{}).items() if v})
    if base["strict_success"]:base["failure_type"]="NONE_FINAL_ARTIFACT_VALID"
    return base

def mcnemar(a,b):
    both=sum(x and y for x,y in zip(a,b));only_a=sum(x and not y for x,y in zip(a,b));only_b=sum(y and not x for x,y in zip(a,b))
    n=only_a+only_b;p=min(1.0,2*sum(math.comb(n,k) for k in range(min(only_a,only_b)+1))/(2**n)) if n else 1.0
    return {"both_success":both,"only_first_success":only_a,"only_second_success":only_b,
            "neither_success":len(a)-both-only_a-only_b,"second_minus_first_pp":100*(sum(b)-sum(a))/len(a),"exact_two_sided_p":p}

def luna_endpoint(row):
    # trace_measures.final_valid is artifact validity, not the no-artifact endpoint.
    # The frozen shared-generation termination rule counts rejected assignments
    # and both downstream branches as known failures, while unknowns remain unknown.
    if row["state"] in {"ASSIGNMENT_REJECTED","NOT_RUN_SHARED_ASSIGNMENT_REJECTED"}:return False
    if row["state"] in {"UNKNOWN_RESPONSE","NOT_RUN_SHARED_RESPONSE_UNKNOWN"}:return None
    return row["final_valid"]

def analyze(folder,run_stop="COMPLETE",write_output=True):
    folder=Path(folder);design=read(HERE/"DESIGN.json")
    rows=[terminal(folder/"tasks"/entry["task_id"],arm,entry["task_id"],run_stop) for entry in design["tasks"] for arm in ("G0","GS","GF")]
    groups={a:{"planned":24,"known":sum(r["known_endpoint"] for r in rows if r["arm"]==a),
               "strict_success":sum(r["strict_success"] for r in rows if r["arm"]==a),
               "strict_success_rate_all_planned":sum(r["strict_success"] for r in rows if r["arm"]==a)/24,
               "received_responses":sum(r["requests"] for r in rows if r["arm"]==a),
               "prompt_tokens":sum(r["prompt_tokens"] for r in rows if r["arm"]==a),
               "completion_tokens":sum(r["completion_tokens"] for r in rows if r["arm"]==a)} for a in ("G0","GS","GF")}
    complete=all(r["known_endpoint"] for r in rows)
    contrasts={}
    if complete:
        for first in ("G0","GS"):
            a=[r["strict_success"] for r in rows if r["arm"]==first];b=[r["strict_success"] for r in rows if r["arm"]=="GF"]
            contrasts[first+"_vs_GF"]=mcnemar(a,b)
        ordered=sorted(contrasts,key=lambda k:contrasts[k]["exact_two_sided_p"]);previous=0
        for index,key in enumerate(ordered):
            previous=max(previous,min(1,contrasts[key]["exact_two_sided_p"]*(2-index)));contrasts[key]["holm_p"]=previous
    historical=read(HERE/"historical_luna/BASELINE_ROWS.json")
    lookup={(r["unit_id"].split(":")[1],r["arm"]):r for r in historical}
    pairs=[{"task_id":r["task_id"],"arm":r["arm"],"luna_success":luna_endpoint(lookup[r["task_id"],r["arm"]]),
            "luna_trace_artifact_final_valid":lookup[r["task_id"],r["arm"]]["final_valid"],
            "luna_state":lookup[r["task_id"],r["arm"]]["state"],
            "supplement_success":r["strict_success"] if r["known_endpoint"] else None} for r in rows]
    budget=Budget(folder/"BUDGET.jsonl").summary() if (folder/"BUDGET.jsonl").exists() else None
    result={"status":run_stop,"all_72_endpoints_known":complete,"groups":groups,"rows":rows,"exploratory_mcnemar_holm":contrasts,
            "luna_same_task_pairs_descriptive_only":pairs,"monetary":budget,
            "truncations":sum(r["truncations"] for r in rows),"refusals":sum(r["refusals"] for r in rows),
            "unknown_usage_responses":sum(r["unknown_usage"] for r in rows),
            "analysis_scope":"Fixed 24 author tasks, one prespecified seed; no superiority or population claim"}
    if write_output:save(folder/"RESULTS.json",result)
    return result

def offline_replay(folder):
    folder=Path(folder)
    if folder.exists():raise BudgetIntegrityError("Use a new offline replay directory; no overwrite")
    design=read(HERE/"DESIGN.json");native=NativeValidator()
    supplement_native.EVIDENCE=folder/"native_evidence"
    with exclusive_lock(folder):
        for number,entry in enumerate(design["tasks"],1):
            task=compiled(entry);source=HERE/"historical_luna/units"/entry["task_id"]
            providers=[LunaReplayProvider(source/name) for name in ("shared_generation","GS","GF")]
            result=generation_branches(task,104729,*providers,folder/"tasks"/entry["task_id"],native)
            save(folder/"checkpoints"/(entry["task_id"]+".json"),{"status":result["status"],"calls":sum(p.calls for p in providers),"network_calls":0})
            print(json.dumps({"offline_task":number,"total":24,"task":entry["task_id"],"status":result["status"],"network_calls":0}),flush=True)
        result=analyze(folder,"OFFLINE_LUNA_REPLAY")
        mismatches=[p for p in result["luna_same_task_pairs_descriptive_only"] if p["luna_success"]!=p["supplement_success"]]
        summary={"pass":not mismatches and result["all_72_endpoints_known"],"mismatches":mismatches,"groups":result["groups"],"network_calls":0,
                 "scope":"Saved Luna replies under unchanged task/schema/prompt/state; only declared model/output-cap metadata differ. These are not Terra observations.",
                 "result_sha256":digest(folder/"RESULTS.json")}
        save(folder/"REPLAY_CHECK.json",summary)
        if not summary["pass"]:raise BudgetIntegrityError("Historical replay does not match all 72 frozen endpoints")
        return summary

def recheck_offline_analysis(folder):
    folder=Path(folder)
    prior=read(folder/"REPLAY_CHECK.json")
    if len(list((folder/"checkpoints").glob("*.json")))!=24:raise BudgetIntegrityError("All 24 offline task checkpoints required")
    result=analyze(folder,"OFFLINE_LUNA_REPLAY",write_output=False)
    save(folder/"RESULTS_ENDPOINT_MAPPING_CORRECTED.json",result)
    mismatches=[p for p in result["luna_same_task_pairs_descriptive_only"] if p["luna_success"]!=p["supplement_success"]]
    summary={"pass":not mismatches and result["all_72_endpoints_known"],"mismatches":mismatches,"groups":result["groups"],"network_calls":0,
             "scope":prior["scope"],"result_sha256":digest(folder/"RESULTS_ENDPOINT_MAPPING_CORRECTED.json"),
             "analysis_mapping_correction":"Use the frozen shared-generation rejection endpoint rule for three no-artifact rows; retain raw trace final_valid=null. Original artifacts, replies, task validation and success counts unchanged.",
             "original_check_sha256":digest(folder/"REPLAY_CHECK.json")}
    save(folder/"REPLAY_CHECK_CORRECTED.json",summary)
    if not summary["pass"]:raise BudgetIntegrityError("Corrected offline endpoint mapping still disagrees")
    print(json.dumps({"offline_reanalysis_pass":True,"network_calls":0,"endpoints":72,"success_counts":{a:g["strict_success"] for a,g in result["groups"].items()}}),flush=True)
    return summary

def source_seal():
    files=[p for p in HERE.glob("*.py")]+[HERE/"DESIGN.json",HERE/"SOURCE_MANIFEST.json",HERE/"PREPARATION_REPORT.json"]
    files+=list((HERE/"workspace").rglob("*.py"))+list((HERE/"workspace/authority").glob("*"))
    files+=list((HERE/"inputs").rglob("*.json"))
    files+=list((HERE/"historical_luna").rglob("*.json"))+list((HERE/"historical_luna").rglob("*.xmi"))
    files+=list((HERE/"workspace/native_validation").rglob("*.jar"))
    files+=list((HERE/"workspace/native_validation/toolchain").rglob("*"))
    return {p.relative_to(HERE).as_posix():digest(p) for p in sorted(set(files)) if p.is_file()}

def prepare_report(replay_folder):
    replay_path=Path(replay_folder)/"REPLAY_CHECK_CORRECTED.json"
    if not replay_path.exists():replay_path=Path(replay_folder)/"REPLAY_CHECK.json"
    replay=read(replay_path)
    if not replay["pass"]:raise BudgetIntegrityError("Passing offline replay required")
    import unittest
    import test_supplement
    suite=unittest.defaultTestLoader.loadTestsFromModule(test_supplement)
    test_result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not test_result.wasSuccessful():raise BudgetIntegrityError("Supplement boundary tests failed")
    source=read(HERE/"SOURCE_MANIFEST.json")
    original=Path(source["source_release"])
    selected_responses=[read(p) for p in (HERE/"historical_luna/units").rglob("response.json")]
    all_g_responses=[read(p) for p in (original/"paid_formal/units").glob("G*/*/*/response.json")]
    raw_requests=[read(p) for p in (HERE/"historical_luna/units").rglob("request.json")]
    sizes=[len(canonical(r["wire_body"]).encode("utf-8")) for r in raw_requests]
    current_requests=[read(p) for p in (Path(replay_folder)/"tasks").rglob("request.json")]
    current_sizes=[len(canonical(r["wire_body"]).encode("utf-8")) for r in current_requests]
    if len(current_requests)!=68 or max(current_sizes)>Budget.MAX_BODY_BYTES:
        raise BudgetIntegrityError("Historical replay request count or new input-size admission differs")
    changed=[]
    for rel,item in source["files"].items():
        local=HERE/"workspace"/rel
        if local.exists() and digest(local)!=item["sha256"]:changed.append({"path":rel,"historical_sha256":item["sha256"],"supplement_sha256":digest(local)})
    result={"status":"READY_AWAITING_PARENT_NETWORK_START","network_calls":0,"credential_values_read":False,
        "design_path":str(HERE/"DESIGN.json"),"design_sha256":digest(HERE/"DESIGN.json"),"configuration":configuration(False),
        "offline_replay":str(Path(replay_folder).resolve()),"offline_replay_pass":True,"offline_replay_received_responses":sum(g["received_responses"] for g in replay["groups"].values()),
        "offline_replay_check":str(replay_path.resolve()),"offline_endpoint_mapping_correction":replay.get("analysis_mapping_correction"),
        "all_72_historical_endpoints_agree":True,"boundary_tests_passed":test_result.testsRun,
        "historical_selected_seed_max_completion_tokens":max(r["usage"]["completion_tokens"] for r in selected_responses),
        "historical_all_G_max_completion_tokens":max(r["usage"]["completion_tokens"] for r in all_g_responses),
        "historical_selected_request_body_bytes_max":max(sizes),"historical_selected_input_tokens_max":max(r["usage"]["prompt_tokens"] for r in selected_responses),
        "supplement_parameter_replay_request_body_bytes_max":max(current_sizes),"request_byte_limit":Budget.MAX_BODY_BYTES,
        "supplement_parameter_replay_requests_within_byte_limit":len(current_requests),"input_token_reservation":Budget.INPUT_CAP,
        "new_completion_cap":4096,"historical_records_over_new_cap":sum(r["usage"]["completion_tokens"]>4096 for r in all_g_responses),
        "changed_historical_source_files":changed,"client_budget_reservation_usd":"1.093728","hard_client_total_ceiling_usd":"5.000000000",
        "billing_assumptions":read(HERE/"DESIGN.json")["budget"]["assumption"],"python":sys.version,"python_executable":sys.executable}
    save(HERE/"PREPARATION_REPORT.json",result)
    seal=source_seal();save(HERE/"EXECUTION_SEAL.json",seal)
    print(json.dumps({"status":result["status"],"preparation_report":str(HERE/"PREPARATION_REPORT.json"),"execution_seal_sha256":digest(HERE/"EXECUTION_SEAL.json")},ensure_ascii=False),flush=True)
    return result

def verify_start(approval):
    report=read(HERE/"PREPARATION_REPORT.json")
    approved=read(approval)
    if approved.get("parent_confirmed_start") is not True or approved.get("budget_usd")!=5 or approved.get("model")!="gpt-5.6-terra":
        raise BudgetIntegrityError("Explicit parent-reviewed start authorization is required")
    if approved.get("design_sha256")!=digest(HERE/"DESIGN.json") or approved.get("execution_seal_sha256")!=digest(HERE/"EXECUTION_SEAL.json"):
        raise BudgetIntegrityError("Start authorization does not match reviewed design/code")
    if read(HERE/"EXECUTION_SEAL.json")!=source_seal():raise BudgetIntegrityError("Code/data changed after preparation review")
    return report

def execute(approval,resume=False):
    verify_start(approval);folder=HERE/"run"
    if folder.exists() and not resume:raise BudgetIntegrityError("Existing run requires explicit resume after review")
    if (folder/"RESULTS.json").exists():raise BudgetIntegrityError("A sealed result cannot make further calls")
    supplement_native.EVIDENCE=folder/"native_evidence"
    stop="COMPLETE";detail=None
    with exclusive_lock(folder):
        budget=Budget(folder/"BUDGET.jsonl")
        if budget.unresolved:raise MonetaryStop("Pending/unknown monetary record blocks resume")
        endpoint,secret=configuration(True)
        try:
            save(folder/"EXECUTION_PARAMETERS.json",{"design_sha256":digest(HERE/"DESIGN.json"),"execution_seal_sha256":digest(HERE/"EXECUTION_SEAL.json"),"model":"gpt-5.6-terra","seed":104729,"budget_usd":5,"mode":"TERRA_AUTHORIZED_SUPPLEMENT","credentials_persisted":False})
            native=NativeValidator()
            for number,entry in enumerate(read(HERE/"DESIGN.json")["tasks"],1):
                checkpoint=folder/"checkpoints"/(entry["task_id"]+".json")
                if checkpoint.exists():continue
                task=compiled(entry)
                providers=[SupplementProvider(budget,endpoint,secret,entry["task_id"],arm) for arm in ("G0","GS","GF")]
                try:
                    result=generation_branches(task,104729,*providers,folder/"tasks"/entry["task_id"],native)
                except MonetaryStop as error:
                    stop="BUDGET_OR_TRANSPORT_GUARD_STOP";detail=str(error);break
                save(checkpoint,{"task_id":entry["task_id"],"status":result["status"],"new_calls":sum(p.new_model_calls for p in providers),"budget":budget.summary()})
                print(json.dumps({"completed_task":number,"task":entry["task_id"],"status":result["status"],"budget":budget.summary()},ensure_ascii=False),flush=True)
                if budget.unresolved or result["status"] in {"UNKNOWN_RESPONSE","INCOMPLETE_VALIDATION"} or result["status"]=="NO_INITIAL_ARTIFACT" and result["shared"].get("status")=="UNKNOWN_RESPONSE":
                    stop="UNKNOWN_OR_INCOMPLETE_STOP";break
        finally:secret=None
        save(folder/"EXECUTION_STATUS.json",{"status":stop,"detail":detail,"finished_utc":now(),"budget":budget.summary(),"additional_samples_allowed":False})
        result=analyze(folder,stop)
        save(folder/"MANIFEST.json",{p.relative_to(folder).as_posix():digest(p) for p in sorted(folder.rglob("*")) if p.is_file() and p.name not in {"RUNNING.lock","MANIFEST.json"}})
        print(json.dumps({"status":stop,"groups":result["groups"],"monetary":result["monetary"]},ensure_ascii=False),flush=True)
        return result

def main():
    parser=argparse.ArgumentParser();commands=parser.add_mutually_exclusive_group(required=True)
    commands.add_argument("--offline-replay",type=Path);commands.add_argument("--prepare-report",type=Path)
    commands.add_argument("--execute",action="store_true");commands.add_argument("--analyze",type=Path)
    commands.add_argument("--recheck-offline-analysis",type=Path)
    parser.add_argument("--approval",type=Path);parser.add_argument("--resume",action="store_true")
    args=parser.parse_args()
    if args.offline_replay:return offline_replay(args.offline_replay)
    if args.prepare_report:return prepare_report(args.prepare_report)
    if args.recheck_offline_analysis:return recheck_offline_analysis(args.recheck_offline_analysis)
    if args.analyze:return analyze(args.analyze,write_output=False)
    if args.approval is None:raise BudgetIntegrityError("--approval is required before paid execution")
    return execute(args.approval,args.resume)

if __name__=="__main__":
    try:main()
    except Exception as error:
        print(json.dumps({"status":"STOPPED","error_type":type(error).__name__,"detail":str(error) if isinstance(error,(MonetaryStop,BudgetIntegrityError,FileExistsError)) else "Inspect retained local evidence; arbitrary error text suppressed"},ensure_ascii=False),flush=True)
        raise SystemExit(1)
