# Evidence and claim boundaries

Read these boundaries with the [current manuscript](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/current/README.md), [evidence map](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md), [ICM guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md) and [statistical analysis](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/STATISTICAL_ANALYSIS.md). The [crosswalk](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/PAPER_ARTIFACT_CROSSWALK.md) links these results to manuscript labels and reviewer comments.

## AUTOSAR: Section 4.2 and Appendix A

The evaluated workflow combines task analysis, case specifications and the existing interface catalogue, metamodel/constraint queries, structured generation, deterministic assembly, serialization and validation. The original task specification supplies acceptance expectations separately from the generated plan. The result evaluates the complete supported workflow.

The 60 accepted bundles contain 255 ARXML files. The 85 core and 15 substitution repair cells use controlled corruptions of accepted reference artifacts and are reported separately. Artifact, domain and task checks have distinct scopes; the result does not establish complete system deployment conformance or a natural-failure repair rate. The [AUTOSAR package](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/README.md) preserves full replay definitions and historical qualifications.

Constraint extraction and automatic metamodel linking prepare the ICM used by the model-generation workflow. Failed or ambiguous links are resolved during domain preparation. The validation plan configures 554 rules; applicability and execution are recorded per artifact. See [ICM_EVIDENCE.md](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md) for source and implementation navigation.

## AUTOSAR–vLLM: Section 4.3 and Appendix B

U/G/A use matched cases and prompts with the same local model. Structural results are 45/60, 60/60 and 60/60. All 60 audited runs record intervention, totaling 516 of 54,942 evaluable steps. G/A output pairs are byte-identical. The study observes execution of generation constraints and audit overhead; it is distinct from the hosted AUTOSAR workflow. The [package guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/README.md) defines retained trace checks, and [statistical analysis](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/STATISTICAL_ANALYSIS.md) explains the case-level comparison.

## Railway: Section 4.4 and Appendix C

The 24 tasks each have three initial-generation runs. G0/GS/GF strict success is 23/29/51 of 72. Fixed-damage S/V/F results are 129/140/141 of 144; task-obligation faults and correctness preservation form separate sets. Localization adds one net success relative to validation feedback on fixed damage, and its interval includes zero. The [native replay](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/README.md) checks supplied XMI and task obligations, including retained failures.

The second-model supplement uses all 24 tasks and one fixed seed. Terra G0/GS/GF is 18/22/22 of 24; the corresponding Luna subset is 6/8/13. Each Terra repair branch recovers four of its six initial failures, with different final success sets. These descriptive comparisons do not establish a monotonic relationship between model capability and the benefit of validation feedback. See [the supplement](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/README.md), Appendix C.3 and Table C4. Main-experiment statistical comparisons are in Table C3.

## PIL: Section 4.5 and Appendix D

The four conditions each contain 180 results. Composite endpoints are 73/96/101/143; structural validity, delivery validity, release and reference compatibility remain separate measures. P3 includes auditing, one repair attempt, revalidation and release control. Of 62 repairs, 40 recover reference compatibility and are released, while three introduce incompatibility. The gain belongs to the combined procedure.

Reference compatibility checks conclusion, principal forum type, evidence and the conditional flag. It does not fully evaluate free-text legal reasoning. Appendix D.3 demonstrates a type-code correction; D.4 discusses targeted expert findings, including an answer that passes the automatic endpoint but makes an unacceptable specific-court inference. The [PIL package](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/README.md) preserves reference review, scoring correction and expert assessment provenance. Full statistical definitions and sensitivity analyses are in [STATISTICAL_ANALYSIS.md](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/STATISTICAL_ANALYSIS.md).

## Across experiments

Repeated runs do not increase the number of independently authored tasks. Do not pool domains, conditions or endpoint definitions into one success rate. Offline agreement with a retained failure shows that the replay reproduced the recorded verdict, not that the artifact passed. The study supports the reported generation, checking and repair behavior within the defined task sets; it does not measure practitioner productivity or universal semantic correctness.
