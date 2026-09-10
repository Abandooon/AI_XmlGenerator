"""Negative controls for the reviewer export; no network or model calls."""
import copy
from pathlib import Path
import unittest

from review_join import join
from verify import jsonl, read, verify_ledger
import pil_v4_contract as contract

ROOT = Path(__file__).resolve().parents[1]

class ReviewerExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = jsonl(ROOT / 'frozen/formal/PIL_V41_RUN_LEDGER.jsonl')
        cls.schedule = read(ROOT / 'frozen/formal/PIL_V41_FORMAL_SCHEDULE.json')
        cls.run_manifest = read(ROOT / 'frozen/formal/PIL_V41_RUN_MANIFEST.json')
        cls.scored = read(ROOT / 'corrections/expected/PIL_V41_ERRATUM1_ANALYSIS.json')['scored_units']
        cls.records = read(ROOT / 'expert_supplement/data/EXPERT_ADJUDICATIONS.json')['records']

    def test_ledger_tampering_is_rejected(self):
        changed = copy.deepcopy(self.ledger)
        changed[0]['row']['final_decision']['reasoning'] = 'Different content after publication.'
        with self.assertRaises(ValueError):
            verify_ledger(changed, self.schedule, self.run_manifest)

    def test_ledger_reordering_is_rejected(self):
        changed = list(self.ledger)
        changed[0], changed[1] = changed[1], changed[0]
        with self.assertRaises(ValueError):
            verify_ledger(changed, self.schedule, self.run_manifest)

    def test_expert_judgment_cannot_follow_altered_text(self):
        changed = copy.deepcopy(self.ledger)
        next(row for row in changed if row['unit_id'] == '42|p1|1')['row']['final_decision']['reasoning'] = 'An improved answer.'
        with self.assertRaises(ValueError):
            join(changed, self.scored, self.records)

    def test_duplicate_expert_judgment_cannot_inflate_coverage(self):
        with self.assertRaises(ValueError):
            join(self.ledger, self.scored, self.records + [self.records[0]])

    def test_duplicate_ledger_row_cannot_hide_behind_dictionary_keys(self):
        with self.assertRaises(ValueError):
            join(self.ledger + [self.ledger[0]], self.scored, self.records)

    def test_unreviewed_answers_have_no_imputed_verdict(self):
        result = join(self.ledger, self.scored, self.records)
        self.assertEqual(result['reviewed_units'], 3)
        self.assertEqual(result['not_reviewed_units'], 717)
        self.assertIsNone(result['full_legal_accuracy'])
        self.assertEqual(result['known_contract_pass_expert_unacceptable'], ['42|p1|1'])
        self.assertTrue(all(row['expert_verdict'] is None for row in result['rows'] if row['expert_review_status'] == 'not_reviewed'))

    def test_case19_clarification_does_not_relax_boolean_matching(self):
        gold = next(row for row in jsonl(ROOT / 'corrections/data/consensus_gold_v41_erratum1.jsonl') if row['id'] == 19)
        decision = copy.deepcopy(next(row for row in self.ledger if row['unit_id'] == '19|p3|1')['row']['final_decision'])
        self.assertTrue(decision['conditional_answer'])
        self.assertFalse(contract.score_against_gold(decision, gold).conditional_answer)
        self.assertFalse(contract.score_against_gold(decision, gold).correct)
        decision['conditional_answer'] = False
        self.assertTrue(contract.score_against_gold(decision, gold).correct)

if __name__ == '__main__':
    unittest.main()
