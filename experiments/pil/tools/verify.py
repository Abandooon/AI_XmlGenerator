"""One-command offline verification of frozen PIL evidence, erratum, and expert supplement."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / 'frozen/prepaid_freeze'
sys.path.insert(0, str(FREEZE))
sys.path.insert(0, str(ROOT / 'tools'))
import review_join

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def verify_ledger(entries, schedule, run):
    require(len(entries) == 720, 'Require 720 ledger rows')
    require([entry['unit_id'] for entry in entries] == [unit['unit_id'] for unit in schedule['units']], 'Ledger order does not match schedule')
    require(len({entry['unit_id'] for entry in entries}) == 720, 'Duplicate ledger unit')
    previous = schedule['content_sha256']
    for index, entry in enumerate(entries):
        require(entry['sequence'] == index and entry['prev_sha256'] == previous, f'Ledger chain sequence failed at row {index + 1}')
        require(canonical({key: value for key, value in entry.items() if key != 'entry_sha256'}) == entry['entry_sha256'], f'Ledger content hash failed at row {index + 1}')
        previous = entry['entry_sha256']
    require(previous == run['ledger_chain_head_sha256'], 'Ledger head mismatch')

def install_offline_guard(work):
    allowed = [ROOT.resolve(), work.resolve(), Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()]
    # Imports are allowed from installed distributions; experiment inputs may only come from this package.
    for value in sys.path:
        if value and ('site-packages' in value or 'dist-packages' in value):
            allowed.append(Path(value).resolve())
    def guard(event, args):
        if event in {'socket.connect', 'socket.getaddrinfo', 'socket.bind'}:
            raise RuntimeError('Network access is disabled for offline verification')
        if event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
            raw_path = os.fsdecode(args[0])
            if raw_path.lower() == os.devnull.lower():
                return
            candidate = Path(raw_path).resolve()
            if not any(candidate.is_relative_to(base) for base in allowed):
                raise RuntimeError(f'Offline input escaped package/runtime roots: {candidate.name}')
    sys.addaudithook(guard)

def verify_sources():
    manifest = read(ROOT / 'PACKAGE_MANIFEST.json')
    for rel, item in manifest['files'].items():
        path = ROOT / rel
        require(path.is_file() and path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], f'Package inventory mismatch: {rel}')
    source = read(ROOT / 'frozen/SOURCE_ARCHIVE_MANIFEST.json')
    require(canonical({key: value for key, value in source.items() if key not in {'content_sha256', 'created_at_utc'}}) == source['content_sha256'], 'Historical source manifest content hash mismatch')
    selection = read(ROOT / 'frozen/SOURCE_SELECTION.json')
    require(set(selection['included_original_paths']) | set(selection['excluded_original_paths']) == set(source['files']), 'Incomplete source selection accounting')
    require(not set(selection['included_original_paths']) & set(selection['excluded_original_paths']), 'Ambiguous source selection')
    for rel in selection['included_original_paths']:
        path, item = ROOT / 'frozen' / rel, source['files'][rel]
        require(path.stat().st_size == item['size_bytes'] and sha(path) == item['sha256'], f'Frozen original bytes changed: {rel}')
    return {'inventory_files_verified': len(manifest['files']), 'selected_frozen_files_verified': len(selection['included_original_paths']), 'original_inventory_files': len(source['files']), 'explicitly_excluded_files': len(selection['excluded_original_paths'])}

def verify_requests(entries, facts):
    import pil_v4_arms as arms
    import pil_v4_client as client
    import pil_v4_contract as contract
    context = arms.ArmContext.load(knowledge_base=FREEZE / 'kb/authoritative_provisions_v41_en.jsonl')
    stored = {(row['case_id'], row['arm']): row for row in jsonl(FREEZE / 'PIL_V41_RENDERED_PROMPTS.jsonl')}
    require(len(stored) == 240, 'Rendered prompt corpus must cover 60 x 4 cells')
    require(all(stored[(cid, 'p1')]['prompt'] == stored[(cid, 'p2')]['prompt'] == stored[(cid, 'p3')]['prompt'] for cid in facts), 'P1/P2/P3 prompt mismatch')
    attempts, responses = [], []
    for entry in entries:
        row = entry['row']
        prompt, evidence = arms.render_primary_prompt(context, arm=entry['arm'], facts=facts[entry['case_id']]['facts_text'])
        require(prompt == stored[(entry['case_id'], entry['arm'])]['prompt'], 'Rebuilt primary prompt mismatch')
        require(hashlib.sha256(prompt.encode()).hexdigest() == entry['prompt_sha256'], 'Primary prompt hash mismatch')
        require([item['evidence_id'] for item in evidence] == row['retrieved_evidence'], 'Retrieved evidence mismatch')
        require(contract.strict_json_parse(row['raw_text'])[0] == row['parsed_decision'], 'Initial raw/parsed mismatch')
        if row['repair']['attempted']:
            require(contract.strict_json_parse(row['repair']['raw_text'])[0] == row['repair']['decision'], 'Repair raw/parsed mismatch')
            require(hashlib.sha256(row['repair']['prompt'].encode()).hexdigest() == row['repair']['prompt_sha256'], 'Repair prompt hash mismatch')
        for stage in ['initial'] + (['repair'] if row['repair']['attempted'] else []):
            request = {'model': contract.PROVIDER_PROTOCOL['model_name'],
                       'messages': [{'role': 'system', 'content': client.COMMON_SYSTEM_INSTRUCTIONS}, {'role': 'user', 'content': prompt if stage == 'initial' else row['repair']['prompt']}],
                       'temperature': contract.PROVIDER_PROTOCOL['temperature'], 'max_completion_tokens': contract.PROVIDER_PROTOCOL['max_completion_tokens'],
                       'reasoning_effort': contract.PROVIDER_PROTOCOL['reasoning_effort'], 'seed': entry['seed']}
            if entry['arm'] in {'p2', 'p3'}:
                projected = client.provider_schema(context.schema)
                name = 'pil_v4_' + hashlib.sha256(json.dumps(projected, sort_keys=True).encode()).hexdigest()[:16]
                request['response_format'] = {'type': 'json_schema', 'json_schema': {'name': name, 'strict': True, 'schema': projected}}
            stage_attempts = [attempt for attempt in row['transport_attempts'] if attempt['logical_request_stage'] == stage]
            require(bool(stage_attempts), 'Missing stage transport record')
            for attempt in stage_attempts:
                require(attempt['request_sha256'] == canonical(request), 'Rebuilt request hash mismatch')
        for key in ['input_tokens', 'output_tokens', 'total_tokens']:
            require(sum(response['usage'][key] for response in row['provider_responses']) == row['usage'][key], 'Response/row usage mismatch')
        attempts.extend(row['transport_attempts'])
        responses.extend(row['provider_responses'])
    require(len(attempts) == 784 and len(responses) == 782 and len({row['response_id'] for row in responses}) == 782, 'Response or transport count mismatch')
    require(Counter(attempt['status'] for attempt in attempts) == {'RESPONSE_RECEIVED': 782, 'FAILED': 2}, 'Transport status mismatch')
    usage = {key: sum(row['usage'][key] for row in responses) for key in ['input_tokens', 'output_tokens', 'total_tokens']}
    require(usage == {'input_tokens': 952689, 'output_tokens': 268036, 'total_tokens': 1220725}, 'Token total mismatch')
    return {'reconstructed_primary_units': 720, 'reconstructed_transport_requests': 784, 'unique_provider_responses': 782, 'response_statuses': dict(Counter(row['status'] for row in attempts)), 'reported_models': dict(Counter(row['response_model'] for row in responses)), 'usage': usage}

def run_tests(work):
    import pil_v4_preflight as preflight
    original_json_reader = preflight._json
    translation_record = FREEZE / 'PIL_V41_TRANSLATION_PARITY_ACCEPTANCE.json'
    local_workbook = FREEZE / 'review_sources/translation/PIL_V41_ENGLISH_INPUT_PARITY_REVIEW_COMPLETED.xlsx'
    require(sha(local_workbook) == read(translation_record)['accepted_workbook_sha256'], 'Rebased review workbook is not the accepted original')
    def rebased_json_reader(path):
        value = original_json_reader(path)
        if Path(path).resolve() == translation_record.resolve():
            value['review_workbook']['accepted_path'] = 'review_sources/translation/PIL_V41_ENGLISH_INPUT_PARITY_REVIEW_COMPLETED.xlsx'
        return value
    loader = unittest.TestLoader()
    original = loader.discover(str(FREEZE / 'tests_v2'), pattern='test_pil_v4.py')
    extra = unittest.TestLoader().discover(str(ROOT / 'tests'), pattern='test_release.py')
    buffer = io.StringIO()
    # One historical locator is rebased in memory to the byte-identical bundled workbook.
    # No frozen source or JSON file, reviewer identity, judgment or scoring field is changed.
    with mock.patch.object(preflight, '_json', side_effect=rebased_json_reader), redirect_stdout(buffer), redirect_stderr(buffer):
        result = unittest.TextTestRunner(stream=buffer, verbosity=2).run(unittest.TestSuite([original, extra]))
    (work / 'test_results.txt').write_text(buffer.getvalue(), encoding='utf-8')
    require(result.wasSuccessful(), f'Unit tests failed; see {work.name}/test_results.txt')
    return {'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'original_test_module': 'frozen/prepaid_freeze/tests_v2/test_pil_v4.py', 'release_test_module': 'tests/test_release.py', 'historical_locator_rebinding': 'Translation acceptance accepted_path is rebased in memory to the included workbook after verifying accepted_workbook_sha256; no score or review fields change.'}


def external_output(path):
    """Keep newly generated files outside the evidence release."""
    path = Path(path).resolve()
    release = next((p for p in Path(__file__).resolve().parents
                    if (p / "verify_release.py").is_file()
                    and (p / "RELEASE_MANIFEST.json").is_file()),
                   Path(__file__).resolve().parent)
    if path == release or path.is_relative_to(release):
        raise ValueError("Output must be outside the evidence release")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', '--work-dir', dest='output_dir', type=Path, default=None, help='External output directory; defaults to a new system temporary directory')
    parser.add_argument('--node', default='node', help='Node.js executable name on PATH, or an explicit executable path')
    args = parser.parse_args()
    work = external_output(args.output_dir) if args.output_dir else Path(tempfile.mkdtemp(prefix='pil_review_'))
    if work.exists() and any(work.iterdir()):
        parser.error('Use a new or empty external output directory')
    work.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(work)
    install_offline_guard(work)
    import pil_v4_contract as contract
    import pil_v4_rescore as scorer
    print('Checking original byte identities and all 720 frozen units...', flush=True)
    integrity = verify_sources()
    formal = ROOT / 'frozen/formal'
    entries, schedule, run = jsonl(formal / 'PIL_V41_RUN_LEDGER.jsonl'), read(formal / 'PIL_V41_FORMAL_SCHEDULE.json'), read(formal / 'PIL_V41_RUN_MANIFEST.json')
    historical = read(formal / 'PIL_V41_FORMAL_ANALYSIS.json')
    for name, obj in [('schedule', schedule), ('run', run), ('analysis', historical)]:
        require(canonical({key: value for key, value in obj.items() if key not in {'content_sha256', 'created_at_utc'}}) == obj['content_sha256'], f'{name} content hash mismatch')
    verify_ledger(entries, schedule, run)
    gold = {row['id']: row for row in jsonl(FREEZE / 'data/consensus_gold_v4.jsonl')}
    facts = {row['id']: row for row in jsonl(FREEZE / 'data/inference_dataset_v41_en.jsonl')}
    require(len(gold) == len(facts) == 60 and set(gold) == set(facts), 'Case identities mismatch')
    scorer._validate_balanced_entries(entries, set(gold))
    request_evidence = verify_requests(entries, facts)
    schema, rules = contract.load_schema(), contract.load_rules()
    before = [scorer.score_row(entry, gold[entry['case_id']], schema, rules) for entry in entries]
    require(before == historical['scored_units'], 'Original 720 scores did not reproduce')
    print('Regenerating corrected gold and replaying erratum with the unchanged scorer...', flush=True)
    node = shutil.which(args.node)
    require(bool(node), 'Node.js must be installed and available as node on PATH')
    generated = work / 'corrected_gold_recomputed.jsonl'
    command = [node, str(ROOT / 'corrections/code/correct_gold.mjs'), '--output', str(generated)]
    completed = subprocess.run(command, cwd=work, capture_output=True, text=True, encoding='utf-8')
    require(completed.returncode == 0, f'Corrected gold derivation failed: {completed.stderr}')
    derivation = json.loads(completed.stdout)
    require(generated.read_bytes() == (ROOT / 'corrections/data/consensus_gold_v41_erratum1.jsonl').read_bytes(), 'Regenerated corrected gold differs from retained result')
    corrected = {row['id']: row for row in jsonl(generated)}
    gold_changes = [{'case_id': cid, 'fields': [key for key in set(gold[cid]) | set(corrected[cid]) if gold[cid].get(key) != corrected[cid].get(key)]} for cid in gold if gold[cid] != corrected[cid]]
    require(gold_changes == [{'case_id': 19, 'fields': ['required_evidence']}], 'Unexpected gold changes')
    after = [scorer.score_row(entry, corrected[entry['case_id']], schema, rules) for entry in entries]
    expected = read(ROOT / 'corrections/expected/PIL_V41_ERRATUM1_ANALYSIS.json')
    require(after == expected['scored_units'], 'Erratum scores did not reproduce')
    changed = [{'unit_id': left['unit_id'], 'fields': {key: [left.get(key), right.get(key)] for key in set(left) | set(right) if left.get(key) != right.get(key)}} for left, right in zip(before, after) if left != right]
    require(len(changed) == 12 and all(row['unit_id'].startswith('19|') and row['fields'] == {'evidence_requirement_met': [False, True]} for row in changed), 'Unexpected erratum score changes')
    summary = scorer.summarize(after)
    require(summary == expected['summary'] == historical['summary'], 'Summary or paired statistics did not reproduce')
    print('Binding the three targeted expert findings and running offline regression tests...', flush=True)
    adjudications = read(ROOT / 'expert_supplement/data/EXPERT_ADJUDICATIONS.json')['records']
    joined = review_join.join(entries, after, adjudications)
    require(joined == read(ROOT / 'expert_supplement/expected/EXPERT_REVIEW_JOIN_720.json'), 'Expert association differs from retained supplement')
    tests = run_tests(work)
    report = {'status': 'PASS', 'offline_network_guard': True, 'external_input_guard': True, 'new_model_requests': 0,
              'integrity': integrity, 'frozen_scored_units_reproduced': len(before), 'ledger_chain_verified': True,
              'request_evidence': request_evidence, 'gold_derivation': derivation, 'changed_gold_cases': gold_changes,
              'changed_scored_units': changed, 'summary_and_paired_statistics_reproduced': True,
              'endpoint_counts': joined['contract_endpoint_counts'], 'expert_reviewed_units': joined['reviewed_units'],
              'expert_not_reviewed_units': joined['not_reviewed_units'], 'full_legal_accuracy': joined['full_legal_accuracy'],
              'known_contract_pass_expert_unacceptable': joined['known_contract_pass_expert_unacceptable'],
              'tests': tests, 'runtime': {'python': platform.python_version(), 'node': subprocess.run([node, '--version'], capture_output=True, text=True).stdout.strip(),
              'dependencies': {name: importlib.metadata.version(name) for name in ['jsonschema', 'openai', 'httpx', 'PyYAML']}}}
    (work / 'verification_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'historical_units': 720, 'corrected_gold_cases': 60, 'changed_evidence_flags': 12, 'expert_reviewed': 3, 'expert_not_reviewed': 717, 'endpoint_counts': joined['contract_endpoint_counts'], 'tests': tests['tests_run'], 'new_model_requests': 0}, indent=2), flush=True)

if __name__ == '__main__':
    main()
