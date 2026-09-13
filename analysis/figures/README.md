# Experiment plots and their source data

This directory contains plotting inputs and code for local AUTOSAR-vLLM decoding and railway generation/repair results, plus source records for a periodic-runnable ICM trace. The `Fig6`, `Fig7` and `Fig8` prefixes are retained file identifiers. The inputs and scripts can be inspected without a manuscript or model calls.

## Data and code

| Experiment | Input and source records | Plotting code |
| --- | --- | --- |
| AUTOSAR periodic-runnable trace | [Trace data](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/data/Fig6_icm_trace_data.json), [source locators](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/data/Fig6_icm_trace_sources.md) | Inspect through the [ICM evidence guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md); no renderer is included for this trace. |
| Local AUTOSAR-vLLM decoding | [Intervention and structural-acceptance data](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/data/Fig7_vllm_intervention_data.json) | [plot_figure7.py](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/scripts/plot_figure7.py) |
| Railway generation and repair | [Main and second-model result data](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/data/Fig8_railway_results_data.json) | [plot_figure8.py](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/scripts/plot_figure8.py) |

The [plot-data hashes](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/DATA_SHA256.json) identify the two plotting inputs. [Plot terminology](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/TERMINOLOGY.md) distinguishes structural acceptance, strict success and the LLM comparison.

## Plotting behavior

Use the [pinned plotting dependencies](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/requirements-plot.txt) and the [command guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md). Both scripts accept `--data` and `--output-dir` as explicit paths and work from any current directory. Fonts are supplied by Matplotlib. When run, each script writes an SVG with editable text, a PDF with embedded fonts, a PNG preview and a data check record. Output directories must be outside the repository.

The AUTOSAR-vLLM plot retains 20 cases and all 60 source requests. Before merging a case's three traces, the script requires identical intervention positions, total steps, evaluable steps and intervention counts. One line represents the three matching traces. The structural-acceptance panel still displays successes out of three runs for each case. Aggregate intervention counts are recorded in `Fig7_plot_receipt.json`; they are not repeated as bottom annotations in the plot.

The railway plot reads all counts and denominators from its input. Its three panels show initial generation and repair, controlled-fault repair, and the second-model comparison. Each bar displays successes/denominator; bar height represents strict success rate. Model legends remain visible. Plotting does not re-estimate statistics or change experimental outcomes.

## Connection to original records

The AUTOSAR-vLLM input identifies audit members and per-request results in the [local experiment archive](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/archives/atlas-vllm-uga-v6-3-4-paper-evidence-20260829.tar.gz). It retains zero-based intervention positions; plotted positions are `100 * (sample_ordinal + 1) / total_steps`.

The AUTOSAR and local-vLLM archives were repackaged to exclude author documents. [Archive selection](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ARCHIVE_SELECTION.json) distinguishes original whole-archive hashes from current ones and records the excluded members. Retained experiment members preserve their original bytes. Historical archive identities in the source data therefore refer to the original containers, not the repackaged archive bytes.

The railway input identifies the retained main-experiment aggregation and second-model results. [Railway evidence](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/README.md) supports the generation and controlled-fault panels. The [second-model guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/README.md) and [paired task table](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/paired_tasks.csv) support the LLM comparison. Historical absolute paths inside the data identify their source files; the plotting scripts do not open those paths.

The [independent plot-data checker](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/inspection/check_figure_evidence.py) reconstructs plotted values from the retained scores and verifies the retained event stream. The [command guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md) lists the supported entry points and expected verification results. The domain verification commands separately execute the relevant validators against the experiment outputs.
