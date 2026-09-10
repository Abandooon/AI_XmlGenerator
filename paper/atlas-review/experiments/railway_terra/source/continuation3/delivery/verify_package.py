"""Read-only verification of all four execution segments and the current package."""
from pathlib import Path
import hashlib,json,sys
BASE=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def verify(root,mapping):
    bad=[]
    for rel,want in mapping.items():
        p=(root/rel).resolve()
        if not p.is_relative_to(BASE) or not p.is_file() or sha(p)!=want:bad.append(rel)
    return {'files':len(mapping),'errors':bad,'pass':not bad}
checks={}
for name,where in [('EXECUTION_SEAL.json','.'),('run/MANIFEST.json','run'),
 ('continuation/CONTINUATION_SEAL.json','continuation'),('continuation/run/MANIFEST.json','continuation/run'),
 ('continuation2/plans/cap5/CONTINUATION_SEAL.json','continuation2'),('continuation2/run/MANIFEST.json','continuation2/run'),
 ('continuation3/plans/cap6/CONTINUATION_SEAL.json','continuation3'),('continuation3/run/MANIFEST.json','continuation3/run')]:
    checks[name]=verify(BASE/where,read(BASE/name))
checks['portable_python']=verify(BASE/'delivery/runtime/python',read(BASE/'delivery/RUNTIME_MANIFEST.json')['files'])
manifest=BASE/'continuation3/delivery/PACKAGE_MANIFEST.json'
if manifest.exists():checks['current_package']=verify(BASE,read(manifest)['files'])
out={'offline_only':True,'pass':all(r['pass'] for r in checks.values()),'checks':checks}
print(json.dumps(out,ensure_ascii=True,indent=2))
sys.exit(0 if out['pass'] else 1)
