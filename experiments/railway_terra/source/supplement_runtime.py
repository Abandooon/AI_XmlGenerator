"""Single-attempt provider with durable pre-dispatch monetary reservations.

All amounts in the admission ledger are integer nano-USD. No credential or
authorization header is written. Real and offline-replay evidence have distinct modes.
"""
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
import hashlib, json, os, re, urllib.request, urllib.error

HERE=Path(__file__).resolve().parent
REAL="TERRA_AUTHORIZED_SUPPLEMENT"
REPLAY="SUPPLEMENT_OFFLINE_LUNA_REPLAY"

def canonical(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def sha_bytes(value): return hashlib.sha256(value).hexdigest()
def identity(value): return sha_bytes(canonical(value).encode("utf-8"))
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def usd(nano): return format(nano/1_000_000_000,".9f")
def now(): return datetime.now(timezone.utc).isoformat()

class MonetaryStop(RuntimeError): pass
class BudgetIntegrityError(RuntimeError): pass

class Budget:
    CAP=5_000_000_000
    INPUT_CAP=272000
    OUTPUT_CAP=4096
    RESERVATION=INPUT_CAP*3750+OUTPUT_CAP*18000
    MAX_BODY_BYTES=120000
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.events=[]; self.entries={}; self.denials=[]
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                event=json.loads(line); h=event.pop("hash")
                if h!=identity(event) or event["previous"]!=(self.events[-1]["hash"] if self.events else "0"*64):
                    raise BudgetIntegrityError("Budget hash chain mismatch")
                event["hash"]=h; self.events.append(event); self._apply(event)
    def _apply(self,event):
        key=event["key"]; kind=event["kind"]
        if kind=="RESERVE":
            if key in self.entries: raise BudgetIntegrityError("Duplicate request reservation")
            self.entries[key]={"state":"RESERVED","reserved_nano":event["reserved_nano"],"occupied_nano":event["reserved_nano"]}
        elif kind in {"SETTLE","UNKNOWN","VIOLATION"}:
            if key not in self.entries or self.entries[key]["state"]!="RESERVED": raise BudgetIntegrityError("Settlement without one open reservation")
            self.entries[key].update(state=kind,occupied_nano=event["occupied_nano"],usage=event.get("usage"),estimated_base_nano=event.get("estimated_base_nano"),cache_estimate=event.get("cache_estimate"))
        elif kind=="DENY": self.denials.append(event)
        else: raise BudgetIntegrityError("Unknown monetary event")
    def _append(self,kind,key,**fields):
        event={"sequence":len(self.events)+1,"utc":now(),"kind":kind,"key":key,
               "previous":self.events[-1]["hash"] if self.events else "0"*64,**fields}
        event["hash"]=identity(event)
        with self.path.open("a",encoding="utf-8",newline="") as stream:
            stream.write(canonical(event)+"\n"); stream.flush(); os.fsync(stream.fileno())
        self.events.append(event); self._apply(event)
    @property
    def occupied(self): return sum(r["occupied_nano"] for r in self.entries.values())
    @property
    def unresolved(self): return [k for k,v in self.entries.items() if v["state"] in {"RESERVED","UNKNOWN","VIOLATION"}]
    def reserve(self,key,wire):
        body=canonical(wire).encode("utf-8")
        if key in self.entries: raise MonetaryStop("Existing monetary opportunity cannot be redispatched")
        if self.unresolved: raise MonetaryStop("Unresolved monetary opportunity; no additional network request")
        if len(self.entries)>=120: raise MonetaryStop("Prespecified logical request ceiling reached")
        if wire.get("max_completion_tokens")!=self.OUTPUT_CAP or wire.get("model")!="gpt-5.6-terra" or wire.get("reasoning_effort")!="low" or wire.get("seed")!=104729:
            raise BudgetIntegrityError("Prespecified model/seed/output cap changed")
        if len(body)>self.MAX_BODY_BYTES:
            self._append("DENY",key,reason="SERIALIZED_REQUEST_TOO_LARGE",bytes=len(body),network_dispatched=False)
            raise MonetaryStop("Serialized request exceeds prespecified conservative input guard")
        if self.occupied+self.RESERVATION>self.CAP:
            self._append("DENY",key,reason="INSUFFICIENT_PRE_DISPATCH_RESERVATION",occupied_nano=self.occupied,required_nano=self.RESERVATION,network_dispatched=False)
            raise MonetaryStop("USD 5 pre-dispatch reservation denied")
        self._append("RESERVE",key,reserved_nano=self.RESERVATION,wire_sha256=identity(wire),serialized_bytes=len(body),
                     input_tokens_reserved=self.INPUT_CAP,output_tokens_reserved=self.OUTPUT_CAP,
                     cap_nano=self.CAP,occupied_after_nano=self.occupied+self.RESERVATION)
        return body
    def settle(self,key,usage):
        if not isinstance(usage,dict) or any(type(usage.get(k)) is not int or usage[k]<0 for k in ("prompt_tokens","completion_tokens")):
            self.unknown(key,"MISSING_OR_INVALID_USAGE")
            return False
        inp,out=usage["prompt_tokens"],usage["completion_tokens"]
        occupied=inp*3750+out*18000
        violated=inp>self.INPUT_CAP or out>self.OUTPUT_CAP or occupied>self.entries[key]["reserved_nano"]
        cache=cache_cost(usage)
        self._append("VIOLATION" if violated else "SETTLE",key,occupied_nano=occupied,usage=usage,
                     estimated_base_nano=inp*3000+out*18000,cache_estimate=cache,
                     reported_input_exceeds_reserved=inp>self.INPUT_CAP,reported_output_exceeds_limit=out>self.OUTPUT_CAP,
                     scope="Conservative budget occupancy, not a provider invoice")
        return not violated
    def unknown(self,key,reason):
        self._append("UNKNOWN",key,occupied_nano=self.entries[key]["reserved_nano"],usage=None,reason=reason)
    def summary(self):
        known=[v for v in self.entries.values() if v.get("usage") is not None]
        cache_known=[v for v in known if (v.get("cache_estimate") or {}).get("nano_usd") is not None]
        return {"cap_usd":usd(self.CAP),"occupied_upper_usd":usd(self.occupied),
                "remaining_unoccupied_usd":usd(self.CAP-self.occupied),"next_request_reservation_usd":usd(self.RESERVATION),
                "known_base_price_estimate_usd":usd(sum(v["estimated_base_nano"] for v in known)),
                "cache_component_estimate_usd":usd(sum(v["cache_estimate"]["nano_usd"] for v in cache_known)),
                "cache_component_estimate_responses":len(cache_known),"cache_components_unknown_responses":len(known)-len(cache_known),
                "known_prompt_tokens":sum(v["usage"]["prompt_tokens"] for v in known),
                "known_completion_tokens":sum(v["usage"]["completion_tokens"] for v in known),
                "reserved_requests":len(self.entries),"unresolved":self.unresolved,"denials":len(self.denials),
                "within_client_ceiling":self.occupied<=self.CAP,"not_a_provider_invoice":True}

def cache_cost(usage):
    details=usage.get("prompt_tokens_details") or {}
    reads=details.get("cached_tokens")
    writes=details.get("cache_write_tokens",details.get("cache_creation_input_tokens"))
    if type(reads) is not int or type(writes) is not int or reads<0 or writes<0 or reads+writes>usage["prompt_tokens"]:
        return {"status":"CACHE_COMPONENTS_UNAVAILABLE_OR_AMBIGUOUS","usd":None}
    normal=usage["prompt_tokens"]-reads-writes
    cost=normal*3000+reads*300+writes*3750+usage["completion_tokens"]*18000
    return {"status":"DISJOINT_COMPONENT_ESTIMATE","ordinary_input_tokens":normal,"cache_read_tokens":reads,
            "cache_write_tokens":writes,"nano_usd":cost,"usd":usd(cost),"assumption":"Read/write counts are disjoint subsets of prompt_tokens; not independently authenticated billing"}

def ledger_accounting(ledger,provider=None):
    receipts=[read(p) for p in ledger.directory.glob("*/response.json")]
    known=[r["usage"] for r in receipts if isinstance(r.get("usage"),dict)]
    return {"new_model_calls":getattr(provider,"new_model_calls",0),"transport_accounting":{
        "mode":ledger.read("binding.json")["mode"],"received_logical_responses":len(receipts),
        "unknown_usage_responses":sum(r.get("usage") is None for r in receipts),
        "known_usage_sums":{k:sum(u.get(k,0) for u in known) for k in ("prompt_tokens","completion_tokens","total_tokens")},
        "all_logical_responses_received":not bool(list(ledger.directory.glob("*/unknown.json"))),
        "new_http_attempts_this_provider":getattr(provider,"new_http_attempts",0)}}

def safe_raw(raw,secret):
    original=sha_bytes(raw); needle=secret.encode("utf-8") if secret else b""
    changed=bool(needle and needle in raw)
    stored=raw.replace(needle,b"<REDACTED_CREDENTIAL>") if changed else raw
    return stored,{"received_raw_sha256":original,"stored_raw_sha256":sha_bytes(stored),"credential_redaction_required":changed}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

class SupplementProvider:
    mode=REAL
    def __init__(self,budget,endpoint,credential,task_id,arm):
        self.budget,self.endpoint,self.credential=budget,endpoint,credential
        self.task_id,self.arm=task_id,arm
        self.calls=self.new_model_calls=self.new_http_attempts=0
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    def obtain_in_ledger(self,ledger,key,request):
        from railway_method_v5.collection import UnknownResponse
        ledger.save(f"{key}/request.json",request)
        response_path=f"{key}/response.json"; logical=f"{self.task_id}/{self.arm}/{key}"
        if ledger.path(response_path).exists():
            response=ledger.read(response_path)
            if response.get("request_sha256")!=identity(request): raise BudgetIntegrityError("Saved receipt/request mismatch")
            if logical not in self.budget.entries or self.budget.entries[logical]["state"]!="SETTLE":
                raise MonetaryStop("Saved response has unresolved budget; review required")
            return response
        if ledger.path(f"{key}/intent.json").exists(): raise MonetaryStop("Existing dispatch intent cannot be replayed over network")
        body=self.budget.reserve(logical,request["wire_body"])
        ledger.save(f"{key}/intent.json",{"mode":self.mode,"logical_key":logical,"request_sha256":identity(request),
            "wire_sha256":sha_bytes(body),"reservation_nano_usd":Budget.RESERVATION,"utc":now(),"automatic_retries":0})
        ledger.path(f"{key}/http_request_body.json").write_bytes(body)
        import time
        started=time.perf_counter(); self.calls+=1; self.new_model_calls+=1; self.new_http_attempts+=1
        raw=None; status=None; headers={}
        try:
            req=urllib.request.Request(self.endpoint,data=body,headers={"Authorization":"Bearer "+self.credential,"Content-Type":"application/json"},method="POST")
            with self.opener.open(req,timeout=180) as stream:
                status=stream.status; raw=stream.read()
                headers={k:v for k,v in stream.headers.items() if k.lower() in {"content-type","date","x-request-id","request-id"}}
        except urllib.error.HTTPError as error:
            status=error.code; raw=error.read()
        except Exception as error:
            self.budget.unknown(logical,"TRANSPORT_"+type(error).__name__)
            ledger.save(f"{key}/unknown.json",{"response_status":"UNKNOWN","usage":None,"error_type":type(error).__name__,"no_automatic_retry":True})
            raise UnknownResponse("Unknown transport; full reserved budget retained and batch stopped") from None
        elapsed=time.perf_counter()-started
        stored,binding=safe_raw(raw,self.credential)
        ledger.path(f"{key}/http_response_body.json").write_bytes(stored)
        ledger.save(f"{key}/http_response_metadata.json",{"status":status,"headers":headers,"elapsed_seconds":elapsed,**binding})
        try: parsed=json.loads(raw)
        except Exception: parsed={}
        usage=parsed.get("usage")
        accepted_usage=self.budget.settle(logical,usage)
        choices=parsed.get("choices") or []
        choice=choices[0] if choices else {}; message=choice.get("message") or {}
        text=message.get("content") if isinstance(message.get("content"),str) else ""
        finish=choice.get("finish_reason")
        refusal=message.get("refusal")
        kind="HTTP_ERROR" if status!=200 else "TRUNCATED" if finish=="length" else "REFUSAL" if refusal else "CONTENT" if text and finish=="stop" else "INVALID_RESPONSE"
        response_model=parsed.get("model")
        receipt={"kind":kind,"text":text,"usage":usage,"response_status":"RECEIVED","mode":self.mode,
                 "request_sha256":identity(request),"response_model":response_model,"response_id":parsed.get("id"),
                 "finish_reason":finish,"refusal":refusal,"elapsed_seconds":elapsed,"actual_http_attempts":1,
                 "transport_intents":1,"semantic_retry_allowed":False,"raw_binding":binding,
                 "max_completion_tokens":4096,"output_truncated":finish=="length",
                 "request_input_within_reserved_tier":isinstance(usage,dict) and usage.get("prompt_tokens",272001)<=272000,
                 "response_model_matches_requested_family":isinstance(response_model,str) and (response_model=="gpt-5.6-terra" or response_model.startswith("gpt-5.6-terra-"))}
        # Credential redaction also applies to structured copies of untrusted provider text.
        receipt=json.loads(canonical(receipt).replace(self.credential,"<REDACTED_CREDENTIAL>"))
        ledger.save(response_path,receipt)
        if not accepted_usage:
            ledger.save(f"{key}/unknown.json",{"response_status":"USAGE_UNKNOWN_OR_EXCEEDS_RESERVATION","usage":usage,"no_automatic_retry":True})
            raise UnknownResponse("Unknown or over-limit usage; budget retained and batch stopped")
        if status!=200 or not receipt["response_model_matches_requested_family"]:
            raise MonetaryStop("Provider error or model identity mismatch; preserve received evidence and stop")
        return receipt

class LunaReplayProvider:
    mode=REPLAY
    def __init__(self,source):
        self.source=Path(source); self.calls=self.new_model_calls=self.new_http_attempts=0
    def obtain_in_ledger(self,ledger,key,request):
        old=read(self.source/key/"request.json")
        wire=deepcopy(request["wire_body"]); prior=deepcopy(old["wire_body"])
        for field in ("model","max_completion_tokens"): wire.pop(field); prior.pop(field)
        if wire!=prior or request["policy"]!=old["policy"] or request["contract_sha256"]!=old["contract_sha256"]:
            raise BudgetIntegrityError("Offline replay changed task/schema/prompt/state beyond declared model/output-cap differences")
        response=read(self.source/key/"response.json")
        if response["usage"]["completion_tokens"]>4096: raise BudgetIntegrityError("Historical response exceeds supplement completion cap")
        ledger.save(f"{key}/request.json",request)
        ledger.save(f"{key}/historical_request.json",old)
        ledger.save(f"{key}/intent.json",{"mode":self.mode,"network_calls":0,"source":str(self.source/key),"request_sha256":identity(request)})
        response={**response,"mode":self.mode,"request_sha256":identity(request),"historical_response_only":True}
        ledger.save(f"{key}/response.json",response)
        self.calls+=1
        return response

def scalar(path,name,separator):
    if not Path(path).exists(): return ""
    found=[]
    pattern=re.compile(r"^\s*"+re.escape(name)+r"\s*"+re.escape(separator)+r"\s*(.*?)\s*$")
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        match=pattern.match(line)
        if not match: continue
        value=match.group(1)
        if value.startswith('"'):
            value,end=json.JSONDecoder().raw_decode(value)
        elif value.startswith("'"): value=value[1:value.index("'",1)]
        else: value=value.split(" #",1)[0].strip()
        if isinstance(value,str): found.append(value)
    if len(found)>1: raise BudgetIntegrityError("Duplicate configured scalar")
    return found[0] if found else ""

def configuration(read_secret=False):
    config=Path(r"E:\git projects\AI_XmlGenerator\config\llm_api_config.yaml")
    dotenv=Path(r"E:\git projects\AI_XmlGenerator\.env")
    base=scalar(config,"llm_api_url",":").strip().rstrip("/")
    if not base.startswith("https://"): raise BudgetIntegrityError("HTTPS endpoint required")
    if not base.endswith("/v1"): base+="/v1"
    endpoint=base+"/chat/completions"
    if not read_secret: return {"endpoint_sha256":sha_bytes(endpoint.encode()),"configuration_path":str(config),"credential_read":False}
    expected=read(HERE/"PREPARATION_REPORT.json")["configuration"]["endpoint_sha256"]
    if sha_bytes(endpoint.encode())!=expected: raise BudgetIntegrityError("Endpoint changed after reviewed preparation")
    choices=[os.environ.get("API_KEY"),scalar(config,"api_key",":"),scalar(dotenv,"API_KEY","=")]
    secret=next((s for s in choices if isinstance(s,str) and s and "${" not in s and not any(c.isspace() for c in s)),None)
    if secret is None: raise BudgetIntegrityError("No usable existing credential")
    return endpoint,secret
