/** Portable, offline replay of the audited production requiredEvidence function. */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { matchesProvision } from './evidence_selection.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const packageRoot = path.dirname(root);
const outputArg = process.argv.indexOf('--output');
if (outputArg < 0 || !process.argv[outputArg + 1]) {
  throw new Error('Use node corrections/code/correct_gold.mjs --output PATH; verification supplies a temporary output path.');
}
const source = fs.readFileSync(path.join(root, 'provenance/revised_builder_source.mjs.txt'), 'utf8');
const start = source.indexOf('function requiredEvidence(item) {');
const end = source.indexOf('\nconst inference = []', start);
assert(start >= 0 && end > start, 'Audited requiredEvidence source boundaries not found');
const context = vm.createContext({ matchesProvision, BRUSSELS: 'BRUSSELS_I_BIS', EUTMR: 'EU_TRADE_MARK_REGULATION' });
// Execute this pure function only. Never execute the historical filesystem builder.
vm.runInContext(source.slice(start, end), context, { timeout: 1000 });
const cases = [
  ['Art.6', 'Art.6', true], ['Art.6(1)', 'Art.6', true], ['Art.6(1)(a)', 'Art.6(1)', true],
  ['Art.62(1)', 'Art.6', false], ['Art.41', 'Art.4', false], ['Art.71', 'Art.7', false],
  ['Art.25(10)', 'Art.25(1)', false], ['Art.24(1)', 'Art.24(1)', true],
];
for (const [actual, requested, expected] of cases) assert.equal(matchesProvision(actual, requested), expected);
const rows = fs.readFileSync(path.join(packageRoot, 'frozen/prepaid_freeze/data/consensus_gold_v4.jsonl'), 'utf8').trim().split(/\r?\n/).map(JSON.parse);
const changes = [];
const corrected = rows.map(row => {
  const required = Array.from(context.requiredEvidence({ ...row, evidence: row.accepted_evidence }));
  if (JSON.stringify(required) !== JSON.stringify(row.required_evidence)) changes.push({ case_id: row.id, before: row.required_evidence, after: required });
  return { ...row, required_evidence: required };
});
assert.equal(corrected.length, 60);
assert.deepEqual(changes, [{ case_id: 19, before: ['BRUSSELS_I_BIS:Art.62(1)'], after: ['BRUSSELS_I_BIS:Art.6(1)'] }]);
assert(corrected.every(row => row.required_evidence.every(value => row.accepted_evidence.includes(value))));
fs.writeFileSync(path.resolve(process.argv[outputArg + 1]), corrected.map(JSON.stringify).join('\n') + '\n');
process.stdout.write(JSON.stringify({ boundary_tests: cases.length, cases_regenerated: corrected.length, changes }) + '\n');
