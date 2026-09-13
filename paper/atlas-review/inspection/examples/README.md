# Browse the three worked examples

These are the retained examples used in Appendices A.4, C.4 and D.3. Open the numbered files in each table to follow the task, generation, diagnostics and resulting artifact. [The source map](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/SOURCE_MAP.json) records every full SHA-256, original archive member or ledger line, and extraction/selection operation. Short hashes below identify the corresponding entries.

AUTOSAR and railway files are byte-for-byte copies of the named original archive members. The PIL schema is a byte-for-byte repository-file copy. The other PIL files are explicitly derived views selected from retained JSONL records: JSON objects are formatted for reading, and stored strings are decoded as UTF-8. Their content is preserved, but they are not whole original files or provider transport captures.

## AUTOSAR periodic component

ASW-FULL-01, repetition 1, repair disabled, attempt 1. This successful generation example connects the task and processed plan to the submitted provider schema, saved output, assembled component and final checks. The provider schema and assembled representation are different stages. The separate controlled-damage repair discussed in Appendix A.4 is not represented as a repair of this successful run.

The source-linked constraint itself is already directly available in the [ICM field trace](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md#one-concrete-field-periodic-activation-at-10-ms) and [selected preparation record](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/supporting/autosar_constraint_preparation/TPS_SWCT_01519_source_excerpt.json).

| Step | Open retained file | SHA-256 prefix |
|---|---|---|
| 1 | [Rendered task requirement](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/autosar/01_requirement.txt) | `1b3586d8e6e3df15` |
| 2 | [Processed task plan retained by Phase 1](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/autosar/02_processed_task_plan.json) | `6140a22b53de5c38` |
| 3 | [Retained component provider schema](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/autosar/03_component_provider_schema.json) | `2da28b11a1d26741` |
| 4 | [Retained component provider output](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/autosar/04_component_provider_raw.json) | `ba3754bbda9e2568` |
| 5 | [Component representation after assembly](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/autosar/05_assembled_component_response.json) | `6638de52952694ab` |
| 6 | [Serialized component artifact](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/autosar/06_component.arxml) | `062b4225e558ab0c` |
| 7 | [Recorded artifact and configured-rule checks](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/autosar/07_artifact_validation.json) | `1314e479025e2808` |
| 8 | [Recorded independent task and XSD evaluation](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/autosar/08_independent_evaluation.json) | `2b13e53ef9bfb9f3` |

## Railway relational repair

BAL-1-01, seed 155921, unit G0291, validation-feedback branch GF. The compiled request records contain prompts and schemas; their saved execution status distinguishes them from dispatch receipts. The received response proposes the repair, and the final XMI and independent score show its outcome.

The original XMI uses serialized identifiers. Appendix C.4 explains their correspondence to the task names. The full original identity maps and acceptance record remain locatable through the [railway member index](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md#railway-relational-repair-example).

| Step | Open retained file | SHA-256 prefix |
|---|---|---|
| 1 | [Original task obligations for BAL-1-01](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/railway/01_task_spec.json) | `1418c8461a4a9678` |
| 2 | [Compiled initial generation prompt and schema](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/railway/02_initial_generation_request.json) | `defc9fe0caf4240a` |
| 3 | [Original shared initial model](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/railway/03_initial_model.xmi) | `4288e1112484ac4d` |
| 4 | [Initial relational diagnostics](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/railway/04_initial_validation.json) | `5af4aa6d7173b2a0` |
| 5 | [Compiled repair prompt and output schema](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/railway/05_repair_request.json) | `ec0c98497056c77a` |
| 6 | [Received repair response; text contains the proposed slot update](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/railway/06_repair_response.json) | `80223f84cf261908` |
| 7 | [Model serialized after the selected repair](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/railway/07_repaired_model.xmi) | `b651769f9f28cef2` |
| 8 | [Recorded final independent checks](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/railway/08_independent_final.json) | `26d96504610635a9` |

## PIL choice-of-court decision

Unit `8|p3|1`, original ledger line 229. The initial answer records `forum_type=exclusive`; the deterministic audit reports two field/basis inconsistencies. The retained repair changes the primary type to `agreement`. The selected ledger record contains the final audit and `system_release=true`; both original answer strings are included without rewriting.

The initial prompt is selected from case 8, condition p3, at line 32 of the rendered-prompt file. The source map identifies the precise record and field for every derived view.

| Step | Open retained or selected file | SHA-256 prefix |
|---|---|---|
| 1 | [Selected case-facts record](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/pil/01_case_facts.json) | `4a4dc20e0fae5632` |
| 2 | [Decoded original prompt string](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/pil/02_initial_prompt.txt) | `f8d0aa7138ddba59` |
| 3 | [Original decision schema](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/pil/03_decision_schema.json) | `d753bb5e72d8e3b8` |
| 4 | [Decoded original initial answer string](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/pil/04_initial_answer.json) | `55e3a3014c3749ab` |
| 5 | [Selected initial diagnostic object](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/pil/05_initial_audit.json) | `fc74456fcd862514` |
| 6 | [Decoded original repair prompt string](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/pil/06_repair_prompt.txt) | `c05557cd92016b9d` |
| 7 | [Decoded original repaired answer string](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/pil/07_repaired_answer.json) | `547e67b7879c4202` |
| 8 | [Selected complete ledger record including final audit and release](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/pil/08_selected_ledger_record.json) | `4989b4618d0ea535` |

## Original sources

| Domain | Original repository source | Exact locator |
|---|---|---|
| AUTOSAR | [Frozen evidence ZIP](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip) | Full archive members are listed per file in SOURCE_MAP.json; the selected run is ASW-FULL-01/R1/repair-off/attempt-001. |
| Railway | [Evidence ZIP 02](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/archives/railway_evidence_02.zip) | `frozen/release/paid_formal/units/G0291/` plus each recorded member suffix. |
| PIL | [Original ledger, line 229](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/formal/PIL_V41_RUN_LEDGER.jsonl#L229); [rendered prompt, line 32](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/prepaid_freeze/PIL_V41_RENDERED_PROMPTS.jsonl#L32); [case record, line 8](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/prepaid_freeze/data/inference_dataset_v41_en.jsonl#L8) | The source map gives the record selector, selected field and serialization of each view. |

Selection verification checked all 24 written files against their source bytes or exact selected values and confirmed that original source-file hashes did not change. The existing [tested review commands](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md) provide the complete domain and evidence checks; this convenience index adds no new execution command.
