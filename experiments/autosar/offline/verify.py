"""Verify the frozen V20 release and recompute all 60 generation / 100 repair cells.

Usage: python -I -B offline/verify.py --work-dir /path/to/new-empty-work-directory
No provider request, repair, generation, or source mutation is performed.
"""
from pathlib import Path
import argparse
from collections import Counter
import importlib.metadata
import json
import shutil
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
sys.path.insert(0, str(HERE))
from post_run_correction_identity import (
    canonical_sha256, canonical_valid, extract_archive, read_json,
    relocate_evidence, sha256_file, under, verify_file_map, write_json,
)
from revalidate_phase12_run import OfflineVerifier

ARCHIVE_NAME = 'AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip'
# Measured original ZIP digest (not derived from a mutable status report).
ARCHIVE_SHA = '3e17cbe0bd5420e494dc527e51cd43746fda04ac3dd0fc459cef17b20b60cf01'
RECOVERY_FIELDS = [
    'suppressed_phase1_selection_count', 'multi_anchor_expansion_count',
    'structured_anchor_index_repair_count', 'structured_anchor_chain_repair_count',
    'absent_value_repair_count', 'structured_value_anchor_binding_count',
    'derived_anchor_identity_count', 'resolved_unsupported_count',
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def only(paths, description):
    paths = list(paths)
    require(len(paths) == 1, 'Expected one '+description+', found '+str(len(paths)))
    return paths[0]


def unique_schema_value(schema):
    """Narrow singleton proof for these archived admitted schemas only."""
    if 'const' in schema:
        return schema['const']
    if len(schema.get('enum', [])) == 1:
        return schema['enum'][0]
    if schema.get('type') == 'object':
        properties = schema.get('properties', {})
        require(schema.get('additionalProperties') is False and not schema.get('patternProperties'), 'Schema permits extra properties')
        require(set(schema.get('required', [])) == set(properties), 'Schema contains optional properties')
        return {key:unique_schema_value(value) for key,value in properties.items()}
    if schema.get('type') == 'array':
        require(schema.get('minItems') == schema.get('maxItems') and schema.get('maxItems') is not None, 'Schema permits variable length')
        return [unique_schema_value(schema['items']) for _ in range(schema['maxItems'])]
    raise ValueError('Schema has an unfixed leaf')


def build_runtime(release, work):
    runtime = work/'runtime'
    freeze = read_json(release/'frozen_contract/PAPER_ARTIFACT_FREEZE_MANIFEST.json')
    require(canonical_sha256({k:v for k,v in freeze.items() if k != 'manifest_sha256'}) == freeze['manifest_sha256'], 'Freeze canonical hash mismatch')
    copied = []
    for group, prefix in [('runtime_assets', 'runtime_assets'), ('repository_files', 'repository')]:
        for relative, expected in freeze[group].items():
            if group == 'repository_files' and relative != 'src/llm_generation/knowledge/element_selection.py':
                continue
            source = under(release/'code_snapshot'/prefix, relative)
            require(sha256_file(source) == expected, 'Frozen runtime source hash mismatch: '+relative)
            target = under(runtime, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied.append({'runtime_path':relative, 'sha256':expected, 'identity':'original_v20_freeze'})
    supplemental = read_json(HERE/'SUPPLEMENTAL_SOURCES.json')
    for entry in supplemental['files']:
        source = under(PACKAGE, entry['path'])
        require(sha256_file(source) == entry['sha256'], 'Supplemental source hash mismatch')
        if 'runtime_path' in entry:
            target = under(runtime, entry['runtime_path'])
            require(not target.exists(), 'Supplement overwrites frozen runtime file')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied.append({'runtime_path':entry['runtime_path'], 'sha256':entry['sha256'], 'identity':'supplemental_2026-09-09'})
    # Missing parent package markers intentionally remain Python namespace packages.
    # No original eager __init__ from the author's full repository is imported.
    write_json(work/'reports/runtime_sources.json', copied)
    return runtime, copied


def run(work):
    started = time.monotonic()
    work = work.resolve()
    require(not work.exists() or (work.is_dir() and not any(work.iterdir())), '--work-dir must be a new or empty directory; no files will be overwritten')
    work.mkdir(parents=True, exist_ok=True)
    (work/'temp').mkdir()
    tempfile.tempdir = str(work/'temp')
    blocked = []
    permitted_reads = [work, PACKAGE.resolve(), Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()]

    def check_io(path, writing):
        if not isinstance(path, (str, bytes)):
            return  # Integer file descriptors are already open process streams.
        resolved = Path(path.decode() if isinstance(path, bytes) else path).resolve()
        allowed = [work] if writing else permitted_reads
        require(any(resolved.is_relative_to(root) for root in allowed), 'Offline file access leaves permitted roots: '+str(resolved))

    def deny_network(event, args):
        if event in ('socket.connect', 'socket.connect_ex', 'socket.getaddrinfo', 'socket.sendto', 'subprocess.Popen', 'os.system'):
            blocked.append(event)
            raise RuntimeError('Offline verification forbids network/subprocess operations: '+event)
        if event == 'open':
            path, mode, flags = args
            import os
            writing = bool(set(str(mode or '')) & set('wax+')) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            check_io(path, writing)
        elif event in ('os.remove', 'os.rmdir', 'os.mkdir'):
            check_io(args[0], True)
        elif event in ('os.rename', 'os.replace'):
            check_io(args[0], True)
            check_io(args[1], True)
    sys.addaudithook(deny_network)

    release = extract_archive(PACKAGE/'frozen'/ARCHIVE_NAME, work/'extracted', ARCHIVE_SHA)
    manifest = read_json(release/'RELEASE_MANIFEST.json')
    integrity = verify_file_map(release, manifest['files'])
    require(not integrity['errors'] and integrity['checked'] == 9673, 'Release file identity failure')
    require(canonical_valid(manifest), 'Release canonical hash mismatch')
    actual_files = {str(p.relative_to(release)).replace('\\', '/') for p in release.rglob('*') if p.is_file()}
    require(actual_files == set(manifest['files']) | {'RELEASE_MANIFEST.json', 'SHA256SUMS.txt'}, 'Unexpected or missing ZIP members')
    browseable = read_json(PACKAGE/'frozen_code/CODE_INDEX.json')
    for item in browseable['files']:
        require(item['sha256'] == manifest['files'][item['archive_relative_path']], 'Browseable code index is not bound to frozen release')
        require(sha256_file(under(PACKAGE, item['path'])) == item['sha256'], 'Browseable frozen source hash mismatch')
    runtime, sources = build_runtime(release, work)
    verifier = OfflineVerifier(release, runtime)
    print('Frozen release: 9,673/9,673 hashes PASS; isolated runtime loaded.', flush=True)

    generation = read_json(release/'evidence/formal_v20/generation/experiment_results.json')
    schedule = read_json(release/'evidence/formal_v20/generation/experiment_schedule.json')
    require(canonical_valid(generation) and canonical_valid(schedule), 'Generation canonical results/schedule identity failure')
    require(sorted(r['run_id'] for r in generation['records']) == sorted(r['run_id'] for r in schedule['runs']), 'Generation schedule does not match results')
    require(len(generation['records']) == 60, 'Generation count mismatch')
    scheduled = {r['run_id']:(r['case_id'],r['repetition'],r['seed']) for r in schedule['runs']}
    g_rows = []
    g_calls = []
    transitions = []
    interventions = Counter()
    applied = 0
    phase2 = []
    from jsonschema import Draft202012Validator
    for index, record in enumerate(generation['records'], 1):
        require(scheduled[record['run_id']] == (record['case_id'],record['repetition'],record['seed']), 'Generation case/repetition/seed mismatch')
        run_root = relocate_evidence(release, record['run_root'], 'generation')
        require(not verify_file_map(run_root, record['artifact_hashes'])['errors'], 'Generation per-run artifact hash failure')
        paths = {'components':sorted((run_root/'atlas_output/ARXML/Components').glob('*.arxml')), 'interfaces':sorted((run_root/'atlas_output/ARXML/Interfaces').glob('*.arxml'))}
        context = read_json(only((run_root/'atlas_output/ARXML').glob('validation_context_*.json'), 'saved validation context'))
        round1 = read_json(only((run_root/'atlas_output/round1_data').glob('round1_*.json'), 'post-intervention Phase 1 design'))
        plans = round1['design']['component_plan']
        v,e,s = verifier.validate(record['case_id'], paths, context, work/'reports/generation'/record['run_id'], plans=plans)
        recoveries = Counter()
        obligations = 0
        for item in round1.get('stats', {}).get('declared_value_reconciliation', []):
            obligations += item.get('applied_count', 0)
            recoveries.update({f:item.get(f,0) for f in RECOVERY_FIELDS})
        interventions.update(recoveries)
        applied += obligations
        calls = jsonl(run_root/'provider_calls.jsonl')
        g_calls.extend(calls)
        transitions.extend(jsonl(run_root/'provider_call_transitions.jsonl'))
        row = {'run_id':record['run_id'], 'case_id':record['case_id'], 'repetition':record['repetition'], 'seed':record['seed'], 'pipeline_attempts':len(record['attempts']), 'decision':e['decision'], 'profile':v['artifact_profile']['decision'], 'full_corpus':v['decision'], 'saved_plan_consistency':s['decision'], 'arxml_files':len(e['xsd']), 'components':len(paths['components']), 'interfaces':len(paths['interfaces']), 'xsd_pass':sum(x['status']=='PASS' for x in e['xsd']), 'structural_obligations':len(e['structural_obligations']), 'structural_failures':e['structural_failure_count'], 'local_references':len(e['reference_integrity']), 'local_reference_failures':e['local_reference_failure_count'], 'logged_applied_obligations':obligations, 'logged_recoveries':sum(recoveries.values()), 'provider_responses':len(calls)}
        g_rows.append(row)
        debug = run_root/'atlas_output/debug'
        for raw in sorted(debug.glob('*provider_raw*.json')):
            if raw.name.startswith('round2_response_interfaces_'):
                schema_path = only(debug.glob('round2_schema_interfaces_provider_admitted_*.json'), 'interface admitted schema')
                kind = 'interfaces'
            else:
                component = raw.name.split('round2_response_',1)[1].split('_provider_raw_',1)[0]
                schema_path = only((p for p in debug.glob('round2_schema_'+component+'_provider_*.json') if '_provider_full_' not in p.name), 'component admitted schema')
                kind = 'component'
            schema = read_json(schema_path)
            synthetic = unique_schema_value(schema)
            Draft202012Validator(schema).validate(synthetic)
            phase2.append({'run_id':record['run_id'], 'kind':kind, 'schema':str(schema_path.relative_to(release)).replace('\\','/'), 'raw':str(raw.relative_to(release)).replace('\\','/'), 'singleton':True, 'unique_json_equals_saved_parsed_response':synthetic==read_json(raw)})
        if index % 10 == 0:
            print('Generation independently revalidated: '+str(index)+'/60', flush=True)

    repair = read_json(release/'evidence/formal_v20/repair/repair_results.json')
    repair_schedule = read_json(release/'evidence/formal_v20/repair/repair_schedule.json')
    require(canonical_valid(repair) and canonical_valid(repair_schedule), 'Repair canonical results/schedule identity failure')
    require(len(repair['records']) == 100 and sorted(r['run_id'] for r in repair_schedule['runs']) == sorted(r['run_id'] for r in repair['records']), 'Repair schedule/count mismatch')
    r_rows = []
    r_calls = []
    for index, record in enumerate(repair['records'], 1):
        run_root = relocate_evidence(release, record['output_root'], 'repair')
        require(not verify_file_map(run_root, record['artifact_hashes'])['errors'], 'Repair per-run artifact hash failure')
        reference = release/'controlled_reference_baselines'/record['case_id']/'generated_arxml/reference'
        base_report = read_json(only(reference.glob('*_validation_reference.json'), 'controlled baseline validation report'))
        context = base_report['validation_context']['manifest']
        base_files = {p.name:sha256_file(p) for p in reference.glob('*.arxml')}
        row = {'run_id':record['run_id'], 'case_id':record['case_id'], 'mutation':record['mutation'], 'analysis_layer':record['analysis_layer']}
        for state in ('input', 'final'):
            paths = {kind:sorted((run_root/state/kind).glob('*.arxml')) for kind in ('components','interfaces')}
            v,e,_ = verifier.validate(record['case_id'], paths, context, work/'reports/repair'/record['run_id'], prefix=state+'_')
            current_files = {p.name:sha256_file(p) for files in paths.values() for p in files}
            row.update({state+'_decision':e['decision'], state+'_profile':v['artifact_profile']['decision'], state+'_full_corpus':v['decision'], state+'_exact_baseline_bytes_and_filenames':current_files==base_files})
        r_rows.append(row)
        r_calls.extend(jsonl(run_root/'provider_calls.jsonl'))
        if index % 20 == 0:
            print('Controlled repair independently revalidated: '+str(index)+'/100', flush=True)

    generation_metrics = {
        'runs':len(g_rows), 'cases':len({r['case_id'] for r in g_rows}),
        'one_pipeline_attempt_runs':sum(r['pipeline_attempts']==1 for r in g_rows),
        'evaluation_pass':sum(r['decision']=='PASS' for r in g_rows),
        'artifact_profile_pass':sum(r['profile']=='PASS' for r in g_rows),
        'full_corpus_incomplete':sum(r['full_corpus']=='INCOMPLETE' for r in g_rows),
        'saved_plan_consistency_pass':sum(r['saved_plan_consistency']=='PASS' for r in g_rows),
        **{k:sum(r[k] for r in g_rows) for k in ['arxml_files','components','interfaces','xsd_pass','structural_obligations','structural_failures','local_references','local_reference_failures']},
        'provider_responses':len(g_calls), 'unique_response_ids':len({c['response_id'] for c in g_calls}),
        'logical_requests':len({t['logical_request_id'] for t in transitions}),
        'physical_dispatches':len({t['provider_call_id'] for t in transitions if t['stage']=='DISPATCH_STARTED'}),
        'continued_logical_requests':len({t['logical_request_id'] for t in transitions if t.get('transport_attempt',1)>1}),
        'logged_total_tokens':sum(c['usage']['total_tokens'] for c in g_calls),
        'logged_duration_seconds':sum(r['total_duration_seconds'] for r in generation['records']),
        'logged_applied_obligations':applied, 'logged_recoveries':sum(interventions.values()),
        'logged_recovery_runs':sum(r['logged_recoveries']>0 for r in g_rows),
        'logged_recovery_categories':dict(interventions),
    }
    repair_metrics = {
        'cells':len(r_rows), 'analysis_layers':dict(Counter(r['analysis_layer'] for r in r_rows)),
        'input_evaluation_fail':sum(r['input_decision']=='FAIL' for r in r_rows),
        'final_evaluation_pass':sum(r['final_decision']=='PASS' for r in r_rows),
        'final_profile_pass':sum(r['final_profile']=='PASS' for r in r_rows),
        'final_full_corpus_incomplete':sum(r['final_full_corpus']=='INCOMPLETE' for r in r_rows),
        'inputs_differ_from_reference':sum(not r['input_exact_baseline_bytes_and_filenames'] for r in r_rows),
        'final_exact_reference_bytes_and_filenames':sum(r['final_exact_baseline_bytes_and_filenames'] for r in r_rows),
        'natural_failure_cells':repair_schedule['natural_failure_count'],
        'provider_responses':len(r_calls), 'unique_response_ids':len({c['response_id'] for c in r_calls}),
        'logged_total_tokens':sum(c['usage']['total_tokens'] for c in r_calls),
    }
    imported_sources = []
    for name, module in sorted(sys.modules.items()):
        filename = getattr(module, '__file__', None)
        if filename and (name.startswith('src.') or name in ('frozen_asw_evaluator','render_cases')):
            path = Path(filename).resolve()
            require(path.is_relative_to(work), 'Project import escaped relocated workspace: '+name)
            imported_sources.append({'module':name, 'relative_path':str(path.relative_to(work)).replace('\\','/'), 'sha256':sha256_file(path)})
    require(not blocked, 'Unexpected network or subprocess attempt')
    expected_generation = {'runs':60,'cases':20,'one_pipeline_attempt_runs':60,'evaluation_pass':60,'artifact_profile_pass':60,'full_corpus_incomplete':60,'saved_plan_consistency_pass':60,'arxml_files':255,'components':60,'interfaces':195,'xsd_pass':255,'structural_obligations':2418,'structural_failures':0,'local_references':675,'local_reference_failures':0,'provider_responses':180,'unique_response_ids':180,'logical_requests':180,'physical_dispatches':184,'continued_logical_requests':2,'logged_total_tokens':11967476,'logged_applied_obligations':1734,'logged_recoveries':527,'logged_recovery_runs':49}
    expected_repair = {'cells':100,'input_evaluation_fail':100,'final_evaluation_pass':100,'final_profile_pass':100,'final_full_corpus_incomplete':100,'inputs_differ_from_reference':100,'final_exact_reference_bytes_and_filenames':100,'natural_failure_cells':0,'provider_responses':130,'unique_response_ids':130,'logged_total_tokens':716624}
    checks = [{'metric':'generation.'+k,'actual':generation_metrics[k],'expected':v,'pass':generation_metrics[k]==v} for k,v in expected_generation.items()]
    checks += [{'metric':'repair.'+k,'actual':repair_metrics[k],'expected':v,'pass':repair_metrics[k]==v} for k,v in expected_repair.items()]
    checks += [{'metric':'formal_v20_admitted_phase2_singleton_and_saved_json_match','actual':sum(r['singleton'] and r['unique_json_equals_saved_parsed_response'] for r in phase2),'expected':120,'pass':len(phase2)==120 and all(r['singleton'] and r['unique_json_equals_saved_parsed_response'] for r in phase2)}]
    result = {'schema_version':'autosar.reviewer.offline-verification.v1','decision':'PASS' if all(c['pass'] for c in checks) else 'FAIL','scope':'Revalidation of preserved V20 artifacts and logged metadata; not a replay of original model interactions.','archive_sha256':ARCHIVE_SHA,'release_file_identity':integrity,'release_manifest_canonical_valid':True,'generation_results_canonical_sha256':generation['content_sha256'],'repair_results_canonical_sha256':repair['content_sha256'],'runtime_sources':{'frozen':sum(s['identity']=='original_v20_freeze' for s in sources),'supplemental':sum(s['identity']=='supplemental_2026-09-09' for s in sources)},'generation':generation_metrics,'repair':repair_metrics,'phase2':{'scope':'Only the post-Phase1 admitted schemas in formal V20; no claim about arbitrary dynamic Phase2 or model-free Phase1.','schemas':len(phase2),'singleton_and_saved_json_match':sum(r['singleton'] and r['unique_json_equals_saved_parsed_response'] for r in phase2)},'checks':checks,'offline_execution':{'network_attempts_blocked':len(blocked),'subprocesses_started':0,'all_project_imports_under_work_dir':True,'writes_only_to_requested_work_dir':True},'environment':{'python':sys.version,'packages':{p:importlib.metadata.version(p) for p in ('lxml','jsonschema','PyYAML','z3-solver')}},'elapsed_seconds':round(time.monotonic()-started,3)}
    write_json(work/'reports/generation_rows.json', g_rows)
    write_json(work/'reports/repair_rows.json', r_rows)
    write_json(work/'reports/phase2_schema_rows.json', phase2)
    write_json(work/'reports/imported_project_sources.json', imported_sources)
    write_json(work/'verification.json', result)
    print(json.dumps({'decision':result['decision'],'generation_pass':generation_metrics['evaluation_pass'],'repair_input_fail':repair_metrics['input_evaluation_fail'],'repair_final_pass':repair_metrics['final_evaluation_pass'],'report':str(work/'verification.json'),'elapsed_seconds':result['elapsed_seconds']},indent=2), flush=True)
    return 0 if result['decision']=='PASS' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', required=True, type=Path, help='New or empty directory for extraction, runtime, reports and temporary XML files (allow 1 GiB).')
    args = parser.parse_args()
    raise SystemExit(run(args.work_dir))
