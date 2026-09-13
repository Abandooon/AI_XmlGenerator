# PIL protocol and reference-review records

This English reading guide covers four retained Chinese records: the frozen protocol, the preflight implementation summary, the second-reviewer report, and the joint-adjudication report. The original records and their hashes are unchanged. Their readiness and authorization statements describe the preparation stage, before the completed 720-unit experiment. Current results and runnable review instructions are in the [PIL package](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/README.md) and the [command list](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v07).

## Frozen experiment protocol

Source: [four-condition replication protocol](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/prepaid_freeze/docs/pil_v4_four_arm_replication_protocol.md), dated 2026-09-04. Its historical status was `READY_FOR_PAID_AUTHORIZATION`, with formal generation disabled and no new model calls during preflight.

### Purpose and study population

The study examines layered constraints for shallow structured legal decisions. It does not instantiate the complete AUTOSAR pipeline or its deeply nested XML models. Earlier exploratory results informed the protocol; the record does not claim that all research decisions preceded that exploration.

The preceding three-condition study contains 60 cases, three repetitions and 540 units. Those records remain separate. Five cases later required factual revision, so the old responses cannot be treated as responses to the revised facts. An interrupted later run produced 132 of 720 scheduled units and 136 logical calls; those units were excluded from the formal study.

The dataset contains 60 synthetic scenarios designed by a private-international-law graduate researcher. Two reviewers independently assessed the initial reference judgments, without seeing one another's initial decisions, and subsequently discussed disagreements. At the recorded preparation stage, 51 cases had initial agreement, four were resolved through discussion, and five required revised facts and reconfirmation. The reference set was fixed before formal generation.

The bilingual input review covered 60 cases and 58 provision records. Fifty-four cases and 55 provision records passed unchanged; six cases and three provision records were corrected. No translation issue remained open at the accepted freeze. This language review did not itself replace legal adjudication.

### Inputs, conditions and generation settings

Model input includes case and cluster identifiers, facts, source classifications and connecting factors, but excludes reference answers. Labels distinguish judicial jurisdiction from the administrative competence of EUIPO. Related actions under Article 30 are distinguished from the same-cause proceedings governed by Article 29. Provision identifiers include their legal instrument, so identically numbered articles in different instruments remain distinct.

| Condition | Information and execution |
| --- | --- |
| P0 | Task and common JSON response contract, without retrieved provisions. |
| P1 | P0 plus the top 12 provisions selected by the fixed lexical retriever. |
| P2 | The same main prompt and retrieved provisions as P1, plus provider-side strict JSON Schema. |
| P3 | P2 plus deterministic checks, at most one repair, and release only when the configured checks permit it. |

P1, P2 and P3 use byte-identical main prompts for a given case and repetition. P2 adds the response-format constraint; P3 adds the subsequent checking and repair policy. P0 and P1 responses are parsed with `json.loads`, without a heuristic JSON-recovery step. The experiment does not separately identify the effect of checking and the effect of repair within P3.

The frozen configuration specifies `gpt-5.6-luna-2026-07-09`, low reasoning effort, temperature 1, a 128,000 completion-token limit, a 180-second timeout, and seeds 104729, 130363 and 155921. Seeds are a best-effort provider setting. SDK retries are disabled; the runner permits up to eight transport attempts under its explicit policy. Transport attempts do not add experimental units. The endpoint is identified by a recorded fingerprint.

The common response contract includes the conclusion, forum, forum type, alternative forum, conditional-answer flag, explicit abstention, legal basis, reasoning and missing facts. Retrieval qualification established that at least one required reference provision occurred in the selected set for each of the 60 cases. The provision store and retriever were developed for this case set, so this qualification is not an evaluation on an independent retrieval benchmark.

### Outcomes and analysis plan

The scheduled size is 60 cases × four conditions × three repetitions, or 720 units. The planned contrasts are P1–P0, P2–P1, P3–P2 and P3–P0. The composite endpoint combines the output and delivery contract, actual release, and the frozen reference obligations. It should be read using the precise current definition in the package README, rather than as a comprehensive measure of legal reasoning accuracy.

Additional measures concern strict JSON validity, rule validity, reference compatibility, releases that do not meet the reference obligations, evidence precision/recall/F1, release coverage, repairs and token usage. Paired analysis aggregates the three repetitions within each case. The protocol specifies 20,000 bootstrap samples and a paired sign procedure, with a sensitivity analysis across 31 scenario clusters. The primary analysis retains all scheduled units; an analysis conditional on release is secondary. Results are not pooled with the earlier experiments.

Refusals, truncations, invalid outputs and unreleased answers remain in the scheduled denominator. An infrastructure interruption preserves the completed records and attempt hashes; any continuation follows the recorded policy. The frozen schedule interleaves conditions and repetitions. It contains 240 distinct main prompts, repeated under the three seeds with their hashes retained.

The historical preflight record established readiness to run. It did not constitute authorization to spend or an experimental result. Reviewers should use the completed offline package, not the historical generation commands, to verify the reported outcomes.

## Preflight implementation summary

Source: [implementation summary](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/prepaid_freeze/docs/pil_v4_preflight_implementation_summary.md). This record also precedes the paid experiment.

### Accepted preparation records

The second-reviewer process covered all 60 cases. Joint discussion resolved four cases without changing their facts; five cases underwent a subsequent fact-revision and reconfirmation step. The returned reconfirmation workbook has SHA-256 `5550e771ab515b43ed28dc38418d4b5018090c7f399d1d881a86db525e3f247c`. All five required reconfirmations were present, and the four worksheets' protected content and formulas were preserved.

The accepted revision separates EUIPO from a court-jurisdiction label, distinguishes Article 30 related actions, and incorporates the recorded factual clarifications. It does not alter the 540 earlier responses.

The prepared files comprise the English inference dataset, consensus reference labels, 58 authoritative-provision paraphrases, decision and reference schemas, delivery rules, adjudication records and the reconfirmation evidence. These file identities are retained in the frozen package. Language-equivalence corrections concern cases 8, 16, 47, 48, 49 and 50 and provisions 24(4), 26(1) and 31(2). The accepted language-review workbook has SHA-256 `8f10fcb88a5ceb5e696284282687e04ca8820b5d3a0fce6624327e5e8778b5da`.

### Implemented controls and qualification

The implementation separates the response contract, condition definitions, provider client, schedule, runner, rescoring, preflight checks, authorization records, prompt rendering, audit and a retained-case diagnostic. The top-12 retriever excludes explicitly negated or inapplicable cues according to its fixed rules; all 60 qualification cases retain a required reference provision.

The recorded preflight test sets contained 27 and 38 tests, for 65 passing tests in total. The checked design contains 60 cases, 60 reference records, 58 provision records, 31 scenario clusters and 720 planned units. No reference-label leak or missing required retrieval item was found by those checks. A mismatch with an earlier experiment's environment fingerprint was handled by refusing execution, rather than silently changing the old experiment's configuration.

### Earlier-data diagnostic

The preparation report also rescored the 55 earlier cases whose facts were unchanged, with 165 units per condition. These are historical diagnostics, not outcomes of the subsequent four-condition study.

| Earlier condition | Exact conclusion/type agreement (%) | Set-compatible conclusion/type agreement (%) |
| --- | ---: | ---: |
| Baseline | 57.6 | 75.8 |
| Retrieval | 60.6 | 72.1 |
| Earlier layered condition, recorded as `prism` | 70.9 | 70.9 |

The corresponding differences for the earlier layered condition versus baseline were 13.3 percentage points under exact matching, with a 95% case-bootstrap interval of [−5.5, 32.1], and −4.8 points under set compatibility, with interval [−21.2, 11.5]. These retrospective comparisons assessed conclusion and jurisdiction type, not the later study's unified delivery and evidence endpoint. They were not predictions or replacements for the formal study. At this preparation stage the interface was read-only, the freeze was checked, and paid execution remained disabled pending authorization.

## Independent reference review

Source: [C1 acceptance and inter-reviewer report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/prepaid_freeze/review/PIL_C1_ACCEPTANCE_AND_INTERREVIEWER_REPORT_2026-09-03.md).

The second review was returned by Yirui Wang, a private-international-law graduate researcher, on 2026-09-02. Its workbook SHA-256 is `e1aacf700b552fee1167b59e7feb0e20f0fe64636b2069f63db25b630449a8f4`. All 60 case identifiers, their order, protected facts and column headers were preserved; no formula error was found. The source review marked 54 cases as passing and six as requiring revision or clarification against the official sources.

For comparison, abstention and referral to domestic law were normalized to the `none` forum type where specified. An initial `special_or_general` label was expanded to the set `{special, general}` only for the set-compatibility comparison.

| Reference component | Agreement | Cohen's kappa |
| --- | ---: | ---: |
| Conclusion | 58/60 (96.7%) | 0.941 |
| Forum type | 56/60 (93.3%) | 0.918 |
| Accepted-type set | 58/60 (96.7%) | Not calculated |
| Insufficient-facts judgment | 54/60 (90.0%) | 0.763 |

Two substantive disagreements and seven priority or information-sufficiency issues formed nine items for joint discussion. These figures describe agreement in constructing the references. They do not measure a model improvement or independent agreement on every generated free-text answer.

## Joint adjudication and fact reconfirmation

Source: [C2 acceptance summary](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/prepaid_freeze/review_sources/C2/PIL_C2_ACCEPTANCE_SUMMARY.md).

The accepted return has SHA-256 `9477e31c0eed765e38fe7d3a5a08fd25d5b1991ffaf37a3a579da063b6c3df19`. All nine discussion items were jointly confirmed; protected facts and formulas remained intact. An additional suggestions worksheet was retained without directly overwriting the reference labels.

Four cases could keep their existing facts. Cases 19, 34, 44, 53 and 55 required revised wording followed by reconfirmation by the original reviewers. In particular, case 34 separates EUIPO's administrative role, and case 44 concerns Article 30 related actions. The C2 decisions were not applied as final input changes before that reconfirmation step. The accepted D1 record described above closes this preparation sequence.

## Retained derivation source

The [revised legacy builder](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/corrections/provenance/revised_builder_source.mjs.txt) contains historical Chinese comments and source data. It is retained as text because the corrected derivation extracts only its audited pure `requiredEvidence` function. The full authoring script is not the public execution entry point. The [portable correction module](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/corrections/code/correct_gold.mjs) and [V08 instructions](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v08) are the current English entry points. Translating strings inside that retained source would change the evidence consumed by the correction check.
