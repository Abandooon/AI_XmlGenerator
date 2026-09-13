# Manuscript and evidence alignment

The [integrated manuscript](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/current/english/main.pdf), [31-comment response matrix](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/REVIEW_RESPONSE_MATRIX.md) and [artifact crosswalk](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/PAPER_ARTIFACT_CROSSWALK.md) share one set of section and table references.

| Item | Paper location | Material to inspect |
| --- | --- | --- |
| Requirement origins and generation inputs | Section 4.1; Appendices A.1, B.1, C.1 and D.1 | [Requirement source guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/sources/AUTOSAR_REQUIREMENT_PROVENANCE_AND_DESIGN.md), [evidence map](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md) |
| Automatic extraction and metamodel linking | Section 3.3; Appendix A.2 | [Context injection, extraction and linker entry points](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md#preparation-implementation) |
| Checker construction and task-dependent execution | Section 3.6; Sections 4.2.2 and 4.4.1; Appendix A.2 | [ICM and executable field trace](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md), [railway native checks](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/README.md) |
| Generation and repair examples | Appendices A.4, C.4 and D.3 | [Exact archive members and record selectors](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md) |
| Main comparisons and second model | Section 4.4; Tables C3–C4 | [Statistical analysis](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/STATISTICAL_ANALYSIS.md), [second-model records](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/README.md) |
| PIL decisions and targeted expert findings | Section 4.5; Appendix D.2–D.4 | [PIL records](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/README.md) |

Constraint extraction and linking belong to domain preparation. The formal AUTOSAR generation results concern instance models produced using the prepared resources. Failed or ambiguous links are routed to human resolution. Custom checkers are developed with human interpretation and LLM assistance; XSD, EMF and VIATRA provide the reused native validation capabilities.

The 554-rule validation plan is a configuration inventory. Applicable and executed checks are recorded per artifact. The original task supplies acceptance requirements separately from the generated plan. AUTOSAR controlled repairs, railway natural-generation repairs and PIL decision repairs retain their own denominators and endpoint definitions.

Original records and previous executed verification reports remain under [validation](https://github.com/Abandooon/AI_XmlGenerator/tree/ATLAS/validation) and the experiment packages. Each report identifies the files and execution it covers. The [current execution audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/COMMAND_AUDIT.md) records the supported commands and their results; Git identifies the published branch commits.
