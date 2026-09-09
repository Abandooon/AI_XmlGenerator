from pathlib import Path
import json,hashlib,collections
O=Path(OUTPUT);R=Path(PAYLOAD)/'frozen/release'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()
def ident(x):return sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
events=[json.loads(l) for l in (R/'paid_formal/QUEUE.jsonl').read_text().splitlines()];plan=read(R/'EXECUTION_PLAN.json');errors=[];prev='0'*64
for i,e in enumerate(events,1):
 if e['sequence']!=i or e['previous_hash']!=prev or ident({k:v for k,v in e.items() if k!='entry_hash'})!=e['entry_hash']:errors.append(f'chain:{i}')
 prev=e['entry_hash']
 if e['index']!=(i-1)//2 or e['event_type']!=('BEGIN' if i%2 else 'COMPLETE'):errors.append(f'queue_order:{i}')
 if i%2:
  if e['action_sha256']!=ident(plan['actions'][e['index']]):errors.append(f'plan_action:{i}')
 else:
  if sha((R/'paid_formal'/e['receipt']).read_bytes())!=e['receipt_sha256']:errors.append(f'receipt_hash:{i}')
out={'events':len(events),'BEGIN':sum(e['event_type']=='BEGIN' for e in events),'COMPLETE':sum(e['event_type']=='COMPLETE' for e in events),'planned_actions':len(plan['actions']),'ordered_execution_matches_plan':not errors,'errors':errors};(O/'train_queue_audit.json').write_text(json.dumps(out,indent=2),'utf-8');print(out)

if errors:raise AssertionError(errors)
