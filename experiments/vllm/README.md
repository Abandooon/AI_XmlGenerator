# Local vLLM–AUTOSAR V6.3.4 offline review

This is the 180-request local U/G/A decoding-mechanism experiment, separate from AUTOSAR V20's dynamic hosted-model pipeline. It uses finite precompiled contracts. No GPU, model weights, API key or Neo4j instance is needed to inspect or replay the saved outputs.

[Tested commands, working directories and expected results](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md).

Use Python 3.12. The output directory must be empty. The entry point verifies the release assets, extracts each original archive into a separate directory, relocates the frozen runtime, materializes all 180 outputs, invokes the frozen formal verifier and recomputes the frozen statistical analysis. Review approximately 0.6 GiB of uncompressed inputs and outputs. The full four-track command is in the repository README.

## Code and evidence navigation

- `runtime/postprocess_uga_results_v028_relocatable.py`: byte-preserved historical postprocessor. Its original source-path checks and evaluator defaults need the new `review.py` relocation adapter; do not use its old launch instructions as the supported entry point.
- `runtime/AI_XmlGenerator/src/llm_generation/core/xsd_serializer.py`: deterministic JSON-to-ARXML serializer.
- `runtime/AI_XmlGenerator/src/validation/v2/`: frozen artifact validation rules and engine.
- `runtime/atlas_model_probe/evaluate_asw_v3_run.py`: independent evaluator, loaded with package-relative schema and case roots by `review.py` without editing its frozen bytes.
- `archives/*bundle*.tar.gz`: original source assets, compiled-schema preparation, deployment tools and the vLLM audit overlay. After extraction, inspect `bundle/vllm_overlay/overlay/vllm/v1/structured_output/` for actual decoding/audit integration.
- `archives/*paper-evidence*.tar.gz`: original 180 responses, compiled schemas, audit observations, manifests, independent postprocessing, verifier and analysis. A historical paper insert is part of this unchanged archive; it is not the current manuscript.
- The remaining two archives retain the formal server-side and qualification evidence. Qualification records do not enter the formal 180 denominator.
- `frozen_code/` makes 50 original deployment, audit-overlay and analysis source files directly browseable; `FROZEN_CODE_INDEX.json` binds them to their paths in the original bundle.
- `validation/REVIEW_RESULT.json`: measured replay from an independently relocated copy. `RUNTIME_AND_ARCHIVES.json` binds the 576 runtime/config/manifest files and four original archives; the original snapshot manifest covers 572 entries.

## Source identity qualification

The replay checks all 572 retained runtime-tree entries, the original input contract/schedule/compiled asset/result hash chain, and eight of ten individually listed historical source files. Two historical source identities were not packaged: the old rendered `run_manifest.json` and `postprocess_uga_results_v026.py`. Their exact expected hashes and unretained status appear in the replay's `PROVENANCE_QUALIFICATION.json`. They are not needed to execute this verified runtime, and their absence is not silently converted into a complete historical source certificate.

The new adapter redirects only filesystem locations and verifies the retained frozen source bytes before importing them. It disables network connections for materialization and rejects attempts to read the original author data paths. Existing evaluator code, requirements, XSD and `xml.xsd` are supplied locally. No model output is generated or altered.

## Reproduced results and limits

All 180 six-gate verdicts and other postprocess scientific fields match the archive, and all 714 materialized ARXML files are byte-equal to their archived counterparts. U/G/A end-to-end acceptance is 45/60, 60/60 and 60/60. The analyzer reads a separate view containing the newly verified formal result and newly materialized reports. `PAPER_ANALYSIS.json` binds this new result identity; all scientific analysis fields agree with the original. Hashes that bind newly generated validation reports differ because those reports contain relocated paths and timings. The replay records these new identities and the exact separately compared provenance fields, without claiming byte-identical new validation or analysis reports.

G/A outputs and token counts match. The retained audit booleans record 516 bound observations in 54,942 evaluable steps; full historical logits and packed token masks were not retained. Case-level comparison has five improvements, zero worsening and fifteen ties, giving a two-sided sign-test p=0.0625. These results do not establish a statistically significant population effect, V20 model superiority, full AUTOSAR compliance or human productivity improvement.
