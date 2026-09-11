# Figure 6: source identities and archive navigation

Figure 6 connects one periodic-runnable constraint to its source, ICM record, object binding and executed checks. The run evidence comes from `ASW-FULL-01`, first repetition, with repair disabled. `R` is `RE_Com_Full_Baseline`; `E` is `TE_Com_Full_Baseline`. The full runnable path is `/Components/ASW_Com_Full_Baseline/IB_Com_Full_Baseline/RE_Com_Full_Baseline`.

Read the figure with Section 4.2.2 and Appendix A.2/A.4 of the [current manuscript](../current/README.md), the [ICM evidence guide](../../docs/ICM_EVIDENCE.md) and the [worked-example archive index](../../docs/REVIEWER_EVIDENCE_MAP.md#autosar-periodic-component-example). The standalone normative excerpt is supplied for inspection in this revision; it is not represented as an entire specification chapter included in the historical runtime.

## Directly browseable sources

| Source | Location and selector | SHA-256 |
| --- | --- | --- |
| Normative source excerpt | [Selected source and preparation records](../../supporting/autosar_constraint_preparation/TPS_SWCT_01519_source_excerpt.json), `normative_source.raw_text`; original chapter 7, line 134, section 7.2.3 | Original complete source file: `f3af5fb5cfc099ecc676f9558a1d67544056ad6d2e95f60d53682809089bbdc0`; excerpt identity is recorded separately in the JSON |
| Structured constraint | [constraints_v2.json](../../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/v2/constraints_v2.json), item 698 | `d6b4ab4f6b5b29af2dd9007405c4fa626b0b219ca51fed5e720fe0de1a14048d` |
| Retrieval identity | [retrieval_manifest.json](../../experiments/vllm/runtime/AI_XmlGenerator/src/llm_generation/knowledge/v2/retrieval_manifest.json), `dataset_sha256` | `5415f606091efc22ae9f8e8f7e71c712c4d003c6ce32fa6e253766d17d9b3524` |
| Original case | [Case YAML](../../experiments/vllm/runtime/atlas_autosar_requirements_v3/asw_cases_v3.yaml), lines 303–319, period at line 316 | `3b61eb5926b5646a12f8767524192cd7ed65a39e27a37aa9672277058489e024` |
| Task evaluator | [Frozen evaluator](../../experiments/autosar/frozen_code/experiment/evaluate_asw_v3_run.py), lines 346–370 | `2e5f4dda22b575dbbed7ee7a1d30ca7bfa108c5bb88367205fc5a4596434b383` |

## Original run and checker members

Open the [original AUTOSAR ZIP](../../experiments/autosar/frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip). Its top-level directory is `AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02/`. The selected run prefix after that directory is:

```text
evidence/formal_v20/generation/runs/gpt-5.6-luna/ASW-FULL-01/R1/repair-off/attempt-001/
```

| Run member after that prefix | Selector | SHA-256 |
| --- | --- | --- |
| `atlas_output/round1_data/round1_20260902_162824.json` | `design.component_plan[0].element_design.selections[18]` | `6140a22b53de5c387247d7ab93404495c6d662cdbdf3f58b54eb2741bbd05c0d` |
| `atlas_output/ARXML/validation_context_8f34364d_1788337723.json` | `declared_targets.TPS_SWCT_01519` | `4340bfbc69da58317ca40cca2f40dd42745938ca32125cfe4ed6f69418676f37` |
| `atlas_output/ARXML/Components/ASW_Com_Full_Baseline_8f34364d_1788337723.arxml` | `TIMING-EVENT` named `TE_Com_Full_Baseline` | `062b4225e558ab0c794421a69af28adef0183188225e0a997dc92bbab33de95f` |
| `atlas_output/ARXML/validation_8f34364d_1788337723.json` | `rules[336]` | `1314e479025e2808fd9f14a080327029fb88cec8abc1986056b0474c1af08a80` |
| `independent_evaluation.json` | `structural_obligations[54]` | `2b13e53ef9bfb9f3a76976eda723e35c637633f8ac4d1dc992f3126f095321c9` |

Additional members are relative to the archive's top-level directory, not the run directory:

| Member | Selector | SHA-256 |
| --- | --- | --- |
| `code_snapshot/runtime_assets/src/generate_formal_constraints/v2/validation_plan.json` | `rules[335]` | `ff719d51316b013051c7814c644b4e79ceeced7a1e210751c121d341f2649e9d` |
| `code_snapshot/runtime_assets/src/validation/v2/value_and_local_plugins.py` | lines 349–366 | `39592a74615820f363d947f6ed9c302c15daed0343f18acc3a41d698f2c39d4c` |
| `evidence/formal_v20/generation/experiment_results.json` | `records[39]` | `6b9c0eaa7ae4b0add4b33e4bf70fe00dd863b66c848c377eaa561b3845aa7def` |

## Interpretation

The normative requirement does not prescribe 10 ms; `0.01 s` belongs to this task. The rule checks the event, runnable reference and numeric period, while the task evaluator separately checks the requested value. Source/semantic review status and actual checker execution are distinct; a passed artifact check does not certify extraction accuracy. The retained task plan is a processed plan. This figure does not depict repair; Appendix A.4 separately identifies its controlled-repair example. Broader replay qualifications remain in the [AUTOSAR package guide](../../experiments/autosar/README.md).
