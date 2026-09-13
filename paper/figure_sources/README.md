# Reproduce Figures 7 and 8

The English figures are generated from the preserved plotting data, without model calls or changes to experimental results. Use the pinned plotting environment and the commands in the shared command list:

[Tested commands, working directories and expected results](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md).

Both scripts also accept `--data` and `--output-dir` as explicit paths and work from any current directory. Fonts are supplied by Matplotlib. Each script writes an editable-text SVG, an embedded-font PDF, a PNG preview and a data check record.

## Input and published output

|Figure|Input|Published image|
|---|---|---|
|7|[Retained decoding events and paired endpoints](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/figure_sources/data/Fig7_vllm_intervention_data.json)|[SVG](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/current/figures/Fig7_vllm_intervention.svg), [PDF](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/current/latex/figures/Fig7_vllm_intervention.pdf)|
|8|[Railway counts and source hashes](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/figure_sources/data/Fig8_railway_results_data.json)|[SVG](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/current/figures/Fig8_railway_results.svg), [PDF](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/current/latex/figures/Fig8_railway_results.pdf)|

Figure 7 retains 20 cases and all 60 source requests. Before merging the three traces for a case, its script requires identical intervention positions, total steps, evaluable steps and intervention counts. One line represents those three identical traces; it is not a newly selected sample. The bottom summary annotations are omitted because the manuscript reports those statistics. The structural-acceptance panel still gives successes out of three runs for each case.

Figure 8 reads all counts and denominators from its input, preserves the three panels and displays successes/denominator above each bar. Bar height represents strict success rate. Necessary model legends remain. [English terminology](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/figure_sources/TERMINOLOGY.md) distinguishes structural acceptance, strict success and LLM comparison.

## Relation to original evidence

The Figure 7 JSON binds the original [local AUTOSAR-vLLM archive](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/archives/atlas-vllm-uga-v6-3-4-paper-evidence-20260829.tar.gz), audit member and per-request results by name and SHA-256. It preserves zero-based intervention positions; plotted positions are `100 * (sample_ordinal + 1) / total_steps`.

Figure 8's source hashes identify the retained main-experiment aggregation and second-model results. [Railway evidence](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/README.md) supports panels (a) and (b). The [second-model guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/README.md) and [paired task table](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/paired_tasks.csv) support panel (c). Historical absolute paths inside the unchanged data JSON identify the original author's files; the plotting scripts do not open those paths.

This directory reproduces the figures from their retained plot inputs. The linked domain review entry points separately verify the underlying original experiment outputs.

The [independent figure checker](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/check_figure_evidence.py) reconstructs the plotted values from original scores and verifies the full retained event stream. Its execution and negative controls are recorded in the [command audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/COMMAND_AUDIT.md). New figures always go outside the release.
