# Paper-to-evidence index

This index uses the [current manuscript](../paper/current/manuscript.md) and [current appendix](../paper/current/appendix.md). All file links are relative to this release. Archive-member paths below are literal paths inside the linked archive, not separate files that GitHub can preview before extraction. Original experiment packages are unchanged. No new model calls were made for this revision.

## Paper locations and direct entries

| Paper location | Question | Evidence |
| --- | --- | --- |
| Section 4.2.1; Appendix A.1/Table A1 | Where do the 20 AUTOSAR requirements come from? | [Source/design guide](../paper/sources/AUTOSAR_REQUIREMENT_PROVENANCE_AND_DESIGN.md), [case YAML](../experiments/vllm/runtime/atlas_autosar_requirements_v3/asw_cases_v3.yaml), [deterministic renderer](../experiments/vllm/runtime/atlas_autosar_requirements_v3/render_cases.py) |
| Section 4.2.2; Appendix A.2/Table A2 | How are source constraints linked to metamodel entities and executable checks? | [ICM evidence and extraction/language details](ICM_EVIDENCE.md), [structured records](../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/v2/constraints_v2.json), [constraint links](../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/output/constraints_linked.json) |
| Section 4.2; Appendix A.4; Figure 6 | Which prompt, schema, ARXML and checks belong to the periodic-component example? | [AUTOSAR member index below](#autosar-periodic-component-example), [Figure 6 source identities](../paper/论文图/Fig6_icm_trace_sources.md), [frozen source index](../experiments/autosar/frozen_code/CODE_INDEX.json) |
| Section 4.3; Appendix B/Table B1–B2 | How are U/G/A prompts, schemas, decoding and outputs connected? | [vLLM guide](../experiments/vllm/README.md), [prompt construction](../experiments/vllm/frozen_code/tools/qwen35_prompt_v026.py), [schema compilation](../experiments/vllm/frozen_code/tools/compile_qwen35_uga_assets_v026.py), [audit implementation](../experiments/vllm/frozen_code/vllm_overlay/overlay/vllm/v1/structured_output/audit.py), [frozen source index](../experiments/vllm/FROZEN_CODE_INDEX.json) |
| Section 4.4; Appendix C.1–C.2/Table C1–C2 | Which model queries, tasks, repair conditions and actual XMI are checked? | [Railway guide](../experiments/railway/README.md), [payload member inventory](../experiments/railway/PAYLOAD_MANIFEST.json), [original-XMI scorer](../experiments/railway/corrected/raw_native_score.py), [worked-example members below](#railway-relational-repair-example) |
| Section 4.4.2; Table C3 | What do the railway differences and intervals mean? | [Statistical explanation](STATISTICAL_ANALYSIS.md), [retained statistical audit](../experiments/railway/results/train_statistics_audit.json), [statistical replay](../experiments/railway/corrected/replay_statistics.py) |
| Section 4.4.3; Appendix C.3/Table C4 | Which records support the second-model comparison? | [Terra guide](../experiments/railway_terra/README.md), [paired tasks](../experiments/railway_terra/reports/paired_tasks.csv), [summary](../experiments/railway_terra/reports/CURRENT_RESULTS_SUMMARY.json), [source index](../experiments/railway_terra/SOURCE_INDEX.json), [archive parts](../experiments/railway_terra/PARTS_MANIFEST.json) |
| Section 4.5; Appendix D.1–D.2/Table D1–D3 | Where are PIL facts, prompts, schema, audit and statistical results? | [English facts](../experiments/pil/frozen/prepaid_freeze/data/inference_dataset_v41_en.jsonl), [rendered prompts](../experiments/pil/frozen/prepaid_freeze/PIL_V41_RENDERED_PROMPTS.jsonl), [schema](../experiments/pil/frozen/prepaid_freeze/schema/decision_schema_v4.json), [audit rules](../experiments/pil/frozen/prepaid_freeze/rules/delivery_rules_v4.json), [corrected analysis](../experiments/pil/corrections/expected/PIL_V41_ERRATUM1_ANALYSIS.json), [statistical explanation](STATISTICAL_ANALYSIS.md) |
| Appendix D.3 | Where are the before/after decisions and actual diagnostics? | [Original ledger](../experiments/pil/frozen/formal/PIL_V41_RUN_LEDGER.jsonl), unit `8\|p3\|1`; see [selectors below](#pil-choice-of-court-example) |
| Appendix D.4 | Where are the targeted expert findings? | [Expert assessments](../experiments/pil/expert_supplement/data/EXPERT_ADJUDICATIONS.json), [field-semantics clarification](../experiments/pil/expert_supplement/protocol/FIELD_SEMANTICS_CLARIFICATION.json), [PIL guide](../experiments/pil/README.md) |

Language is recorded by input role: source specifications, authored requirements, extraction instructions, generation/control prompts and comments. The [ICM guide](ICM_EVIDENCE.md) records this distinction. Chinese documentation alone does not establish that a formal model request was Chinese, and a generation template does not identify the model used for prior constraint preparation.

## AUTOSAR periodic-component example

Open the [original AUTOSAR ZIP](../experiments/autosar/frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip). Every member below begins with `AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02/`.

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

For admitted per-run schemas, use [the schema inventory](../experiments/autosar/validation/phase2_schema_rows.json) and its recorded paths, rather than an unrelated development example. The [frozen prompt source](../experiments/autosar/frozen_code/repository/src/llm_generation/llm/prompt_templates.py), [artifact validator](../experiments/autosar/frozen_code/runtime_assets/src/validation/v2/validate_arxml.py) and [task evaluator](../experiments/autosar/frozen_code/experiment/evaluate_asw_v3_run.py) are directly browseable copies. Appendix A.4 distinguishes successful formal generation from an independent controlled-damage repair on the same requirement.

## Railway relational-repair example

For `BAL-1-01`, seed `155921`, unit `G0291`, open [railway_evidence_02.zip](../experiments/railway/archives/railway_evidence_02.zip). The relevant member prefix is `frozen/release/paid_formal/units/G0291/`.

| Evidence | Member after that prefix |
| --- | --- |
| Initial actual model | `shared_generation/artifact/model.xmi` |
| Task obligations, structural plan and ICM | `GF/task_spec.json`, `GF/structural_plan.json`, `GF/icm.json` |
| Binding and constraint registry | `GF/binding.json`, `GF/constraint_registry.json` |
| Initial relational diagnostics | `GF/initial.validation.json` |
| Proposed edit and acceptance | `GF/round_01/edit.json`, `GF/round_01/acceptance.json` |
| Repaired actual model and identity map | `GF/final_artifact/model.xmi`, `GF/final_artifact/identity.json` |
| Final task and domain verdict | `GF/independent_final.json` |

The original query is `frozen/workspace/authority/SemaphoreNeighbor.vql` inside [railway_evidence_05.zip](../experiments/railway/archives/railway_evidence_05.zip). The [payload manifest](../experiments/railway/PAYLOAD_MANIFEST.json) maps the full task/prompt/source collection and every original member to its archive and SHA-256. Native receipts are retained in [direct_native_receipts.zip](../experiments/railway/results/direct_native_receipts.zip); they are matched using both XMI and identity-file hashes. Appendix C.4 explains the identity mapping before displaying the selected XML.

For the second model, [PARTS_MANIFEST.json](../experiments/railway_terra/PARTS_MANIFEST.json) specifies how four lossless parts reconstruct the original ZIP. The complete result member is `ATLAS_TERRA_SUPPLEMENT/continuation3/run/RESULTS.json`; the [source index](../experiments/railway_terra/SOURCE_INDEX.json) identifies the retained implementation and audit members. Use the supported entry point below to reconstruct the archive.

## PIL choice-of-court example

The [original JSONL ledger](../experiments/pil/frozen/formal/PIL_V41_RUN_LEDGER.jsonl) contains unit `8|p3|1` at line 229. Read `row.parsed_decision`, `row.internal_audit.findings`, `row.repair.decision`, `row.repair.audit` and `row.system_release`. The original JSON response strings are retained in `row.raw_text` and `row.repair.raw_text`.

The initial and repaired fields use `forum_type` and `alternative_forum_types`; the selected court and Article 25/25(1) evidence remain the same. The [corrected analysis](../experiments/pil/corrections/expected/PIL_V41_ERRATUM1_ANALYSIS.json), `scored_units` item with `unit_id=8|p3|1`, records release, reference compatibility and the composite endpoint. The [corrected reference](../experiments/pil/corrections/data/consensus_gold_v41_erratum1.jsonl) has `id=8`. These selectors connect Appendix D.3 to the actual records without inventing JSON keys or making a claim about complete legal correctness.

## Offline checks

Run from the release root after installing the [pinned dependencies](../requirements-lock.txt). Use a new output directory outside the release; Python 3.12, Node.js 22 or newer and Java 8 are the documented common configuration.

```sh
python verify_release.py --integrity-only
python verify_release.py --track autosar --work-dir ../review-autosar
python verify_release.py --track vllm --work-dir ../review-vllm
python verify_release.py --track railway --work-dir ../review-railway --java java
python verify_release.py --track railway_terra --work-dir ../review-terra --java java
python verify_release.py --track pil --work-dir ../review-pil --node node
```

Each package guide explains the outputs and its scope. Replay preserves a distinction between successful artifacts and reproduced expected failures. [Statistical analysis](STATISTICAL_ANALYSIS.md) explains aggregation, paired comparisons and sensitivity analyses. [Access status](ACCESS.md) describes branch navigation separately from the offline checks; these commands do not publish the release or call a model.
