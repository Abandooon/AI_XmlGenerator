# Supported commands and expected results

This is the complete active reviewer command list. [Actual executions and result checks](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/COMMAND_AUDIT.md) record each entry. [Manuscript numbers](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/PAPER_DATA_CROSSCHECK.md) are checked against the underlying evidence separately from file integrity.

## Environment and output

Use Python 3.12. Run S01 from the release root; use the resulting `.venv` interpreter for every later `python` command. On Windows it is `.venv/Scripts/python.exe`; on Unix it is `.venv/bin/python`. Activate that environment or substitute its interpreter path. S02 and S03 need package-download access during setup. Evidence checks then run offline and make no model API calls.

PIL requires Node.js 22 or newer, available as `node`. Railway checks require Java 8; native recompilation requires the Java 8 JDK. The commands below use PowerShell's `$env:JAVA8_HOME` variable, which must point to the installed Java 8 JDK. This is an external runtime prerequisite, not a repository material location. The audit supplies and records the actual runtime versions. Do not rely on an unrelated default Java installation. For Unix, substitute the equivalent executable path and shell variable syntax.

Tectonic 0.17.0 is used for P01. Its first build may download its TeX bundle; the audited build used an existing cache with `--offline`. Overleaf users instead upload the [English submission inputs](https://github.com/Abandooon/AI_XmlGenerator/tree/ATLAS/paper/current/english) and select XeLaTeX. No unexecuted XeLaTeX command is advertised as a locally verified check.

Each command gives its working directory relative to the release root. Output paths resolve from that directory and lead outside the release. Use new or empty output directories; railway and Terra require a directory that does not yet exist. Run V05 before V09. F01 and F02 can share their figures directory. If you run V02 and individual entries, they must use separate output directories as shown. Allow several GiB of free space.

PIL verification and both plotting scripts also support omitted output arguments; they create a fresh system temporary directory. They no longer write to retained `verification/latest` or figure folders. Deliberately choosing a location inside the release is rejected. [Boundary regression tests](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/OUTPUT_GUARD_TEST_RESULTS.json) cover all applicable entry points.

<a id="s01"></a>

## S01 · Create the Python environment

Working directory: `.`.

```powershell
python -m venv .venv
```

Expected: A new Python 3.12 environment is created.

<a id="s02"></a>

## S02 · Install pinned review dependencies

Working directory: `.`.

```powershell
python -m pip install -r requirements-lock.txt
```

Expected: All pinned packages install in that environment.

<a id="s03"></a>

## S03 · Install pinned plotting dependencies

Working directory: `.`.

```powershell
python -m pip install -r paper/figure_sources/requirements-plot.txt
```

Expected: Matplotlib 3.11.1 and its dependencies install.

<a id="v01"></a>

## V01 · Verify release file identity

Working directory: `.`.

```powershell
python -B verify_release.py --integrity-only
```

Expected: PASS; every manifest entry has the declared size and SHA-256.

<a id="v02"></a>

## V02 · Review all five experiment packages

Working directory: `.`.

```powershell
python -B verify_release.py --track all --work-dir ../review-output/all --node node --java "$env:JAVA8_HOME/bin/java.exe" --jobs 4
```

Expected: All five tracks PASS; RELEASE_REVIEW_RESULT.json lists each result and log.

<a id="v03"></a>

## V03 · AUTOSAR direct isolated entry

Working directory: `experiments/autosar`.

```powershell
python -I -B review.py --work-dir ../../../review-output/autosar
```

Expected: 60 generation units and 100 repair cells match the frozen results; scoped PASS remains distinct from full-corpus INCOMPLETE.

<a id="v04"></a>

## V04 · Local AUTOSAR–vLLM direct entry

Working directory: `experiments/vllm`.

```powershell
python -B review.py --work-dir ../../../review-output/vllm
```

Expected: 180 requests are checked; structural acceptance is 45/60, 60/60, 60/60; 714 reconstructed ARXML files match the saved bytes.

<a id="v05"></a>

## V05 · Railway direct entry

Working directory: `experiments/railway`.

```powershell
python -B review.py --work-dir ../../../review-output/railway --java "$env:JAVA8_HOME/bin/java.exe"
```

Expected: 891 endpoints, including 888 artifact-bearing endpoints, and the retained statistics are verified.

<a id="v06"></a>

## V06 · Second railway model direct entry

Working directory: `experiments/railway_terra`.

```powershell
python -B review.py --work-dir ../../../review-output/railway_terra --java "$env:JAVA8_HOME/bin/java.exe"
```

Expected: Terra strict-success counts 18/22/22 out of 24 match the retained results.

<a id="v07"></a>

## V07 · PIL direct entry

Working directory: `experiments/pil`.

```powershell
python -B tools/verify.py --output-dir ../../../review-output/pil --node node
```

Expected: 720 units are rescored; composite endpoints are 73/96/101/143 out of 180; contract tests pass.

<a id="v08"></a>

## V08 · Regenerate corrected PIL reference

Working directory: `experiments/pil`.

```powershell
node corrections/code/correct_gold.mjs --output ../../../review-output/corrected_gold.jsonl
```

Expected: 60 reference records are regenerated; the declared Article 6/62 correction affects case 19 only.

<a id="v09"></a>

## V09 · Recompile the retained railway native checker

Working directory: `experiments/railway`.

```powershell
python -B rebuild_native.py --payload ../../../review-output/railway/payload --out ../../../review-output/native-build --javac "$env:JAVA8_HOME/bin/javac.exe"
```

Expected: After V05, 101 retained Java sources compile to 196 matching class files.

<a id="v10"></a>

## V10 · Inspect ICM, actual element binding and ARXML field

Working directory: `.`.

```powershell
python -B inspection/check_icm_evidence.py
```

Expected: PASS; the selected v2 binder output is recomputed; 60 original reports establish 11–24 checked rule objects per task and 24 across the batch.

<a id="v11"></a>

## V11 · Check every plotted count and decoding position

Working directory: `.`.

```powershell
python -B inspection/check_figure_evidence.py
```

Expected: PASS; all 165,066 original event hashes and 516 intervention positions are checked, and Figure 8 counts are recomputed from raw experiment scores.

<a id="v12"></a>

## V12 · Recompute PIL decision flow and test corruption detection

Working directory: `.`.

```powershell
python -B inspection/check_pil_decision_flow.py --self-test
```

Expected: PASS; 720 initial decisions, 62 repairs and final release decisions match; four deliberately altered copies are rejected.

<a id="v13"></a>

## V13 · Compare manuscript data with original evidence

Working directory: `.`.

```powershell
python -B inspection/check_paper_data.py --self-test
```

Expected: PASS for all 19 inventoried tables and 428 specified numerical occurrences, plus rejection of a deliberately altered manuscript number. See the data crosscheck for exact fields, denominators and sources.

<a id="f01"></a>

## F01 · Regenerate Figure 7

Working directory: `.`.

```powershell
python -B paper/figure_sources/scripts/plot_figure7.py --output-dir ../review-output/figures
```

Expected: SVG, PDF, PNG and receipt are written outside the release; all three retained traces of each merged case agree.

<a id="f02"></a>

## F02 · Regenerate Figure 8

Working directory: `.`.

```powershell
python -B paper/figure_sources/scripts/plot_figure8.py --output-dir ../review-output/figures
```

Expected: SVG, PDF, PNG and receipt are written outside the release using the checked counts.

<a id="p01"></a>

## P01 · Compile the English manuscript

Working directory: `.`.

```powershell
python -B inspection/build_paper.py --output-dir ../review-output/paper --tectonic tectonic
```

Expected: Tectonic builds main.pdf and a BUILD_RESULT.json outside the release. Add --offline only when its required bundle and fonts are already cached.

<a id="v14"></a>

## V14 · Check repository navigation

Working directory: `.`.

```powershell
python -B inspection/check_navigation.py
```

Expected: PASS. Current manuscript, response and evidence links resolve inside the published repository tree; source line anchors and Markdown section anchors are valid. No navigation target uses a local drive or a file URL. External publisher URLs are classified separately.

## What PASS means

File integrity, experimental rescoring, event reconstruction and manuscript comparison are separate checks. A successful process exit is accepted only together with its expected report fields. In AUTOSAR, task-scoped acceptance does not turn the saved full-corpus INCOMPLETE status into PASS. The data crosscheck reports the unit and denominator for each manuscript value.

The frozen source snapshots also preserve original development and generation code. They are source evidence, not additional reviewer commands; rerunning paid model generation is not part of this offline workflow. Earlier execution reports retain the commands and output locations used at that time. Their command examples are superseded by this page.
