# Instance-model generation: implementation and experiment evidence

This repository provides code, ICM records, prompts, generation constraints, generated artifacts and offline verification for five experiment tracks.

| Track | Evidence and main result |
| --- | --- |
| AUTOSAR | [Package](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/README.md): 20 requirements × 3 runs; 60/60 accepted bundles; 255/255 ARXML files pass XSD; 85 core and 15 substitution repair cells |
| AUTOSAR–vLLM | [Package](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/README.md): 20 cases × 3 repetitions × three conditions; structural acceptance 45/60, 60/60, 60/60 |
| Railway | [Package](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/README.md): 24 tasks × 3 repetitions; initial generation, self-repair and validation-feedback repair achieve 23, 29 and 51 successes out of 72 |
| Second railway model | [Package](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/README.md): same 24 tasks and one seed; Terra 18/22/22 and Luna 6/8/13 successes out of 24 |
| Private international law (PIL) | [Package](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/pil/README.md): 60 cases × 3 repetitions × four conditions; composite endpoint 73/96/101/143 out of 180 |

## Inspect the materials

| Material | Entry |
| --- | --- |
| Requirements and their design sources | [AUTOSAR provenance](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/AUTOSAR_REQUIREMENT_PROVENANCE_AND_DESIGN.md); [domain evidence map](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md) |
| ICM, extraction, element binding and checks | [ICM evidence guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md) |
| Prompts, schemas, candidate models and serialized artifacts | [Three worked examples](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/examples/README.md); [complete evidence map](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md) |
| Counts, denominators and source records | [Experiment data index](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/EXPERIMENT_DATA.md) |
| Decoding events and railway plots | [Data and plotting scripts](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/README.md) |
| Runnable checks and observed results | [Command list](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md); [execution audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/COMMAND_AUDIT.md) |
| Source identities and export selection | [Provenance](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/PROVENANCE.md); [archive selection](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ARCHIVE_SELECTION.json) |
| English reading guides for retained preparation records | [Documentation language guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ENGLISH_REVIEW_GUIDE.md) |
| Independent railway replay and native recompilation | [Completed audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/review_closure_2026-09-14/RAILWAY_AUDIT.md) |

## Offline verification

The [command list](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md) states the working directory, prerequisites, output location and expected result for each supported command. These checks require no model API calls, model weights, GPU or Neo4j service. New results are written outside the release.

The ATLAS branch contains this tree at its root. The api_rag branch contains the identical export under `paper/atlas-review/`. [Access instructions](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ACCESS.md) provide both branch locations and source download links.

The current tree distributes implementation and experiment evidence. Submission documents are maintained separately. Historical Git commits are retained. Two archives were curated to remove author documents; every retained experimental member preserves its original bytes, as recorded in the archive selection manifest.

Repository-authored code retains its [Apache 2.0 license](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/LICENSE). See [third-party notices](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/THIRD_PARTY_NOTICES.md) for other materials.
