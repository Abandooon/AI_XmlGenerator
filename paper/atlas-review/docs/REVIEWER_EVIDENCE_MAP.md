# Domain evidence index

[Browse the three worked examples directly](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/README.md): selected AUTOSAR and railway originals, and clearly identified PIL views, with per-file hashes and original source locators.

[AUTOSAR-vLLM and railway plotting scripts](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/README.md) read the retained inputs without new model calls. The [experiment data index](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/EXPERIMENT_DATA.md) connects aggregate values to source selectors and verification code.


## Inputs, implementations and results

| Domain and resource | Inspection question | Evidence |
| --- | --- | --- |
| AUTOSAR requirements | Where do the 20 AUTOSAR requirements come from? | [Source/design guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/AUTOSAR_REQUIREMENT_PROVENANCE_AND_DESIGN.md), [case YAML](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/runtime/atlas_autosar_requirements_v3/asw_cases_v3.yaml), [deterministic renderer](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/runtime/atlas_autosar_requirements_v3/render_cases.py) |
| AUTOSAR constraint preparation | How are source constraints linked to metamodel entities and executable checks? | [ICM construction and binding replay](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md), [current 1,085 records and their targets](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/v2/constraints_v2.json), [v2 metamodel binder](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/v2/tools/bind_semantic_targets.py), [selected source and binding record](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/supporting/autosar_constraint_preparation/TPS_SWCT_01519_source_excerpt.json) |
| AUTOSAR periodic-component trace | Which prompt, schema, ARXML and checks belong to the periodic-component example? | [AUTOSAR member index below](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md#autosar-periodic-component-example), [Periodic-runnable source identities](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/data/Fig6_icm_trace_sources.md), [frozen source index](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/frozen_code/CODE_INDEX.json) |
| Local AUTOSAR-vLLM decoding | How are U/G/A prompts, schemas, decoding and outputs connected? | [vLLM guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/README.md), [prompt construction](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/frozen_code/tools/qwen35_prompt_v026.py), [schema compilation](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/frozen_code/tools/compile_qwen35_uga_assets_v026.py), [audit implementation](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/frozen_code/vllm_overlay/overlay/vllm/v1/structured_output/audit.py), [frozen source index](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/FROZEN_CODE_INDEX.json) |
| Railway generation and repair | Which model queries, tasks, repair conditions and actual XMI are checked? | [Railway guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/README.md), [payload member inventory](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/PAYLOAD_MANIFEST.json), [original-XMI scorer](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/corrected/raw_native_score.py), [worked-example members below](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md#railway-relational-repair-example) |
| Railway paired analysis | What do the railway differences and intervals mean? | [Statistical explanation](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/STATISTICAL_ANALYSIS.md), [retained statistical audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/results/train_statistics_audit.json), [statistical replay](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/corrected/replay_statistics.py) |
| Railway second model | Which records support the second-model comparison? | [Terra guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/README.md), [paired tasks](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/paired_tasks.csv), [summary](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/CURRENT_RESULTS_SUMMARY.json), [source index](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/SOURCE_INDEX.json), [archive parts](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/PARTS_MANIFEST.json) |
| PIL inputs and evaluation | Where are PIL facts, prompts, schema, audit and statistical results? | [English facts](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/prepaid_freeze/data/inference_dataset_v41_en.jsonl), [rendered prompts](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/prepaid_freeze/PIL_V41_RENDERED_PROMPTS.jsonl), [schema](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/prepaid_freeze/schema/decision_schema_v4.json), [audit rules](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/prepaid_freeze/rules/delivery_rules_v4.json), [corrected analysis](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/corrections/expected/PIL_V41_ERRATUM1_ANALYSIS.json), [statistical explanation](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/STATISTICAL_ANALYSIS.md) |
| PIL decision repair | Where are the before/after decisions and actual diagnostics? | [Original ledger](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/formal/PIL_V41_RUN_LEDGER.jsonl), unit `8\|p3\|1`; see [selectors below](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md#pil-choice-of-court-example) |
| PIL expert assessments | Where are the targeted expert findings? | [Expert assessments](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/expert_supplement/data/EXPERT_ADJUDICATIONS.json), [field-semantics clarification](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/expert_supplement/protocol/FIELD_SEMANTICS_CLARIFICATION.json), [PIL guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/README.md) |

Formal evaluation inputs are linked in each track: AUTOSAR requirements and component prompts, local decoding cases, railway TaskSpec inputs and PIL scenarios. Domain preparation is documented separately in [ICM_EVIDENCE.md](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md).

## AUTOSAR periodic-component example

Open the [AUTOSAR experiment ZIP](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip). Every member below begins with `AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02/`. The AUTOSAR ZIP and local-vLLM evidence archive were repackaged to exclude author documents; retained experiment members preserve their original bytes. [Archive selection](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ARCHIVE_SELECTION.json) records original and current archive identities and the excluded members.

| Evidence | Member after that prefix |
| --- | --- |
| Requirement specification | `requirements/asw_cases_v3.yaml` — case `ASW-FULL-01` |
| Rendered requirement | `requirements/rendered/prompts/ASW-FULL-01.txt` |
| Run schedule and prompt identities | `requirements/rendered/run_manifest.json` |
| Frozen generation prompt implementation | `code_snapshot/repository/src/llm_generation/llm/prompt_templates.py` |
| Aggregate original generation results | `evidence/formal_v20/generation/experiment_results.json` |

The selected first generation run is under:

```text
evidence/formal_v20/generation/runs/gpt-5.6-luna/ASW-FULL-01/R1/repair-off/attempt-001/
```

Within that run, inspect:

| Evidence | Member relative to the run directory |
| --- | --- |
| Saved component prompt | `atlas_output/debug/round2_prompt_ASW_Com_Full_Baseline_20260902_162842.txt` |
| Processed task plan | `atlas_output/round1_data/round1_20260902_162824.json` |
| Actual component ARXML | `atlas_output/ARXML/Components/ASW_Com_Full_Baseline_8f34364d_1788337723.arxml` |
| Rule bindings and task context | `atlas_output/ARXML/validation_context_8f34364d_1788337723.json` |
| Executed artifact checks | `atlas_output/ARXML/validation_8f34364d_1788337723.json` |
| Independent task evaluation | `independent_evaluation.json` |

For the per-run generation schemas, use [the schema inventory](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/validation/phase2_schema_rows.json) and its recorded paths, rather than an unrelated development example. The [frozen prompt source](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/frozen_code/repository/src/llm_generation/llm/prompt_templates.py), [artifact validator](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/frozen_code/runtime_assets/src/validation/v2/validate_arxml.py) and [task evaluator](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/frozen_code/experiment/evaluate_asw_v3_run.py) are directly browseable copies. The retained generation run and the controlled-damage repair records are separate executions on the same requirement; the linked example index identifies them separately.

## Local AUTOSAR–vLLM prompts, decoding and artifacts

Open the [local decoding evidence archive](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/archives/atlas-vllm-uga-v6-3-4-paper-evidence-20260829.tar.gz). Every member below begins with `atlas_vllm_uga_v6_3_4_formal_b1_evidence_2026-08-29/`.

| Evidence | Member after the prefix |
| --- | --- |
| Formal cases and paired conditions | `FORMAL_SCHEDULE.json` |
| Compiled prompt and schema | `compiled_assets/cases/ASW-MIN-01.json`, fields `prompt`, `schema` and their hashes |
| One saved response | `formal_run_b1/001.json`; its `schedule` identifies ASW-MIN-01, repetition 1, condition U |
| Corresponding component artifact | `formal_postprocess_local_v1/001/ASW_Com_Min_EmergShutdown.arxml` |
| Corresponding artifact and task checks | `formal_postprocess_local_v1/001/validation.json` and `formal_postprocess_local_v1/001/independent_evaluation.json` |
| Recorded decoding intervention | `formal_audit_b1/structured-output-audit-20541.ndjson`; match requests through the schedule and response request IDs |
| Request time and token records | `formal_metrics_b1.ndjson` and individual `formal_run_b1/` records |
| Aggregate analysis and its implementation | `PAPER_ANALYSIS.json` and `analyze_formal_results_v1.py` |

The [frozen source index](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/FROZEN_CODE_INDEX.json) links the schema compiler, prompt builder and modified decoding backend to their archive members. These records belong to the local decoding experiment; the hosted AUTOSAR workflow has its own inputs and artifacts.

## Railway relational-repair example

For `BAL-1-01`, seed `155921`, unit `G0291`, open [railway_evidence_02.zip](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/archives/railway_evidence_02.zip). The relevant member prefix is `frozen/release/paid_formal/units/G0291/`.

| Evidence | Member after that prefix |
| --- | --- |
| Initial actual model | `shared_generation/artifact/model.xmi` |
| Task obligations, structural plan and ICM | `GF/task_spec.json`, `GF/structural_plan.json`, `GF/icm.json` |
| Binding and constraint registry | `GF/binding.json`, `GF/constraint_registry.json` |
| Initial relational diagnostics | `GF/initial.validation.json` |
| Proposed edit and acceptance | `GF/round_01/edit.json`, `GF/round_01/acceptance.json` |
| Repaired actual model and identity map | `GF/final_artifact/model.xmi`, `GF/final_artifact/identity.json` |
| Final task and domain verdict | `GF/independent_final.json` |

The six railway query conditions use official commit `9c76520`. The [query source note](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/supporting/reference_source_recheck/README.md#train-benchmark) identifies `authority/MANIFEST.json`, `authority/SwitchSet.vql` and the frozen query/runtime hashes, including the SwitchSet active condition.

The original query is `frozen/workspace/authority/SemaphoreNeighbor.vql` inside [railway_evidence_05.zip](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/archives/railway_evidence_05.zip). The same archive contains the task compiler at `frozen/workspace/railway_method_v5/task_compiler.py` and prompt construction at `frozen/workspace/formal_runtime/prompts.py`. The formal generation and damage schedules are `G_SCHEDULE.json` and `R_SCHEDULE.json` under `frozen/workspace/railway_formal_v5/outputs/20260908T101621938149Z/`. The [payload manifest](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/PAYLOAD_MANIFEST.json) maps the full task/prompt/source collection and every original member to its archive and SHA-256. Native receipts are retained in [direct_native_receipts.zip](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/results/direct_native_receipts.zip); they are matched using both XMI and identity-file hashes. The identity file maps generated identifiers to task objects and must be paired with the corresponding XMI bytes when checking task obligations.

For the second model, [PARTS_MANIFEST.json](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/PARTS_MANIFEST.json) specifies how four lossless parts reconstruct the original ZIP. The complete result member is `ATLAS_TERRA_SUPPLEMENT/continuation3/run/RESULTS.json`; the [source index](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/SOURCE_INDEX.json) identifies the retained implementation and audit members. Use the supported entry point below to reconstruct the archive.

## PIL choice-of-court example

The [original JSONL ledger](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/frozen/formal/PIL_V41_RUN_LEDGER.jsonl) contains unit `8|p3|1` at line 229. Read `row.parsed_decision`, `row.internal_audit.findings`, `row.repair.decision`, `row.repair.audit` and `row.system_release`. The original JSON response strings are retained in `row.raw_text` and `row.repair.raw_text`.

The initial and repaired fields use `forum_type` and `alternative_forum_types`; the selected court and Article 25/25(1) evidence remain the same. The [corrected analysis](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/corrections/expected/PIL_V41_ERRATUM1_ANALYSIS.json), `scored_units` item with `unit_id=8|p3|1`, records release, reference compatibility and the composite endpoint. The [corrected reference](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/corrections/data/consensus_gold_v41_erratum1.jsonl) has `id=8`. These selectors connect the input, initial decision, diagnostics, repaired decision and final endpoint for the same unit.

## Offline checks

Run from the release root after installing the [pinned dependencies](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/requirements-lock.txt). Use a new output directory outside the release; Python 3.12, Node.js 22 or newer and Java 8 are the documented common configuration.

[Tested commands, working directories and expected results](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md).

Each package guide explains the outputs and its scope. Replay preserves a distinction between successful artifacts and reproduced expected failures. [Statistical analysis](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/STATISTICAL_ANALYSIS.md) explains aggregation, paired comparisons and sensitivity analyses. [Access status](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ACCESS.md) describes branch navigation separately from the offline checks; these commands do not publish the release or call a model.
