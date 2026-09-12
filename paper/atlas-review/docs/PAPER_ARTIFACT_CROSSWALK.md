# Paper, appendix, artifact and reviewer crosswalk

[Figure reproduction](../paper/figure_sources/README.md) connects Figures 7 and 8 to the retained data and portable plotting scripts. Figure 7(a) merges identical repeats without changing the experiment counts.

The [source recheck](../supporting/reference_source_recheck/README.md) supplies the verified AUTOSAR original-version locators and the fixed Train Benchmark query version used in Appendix C.1 and Table C1.

The [bibliography audit](../paper/current/latex/引用核对/README.md) connects the current numbered references and citation contexts to the downloaded official exports. The [key mapping](../paper/current/latex/引用核对/KEY_MAP.json) and [redline](../paper/current/latex/引用核对/引文修改对照.html) accompany the source.

The [compiled location index](../paper/current/latex/LOCATIONS.md) maps all 80 stable LaTeX labels to their Chinese titles, displayed numbers and exact PDF pages, with direct page links.

Use this index alongside the [integrated manuscript](../paper/current/latex/main.pdf), its [LaTeX source](../paper/current/latex/main.tex), and the [31-comment response matrix](../paper/REVIEW_RESPONSE_MATRIX.md). LaTeX labels remain stable when pagination changes. Each row in the final table gives a route from a reviewer comment to the main text, appendix and the materials defined below.

The main text and Appendices A–D are one document. Full input/output files, source snapshots and detailed analysis remain in the repository. Archive-member names are exact paths inside their linked archive; they are not separate browser links.

## Material routes

| Route | Paper and appendix | Original material | Code or offline entry |
| --- | --- | --- | --- |
| P | Sections 1–3 and 5; domain adaptations in Appendices A, C and D | [Original submission](../paper/sources/ATLAS_原版.tex), [decision letter](../paper/sources/SOSYM-26-00005681_DECISION_LETTER_2026-06-18.txt), [current LaTeX](../paper/current/latex/main.tex), [bibliography](../paper/current/latex/references.bib) | Follow the specific domain route below for implementation evidence |
| A1 | Section 4.2.1; Appendix A.1; Tables 4, A1 | [Requirement provenance](../paper/sources/AUTOSAR_REQUIREMENT_PROVENANCE_AND_DESIGN.md); [20 case specifications](../experiments/vllm/runtime/atlas_autosar_requirements_v3/asw_cases_v3.yaml); [AUTOSAR archive](../experiments/autosar/frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip), members `requirements/rendered/prompts/ASW-FULL-01.txt` and `requirements/rendered/run_manifest.json` after the archive prefix | [Requirement renderer](../experiments/vllm/runtime/atlas_autosar_requirements_v3/render_cases.py); `verify_release.py --track autosar` |
| A2 | Sections 3.2–3.3, 3.6 and 4.2.2; Appendix A.2; Tables 1–3, A2 | [Metamodel representation](../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/data/unified_metadata_with_inlines.json); [ICM records](../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/v2/constraints_v2.json); [selected source/link records](../supporting/autosar_constraint_preparation/TPS_SWCT_01519_source_excerpt.json); [validation plan](../experiments/vllm/runtime/AI_XmlGenerator/src/generate_formal_constraints/v2/validation_plan.json) | [Extraction and automatic linking](ICM_EVIDENCE.md#preparation-implementation); [read-only inspector](../inspection/check_icm_evidence.py); `python -B inspection/check_icm_evidence.py` |
| A3 | Section 4.2.3; Appendix A.3; Tables 5, A3–A4 | [Generation rows](../experiments/autosar/validation/generation_rows.json); [repair rows](../experiments/autosar/validation/repair_rows.json); [original archive](../experiments/autosar/frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip), generation aggregate `evidence/formal_v20/generation/experiment_results.json` after the prefix | [Frozen code index](../experiments/autosar/frozen_code/CODE_INDEX.json); [independent task evaluator](../experiments/autosar/frozen_code/experiment/evaluate_asw_v3_run.py); `verify_release.py --track autosar` |
| A4 | Sections 3.1, 3.5–3.7 and 4.2.2; Appendix A.4; Figure 6 | [Exact task, prompt, schema, ARXML and check members](REVIEWER_EVIDENCE_MAP.md#autosar-periodic-component-example); selected unit `ASW-FULL-01/R1/repair-off/attempt-001`; [field trace](ICM_EVIDENCE.md#one-concrete-field-periodic-activation-at-10-ms) | [Prompt implementation](../experiments/autosar/frozen_code/repository/src/llm_generation/llm/prompt_templates.py); [artifact validator](../experiments/autosar/frozen_code/runtime_assets/src/validation/v2/validate_arxml.py); `verify_release.py --track autosar` |
| B1 | Sections 3.5.2 and 4.3; Appendix B.1; Figures 4, 7 | [Local AUTOSAR–vLLM evidence](../experiments/vllm/archives/atlas-vllm-uga-v6-3-4-paper-evidence-20260829.tar.gz); [prompt/schema/response member paths](REVIEWER_EVIDENCE_MAP.md#local-autosarvllm-prompts-decoding-and-artifacts); [source/member index](../experiments/vllm/FROZEN_CODE_INDEX.json) | [Prompt construction](../experiments/vllm/frozen_code/tools/qwen35_prompt_v026.py); [schema compiler](../experiments/vllm/frozen_code/tools/compile_qwen35_uga_assets_v026.py); [decoding backend](../experiments/vllm/frozen_code/vllm_overlay/overlay/vllm/v1/structured_output/backend_xgrammar.py); `verify_release.py --track vllm` |
| B2 | Section 4.3; Appendix B.2; Figure 7; Tables B1–B2 | [Retained paper evidence](../experiments/vllm/archives/atlas-vllm-uga-v6-3-4-paper-evidence-20260829.tar.gz); [audit and statistics member paths](REVIEWER_EVIDENCE_MAP.md#local-autosarvllm-prompts-decoding-and-artifacts); [recorded review result](../experiments/vllm/validation/REVIEW_RESULT.json) | [Audit implementation](../experiments/vllm/frozen_code/vllm_overlay/overlay/vllm/v1/structured_output/audit.py); [source index](../experiments/vllm/FROZEN_CODE_INDEX.json); `verify_release.py --track vllm` |
| C1 | Section 4.4.1; Appendix C.1; Table C1 | [Payload manifest](../experiments/railway/PAYLOAD_MANIFEST.json); [archive 05](../experiments/railway/archives/railway_evidence_05.zip), including `frozen/workspace/authority/SemaphoreNeighbor.vql`, formal task schedules and TaskSpec inputs | [Railway guide](../experiments/railway/README.md); [original-XMI scorer](../experiments/railway/corrected/raw_native_score.py); `verify_release.py --track railway --java java` |
| C2 | Section 4.4.2; Appendix C.2; Figure 8; Tables C2–C3 | [Recomputed results](../experiments/railway/results/train_recomputed.json); [statistical audit](../experiments/railway/results/train_statistics_audit.json); [native receipts](../experiments/railway/results/direct_native_receipts.zip); [payload manifest](../experiments/railway/PAYLOAD_MANIFEST.json) | [Statistical replay](../experiments/railway/corrected/replay_statistics.py); [statistical definitions](STATISTICAL_ANALYSIS.md); `verify_release.py --track railway --java java` |
| C3 | Section 4.4.3; Appendix C.3; Table C4 | [Paired tasks](../experiments/railway_terra/reports/paired_tasks.csv); [summary](../experiments/railway_terra/reports/CURRENT_RESULTS_SUMMARY.json); [four-part archive manifest](../experiments/railway_terra/PARTS_MANIFEST.json), reconstructed member `ATLAS_TERRA_SUPPLEMENT/continuation3/run/RESULTS.json` | [Source/member index](../experiments/railway_terra/SOURCE_INDEX.json); `verify_release.py --track railway_terra --java java` |
| C4 | Sections 3.7 and 4.4.2; Appendix C.4 | [Archive 02](../experiments/railway/archives/railway_evidence_02.zip), prefix `frozen/release/paid_formal/units/G0291/`; initial XMI, diagnosis, edit and final XMI listed in the [member index](REVIEWER_EVIDENCE_MAP.md#railway-relational-repair-example) | [Original-XMI scorer](../experiments/railway/corrected/raw_native_score.py); `verify_release.py --track railway --java java` |
| D1 | Section 4.5; Appendix D.1; Table D1 | [English scenarios](../experiments/pil/frozen/prepaid_freeze/data/inference_dataset_v41_en.jsonl); [rendered prompts](../experiments/pil/frozen/prepaid_freeze/PIL_V41_RENDERED_PROMPTS.jsonl); [decision schema](../experiments/pil/frozen/prepaid_freeze/schema/decision_schema_v4.json); [legal sources](../experiments/pil/frozen/prepaid_freeze/PIL_V41_ENGLISH_LEGAL_SOURCE_AUDIT.json) | [PIL generation and scoring sources](../experiments/pil/frozen/prepaid_freeze/); [offline verifier](../experiments/pil/tools/verify.py); `verify_release.py --track pil --node node` |
| D2 | Section 4.5; Appendix D.2; Tables 6, D2–D3 | [720 original units](../experiments/pil/frozen/formal/PIL_V41_RUN_LEDGER.jsonl); [delivery checks](../experiments/pil/frozen/prepaid_freeze/rules/delivery_rules_v4.json); [corrected scores](../experiments/pil/corrections/expected/PIL_V41_ERRATUM1_ANALYSIS.json) | [Offline verifier](../experiments/pil/tools/verify.py); [statistical definitions](STATISTICAL_ANALYSIS.md); `verify_release.py --track pil --node node` |
| D3 | Section 4.5; Appendix D.3 | Original ledger unit `8\|p3\|1`; `row.parsed_decision`, `row.internal_audit.findings`, `row.repair.decision`, `row.repair.audit`, `row.system_release`; [exact selectors](REVIEWER_EVIDENCE_MAP.md#pil-choice-of-court-example) | [Corrected reference](../experiments/pil/corrections/data/consensus_gold_v41_erratum1.jsonl), `id=8`; [offline verifier](../experiments/pil/tools/verify.py) |
| D4 | Sections 4.5–4.6; Appendix D.4 | [Targeted expert findings](../experiments/pil/expert_supplement/data/EXPERT_ADJUDICATIONS.json); [field clarification](../experiments/pil/expert_supplement/protocol/FIELD_SEMANTICS_CLARIFICATION.json); [association with stored decisions](../experiments/pil/expert_supplement/expected/EXPERT_REVIEW_JOIN_720.json) | [Expert-record association](../experiments/pil/tools/review_join.py); `verify_release.py --track pil --node node` |

The AUTOSAR ZIP prefix is `AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02/`. The [detailed evidence map](REVIEWER_EVIDENCE_MAP.md) expands the selected run directories and filenames. The root verifier commands above should be run with an output directory outside the release, as shown in the [offline instructions](../README.md#offline-review).

## One route for every reviewer comment

The IDs preserve the previous 31-comment organization. The original wording remains in the decision letter; concern summaries and responses are in the response matrix. A comment may concern several experiments, so its route includes the relevant appendix and materials rather than assigning unrelated evidence to a single location.

| Comment | Main-text LaTeX labels | Appendix and table labels | Material routes |
| --- | --- | --- | --- |
| E-01 | `sec:introduction`, `sec:method`, `fig:1`, `fig:2` | `app:A-4`, `app:C-4`, `app:D-3` | P, A4, C4, D3 |
| E-02 | `sec:method-3-1`, `sec:method-3-8`, `tab:3`, `sec:eval-4-6` | `app:A`, `app:C`, `app:D` | P, A1, C1, D1 |
| E-03 | `sec:eval-4-1`, `tab:4`, `sec:eval-4-4-3` | `app:A-1`, `app:B-1`, `app:C-1`, `app:C-3`, `app:D-1` | A1, B1, C1, C3, D1 |
| E-04 | `sec:method-3-7`, `sec:eval-4-2-3`, `sec:eval-4-4-2`, `sec:eval-4-6` | `app:A-3`, `app:C-2`, `app:C-3`, `app:D-2` | A3, C2, C3, D2 |
| R1-01 | `sec:introduction`, `sec:related`, `sec:method-3-3`, `sec:method-3-5`, `sec:method-3-7` | `app:A-2`, `app:A-4` | P, A2, A4 |
| R1-02 | `sec:eval-4-2`, `sec:eval-4-6`, `tab:5` | `app:A-1` | A1, A3 |
| R1-03 | `sec:eval-4-1`, `sec:eval-4-3`, `sec:eval-4-4-3` | `app:B-1`, `app:C-3`, `tab:C4` | B1, C3 |
| R1-04 | `sec:eval-4-1` | `app:A-1`, `app:B-1`, `app:C-1`, `app:D-1` | A1, B1, C1, D1 |
| R1-05 | `sec:eval-4-2-1`, `sec:eval-4-2-3`, `tab:5` | `app:A-1` | A1, A3 |
| R1-06 | `sec:method-3-5-2`, `sec:method-3-5-3`, `sec:eval-4-3`, `fig:4` | `app:B-1` | A4, B1 |
| R1-07 | `sec:eval-4-3`, `fig:7` | `app:B-2` | B2 |
| R1-08 | `sec:eval-4-3`, `sec:eval-4-6` | `app:B-2`, `tab:B2` | B2 |
| R1-09 | `sec:eval-4-2-3`, `sec:eval-4-4-2`, `sec:eval-4-5`, `tab:5`, `tab:6` | `app:A-3`, `app:C-2`, `app:D-2` | A3, C2, D2 |
| R1-10 | `sec:eval-4-2-3`, `sec:eval-4-4-1`, `sec:eval-4-4-2` | `app:A-3`, `app:C-2` | A3, C2 |
| R1-11 | `sec:method-3-6`, `sec:eval-4-1`, `sec:eval-4-6` | `app:A-2`, `app:A-3`, `app:B-2`, `app:C-2`, `app:C-3`, `app:D-1` | A2, A3, B2, C2, C3, D1 |
| R1-12 | `sec:method-3-1`, `sec:method-3-8`, `sec:eval-4-6`, `sec:conclusion` | `app:C`, `app:D` | P, C1, D1 |
| R1-13 | `sec:eval-4-2-1`, `sec:eval-4-6` | `app:A-1`, `tab:A1` | A1 |
| R2-01 | `sec:eval-4-2-1`, `tab:5` | `app:A-1` | A1, A4 |
| R2-02 | `sec:method-3-3`, `sec:eval-4-2-2`, `fig:6` | `app:A-2`, `app:A-4` | A2, A4 |
| R2-03 | `sec:method-3-3`, `sec:method-3-6`, `sec:method-3-8`, `tab:3` | `app:A-2` | A2 |
| R2-04 | `sec:method-3-2`, `sec:conclusion` | `app:C-1` | P, C1 |
| R2-05 | `sec:method-3-2`, `sec:method-3-5-3`, `sec:method-3-6`, `sec:method-3-8`, `tab:3` | `app:A-2`, `app:C-1`, `app:D-1` | A2, C1, D1 |
| R2-06 | `sec:eval-4-2-1`, `sec:eval-4-2-3`, `tab:5` | `app:A-1` | A1, A3 |
| R2-07 | `sec:method`, `fig:1`, `fig:2`, `fig:3`, `fig:4`, `fig:5` | `app:A-4` | P, A4 |
| R2-08 | `sec:method-3-6`, `sec:eval-4-2-3`, `sec:eval-4-6` | `app:A-2`, `app:C-1`, `app:D-4` | A2, C1, D4 |
| R3-01 | `sec:method-3-1`, `sec:eval-4-2-2`, `fig:1`, `fig:6` | `app:A-4`, `app:C-4`, `app:D-3` | A4, C4, D3 |
| R3-02 | `sec:eval-4-2-1`, `sec:eval-4-4-1`, `sec:eval-4-5` | `app:A-1`, `app:C-1`, `app:D-1` | A1, C1, D1 |
| R3-03 | `sec:eval-4-2-3`, `sec:eval-4-4-2`, `sec:eval-4-5`, `sec:eval-4-6` | `app:A-3`, `app:C-2`, `app:D-2`, `app:D-4` | A3, C2, D2, D4 |
| R3-04 | `sec:method-3-6`, `sec:eval-4-6`, `sec:conclusion` | `app:A-2`, `app:C-2`, `app:D-4` | A2, C2, D4 |
| R3-05 | `sec:method-3-3`, `sec:method-3-5`, `sec:method-3-6`, `tab:1`, `tab:2` | `app:A-2`, `app:A-4` | A2, A4 |
| R3-06 | `sec:method-3-6`, `sec:eval-4-6`, `sec:conclusion` | `app:A-2`, `app:D-1`, `app:D-4` | P, A2, D1, D4 |
