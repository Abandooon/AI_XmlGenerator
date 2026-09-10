from pathlib import Path
import json,random,statistics,collections,math
O=Path(OUTPUT);R=Path(PAYLOAD)/'frozen/release'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
plan=read(R/'EXECUTION_PLAN.json');out={};paper=read(R/'formal_export/PAPER_RESULTS.json');errors=[]
for stage,contrasts in [('G',[('GF','G0'),('GF','GS')]),('R',[('F','S'),('F','V')])]:
 rows=read(R/f'formal_export/paired/{stage}.json')['records'];cells=collections.defaultdict(lambda:collections.defaultdict(list))
 for r in rows:
  tok=r['unit_id'].split(':');cells[tok[1]][tok[-1]].append(int(r['outcome']))
 cases={b:{a:statistics.fmean(v) for a,v in ar.items()} for b,ar in cells.items()};names=sorted(cases);rng=random.Random(8675309);distributions={a+'-'+b:[] for a,b in contrasts}
 for _ in range(9999):
  sample=[rng.choice(names) for _ in names]
  for a,b in contrasts:distributions[a+'-'+b].append(statistics.fmean(cases[n][a]-cases[n][b] for n in sample))
 result={}
 for a,b in contrasts:
  dist=sorted(distributions[a+'-'+b]);bounds=[]
  for p in [.00625,.99375]:
   x=p*(len(dist)-1);i=math.floor(x);bounds.append(dist[i]+(x-i)*(dist[min(i+1,len(dist)-1)]-dist[i]))
  est=statistics.fmean(cases[n][a]-cases[n][b] for n in names);reported=paper['main_and_strata'][stage]['main']['resampling']['base']['contrasts'][a+'-'+b]
  good=abs(est-reported['estimate'])<1e-12 and all(abs(x-y)<1e-12 for x,y in zip(bounds,reported['interval']))
  if not good:errors.append(stage+':'+a+'-'+b)
  result[a+'-'+b]={'estimate':est,'interval':bounds,'matches_report':good}
 out[stage]=result
units={u['unit_key']:u for u in plan['units']};orders=collections.defaultdict(list)
for action in plan['actions']:
 for k in action['unit_keys']:
  u=units[k]
  if u['stage']=='R':orders[u['unit_id'].rsplit(':',1)[0]].append(u['arm'])
out['R_planned_arm_orders']=dict(collections.Counter(''.join(o) for o in orders.values()));out['errors']=errors
(O/'train_statistics_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))

if errors:raise AssertionError(errors)
