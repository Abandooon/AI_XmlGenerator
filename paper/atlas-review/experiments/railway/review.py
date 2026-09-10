"""One-command, offline Railway V5 evidence replay (Python standard library)."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,runpy,shutil,subprocess,sys,tempfile,time,zipfile
ROOT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True

def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir',type=Path,help='New directory for extracted frozen inputs and fresh results. Must not already exist.')
    parser.add_argument('--java',default='java',help='Java 8 executable, resolved from PATH by default. No Java download is performed.')
    parser.add_argument('--jobs',type=int,default=4,choices=range(1,9))
    args=parser.parse_args()
    java=shutil.which(args.java)
    if not java:parser.error('Java executable not found; install Java 8 and pass --java /path/to/java')
    checked=subprocess.run([java,'-version'],capture_output=True,text=True,timeout=15)
    version=(checked.stderr or checked.stdout).strip()
    if checked.returncode or '1.8.' not in version:parser.error('This frozen native stack is qualified for Java 8; received '+version.splitlines()[0])
    if args.work_dir:
        work=args.work_dir.resolve()
        if work.exists():parser.error('Refusing to overwrite existing work directory: '+str(work))
        work.mkdir(parents=True)
    else:work=Path(tempfile.mkdtemp(prefix='atlas_railway_review_'))
    payload=work/'payload';payload.mkdir();output=work/'results';output.mkdir()
    manifest=json.loads((ROOT/'PAYLOAD_MANIFEST.json').read_text('utf-8'));files=manifest['files'];seen=set();start=time.monotonic()
    try:
        for record in manifest['archives']:
            archive=ROOT/record['path']
            if archive.stat().st_size!=record['bytes'] or sha_file(archive)!=record['sha256']:raise ValueError('Archive hash mismatch: '+record['path'])
            with zipfile.ZipFile(archive) as z:
                for member in z.infolist():
                    name=member.filename;p=PurePosixPath(name)
                    if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or member.is_dir() or name in seen or name not in files:raise ValueError('Unexpected ZIP entry: '+name)
                    data=z.read(member);expected=files[name]
                    if len(data)!=expected['bytes'] or hashlib.sha256(data).hexdigest()!=expected['sha256']:raise ValueError('Payload hash mismatch: '+name)
                    dest=payload.joinpath(*p.parts);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);seen.add(name)
        if seen!=set(files):raise ValueError('Incomplete payload')
        print('Verified and extracted',len(seen),'immutable payload files.',flush=True)
        sys.path.insert(0,str(ROOT/'corrected'))
        scope={'PAYLOAD':payload,'OUTPUT':output,'JAVA':java,'JOBS':args.jobs}
        for script in ['replay_evidence.py','replay_queue.py','replay_transport.py','replay_statistics.py']:
            runpy.run_path(str(ROOT/'corrected'/script),init_globals=scope)
        replay=json.loads((output/'train_recomputed.json').read_text('utf-8'))
        regression=json.loads((output/'namespace_regression.json').read_text('utf-8'))
        transport=json.loads((output/'train_transport_audit.json').read_text('utf-8'))
        report={'status':'PASS','format':'atlas.railway.reviewer.replay.v1','payload_files':len(seen),'actions':747,'endpoints':len(replay['rows']),
                'artifact_endpoints':replay['counts']['artifact_endpoints'],'unique_xmi_identity_pairs':replay['counts']['unique_artifact_and_identity'],
                'responses':replay['responses'],'historical_outcome_discrepancies':len(replay['errors']),'malformed_namespace_rejected':regression['pass'],
                'physical_send_intents':transport['physical_intents_cross_lineage'],'unknown_usage_attempts':transport['unknown_attempts'],
                'billing_complete':False,'network_or_model_calls':0,'java_version':version,'python_version':sys.version.split()[0],
                'elapsed_seconds':round(time.monotonic()-start,3),'counts':replay['counts']}
    except Exception as error:
        report={'status':'FAIL','error':type(error).__name__+': '+str(error),'elapsed_seconds':round(time.monotonic()-start,3)}
        (output/'REVIEW_RESULT.json').write_text(json.dumps(report,indent=2),'utf-8')
        raise
    (output/'REVIEW_RESULT.json').write_text(json.dumps(report,indent=2),'utf-8')
    print(json.dumps(report,indent=2),flush=True)
    print('Fresh results:',output,flush=True)

if __name__=='__main__':main()
