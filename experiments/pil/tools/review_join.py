"""Portable evidence binding; targeted expert findings never impute unreviewed outcomes."""
import hashlib
import json

VERDICTS = {'unacceptable', 'conditionally_acceptable', 'substantively_acceptable_with_label_ambiguity', 'acceptable'}

def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def join(ledger, scored, records):
    raw = {entry['unit_id']: entry for entry in ledger}
    scores = {row['unit_id']: row for row in scored}
    if len(ledger) != 720 or len(scored) != 720 or len(raw) != 720 or len(scores) != 720 or set(raw) != set(scores):
        raise ValueError('Require exactly 720 unique matching original units')
    reviewed = {}
    for record in records:
        uid = record['unit_id']
        if uid in reviewed or uid not in raw:
            raise ValueError('Duplicate or unknown expert unit')
        if record['verdict'] not in VERDICTS:
            raise ValueError('Unknown expert verdict')
        entry = raw[uid]
        if record['ledger_entry_sha256'] != entry['entry_sha256'] or record['final_decision_sha256'] != canonical(entry['row']['final_decision']):
            raise ValueError('Expert judgment does not bind to this original decision')
        reviewed[uid] = record
    rows = [{'unit_id': entry['unit_id'], 'case_id': entry['case_id'], 'arm': entry['arm'],
             'frozen_contract_endpoint': scores[entry['unit_id']]['endpoint_success'],
             'expert_review_status': 'reviewed' if entry['unit_id'] in reviewed else 'not_reviewed',
             'expert_verdict': reviewed.get(entry['unit_id'], {}).get('verdict'),
             'expert_reason': reviewed.get(entry['unit_id'], {}).get('reason')} for entry in ledger]
    return {'schema_version': 'atlas.pil.expert_coverage_join.v1', 'units': 720, 'reviewed_units': len(reviewed),
            'not_reviewed_units': 720 - len(reviewed), 'full_legal_accuracy': None,
            'full_legal_accuracy_status': 'not estimated; targeted review with incomplete coverage',
            'known_contract_pass_expert_unacceptable': [row['unit_id'] for row in rows if row['frozen_contract_endpoint'] and row['expert_verdict'] == 'unacceptable'],
            'contract_endpoint_counts': {arm: sum(row['endpoint_success'] for row in scored if row['arm'] == arm) for arm in ['p0', 'p1', 'p2', 'p3']},
            'rows': rows}
