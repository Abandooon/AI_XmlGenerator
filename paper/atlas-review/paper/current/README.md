# Current integrated manuscript

Figures 7 and 8 use English labels; identical repeats in Figure 7(a) are merged by case. [Plotting scripts and input data](../figure_sources/README.md) reproduce both figures.

The [bibliography audit](latex/引用核对/README.md) records official export provenance, the key mapping and checked citation contexts; its [redline](latex/引用核对/引文修改对照.html) shows the five current wording/placement revisions and two bibliography updates.

| Material | Files |
| --- | --- |
| Main text, references and Appendices A–D | [PDF](latex/main.pdf), [LaTeX](latex/main.tex) |
| Bibliography and figure assets | [BibTeX](latex/references.bib), [figures](latex/figures/) |
| Markdown reading copies | [Main text](manuscript.md), [appendix](appendix.md), [chapter sources](chapters/) |
| Paper–artifact–response correspondence | [Crosswalk](../../docs/PAPER_ARTIFACT_CROSSWALK.md), [31-comment response matrix](../REVIEW_RESPONSE_MATRIX.md) |
| Evidence and full calculations | [Evidence map](../../docs/REVIEWER_EVIDENCE_MAP.md), [ICM guide](../../docs/ICM_EVIDENCE.md), [statistical analysis](../../docs/STATISTICAL_ANALYSIS.md) |

Section 4.2 and Appendix A cover AUTOSAR; Section 4.3 and Appendix B cover AUTOSAR–vLLM; Section 4.4 and Appendix C cover railway generation and repair, including the second model; Section 4.5 and Appendix D cover PIL. Worked examples appear in A.4, C.4 and D.3. Railway Table C3 reports main-experiment comparisons; Table C4 reports the second-model results.

The PDF is compiled from `latex/main.tex`, which includes the appendix in the same document. Stable labels such as `sec:method-3-3`, `sec:eval-4-2`, `app:A-2` and `tab:A2` are used by the crosswalk and response matrix. For the build command and required fonts, use the instructions alongside the LaTeX source.

Earlier Word drafts remain in repository history or in the historical source directories listed in [paper/README.md](../README.md). They are not parallel current versions. Repository access and the complete offline archive are described in [ACCESS.md](../../docs/ACCESS.md).
