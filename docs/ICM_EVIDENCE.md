# ICM construction and an executed field trace

This guide connects Section 3.3 and Appendix A.2 to the metamodel representation, constraint extractor, automatic linker and retained ICM. Section 4.2.2 and Appendix A.4 then follow one source-linked constraint into an actual ARXML artifact and its checks. The [crosswalk](PAPER_ARTIFACT_CROSSWALK.md) gives the corresponding LaTeX labels and reviewer comments.

## Start with the read-only inspection

From the release root, run:

```text
python -B inspection/check_icm_evidence.py
```

The [inspection script](../inspection/check_icm_evidence.py) uses only the Python
standard library. It reads JSON and selected ZIP members, checks the retained
identities and the field trace below, and prints its report. It does not import
the extraction application, call an API, start a database, extract an archive,
build a graph, rerun a validator, or write a result file. Its `PASS` means that the
specified retained evidence agrees; reported XSD and rule outcomes remain the
outcomes recorded by the original run.

## Locate M, C, A, P, and the execution resources

The paper's `I = (M, C, A, P)` is an information model. Its parts are represented
in several files and embedded records, rather than four independently generated
models.

| Part | Inspectable resource and locator | What it establishes |
|---|---|---|
| M: metamodel representation | [Unified metadata with inlines][metadata], for example `groups.TimingEvent` and `groups.RunnableEntity` | Types, properties, inheritance-related information, XML tags and mapping information available to the implementation. `groups.TimingEvent.elements[name=period]` maps `TimingEvent.period` to the `PERIOD` XML element and describes its unit as seconds. |
| C: domain constraint records | [Published constraints][constraints], array element 698, selected by `id == "TPS_SWCT_01519"` | The retained source record, structured semantics, intended uses, verification policy, element targets, and quality flags for this constraint. |
| A: links to metamodel elements | The same record's `targets`; the [selected preparation excerpt][excerpt], `preparation_layers.binding_decisions.jsonl.record` | Resolved class/XML targets, their roles and the binding result. This example includes `RunnableEntity`, `TimingEvent`, `SwcInternalBehavior`, and variants of `AtomicSwComponentType`. The binding record identifies which metamodel entities are associated with the clause. |
| P: source information | The constraint's `source.source`; the [selected source excerpt][excerpt], `normative_source` | Document name, section path, source line, retained original wording and its text hash. The excerpt also records its enclosing retained chapter file's byte hash. |
| Quality and review state | The constraint's `quality`; [publication manifest][publication]; [publication code][publish] | Separate semantic, binding and derived review states. Their exact interpretation and counts are given below. |
| Executable checks | [Validation plan][plan], select `constraint_id == "TPS_SWCT_01519"`; [plan compiler][compiler] | Registered rule, plugin, activation requirements, source hash and implementation metadata. The plan contains 554 configured rules, not 554 rules executed on every task. |
| Retrieval | [Retrieval manifest][retrieval-manifest], [card construction][cards], [retriever][retriever] | A 1,085-card resource and the ranking policy. The retrieval dataset hash is an identity defined by this resource, not the byte hash of `constraints_v2.json`. |
| Trace to one artifact | [Figure 6 data][figure-data], [AUTOSAR frozen archive][archive], and the inspection script | The actual task binding, enhanced schema, ARXML and recorded validation for ASW-FULL-01, repetition 1, with repair disabled. |

The full published constraint file has SHA-256
`d6b4ab4f6b5b29af2dd9007405c4fa626b0b219ca51fed5e720fe0de1a14048d`.
The readable validation plan has SHA-256
`ff719d51316b013051c7814c644b4e79ceeced7a1e210751c121d341f2649e9d`,
matching the plan in the frozen archive used for the example. The retrieval
identity is
`1d5e86347e1a709d2f4529c129fe8b5701759c400c23fb6631194ad95658663d`;
the retained run's validation context carries this same identity.

## Stored publication states

The following table documents the labels stored in the released file. Extraction and metamodel linking are automated, with failed or ambiguous links routed for human resolution. Publication labels record the resulting resource state.

| Dimension | Label | Count |
|---|---|---:|
| `semantic_status` | `curated` | 473 |
| `semantic_status` | `provisional` | 612 |
| `review_status` | `approved` | 472 |
| `review_status` | `needs_review` | 613 |
| `binding_status` | `complete` | 1,052 |
| `binding_status` | `not_applicable` | 30 |
| `binding_status` | `partial` | 2 |
| `binding_status` | `unresolved` | 1 |

In `publish_constraints.py`, the `approved` label is derived by the program when:

1. the semantic curation status is `curated`;
2. binding is `complete` or `not_applicable`; and
3. the combined issues do not contain `formal_rule_planned`.

The publisher first combines curation issues, binding issues, and any issue
arising from a linked implementation that is still planned. The formula is
visible around lines 69–90. The inspection script recomputes it for all 1,085
published records. `approved` is therefore a computed publication label, not a human signature. The publication manifest's source-coverage field measures record inclusion.

`constraint_retriever.py` iterates the available cards and ranks them using
paths, classes, properties, query terms, intended use and importance. Around
lines 75–76, `approved` contributes five extra ranking points. It is not a filter
that excludes `needs_review` cards. A relevant provisional card can therefore
be selected. In the retained example, the validation context actually includes
`TPS_SWCT_01519` among the selected IDs while its ICM record remains provisional.
The selected card and its ranking inputs can be inspected in the retained validation context.

## Preparation implementation

The existing release already contains the earlier extraction implementation.
These files describe the preparation implementation. The published resource and selected source/binding records are separate retained data products; the implementation reference is not an execution log for every record. The [selected excerpt's manifest][excerpt]
records the existing release paths, development-source paths and SHA-256 values
for the principal files; those source and release copies match byte for byte.

| Preparation step | Code and precise entry point | Observable behavior |
|---|---|---|
| Load annotated text and metadata | [Extraction orchestration][extract-main], `main`, around lines 33–45 | Reads the selected document and unified metadata, then invokes context injection. |
| Add metamodel terminology | [Context injector][context], `get_class_info`, `get_enum_literals`, `inject_local_context`, `process_document_for_llm` | Collects class properties, inherited or related properties, enum literals and section context, and adds them to the document input. |
| Build the extraction prompt | [LLM extractor][extractor], `LlmExtractor._build_extraction_prompt`, lines 40–213 | Defines the extraction instruction template and the `extracted_constraints` response: preserve identified clauses, distinguish normative material from examples, and propose target entities and attributes. |
| Specify the earlier output shape | [Extraction configuration][extract-config], `CONSTRAINT_SCHEMA`, lines 122–218 | Defines the earlier extraction response schema; this is distinct from the published v2 constraint-record schema and from an ARXML generation schema. |
| Split input and request candidates | [LLM extractor][extractor], `_split_document_into_chunks` and `extract_constraints_from_block` | Carries section context into chunks and contains the API request code. Inspect it as text; it is not part of the read-only verification command. |
| Check candidate targets | [Linker and validator][linker], `validate_and_link_constraints` | Automatically resolves and checks target classes, properties and enum literals against metadata. Valid links enter the linked collection; missing, ambiguous or incompatible targets enter the issue collection for human resolution. |
| Publish the curated resource | [Publisher][publish] and the [v2 record schema][record-schema] | Combines retained source and binding records with preparation metadata, validates the record structure and derives the publication state. |
| Attach executable behavior | [Plan compiler][compiler] and [validation plan][plan] | Uses registered implementation decisions to attach rule backends, plugins, selectors, parameters and completeness requirements. It does not demonstrate unrestricted natural-language-to-validator synthesis. |

The read-only inspection command accesses these files as data; it does not run extraction. The extraction application and its API configuration are only needed to prepare a new resource.

The added [selected preparation excerpt][excerpt] preserves exactly one record
from each retained source, semantic-curation and binding layer, including source
file hashes and line numbers. It is a selection for review, not a reconstructed
full preparation history. The source line is identical to the wording embedded
in the frozen constraint record and has SHA-256
`6adb7414191c8c584191b0c8c45bc6079de3c68f0353c7d1bda6224b9acf6702`.
Its enclosing retained chapter file has byte SHA-256
`f3af5fb5cfc099ecc676f9558a1d67544056ad6d2e95f60d53682809089bbdc0`.
These are different hash scopes; the current enclosing-file byte hash is not
substituted for a historical build manifest's document hash.

## One concrete field: periodic activation at 10 ms

All execution artifacts below belong to **ASW-FULL-01, repetition 1, repair off**.
The normative rule says that periodic execution requires a TimingEvent with a
desired period and a reference to the runnable. It does not prescribe a universal
10 ms value. The `0.01` seconds value comes from this task.

The members reside in the [frozen AUTOSAR archive][archive]. Its top-level
directory is `AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02/`. Relative to it:

- The task is `requirements/asw_cases_v3.yaml`, case `ASW-FULL-01`.
- The run directory is
  `evidence/formal_v20/generation/runs/gpt-5.6-luna/ASW-FULL-01/R1/repair-off/attempt-001/`.
- The execution plan is
  `code_snapshot/runtime_assets/src/generate_formal_constraints/v2/validation_plan.json`.

Within that run directory, inspect these members in order:

| Step | Member and locator | Retained fact |
|---|---|---|
| Task binding | `atlas_output/round1_data/round1_20260902_162824.json`, `design.component_plan[0].element_design.selections[18]` | The processed plan binds the event's `PERIOD/#TEXT` selection to `"0.01"` and identifies `TE_Com_Full_Baseline`. |
| Schema/mapping | `atlas_output/debug/round2_schema_ASW_Com_Full_Baseline_enhanced_20260902_162833.json`, the `PERIOD` property below | Numeric representation, the XML tag and the event-specific value binding are preserved together. |
| Assembly and serialization | `atlas_output/ARXML/Components/ASW_Com_Full_Baseline_8f34364d_1788337723.arxml` | Declares `RE_Com_Full_Baseline`; `TE_Com_Full_Baseline` references that runnable and contains `<PERIOD>0.01</PERIOD>`. |
| Domain check | `atlas_output/ARXML/validation_8f34364d_1788337723.json`, rule `TPS_SWCT_01519#r1` | `applicable_count=1`, `checked_count=1`, `status=PASS`. |
| Task and artifact checks | `independent_evaluation.json`, `structural_obligations[code=runnable_period]` and `xsd` | Original requested period `0.01` is compared with actual `"0.01"`; the obligation passes and all seven recorded XSD checks pass. |

The exact schema locator is:

```text
properties/APPLICATION-SW-COMPONENT-TYPE/properties/SWC-INTERNAL-BEHAVIOR/
properties/EVENTS/properties/TIMING-EVENT/items/properties/PERIOD
```

The following subtree is copied from that schema; only whitespace is formatted:

```json
{
  "type": "number",
  "x-xml-tag": "PERIOD",
  "x-atlas-instance-value-constraints": [
    {
      "anchors": [
        {"path_index": 2, "short_name": "TE_Com_Full_Baseline"}
      ],
      "value": "0.01"
    }
  ]
}
```

`type` is a JSON Schema restriction. The `x-xml-tag` and
`x-atlas-instance-value-constraints` entries are application mapping metadata,
not standard JSON Schema assertions enforced by an arbitrary backend. The
pipeline uses its retained selection, provider adaptation and materialization
logic to carry these bindings into the artifact. Inspect
[element selection and materialization][selection], including
`project_provider_to_admitted_instances`, `materialize_admitted_provider_payload`
and `materialize_deterministic_values`, and the [XSD serializer][serializer].
The corresponding frozen code is also present under the archive's
`code_snapshot/repository/src/llm_generation/knowledge/element_selection.py`
and `code_snapshot/repository/src/llm_generation/core/xsd_serializer.py`.
The enhanced schema is an intermediate schema with mapping annotations; it must
not be described as the exact submitted provider schema. The same run retains
`round2_schema_ASW_Com_Full_Baseline_provider_20260902_162833.json` in its debug
directory for inspecting that interface separately.

The actual event reference is
`/Components/ASW_Com_Full_Baseline/IB_Com_Full_Baseline/RE_Com_Full_Baseline`,
with `DEST="RUNNABLE-ENTITY"`. The component bytes have SHA-256
`062b4225e558ab0c794421a69af28adef0183188225e0a997dc92bbab33de95f`;
the inspection script checks that the recorded XSD input carries this same hash.
It also reads the runnable declaration, event reference and period directly from
the archived XML and compares the schema and plan bindings with the original
task value.

## Keep the example's four judgments separate

| Judgment | Actual retained state for `TPS_SWCT_01519` | Interpretation |
|---|---|---|
| Normative interpretation in the ICM | `semantic_status=provisional`, `review_status=needs_review`, issue `triage_only_requires_deep_curation` | Further semantic curation remains recorded as necessary. |
| Element binding | `binding_status=complete` | The target names have been linked to the representation. |
| Executable rule configuration | `implementation.status=implemented`, plugin `periodic_runnable_event`, `formal_spec.status=reviewed` | A checking implementation has been registered with an explicit activation contract. This label does not retroactively confirm all source interpretations. |
| This run's result | One applicable and checked target, `PASS`; independent period obligation `PASS` | The configured check and the original task's period obligation passed for this artifact. |

The [periodic-event plugin][plugin] checks event existence, the runnable
reference and a parseable period. Equality to the task's requested period is
checked separately by the [independent task evaluator][evaluator]. The example
therefore demonstrates a trace from a source-linked record and task binding to
actual artifact checks, rather than an extraction-accuracy result.

The configured plan contains 400 Python rules and 154 declarative rules. The
example's artifact profile passes, while `full_corpus_decision` remains
`INCOMPLETE`. Configured rules, applicable rules, executed checks and global
coverage have different denominators. Neither this local pass nor the reported
1,085-record inventory establishes complete AUTOSAR semantic compliance.

[metadata]: ../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/data/unified_metadata_with_inlines.json
[constraints]: ../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/v2/constraints_v2.json
[excerpt]: ../supporting/autosar_constraint_preparation/TPS_SWCT_01519_source_excerpt.json
[publication]: ../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/v2/publication_manifest.json
[publish]: ../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/v2/tools/publish_constraints.py
[plan]: ../experiments/vllm/runtime/AI_XmlGenerator/src/generate_formal_constraints/v2/validation_plan.json
[compiler]: ../experiments/vllm/runtime/AI_XmlGenerator/src/generate_formal_constraints/v2/compile_validation_plan.py
[retrieval-manifest]: ../experiments/vllm/runtime/AI_XmlGenerator/src/llm_generation/knowledge/v2/retrieval_manifest.json
[cards]: ../experiments/vllm/runtime/AI_XmlGenerator/src/llm_generation/knowledge/v2/build_retrieval_cards.py
[retriever]: ../experiments/vllm/runtime/AI_XmlGenerator/src/llm_generation/knowledge/v2/constraint_retriever.py
[figure-data]: ../paper/论文图/Fig6_icm_trace_data.json
[archive]: ../experiments/autosar/frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip
[context]: ../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/context_injector.py
[extractor]: ../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/llm_extractor.py
[extract-config]: ../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/config.py
[extract-main]: ../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/main.py
[linker]: ../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/linker_validator.py
[record-schema]: ../experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/v2/schema/structured_constraint.schema.json
[selection]: ../experiments/vllm/runtime/AI_XmlGenerator/src/llm_generation/knowledge/element_selection.py
[serializer]: ../experiments/vllm/runtime/AI_XmlGenerator/src/llm_generation/core/xsd_serializer.py
[plugin]: ../experiments/vllm/runtime/AI_XmlGenerator/src/validation/v2/value_and_local_plugins.py
[evaluator]: ../experiments/autosar/frozen_code/experiment/evaluate_asw_v3_run.py
