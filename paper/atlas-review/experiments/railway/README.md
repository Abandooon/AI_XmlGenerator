# Railway V5: offline reviewer package and raw-XMI scoring correction

Query source/version: Appendix C.1 and Table C1 use the six VIATRA queries from official Train Benchmark commit `9c76520`. SwitchSet includes `Route.active(route, true)`. The [source note](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/supporting/reference_source_recheck/README.md#train-benchmark) provides the full commit, official query and frozen-member locators.

This package preserves the completed Railway V5 formal evidence and provides a corrected, portable offline scoring entry point. It makes **no model/API requests**. Original evidence and source bytes are retained under `frozen/` inside the numbered ZIP files; corrected reviewer code is separate in `corrected/`.

Requirements: **Python 3.10 or newer**, standard library only, and **Java 8** on your PATH. No pip packages, network downloads, Gradle, database, or model credentials are needed for the review. Allow approximately 450 MB of temporary disk space. All five numbered ZIP files must remain in `archives/`.

From this directory, run:

[Tested commands, working directories and expected results](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md).

The work directory must not already exist. Use `--java /path/to/java` when Java 8 is not your default Java; on Windows quote paths containing spaces. Omit `--work-dir` to use a newly allocated temporary directory. The package may be moved to another location. Paths in historical logs are preserved as evidence, but the reviewer entry point does not use the original author's paths, machine configuration, credentials, or running services.

The command verifies archive and per-file SHA-256 hashes, extracts into the selected work directory, directly executes EMF/VIATRA against all **139 distinct original XMI + identity byte pairs**, and scores all **891 endpoints**. It also checks 747 queue actions, replays retained semantic assignments and typed edits, verifies all **1,074 received responses** against their raw HTTP blobs, reconciles transport recovery, and recomputes the reported four finite-case sensitivity contrasts. Fresh results appear in `railway-review-output/results/REVIEW_RESULT.json` and the accompanying per-check JSON files. A nonzero exit or `FAIL` means a discrepancy or a missing requirement; it is not silently converted into a success.

## The defect and correction

The historical `railway_method_v5/independent_score.py` parsed the supplied XMI into a Python projection and passed that projection to an adapter which serialized a new XMI before native validation. A malformed namespace/type reference could therefore be repaired by reserialization before the supposed independent check.

`corrected/raw_native_score.py` now calls the native verifier on the **actual supplied XMI and identity files first**. It binds both input SHA-256 hashes before and after execution and rejects changes. It never invokes an XML serializer. Only the native EObject projection is used for subsequent independently written relational queries, public task obligations and protected-field checks. The regression changes the root/declared prefix to `q` while leaving `xsi:type="railway:Segment"` with an undefined prefix; actual EMF loading and the corrected scorer must reject it.

Historical freezes remain unchanged. The correction is an additional offline review layer, not a rerun of the original model experiment. The completed reviewer test and exact changes against historical outcomes are recorded in `PACKAGE_STATUS.json` and `results/`. The 139-pair agreement count includes expected semantic failures; it does **not** mean that all 139 models are strictly successful.

## Expected historical endpoint totals

| Cohort | G0 or S | GS or V | GF or F |
|---|---:|---:|---:|
| G | 23/72 | 29/72 | 51/72 |
| R | 129/144 | 140/144 | 141/144 |
| T | 67/72 | 69/72 | 72/72 |
| CLEAN | 9/9 | 9/9 | 9/9 |

There are 888 artifact-bearing endpoints and three endpoints without an artifact, caused by one initial assignment rejection and its two downstream branches. There are 72 shared initial generations, not 891 independent initial generations. Of 48 materialized failing initial models, GF repairs 28 and GS repairs six. CLEAN measures preservation and is not a repair-success denominator; T is reported separately from fixed-damage R.

The cohort comprises 24 author-designed, development-exposed tasks with one template ancestor. It supports executable bounded MDE artifact transfer and repair within this cohort. It does not establish blind or cross-template generalization, unrestricted natural-language TaskSpec extraction, railway operational safety, or practitioner productivity. R's F−V contrast is only 0.69 percentage points, with a finite-case sensitivity interval of [-3.47, 5.91]; it does not establish a robust advantage of localized F over validation-feedback V. S/V/F differ in acceptance and stopping policies and are not a factorial isolation of each component.

The recovery lineage contains **1,085 physical send intents, 1,074 unique received responses and 11 attempts with unknown usage**. Unknown usage is not zero; billing is incomplete. Send intent does not establish that the server completed or billed that attempt. Local hash consistency and replay do not authenticate a provider's internal model deployment or an external billing statement.

## Contents and provenance

- `PAYLOAD_MANIFEST.json`: archive hashes, every extracted file hash and origin, and explicit exclusions.
- `archives/railway_evidence_*.zip`: original formal results/HTTP evidence, paired exports, frozen protocol and source, required formal task inputs, recovery-lineage journals, native runtime and source.
- `corrected/`: repaired raw-input scorer and portable evidence, queue, transport and statistics replay scripts.
- `SECRET_SCAN.json`: scan paths and classification, without credential values. The two retained findings are explicit synthetic credentials in no-network unit tests. Actual local credential/configuration files are not included.
- `native/lib/` after extraction: all separate frozen runtime JARs. They must remain separate because EMF/Eclipse bundles contain colliding resource names; this is not a flattened fat JAR.
- `native/source/`: frozen runner/matcher/build sources and the 28 existing generated model Java sources recovered from the original execution workspace. The latter are supplemental build material, not newly generated evidence.
- `native/licenses/`: the Train Benchmark license, notices/manifests extracted from each retained JAR, cached Maven metadata where available, and an inventory. Third-party files retain their own licenses; no blanket new license is asserted over them.
- `licenses/maven_parents/` in the package: 26 locally retained parent POMs, with an inventory, completing the parent metadata chain for the 90 archived Maven POMs.
- `native/provenance/`: historical dependency lock and qualification/source reports. Their historical local paths are provenance only.

Excluded: mock runs, development/pilot result cohorts, fault/probe scratch runs, redundant native scratch outputs, local Java installations, Gradle caches and machine-specific configuration. The frozen SOURCE.zip includes its original tests and orchestration source; their presence does not add mock data to the formal denominators. The retired Train/BESSER V2 experiment is not included or used as supporting evidence.

## Optional offline source recompilation

For readers with a **Java 8 JDK**, the three project JARs can be rebuilt from retained Java using the same runtime dependencies:

[Tested commands, working directories and expected results](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md).

This compiles 101 Java source files and compares every resulting class with the frozen project JARs. The validation run produced 196/196 byte-identical class files: runner 3, model 30, matchers 163. Non-class resources are retained unchanged from the corresponding original JARs. This command recompiles the retained **generated Java**; it does not rerun the Xcore/VQL source generators or rebuild third-party libraries. Those boundaries are intentional and are recorded in `REBUILD_RESULT.json`.
