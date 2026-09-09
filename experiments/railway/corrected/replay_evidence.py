"""Portable replay of preserved evidence; no provider calls."""
from pathlib import Path
import json,hashlib,base64,sys,copy,collections,concurrent.futures,subprocess,zipfile,time
from raw_native_score import run_native,score_native_receipt
W=Path(PAYLOAD)/'frozen/workspace'
R=Path(PAYLOAD)/'frozen/release'
O=Path(OUTPUT);N=O/'native';N.mkdir(exist_ok=True)
sys.path.insert(0,str(W));sys.dont_write_bytecode=True
from railway.materialize import from_xmi
from railway_method_v5.task_compiler import compile_task,assign
from railway_method_v5.typed_patch import apply_patch
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()
def ident(d):return sha(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
errors=[];counts=collections.Counter();rows=[];unique={}; rawids=set();response_models=collections.Counter();usages=collections.Counter()
def ck(ok,typ,detail):
 if not ok:errors.append({'type':typ,'detail':str(detail)})
def oracle(e):
 out={q:set() for q in ['PosLength','SwitchMonitored','SwitchSet','RouteSensor','ConnectedSegments','SemaphoreNeighbor']}
 tracks={t['id']:t for t in e['segments']+e['switches']};sensors={s['id']:set(s['monitors']) for s in e['sensors']};pos={p['id']:p for p in e['switch_positions']};sw={s['id']:s for s in e['switches']};sem={s['id']:s for s in e['semaphores']}
 for s in e['segments']:
  if s['length']<=0:out['PosLength'].add((s['id'],))
 for s in e['switches']:
  if not any(s['id'] in ts for ts in sensors.values()):out['SwitchMonitored'].add((s['id'],))
 for r in e['routes']:
  for pid in r['follows']:
   p=pos[pid];s=sw[p['target']]
   if r['active'] and sem[r['entry']]['signal']=='GO' and p['position']!=s['current_position']:out['SwitchSet'].add((r['entry'],r['id'],pid,s['id']))
   for sid,ts in sensors.items():
    if s['id'] in ts and sid not in r['requires']:out['RouteSensor'].add((r['id'],sid,pid,s['id']))
 segids={s['id'] for s in e['segments']}
 for sid,ts in sensors.items():
  allowed=ts & segids
  def walk(path):
   if len(path)==6:out['ConnectedSegments'].add((sid,*path));return
   for nxt in tracks[path[-1]]['connects_to']:
    if nxt in allowed:walk(path+[nxt])
  for start in allowed:walk([start])
 for r in e['routes']:
  for q in e['routes']:
   if r['id']==q['id'] or r['exit']==q['entry']:continue
   for a in r['requires']:
    for b in q['requires']:
     for t in sensors[a]:
      for target in tracks[t]['connects_to']:
       if target in sensors[b]:out['SemaphoreNeighbor'].add((r['exit'],r['id'],q['id'],a,b,t,target))
 return {k:sorted('|'.join(t) for t in v) for k,v in out.items()}
plan=read(R/'EXECUTION_PLAN.json');paired={r['unit_id']:r for s in ['G','R','T','CLEAN'] for r in read(R/f'formal_export/paired/{s}.json')['records']}
ck(len(paired)==len(plan['units'])==891,'denominator',len(paired))
ck(len(plan['actions'])==747,'actions',len(plan['actions']))

# Validate each original XMI/identity byte pair once, before any Python projection.
native_jobs={}
for u in plan['units']:
 d=R/'paid_formal'/u['directory'];a=d/('artifact' if u['arm']=='G0' else 'final_artifact')
 if a.exists():
  key=sha((a/'model.xmi').read_bytes())+'_'+sha((a/'identity.json').read_bytes())
  native_jobs.setdefault(key,a)
def run_one(item):
 key,a=item
 return key,run_native(a/'model.xmi',a/'identity.json',N/(key+'.json'),JAVA,Path(PAYLOAD)/'native/lib')
native_receipts={}
with concurrent.futures.ThreadPoolExecutor(max_workers=JOBS) as pool:
 for key,receipt in pool.map(run_one,native_jobs.items()):
  native_receipts[key]=receipt
  if len(native_receipts)%25==0:print('Original XMI verified:',len(native_receipts),'/',len(native_jobs),flush=True)
ck(len(native_receipts)==139,'native_unique_count',len(native_receipts))

manifest=read(R/'paid_formal/RUN_MANIFEST.json')
for rel,h in manifest.items():
 p=R/'paid_formal'/rel;ck(p.is_file() and sha(p.read_bytes())==h,'raw_manifest',rel)
counts['raw_manifest_files']=len(manifest)
with zipfile.ZipFile(R/'SOURCE.zip') as z:
 for name in z.namelist():
  if name.endswith('/'):continue
  p=W/name;ck(p.is_file() and sha(p.read_bytes())==sha(z.read(name)),'source_zip',name);counts['source_zip_files']+=1
for u in plan['units']:
 d=R/'paid_formal'/u['directory'];rec=paired[u['unit_id']];run=read(d/'result.json');pub=read(d/'task_spec.json');task=compile_task(pub)
 run_prefix=u['directory']+'/'
 run_manifest={name[len(run_prefix):]:h for name,h in manifest.items() if name.startswith(run_prefix)}
 ck(pub==read(W/u['task_file']),'task_changed',u['unit_id']);ck(task.contract_hash==u['contract_sha256'],'contract_hash',u['unit_id']);ck(ident(run_manifest)==rec['run_sha256'],'run_hash',u['unit_id'])
 art=d/('artifact' if u['arm']=='G0' else 'final_artifact');initial=run.get('model') if u['arm']=='G0' else run.get('final_model')
 ck(run.get('mode')=='LIVE_FORMAL_RAILWAY_V5','nonformal_mode',u['unit_id'])
 if art.exists():
  xmi=(art/'model.xmi').read_text('utf-8');mapping=read(art/'identity.json');model=from_xmi(xmi,mapping['identity_mapping']);sc=rec['independent_score'];native=native_receipts[sha((art/'model.xmi').read_bytes())+'_'+sha((art/'identity.json').read_bytes())]
  ck(model==read(art/'model.json')==initial==native['eobject_projection'],'model_projection',u['unit_id']);ck(sha(xmi.encode())==sc['artifact_sha256'],'artifact_hash',u['unit_id']);ck(ident(model)==rec['final_model_sha256'],'final_hash',u['unit_id'])
  queries=oracle(model['elements']);ck(queries==sc['independent_query_matches']=={q:sorted('|'.join(v) for v in vv) for q,vv in native['query_tuples'].items()},'query_recompute',u['unit_id'])
  idx={c:{r['id']:r for r in rs} for c,rs in model['elements'].items()};taskpass=True
  for ob in pub['obligations']:
   c,k,f=ob['path'];v=idx[c][k][f];expected=ob['expected'];ok=type(v)==type(expected) and v==expected if ob['operator']=='equals' else isinstance(v,list) and set(expected)<=set(v)
   taskpass &=ok
  mutable={tuple(s['path']) for s in pub['semantic_slots'] if s['generate'] or s['repair']};derived={('segments','monitored_by'),('switches','monitored_by'),('switch_positions','route'),('switch_positions','target')};frame=True
  for c,rs in task.structural_plan['elements'].items():
   frame &= [r['id'] for r in rs]==[r['id'] for r in model['elements'][c]]
   for r in rs:
    for f,v in r.items():
     if (c,r['id'],f) not in mutable and (c,f) not in derived:frame &=idx[c][r['id']][f]==v
  valid=bool(native['loaded'] and native['root_valid'] and native['all_native_checks_executed'] and native['identity_checks']['pass'] and native['diagnostician']['severity']==0 and not native['resource_errors'] and not native['resource_warnings'] and not native['unresolved_proxies'] and not any(queries.values()) and taskpass and frame)
  revised=score_native_receipt(native,pub);ck(revised['strict_success']==valid,'corrected_score',u['unit_id']);ck(valid==rec['outcome']==sc['strict_success'],'strict_recompute',u['unit_id']);key=sha((art/'model.xmi').read_bytes())+'_'+sha((art/'identity.json').read_bytes());unique.setdefault(key,{'artifact':art,'model':model,'queries':queries,'units':[]})['units'].append(u['unit_id'])
 else:valid=False;counts['no_artifact']+=1;ck(rec['outcome'] is False and run.get('status') in ['ASSIGNMENT_REJECTED','NOT_RUN_SHARED_ASSIGNMENT_REJECTED'],'missing_artifact',u['unit_id'])
 counts[f'{u["stage"]}/{u["arm"]}/total']+=1;counts[f'{u["stage"]}/{u["arm"]}/pass']+=int(valid)
 rows.append({'unit_id':u['unit_id'],'stage':u['stage'],'arm':u['arm'],'directory':u['directory'],'valid':valid})
 # Replay actual preserved response through generation/editor; no provider or validator.
 if u['arm']=='G0':
  res=read(d/'shared_initial/response.json')
  try: regen,_=assign(task,json.loads(res['text']));ck(regen==run['model'],'assignment_replay',u['unit_id']);counts['generation_replayed']+=1
  except Exception as ex:ck(run.get('status')=='ASSIGNMENT_REJECTED','assignment_exception',f'{u["unit_id"]}:{ex}');counts['generation_rejected']+=1
 elif (d/'initial.model.json').exists():
  current=read(d/'initial.model.json')
  if u['stage']!='G':ck(ident(current)==u['initial']['sha256'],'initial_mismatch',u['unit_id'])
  else:
   g0=read(d.parent/'shared_generation/result.json');ck(current==g0['model'],'shared_g0_mismatch',u['unit_id'])
  for a in run['attempts']:
   rd=d/f'round_{a["round"]:02d}';rsp=read(rd/'response.json');rp=read(rd/'plan.json')
   try:
    proposal=json.loads(rsp['text']);candidate,edit=apply_patch(current,proposal,rp,run['arm'])
    if (rd/'candidate.model.json').exists():ck(candidate==read(rd/'candidate.model.json'),'patch_replay',u['unit_id']);counts['patch_replayed']+=1
    if a['selected']:current=candidate
   except Exception as ex:ck(a['status'] in ['CONTRACT_REJECTED','PARSE_REJECTED'],'patch_exception',f'{u["unit_id"]}:{ex}')
  ck(current==run['final_model'],'final_selection',u['unit_id'])
for p in (R/'paid_formal/units').rglob('transport_evidence.json'):
 ev=read(p);counts['transport_evidence']+=1;blobs={h:base64.b64decode(b) for h,b in ev['blobs_base64'].items()}
 for h,b in blobs.items():ck(sha(b)==h,'blob_hash',p)
 rsp=read(p.parent/'response.json');req=read(p.parent/'request.json');h=rsp['raw_sha256'];raw=json.loads(blobs[h]);ck(raw['choices'][0]['message'].get('content')==rsp['text'],'wire_response_content',p);ck(raw['usage']==rsp['usage'],'wire_usage',p);ck(raw['id']==rsp['response_id'],'wire_response_id',p)
 ck(sha((p.parent/'request.json').read_bytes())==rsp['request_sha256'],'request_hash',p);ck(ident(req['wire_body'])==req['wire_sha256'],'wire_body_hash',p);ck(ev['mode']==rsp['mode']=='LIVE_FORMAL_RAILWAY_V5','response_mode',p)
 ck(h not in rawids,'duplicate_response',p);rawids.add(h);response_models[rsp['response_model']]+=1
 for k in ['prompt_tokens','completion_tokens','total_tokens']:usages[k]+=rsp['usage'][k]
 if (p.parent/'proposal.json').exists():ck(json.loads(rsp['text'])==read(p.parent/'proposal.json'),'response_proposal',p)
 event_received=[e for e in ev['events'] if e['event_type']=='RECEIVED'];ck(len(event_received)==1 and event_received[0]['receipt']==rsp,'received_count',p)
counts['unique_artifact_and_identity']=len(unique)
counts['artifact_endpoints']=sum(len(v['units']) for v in unique.values())
ck(counts['artifact_endpoints']==888,'artifact_count',counts['artifact_endpoints'])
ck(len(rawids)==1074,'response_count',len(rawids))
result={'counts':dict(counts),'responses':len(rawids),'response_models':dict(response_models),'usage':dict(usages),'errors':errors,'rows':rows}
(O/'train_recomputed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8');print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2),flush=True)
# Regression: undefined prefix in xsi:type must be rejected by actual EMF.
example=next(u for u in plan['units'] if u['arm']=='F' and paired[u['unit_id']]['outcome'])
directory=R/'paid_formal'/example['directory'];art=directory/'final_artifact'
original=(art/'model.xmi').read_bytes()
malformed=original.replace(b'xmlns:railway=',b'xmlns:q=').replace(b'<railway:RailwayContainer',b'<q:RailwayContainer').replace(b'</railway:RailwayContainer',b'</q:RailwayContainer')
bad=O/'malformed_namespace.xmi';bad.write_bytes(malformed)
bad_receipt=run_native(bad,art/'identity.json',O/'malformed_namespace_native.json',JAVA,Path(PAYLOAD)/'native/lib')
bad_score=score_native_receipt(bad_receipt,read(directory/'task_spec.json'))
regression={'source_unit':example['unit_id'],'mutation':'Rename declared/root prefix to q while leaving xsi:type railway:Segment/Switch with undefined railway prefix.','native_loaded':bad_receipt.get('loaded'),'strict_success':bad_score['strict_success'],'original_source_unchanged':(art/'model.xmi').read_bytes()==original,'pass':not bad_receipt.get('loaded') and not bad_score['strict_success']}
ck(regression['pass'] and regression['original_source_unchanged'],'namespace_regression',regression)
(O/'namespace_regression.json').write_text(json.dumps(regression,indent=2),'utf-8')
result['errors']=errors
(O/'train_recomputed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print('Corrected raw-input scores:',len(rows),'endpoints; differences:',len(errors),'; namespace regression:',regression['pass'],flush=True)
if errors:raise AssertionError('Offline replay found '+str(len(errors))+' discrepancies')
