# Manuscript, implementation and reviewer evidence

The current submission is the **English integrated manuscript**, including Appendices A–D. Review the response first, follow its links into the manuscript, and then use the evidence and command indexes to check the corresponding implementation and results.

| Review step | Repository entry |
| --- | --- |
| Reviewer concerns and responses | [Response matrix](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/REVIEW_RESPONSE_MATRIX.md); [31-comment source map](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/COMMENT_SOURCE_MAP.md) |
| Current manuscript | [PDF](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/current/english/main.pdf); [LaTeX source](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/current/english/main.tex); [Section, figure and table index](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/current/english/LOCATIONS.md) |
| Paper numbers compared with original experiment records | [Manuscript–data crosscheck](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/PAPER_DATA_CROSSCHECK.md) |
| Every supported review command and its execution result | [Commands](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md); [Command audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/COMMAND_AUDIT.md) |
| Requirements, ICM, prompts, schemas and generated artifacts | [Evidence map](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md); [ICM guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md) |
| Main text, appendix and reviewer-comment correspondence | [Artifact crosswalk](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/PAPER_ARTIFACT_CROSSWALK.md) |
| Three worked examples with directly readable prompts and artifacts | [AUTOSAR, railway and PIL files](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/README.md) |
| Figures 7 and 8, original inputs and replay | [Figure reproduction](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/figure_sources/README.md) |
| Source attribution and access | [Provenance](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/PROVENANCE.md); [Access guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ACCESS.md) |

## Experimental tracks

| Manuscript | Evidence package | Main result |
| --- | --- | --- |
| Section 4.2; Appendix A | [AUTOSAR](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/README.md) | 20 requirements × 3 runs; 60/60 accepted bundles; 255/255 ARXML files pass XSD; repair tests contain 85 core and 15 substitution cells |
| Section 4.3; Appendix B | [AUTOSAR–vLLM](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/README.md) | 20 cases × 3 repetitions × three conditions; structural acceptance 45/60, 60/60, 60/60 |
| Section 4.4; Appendix C | [Railway](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/README.md) | 24 tasks × 3 repetitions; initial generation, self-repair and validation-feedback repair achieve 23, 29 and 51 successes out of 72 |
| Section 4.4.3; Appendix C.3 | [Second railway model](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/README.md) | Same 24 tasks and one seed; Terra 18/22/22 and Luna 6/8/13 successes out of 24 |
| Section 4.5; Appendix D | [Private international law (PIL)](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/README.md) | 60 cases × 3 repetitions × four conditions; composite endpoint 73/96/101/143 out of 180 |

Domain preparation provides the metamodel representation, linked constraints, generation mappings and validators. The generation experiments use those resources to construct and check instance models or structured decisions. The data index distinguishes configuration size, task-level checks, experimental units and repeated runs.

## Offline review

The [Commands](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md) page is the authoritative command list. It includes environment creation, dependency installation, whole-release and individual experiment checks, [ICM guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md) binding, decoding events, [Private international law (PIL)](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/README.md) decision flow, manuscript data, figure plotting, native Java recompilation and manuscript compilation. Each entry states its working directory, prerequisites, output and expected result. [Command audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/COMMAND_AUDIT.md) records the tested commands and outcomes.

Model API calls, GPU access, model weights and a Neo4j service are unnecessary for these evidence checks. All newly generated results go outside the release. Its manifests continue to detect changes to the preserved files after the commands finish.

The ATLAS branch contains this review tree at its root. The api_rag branch contains the identical tree under `paper/atlas-review/`. [Access guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ACCESS.md) provides both links and an anonymous source ZIP download. Original experimental archives remain byte-for-byte unchanged; the review adapters and navigation are maintained separately.

Repository-authored code retains its [Apache 2.0 license](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/LICENSE). See [Third-party notices](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/THIRD_PARTY_NOTICES.md) for other materials.
