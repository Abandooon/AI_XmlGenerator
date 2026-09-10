"""Offline V6.3.4 replay with explicit relocation and qualified provenance."""
from pathlib import Path, PureWindowsPath
import argparse, copy, hashlib, importlib.util, json, os, shutil, subprocess, sys, tarfile, tempfile

ROOT=Path(__file__).resolve().parent
MISSING={
    'E:/54239/Documents/atlas_autosar_requirements_v3/rendered/run_manifest.json':'0af861da7b10dfe80261080b58dba1c3758378d0a2a1bfe55b5084d90bc202b4',
    'E:/54239/Documents/atlas_vllm_audit_2026-08-09/postprocess_uga_results_v026.py':'717846d4884f852eb7faa206bb099eb113c4cc9eab5300eb5919bd22ea7ba4bc',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,x): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def module_at(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def extract(archive,dst):
    with tarfile.open(archive,'r:gz') as tf:
        for member in tf.getmembers():
            target=(dst/member.name).resolve()
            need(target.is_relative_to(dst.resolve()),'unsafe_archive_path')
            need(member.isfile() or member.isdir(),'archive_link_or_special_file')
        tf.extractall(dst,filter='data')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work-dir',type=Path,required=True);args=p.parse_args()
    work=args.work_dir.resolve();need(not work.exists() or not any(work.iterdir()),'work_dir_must_be_empty');work.mkdir(parents=True,exist_ok=True)
    temporary=work/'temporary';temporary.mkdir();tempfile.tempdir=str(temporary)
    for key in ('TMP','TEMP','TMPDIR'):os.environ[key]=str(temporary)
    sys.dont_write_bytecode=True
    manifest=read(ROOT/'RUNTIME_AND_ARCHIVES.json')
    for row in manifest['runtime']+manifest['archives']:
        f=ROOT/row['path'];need(f.is_file() and f.stat().st_size==row['bytes'] and sha(f)==row['sha256'],'release_asset_hash_mismatch:'+row['path'])
    # Block network calls in the replay process; no provider or graph connection is needed.
    def offline_guard(event,args):
        if event in {'socket.connect','socket.getaddrinfo'}: raise RuntimeError('network_is_disabled_for_offline_review')
        if event=='open' and isinstance(args[0],(str,bytes)):
            path=Path(os.fsdecode(args[0])).resolve()
            if path==Path(os.devnull).resolve():return
            allowed=[ROOT,work,Path(sys.prefix).resolve(),Path(sys.base_prefix).resolve()]
            allowed.extend(Path(s).resolve() for s in sys.path if s and ('site-packages' in s or 'dist-packages' in s))
            if not any(path.is_relative_to(root) for root in allowed):
                raise RuntimeError('outside_package_data_access_forbidden:'+str(path))
    sys.addaudithook(offline_guard)
    for row in manifest['archives']:
        archive=ROOT/row['path'];extract(archive,work/'unpacked'/archive.name.removesuffix('.tar.gz'))
    bundle=work/'unpacked/atlas-vllm-uga-v6-3-4-bundle-20260829/bundle'
    evidence=work/'unpacked/atlas-vllm-uga-v6-3-4-paper-evidence-20260829/atlas_vllm_uga_v6_3_4_formal_b1_evidence_2026-08-29'
    runtime=ROOT/'runtime';atlas=runtime/'AI_XmlGenerator';probe=runtime/'atlas_model_probe';cases=runtime/'atlas_autosar_requirements_v3'
    for key,value in [('ATLAS_V634_ATLAS_ROOT',atlas),('ATLAS_V634_PROBE_ROOT',probe),('ATLAS_V634_REQUIREMENTS_ROOT',cases)]: os.environ[key]=str(value)
    os.environ['LLM_API_KEY']='offline-local-placeholder'
    sys.path[:0]=[str(bundle/'tools'),str(probe),str(cases),str(atlas)]
    m=module_at('review_archived_postprocess',runtime/'postprocess_uga_results_v028_relocatable.py')
    roots={PureWindowsPath('E:/git projects/AI_XmlGenerator'):atlas,PureWindowsPath('E:/54239/Documents/atlas_model_probe'):probe,PureWindowsPath('E:/54239/Documents/atlas_autosar_requirements_v3'):cases}
    def relocate(s):
        path=PureWindowsPath(s)
        for old,new in roots.items():
            if path.is_relative_to(old): return str(new.joinpath(*path.relative_to(old).parts))
        return None
    original_verify=m.verify_source_files
    qualification={}
    def verify_relocated(source):
        moved=copy.deepcopy(source);present=[];absent=[]
        for row in moved['source_files']:
            portable=relocate(row['path'])
            if portable and Path(portable).is_file(): row['path']=portable;present.append(row)
            else:
                key=PureWindowsPath(row['path']).as_posix()
                need(MISSING.get(key)==row['sha256'],'unexpected_missing_historical_source:'+key)
                absent.append({'historical_path':key,'expected_sha256':row['sha256'],'status':'not_retained; not certified'})
        need(len(present)==8 and len(absent)==2,'historical_provenance_counts_changed')
        moved['source_files']=present
        for tree in moved['source_trees']:
            tree['root']=relocate(tree['root']);need(tree['root'] is not None,'unmapped_source_tree')
        original_verify(moved)
        qualification.update({'runtime_tree_entries_verified':572,'individual_historical_sources_verified':8,'missing_historical_sources':absent,'complete_historical_source_certificate':False,'frozen_source_bytes_modified':False,'relocation_only':True})
        save(work/'PROVENANCE_QUALIFICATION.json',qualification)
    m.verify_source_files=verify_relocated
    evaluator=module_at('evaluate_asw_v3_run',probe/'evaluate_asw_v3_run.py')
    evaluator.ATLAS_ROOT=atlas;evaluator.CASES_ROOT=cases;evaluator.XSD=atlas/'src/validation/data/AUTOSAR_4-2-2.xsd'
    post=work/'postprocess'
    result=m.postprocess(contract_path=evidence/'FORMAL_CONTRACT.json',schedule_path=evidence/'FORMAL_SCHEDULE.json',compiled_manifest_path=evidence/'compiled_assets/COMPILED_ASSET_MANIFEST.json',source_root=bundle/'source_assets',run_root=evidence/'formal_run_b1',output_root=post)
    archived=evidence/'formal_postprocess_local_v1';differences=[];counts={k:0 for k in 'UGA'}
    for f in sorted(post.glob('[0-9][0-9][0-9].json')):
        fresh=read(f);old=read(archived/f.name)
        # Preserve actual original gate names, including reference/semantic checks.
        keys=sorted(k for k in old if k.endswith('_decision'))
        need(len(keys)==6,'unexpected_gate_set')
        for k in keys:
            if fresh.get(k)!=old[k]: differences.append([f.name,k,fresh.get(k),old[k]])
        separately_bound={'content_sha256','independent_evaluation_file_sha256','validation_file_sha256'}
        need({k:v for k,v in fresh.items() if k not in separately_bound}=={k:v for k,v in old.items() if k not in separately_bound},'postprocess_scientific_fields_changed:'+f.name)
        counts[fresh['arm']]+=fresh['end_to_end_structural_decision']=='PASS'
    fresh_arxml={f.relative_to(post).as_posix():sha(f) for f in post.rglob('*.arxml')}
    old_arxml={f.relative_to(archived).as_posix():sha(f) for f in archived.rglob('*.arxml')}
    need(not differences,'gate_verdict_differences');need(fresh_arxml==old_arxml,'materialized_arxml_byte_differences')
    need(result['request_count']==180 and counts=={'U':45,'G':60,'A':60} and len(fresh_arxml)==714,'unexpected_replay_counts')
    # Run the frozen formal verifier and analyzer against the new materialization.
    env=os.environ.copy();env['PYTHONPATH']=str(bundle/'tools');env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONIOENCODING']='utf-8'
    analysis_view=work/'analysis_view'
    commands=[
        [str(evidence/'verify_uga_formal_v032.py'),'--contract',str(evidence/'FORMAL_CONTRACT.json'),'--schedule',str(evidence/'FORMAL_SCHEDULE.json'),'--run-root',str(evidence/'formal_run_b1'),'--audit-root',str(evidence/'formal_audit_b1'),'--postprocess-root',str(post),'--audit-verifier',str(bundle/'vllm_overlay/overlay/vllm/v1/structured_output/audit.py'),'--qualification-manifest',str(evidence/'QUALIFICATION_RESULT.json'),'--output',str(work/'FORMAL_RESULT.json')],
        [str(evidence/'analyze_formal_results_v1.py'),'--root',str(analysis_view),'--output',str(work/'PAPER_ANALYSIS.json')],
    ]
    for index,command in enumerate(commands):
        if index==1:
            analysis_view.mkdir()
            for name in ['formal_run_b1','compiled_assets']:shutil.copytree(evidence/name,analysis_view/name)
            shutil.copy2(evidence/'FORMAL_SCHEDULE.json',analysis_view/'FORMAL_SCHEDULE.json')
            shutil.copy2(work/'FORMAL_RESULT.json',analysis_view/'FORMAL_RESULT.json')
            shutil.copytree(post,analysis_view/'formal_postprocess_local_v1')
        proc=subprocess.run([sys.executable,'-B']+command,cwd=work,env=env,text=True,encoding='utf8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (work/f'verify_{index}.log').write_text(proc.stdout,encoding='utf8');need(proc.returncode==0,'frozen_verifier_failed:'+str(index))
    identities={}
    for name in ['FORMAL_RESULT.json','PAPER_ANALYSIS.json']:
        observed=read(work/name);original=read(evidence/name)
        # Fresh validation reports contain relocated paths/timings. Their hashes,
        # and the manifests binding those hashes, must be new identities.
        omitted={'content_sha256','postprocess_manifest_content_sha256','postprocess_manifest_file_sha256','postprocess_files'} if name=='FORMAL_RESULT.json' else {'content_sha256','formal_result_content_sha256','formal_result_file_sha256'}
        same={k:v for k,v in observed.items() if k not in omitted}=={k:v for k,v in original.items() if k not in omitted}
        if name=='FORMAL_RESULT.json':
            need([r['path'] for r in observed['postprocess_files']]==[r['path'] for r in original['postprocess_files']],'postprocess_file_set_changed')
        else:
            need(observed['formal_result_file_sha256']==sha(work/'FORMAL_RESULT.json') and observed['formal_result_content_sha256']==read(work/'FORMAL_RESULT.json')['content_sha256'],'analysis_does_not_bind_new_formal_result')
        identities[name]={'archived_content_sha256':original.get('content_sha256'),'replayed_content_sha256':observed.get('content_sha256'),'byte_identity_claimed':False,'json_exact_equal':observed==original,'scientific_result_fields_equal':same,'relocated_provenance_fields_compared_separately':sorted(omitted)}
        need(same,'formal_analysis_changed:'+name)
    report={'status':'PASS','external_model_api_calls':0,'network_disabled_for_materialization':True,'author_filesystem_access_blocked':True,'requests':180,'end_to_end_pass_counts':counts,'six_gate_differences':differences,'all_postprocess_scientific_fields_equal':True,'analysis_bound_to_new_formal_result':True,'arxml_files_byte_equal':len(fresh_arxml),'formal_outputs':identities,'provenance_qualification':qualification,'limitations':['Historical pre-mask logits and token-ID masks were not retained; observed binding booleans can be recounted, not regenerated.','Finite compiled contracts are separate from the dynamic Neo4j-backed AUTOSAR V20 pipeline.']}
    save(work/'REVIEW_RESULT.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ['provenance_qualification','formal_outputs']},indent=2))
if __name__=='__main__': main()
