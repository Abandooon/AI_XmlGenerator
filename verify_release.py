"""Verify release file identities and run selected offline experiment checks."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parent
TRACKS=('autosar','vllm','pil','railway','railway_terra')
EXCLUDED={'RELEASE_MANIFEST.json','RELEASE_MANIFEST.sha256'}
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def verify_files():
    path=ROOT/'RELEASE_MANIFEST.json'
    if digest(path)!=(ROOT/'RELEASE_MANIFEST.sha256').read_text().split()[0]: raise RuntimeError('Release manifest checksum mismatch')
    data=json.loads(path.read_text(encoding='utf8'));expected=set()
    for row in data['files']:
        p=(ROOT/row['path']).resolve()
        if not p.is_relative_to(ROOT) or row['path'] in expected:raise RuntimeError('Invalid or duplicate manifest path')
        expected.add(row['path'])
        if not p.is_file() or p.stat().st_size!=row['bytes'] or digest(p)!=row['sha256']:raise RuntimeError('File identity mismatch: '+row['path'])
    current={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p.name not in EXCLUDED and not any(x in {'.git','.venv','__pycache__','review-output'} for x in p.relative_to(ROOT).parts) and p.suffix!='.pyc'}
    if current!=expected:raise RuntimeError('Unexpected release file set: '+repr(sorted(current^expected)[:20]))
    return {'status':'PASS','files_verified':len(expected),'release_id':data['release_id']}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--integrity-only',action='store_true');p.add_argument('--track',choices=('all',)+TRACKS,default='all')
    p.add_argument('--work-dir',type=Path);p.add_argument('--node',default='node');p.add_argument('--java',default='java')
    p.add_argument('--jobs',type=int,choices=range(1,6),default=1,help='Concurrent independent tracks (default: 1)')
    a=p.parse_args();integrity=verify_files();print(json.dumps(integrity))
    if a.integrity_only:return 0
    if a.work_dir is None:p.error('--work-dir is required for replay')
    work=a.work_dir.resolve()
    if work==ROOT or work.is_relative_to(ROOT):p.error('Use a work directory outside the release tree')
    if work.exists() and any(work.iterdir()):p.error('Use an empty work directory')
    work.mkdir(parents=True,exist_ok=True)
    tracks=TRACKS if a.track=='all' else (a.track,)
    node=shutil.which(a.node)
    if 'pil' in tracks and not node:p.error('Node executable not found: '+a.node)
    java=shutil.which(a.java)
    if any(t in tracks for t in ('railway','railway_terra')) and not java:p.error('Java executable not found: '+a.java)
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONIOENCODING']='utf-8';env.pop('PYTHONPATH',None)
    if node:env['PATH']=str(Path(node).resolve().parent)+os.pathsep+env.get('PATH','')
    def run_track(track):
        experiment=ROOT/'experiments'/track
        if track=='pil':command=[str(experiment/'tools/verify.py'),'--output-dir',str(work/track),'--node',str(Path(node).resolve())]
        else:command=[str(experiment/'review.py'),'--work-dir',str(work/track)]
        if track in ('railway','railway_terra'):command+=['--java',str(Path(java).resolve())]
        print('Reviewing '+track+' ...',flush=True)
        with (work/(track+'.log')).open('w',encoding='utf8') as stream:
            run=subprocess.run([sys.executable,'-B']+command,cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT)
        result_path={'autosar':'autosar/verification.json','vllm':'vllm/REVIEW_RESULT.json','pil':'pil/verification_report.json','railway':'railway/results/REVIEW_RESULT.json','railway_terra':'railway_terra/results/REVIEW_RESULT.json'}[track]
        outcome={'track':track,'exit_code':run.returncode,'status':'PASS' if run.returncode==0 else 'FAIL','log':track+'.log','result':result_path}
        print(json.dumps(outcome),flush=True)
        return outcome
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        outcomes=list(pool.map(run_track,tracks))
    report={'release_integrity':integrity,'tracks':outcomes,'status':'PASS' if all(r['exit_code']==0 for r in outcomes) else 'FAIL','scope':'Offline review of retained evidence; no new model generation','inspection_index':'docs/COMMANDS.md','data_crosscheck':'docs/EXPERIMENT_DATA.md'}
    (work/'RELEASE_REVIEW_RESULT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return 0 if report['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
