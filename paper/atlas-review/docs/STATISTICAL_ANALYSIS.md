# Statistical analysis of the retained experiments

The manuscript appendix contains the primary contrasts and the information needed to read them: Appendix C.2, Table C3 for railway models, and Appendix D.2, Table D3 for PIL decisions. This repository note retains the complete sensitivity analyses and test results. It is part of the reproducibility package, not a separately required manuscript supplement. No new experiment or model call was conducted to prepare this note.

## Units and interpretation

Conditions are paired on the same underlying task or case. Repeated runs are first aggregated within that task or case; they do not create additional independent tasks. Each difference is the first condition minus the second, multiplied by 100 and reported in percentage points (pp).

Resampling retains the paired condition results. Its intervals describe variation under resampling of the observed tasks or cases; they do not establish coverage of arbitrary engineering tasks or legal questions. Grouped sensitivity analyses retain shared layouts or design sources. All comparisons below are retained, including small or inconclusive differences.

## Railway models

These four contrasts use the main gpt-5.6-luna experiment. The natural-generation set contains 24 tasks with three initial generations each (72 starting units). The controlled-damage set contains 24 single-fault models and 24 composite-fault models (12 coupled and 12 concurrent), each repeated three times (144 inputs per repair condition).

Within each task, results are averaged over the relevant repetitions and damage conditions; the 24 task means then receive equal weight. Paired task resampling uses 9,999 draws. The four comparisons allocate the nominal 0.05 error level equally, yielding a nominal marginal percentile interval of 1 - 0.05/4 = 98.75% for each contrast. Resampling the eight layouts provides a sensitivity analysis. These are the retained analysis settings, not a new retrospective choice of comparisons.

| Paired contrast | Difference / pp | Task interval / pp | Layout interval / pp |
| --- | ---: | --- | --- |
| Natural generation: validation-feedback repair minus initial generation | +38.89 | [22.22, 56.94] | [25.00, 51.39] |
| Natural generation: validation-feedback repair minus self-repair | +30.56 | [15.28, 47.22] | [15.28, 44.44] |
| Controlled damage: feedback plus localization minus self-repair | +8.33 | [0.00, 19.44] | [1.39, 20.83] |
| Controlled damage: feedback plus localization minus feedback | +0.69 | [-3.47, 5.91] | [-3.47, 5.56] |

For natural generation, both intervals for each comparison lie above zero. For controlled damage, the localization-versus-self-repair comparison is sensitive to grouping; adding localization to the existing feedback configuration yields a small net difference and both intervals include zero. The compared configurations include their actual feedback, acceptance and stopping policies.

Inspect [the retained statistical audit](../experiments/railway/results/train_statistics_audit.json), [the replay script](../experiments/railway/corrected/replay_statistics.py) and [the railway entry](../experiments/railway/README.md). Original schedules, paired records, generated XMI and source snapshots are in [the numbered evidence archives](../experiments/railway/archives/); the entry explains how to extract and verify them. The second-model study is separate: [paired tasks](../experiments/railway_terra/reports/paired_tasks.csv), [summary](../experiments/railway_terra/reports/CURRENT_RESULTS_SUMMARY.json) and [source index](../experiments/railway_terra/SOURCE_INDEX.json).

## PIL decisions

Each condition contains 60 cases with three repetitions (180 results). The primary composite endpoint requires structural validity, common delivery validity, compatibility with the four reference obligations, and actual release. Reference compatibility alone is a different measure.

The analysis first averages each case's three results under each condition, then calculates paired differences. Case resampling uses 20,000 draws and 95% percentile intervals. Sensitivity analysis resamples 31 shared design-source groups; after groups are sampled, cases remain equally weighted rather than assigning equal weight to groups of different sizes.

Two-sided paired sign tests count improving and worsening cases and exclude ties. Four p values receive Holm correction. The mean-difference intervals are not simultaneously corrected; the sign tests evaluate directions of non-tied case differences. Consequently, an interval above zero and a non-significant adjusted sign test can coexist.

| Paired contrast | Difference / pp | Case 95% interval / pp | Source-group 95% interval / pp | Holm-adjusted p |
| --- | ---: | --- | --- | ---: |
| Retrieval augmentation minus basic prompting | +12.8 | [2.2, 23.3] | [0.6, 25.3] | 0.1459 |
| Structural constraints minus retrieval augmentation | +2.8 | [-3.3, 9.4] | [-3.3, 8.3] | 0.5572 |
| Full checks minus structural constraints | +23.3 | [13.3, 33.9] | [12.3, 35.6] | 0.000540 |
| Full checks minus basic prompting | +38.9 | [27.8, 50.0] | [26.6, 51.3] | 0.00000553 |

The two full-check comparisons pass the adjusted sign tests. The retrieval-only comparison does not, and the isolated structural-constraint increment remains uncertain. This does not change the reported endpoint totals. Within the repair subset, 40 reference-compatibility recoveries and 42 final primary-endpoint successes describe different quantities.

Inspect [the current analysis](../experiments/pil/corrections/expected/PIL_V41_ERRATUM1_ANALYSIS.json), [the formal ledger](../experiments/pil/frozen/formal/PIL_V41_RUN_LEDGER.jsonl), and [the PIL review entry](../experiments/pil/README.md). The entry links the frozen analyzer, inference inputs, reference labels and correction layer.

## Offline reproduction

The root [README](../README.md) supplies the supported offline entry. It can check all five experiment tracks without new model calls. For a focused review, use the railway or PIL track and inspect the resulting statistical report; do not replace a recorded expected failure with a success merely because its replay matches.

```sh
python verify_release.py --track railway --work-dir ../railway-review --java java
python verify_release.py --track pil --work-dir ../pil-review --node node
```

Each output directory must be empty. Java 8 is required for the railway native verifier. The exact release files are identified by the root manifest.
