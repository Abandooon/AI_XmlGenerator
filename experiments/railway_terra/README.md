# Railway second-model supplement

The completed study uses gpt-5.6-terra, low reasoning effort, on all 24 predefined railway tasks with seed 104729. Each GS/GF branch shares its own model's G0 artifact and allows at most two repair proposals. Strict success is G0 18/24, GS 22/24, GF 22/24. The same-task, same-seed Luna subset is 6/24, 8/24, 13/24.

Both Terra repair policies recover four of six initial failures and preserve all 18 initial successes. Each has one uniquely successful task. The internally paired, Holm-adjusted p values are 0.25 for GF–G0 and 1 for GF–GS. The study is exploratory: shared templates, one seed and different completion-token caps limit inference. The two models have different initial failure sets, so their conditional recovery proportions do not isolate repair ability.

See [the study report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/RAILWAY_SECOND_MODEL_REPORT_EN.md), [current summary](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/CURRENT_RESULTS_SUMMARY.json), [paired tasks](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/paired_tasks.csv), [received responses](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/received_responses.csv), and [the retained independent audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/%E6%9C%80%E7%BB%88%E7%8B%AC%E7%AB%8B%E5%AE%A1%E8%AE%A1.json). Sixty responses were retained from 62 actual dispatches; two historical outcomes have unknown usage. Known cache-component cost is estimated at USD 1.7906145; conservative client occupancy including unknown reserves is USD 3.9782055, not a provider invoice. The final authorized cap was USD 6. No further model generation is needed for review.

## Reproduce the offline review

Use [V06 in the command list](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v06), which specifies the working directory, external output directory and expected results.

Use Python 3.12 and Java 8. The entry verifies each part, reconstructs the unchanged original ZIP, safely extracts it, checks its 9,433 manifested files, and runs the original independent audit on the saved final XMI. It does not call the generation runner or model API. Reports are written beneath the external work directory. The bundled Windows Python and JDK remain in the original archive for provenance; this entry executes the caller's Python and selected Java 8. Only Windows execution has been qualified.

## Archive and source identities

The original ZIP is 157,646,776 bytes, SHA-256 `3382364e8c94a361a496987633c34b8733086d8e074e77bc46f5b069d5e11a7e`. Four parts of at most 40 MiB preserve every byte; [PARTS_MANIFEST.json](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/PARTS_MANIFEST.json) gives their order, sizes and hashes. No archived scientific source, execution seal, response, budget record, or runtime file was changed by splitting.

The [source index](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/SOURCE_INDEX.json) maps browsable, byte-identical core source copies to archive members. They are excerpts for inspection; execute the complete sealed package through the supplied review entry. Historical partial-stage reports inside the archive retain their original status. The current complete result is `continuation3/run/RESULTS.json`, and the final audit is `review/continuation3/verify_final.py`.

Files under `reports/` are unchanged delivery records, so their original relative paths refer to the reconstructed archive or original delivery context. This README is the current Git entry point. The linked English reading guide explains both Chinese reports and distinguishes historical partial stages from the completed study. Licenses bundled in the archive continue to apply.
