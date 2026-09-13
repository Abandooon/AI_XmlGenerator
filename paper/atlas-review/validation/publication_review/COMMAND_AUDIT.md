# Executed experiment verification commands

Status: **PASS**. This execution record covers the original 19 entries. The [subsequent railway audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/review_closure_2026-09-14/RAILWAY_AUDIT.md) records another independent railway execution and the added V15 rebuild tests. No model calls were made.

[Commands and prerequisites](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md) · [Execution record](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/COMMAND_AUDIT.json) · [Metric sources](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/EXPERIMENT_DATA.md)

| ID | Check | Result | Evidence |
| --- | --- | --- | --- |
| [S01](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#s01) | Python environment | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/SETUP.json) |
| [S02](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#s02) | Review dependencies | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/SETUP.json) |
| [S03](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#s03) | Plot dependencies | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/SETUP.json) |
| [V01](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v01) | Release identity | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/INTEGRITY.json) |
| [V02](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v02) | Five experiment tracks | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/ALL_TRACKS.json) |
| [V03](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v03) | AUTOSAR | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/AUTOSAR.json) |
| [V04](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v04) | AUTOSAR–vLLM | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/AUTOSAR_VLLM.json) |
| [V05](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v05) | Railway | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/RAILWAY.json) |
| [V06](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v06) | Second railway model | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/RAILWAY_TERRA.json) |
| [V07](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v07) | PIL | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/PIL.json) |
| [V08](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v08) | Corrected PIL reference | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/GOLD.json) |
| [V09](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v09) | Native Java rebuild | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/NATIVE_REBUILD.json) |
| [V10](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v10) | ICM binding | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/ICM.json) |
| [V11](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v11) | Plot source evidence | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/FIGURES.json) |
| [V12](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v12) | PIL decision flow | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/PIL_FLOW.json) |
| [V13](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v13) | Experiment metrics | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/EXPERIMENT_DATA.json) |
| [V14](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v14) | Repository navigation | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/NAVIGATION.json) |
| [F01](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#f01) | Decoding plot | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/FIGURE7_PLOT.json) |
| [F02](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#f02) | Railway plot | PASS | [report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/FIGURE8_PLOT.json) |

Environment setup is documented separately from experiment checks. The existing pinned environment was reused; environment creation and installed dependency resolution were rechecked.

The all-track and individual entry points produce the same scientific fields. [Field comparison](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/ENTRYPOINT_RESULT_COMPARISON.json) records the equality checks. Reports state the file inventory present when their execution began; V01 separately checks the final manifest.

Two archives exclude author documents under the [selection manifest](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ARCHIVE_SELECTION.json). Retained experimental member bytes are unchanged. Their whole-archive hashes therefore differ from the historical originals.

The data check aggregates 332 metrics and identifies sources, selectors, units and denominators. AUTOSAR task-scoped acceptance and full-corpus INCOMPLETE remain distinct.

The previously recorded output-boundary and plot negative-control reports are historical checks; their listed input identities define their scope. Current direct, aggregate, ICM, decision-flow, plot and navigation results are listed above.
