"""Erratum1: validate the supplied XMI bytes, never a reserialization.

No provider, XML serializer, or model-generation module is imported here.
The native EObject projection is used only after original-input validation.
"""
from pathlib import Path
from copy import deepcopy
import hashlib,json,os,subprocess

def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def run_native(xmi_path, identity_path, output_path, java, library):
    xmi_path,identity_path,output_path=map(lambda p:Path(p).resolve(),(xmi_path,identity_path,output_path))
    if output_path.exists() or output_path in (xmi_path,identity_path):
        raise ValueError('Native output must be a new file distinct from both inputs')
    before={'xmi_sha256':sha_file(xmi_path),'identity_sha256':sha_file(identity_path)}
    output_path.parent.mkdir(parents=True,exist_ok=True)
    command=[str(java),'-Djava.net.useSystemProxies=false','-cp',str(Path(library).resolve()/'*'),
             'org.atlas.railway.NativeVerifier','--input',str(xmi_path),'--identity',str(identity_path),'--out',str(output_path)]
    env=os.environ.copy()
    for key in list(env):
        if key.lower() in {'http_proxy','https_proxy','all_proxy','no_proxy','java_tool_options','_java_options','jdk_java_options'}:env.pop(key)
    completed=subprocess.run(command,env=env,capture_output=True,text=True,timeout=90)
    after={'xmi_sha256':sha_file(xmi_path),'identity_sha256':sha_file(identity_path)}
    if before!=after:raise RuntimeError('Original XMI or identity changed during native validation')
    if not output_path.exists():raise RuntimeError('Native verifier wrote no result; exit='+str(completed.returncode))
    result=json.loads(output_path.read_text('utf-8'))
    result['reviewer_raw_input_binding']={'before':before,'after':after,'unchanged':True,'reserialized':False,'native_exit_code':completed.returncode}
    # The runner's own hash must describe the same source bytes, where present.
    for field in ('input_sha256','input_sha256_before'):
        if field in result and result[field]!=before['xmi_sha256']:raise RuntimeError('Native input hash disagrees')
    output_path.write_text(json.dumps(result,indent=2,ensure_ascii=False),'utf-8')
    return result

def relational_queries(e):
    out={q:set() for q in ['PosLength','SwitchMonitored','SwitchSet','RouteSensor','ConnectedSegments','SemaphoreNeighbor']}
    tracks={t['id']:t for t in e['segments']+e['switches']};sensors={s['id']:set(s['monitors']) for s in e['sensors']}
    pos={p['id']:p for p in e['switch_positions']};sw={s['id']:s for s in e['switches']};sem={s['id']:s for s in e['semaphores']}
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

def score_native_receipt(receipt,public):
    """Score actual native projection. Does not accept a Python input model."""
    result={'strict_success':False,'status':'NATIVE_REJECTED','oracle_agreement':False,'task_results':[],'frame_errors':[]}
    if not (receipt.get('loaded') and receipt.get('all_native_checks_executed') and receipt.get('read_only_input_unchanged')
            and receipt.get('identity_checks',{}).get('pass') and receipt.get('reviewer_raw_input_binding',{}).get('unchanged')):return result
    actual=receipt['eobject_projection']['elements']
    relational=relational_queries(actual)
    tuples={q:sorted('|'.join(map(str,row)) for row in rows) for q,rows in receipt['query_tuples'].items()}
    result.update(status='EVALUATED',oracle_agreement=tuples==relational,independent_query_matches=relational)
    indexes={c:{row['id']:row for row in rows} for c,rows in actual.items()}
    for obligation in public['obligations']:
        c,oid,field=obligation['path'];value=indexes[c][oid][field];wanted=obligation['expected']
        if obligation['operator']=='equals':ok=json.dumps(value,sort_keys=True)==json.dumps(wanted,sort_keys=True)
        elif obligation['operator']=='contains_all':ok=isinstance(value,list) and all(x in value for x in wanted)
        else:raise ValueError('Unsupported obligation operator')
        result['task_results'].append({'id':obligation['id'],'actual':value,'expected':wanted,'pass':ok})
    expected=deepcopy(public['physical_model']['elements']);switches={r['id']:r for r in expected['switches']}
    for service in public['services']:
        expected['routes'].append({'id':service['id'],'active':service['active'],'entry':service['entry'],'exit':service['exit'],'requires':service['requires'],'follows':[p['id'] for p in service['positions']]})
        for pos in service['positions']:
            expected['switch_positions'].append({'id':pos['id'],'position':pos['position'],'target':pos['target'],'route':service['id']})
            switches[pos['target']]['positions'].append(pos['id'])
    mutable={tuple(s['path']) for s in public['semantic_slots'] if s['generate'] or s['repair']}
    derived={('segments','monitored_by'),('switches','monitored_by'),('switch_positions','route'),('switch_positions','target')}
    for c,rows in expected.items():
        if [r['id'] for r in rows]!=[r['id'] for r in actual[c]]:
            result['frame_errors'].append({'collection':c,'reason':'object_identity_or_order'});continue
        for planned in rows:
            observed=indexes[c][planned['id']]
            if set(planned)!=set(observed):result['frame_errors'].append({'object':planned['id'],'reason':'field_set'})
            for field,wanted in planned.items():
                if (c,planned['id'],field) not in mutable and (c,field) not in derived and observed.get(field)!=wanted:
                    result['frame_errors'].append({'path':[c,planned['id'],field],'reason':'protected_field'})
    structural=receipt.get('root_valid') and receipt.get('diagnostician',{}).get('severity')==0 and not receipt.get('resource_errors') and not receipt.get('resource_warnings') and not receipt.get('unresolved_proxies')
    result['strict_success']=bool(structural and result['oracle_agreement'] and not any(tuples.values()) and all(r['pass'] for r in result['task_results']) and not result['frame_errors'])
    return result
