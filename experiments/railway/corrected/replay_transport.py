from pathlib import Path
import json,collections,hashlib
ROOT=Path(PAYLOAD)/'frozen/lineage';R=Path(PAYLOAD)/'frozen/release';O=Path(OUTPUT)
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()
def ident(x):return sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
errors=[]
def journal(p):
 es=[json.loads(l) for l in p.read_text().splitlines() if l];prev='0'*64
 for i,e in enumerate(es,1):
  if e['sequence']!=i or e['previous_hash']!=prev or ident({k:v for k,v in e.items() if k!='entry_hash'})!=e['entry_hash']:errors.append(str(p)+':chain')
  prev=e['entry_hash']
 return es
old={};jcounts={};oldresponses={}
for name in ['20260908T182751363462Z','20260909_26f3c9b0_recovery_once']:
 events=[e for p in (ROOT/name/'paid_formal/transport').glob('*/TRANSPORT.jsonl') for e in journal(p)]
 jcounts[name]=dict(collections.Counter(e['event_type'] for e in events))
 for e in events:
  if e['event_type']=='INTENT':old[e['entry_hash']]=e
  if e['event_type']=='RECEIVED':oldresponses[e['key']]=e['receipt']['raw_sha256']
events=journal(R/'automatic_operation/PHYSICAL_TRANSPORT.jsonl');types=collections.Counter(e['event_type'] for e in events);wires=collections.defaultdict(set);responses={}
for e in events:
 if e['event_type']=='PHYSICAL_INTENT':
  wires[e['key']].add(e['wire_sha256']);b=(R/'automatic_operation/blobs'/e['wire']['relative_path']).read_bytes()
  if sha(b)!=e['wire_sha256']:errors.append(e['key']+':wire_hash')
 if e['event_type']=='PHYSICAL_HTTP':
  if e['key'] in responses:errors.append(e['key']+':received_resample')
  h=e['retained_success'];b=(R/'automatic_operation/blobs'/h['relative_path']).read_bytes()
  if sha(b)!=h['sha256'] or sha(b)!=e['original_body_sha256']:errors.append(e['key']+':http_hash')
  responses[e['key']]=h['sha256']
if set(oldresponses)&set(responses):errors.append('Inherited received key resent')
if any(len(v)!=1 for v in wires.values()):errors.append('Retry wire differed')
pr=read(R/'AUTO_TRANSPORT_PROJECTION.json');m=read(R/'paid_formal/RUN_MANIFEST.json')
for path,h in pr['inherited_files'].items():
 if m[path]!=h:errors.append(path+':inherited_changed')
fvpairs=collections.defaultdict(dict)
for r in read(R/'formal_export/paired/R.json')['records']:
 k,arm=r['unit_id'].rsplit(':',1);fvpairs[k][arm]=r['outcome']
res={'prior_journals':jcounts,'deduplicated_prior_intents':len(old),'prior_received_unique':len(oldresponses),'new_physical_journal':dict(types),'physical_intents_cross_lineage':len(old)+types['PHYSICAL_INTENT'],'responses_cross_lineage':len(oldresponses)+len(responses),'unknown_attempts':len(old)-len(oldresponses)+types['TRANSPORT_EXCEPTION'],'wire_identical_for_retries':all(len(v)==1 for v in wires.values()),'inherited_received_resent':len(set(oldresponses)&set(responses)),'inherited_files_verified_against_checked_manifest':len(pr['inherited_files']),'unknown_usage':None,'billing_complete':False,'F_V_144_pairs':dict(collections.Counter(str((p['F'],p['V'])) for p in fvpairs.values())),'errors':errors}
(O/'train_transport_audit.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),'utf-8');print(json.dumps(res,ensure_ascii=False,indent=2))

assert res["physical_intents_cross_lineage"]==1085 and res["responses_cross_lineage"]==1074 and res["unknown_attempts"]==11
if errors:raise AssertionError(errors)
