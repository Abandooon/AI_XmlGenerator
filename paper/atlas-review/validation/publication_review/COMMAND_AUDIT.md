# Executed reviewer commands and result consistency

Status: **PASS**. The complete active command list contains 20 entries. Each was executed using the stated dependencies. All checks use preserved experiment evidence; no new model generation was performed.

[Commands and prerequisites](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md) · [Machine-readable execution record](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/COMMAND_AUDIT.json) · [Paper–data crosscheck](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/PAPER_DATA_CROSSCHECK.md)

| ID | Check | Result | Execution evidence |
| --- | --- | --- | --- |
| [S01](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#s01) | Python environment | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/SETUP.json) |
| [S02](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#s02) | Pinned review packages | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/SETUP.json) |
| [S03](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#s03) | Pinned plotting packages | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/SETUP.json) |
| [V01](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v01) | Release file identity | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/INTEGRITY.json) |
| [V02](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v02) | Five-track offline check | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/ALL_TRACKS.json) |
| [V03](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v03) | AUTOSAR isolated direct entry | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/AUTOSAR.json) |
| [V04](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v04) | AUTOSAR–vLLM direct entry | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/AUTOSAR_VLLM.json) |
| [V05](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v05) | Railway direct entry | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/RAILWAY.json) |
| [V06](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v06) | Terra direct entry | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/RAILWAY_TERRA.json) |
| [V07](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v07) | PIL direct entry | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/PIL.json) |
| [V08](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v08) | PIL corrected reference | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/GOLD.json) |
| [V09](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v09) | Native Java rebuild | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/NATIVE_REBUILD.json) |
| [V10](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v10) | ICM binding and field check | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/ICM.json) |
| [V11](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v11) | Original figure evidence | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/FIGURES.json) |
| [V12](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v12) | PIL decision flow and negative controls | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/PIL_FLOW.json) |
| [V13](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v13) | Manuscript numerical crosscheck | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/PAPER_DATA.json) |
| [V14](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v14) | Repository navigation | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/NAVIGATION.json) |
| [F01](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#f01) | Figure 7 plotting | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/FIGURE7_PLOT.json) |
| [F02](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#f02) | Figure 8 plotting | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/FIGURE8_PLOT.json) |
| [P01](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#p01) | English manuscript compilation | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/BUILD_RESULT.json) |

The all-track report retains the inventory present when that run began. The final release also includes this audit and the navigation records; V01 separately verifies the delivered file set.

The complete-release and direct-entry executions produced identical scientific result fields for all five tracks. [Field comparisons](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/ENTRYPOINT_RESULT_COMPARISON.json) distinguish those values from elapsed times and relocated output paths.

The manuscript check covers all 19 tables by category and 428 specified numerical occurrences, derived from 332 metrics. It also rejects an altered manuscript token count. The [PDF check](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/PDF_QA.json) verifies the 38-page manuscript, 33 bibliography entries, 80 labels and 135 internal links.

The default PIL and figure commands were rerun and left retained evidence unchanged. [Output-boundary tests](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/OUTPUT_GUARD_TEST_RESULTS.json) exercised 10 unique entry points and a PIL argument alias. All 11 rejected a release-internal output directory. Fourteen original archives or parts retained the same SHA-256 hashes.

[Figure negative controls](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/FIGURE_NEGATIVE_CONTROLS.json) reject a changed decoding position and changed Terra bar count. The [PIL flow check](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/PIL_FLOW.json) rejects four altered decision/repair records. [Navigation self-tests](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/NAVIGATION_SELF_TESTS.json) reject missing files, invalid anchors and local filesystem targets.

AUTOSAR task-scoped PASS and full-corpus INCOMPLETE remain separate report fields. Recorded graph-context counts are not a fresh Neo4j reconstruction. The native rebuild recompiles retained Java sources, while the independent experiment checks operate on the preserved model artifacts. These distinctions define what each successful command establishes.

[Bibliography compatibility corrections](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/supporting/bibliography_compatibility/README.md) remove malformed publisher-export markup and restore printed locators without changing the 33 citation keys.
