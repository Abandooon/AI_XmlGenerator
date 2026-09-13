# AUTOSAR V20: portable offline reviewer package

This package verifies the preserved V20 evidence and recomputes artifact checks for **60 generation runs (20 cases x 3 repetitions) and 100 controlled repair cells**. It does not call a model, start Neo4j, run a GPU workload, regenerate an artifact, or replay the original model interactions. The retained experimental members preserve their original bytes.

## Run

Use Python 3.10 or newer in an environment with `pip install -r requirements.txt` completed beforehand. The four pinned packages are the dependencies of this offline entrypoint; a normal pip installation resolves their transitive dependencies. No author repository, credentials, database, or model installation is needed.

From this package directory, run one offline command:

[Tested commands, working directories and expected results](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md).

`--work-dir` may be any new or empty directory. Allow at least 1 GiB of free space. The entrypoint verifies the frozen ZIP digest, safely extracts it there, checks the 9,661 retained manifest-listed file hashes and the explicit 12-entry document exclusion list, restores the runtime from frozen source files and the declared supplement, and writes fresh per-run reports plus `reviewer-work/verification.json`. It refuses to overwrite a nonempty work directory. Exit code 0 means every identity check and expected metric matched; failures raise an error or return exit code 1. The Python audit hook rejects network/subprocess attempts, reads outside the package/work/Python-installation roots, and writes outside the requested work directory. No result is sent anywhere.

The installed dependency environment is a prerequisite. The command itself is offline and does not run pip. The supplied `validation/` results document a separate execution after copying the package to another directory and running Python with isolated imports (`-I`).

## Layout and provenance

| Path | Role |
| --- | --- |
| `frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip` | Selected experiment archive containing original evidence, code snapshots, requirements and baseline artifacts. The 12 document-related exclusions are recorded in `ARCHIVE_SELECTION.json`. |
| `offline/verify.py` | New portable orchestration, identity gates, all-run recomputation, and report generation. |
| `review.py` | Root wrapper for the same supported offline entrypoint. |
| `frozen_code/` | Directly browseable original generator/assembler/repair/validator/evaluator source; `CODE_INDEX.json` binds each copy to its ZIP member and SHA-256. These are inspection copies, not a second runtime. |
| `offline/revalidate_phase12_run.py` | New saved-artifact adapter importing the frozen validator and parsed YAML evaluator. |
| `offline/post_run_correction_identity.py` | New portable hash/path helpers used by the supported entrypoint. |
| `offline/supplemental_runtime/` | Missing `xml.xsd`, XSD content-model parser, and serialization-manifest loader, copied unchanged from the separately supplied vLLM dependency snapshot. |
| `offline/provenance/recovered_legacy/` | Recovered original `revalidate_phase12_run.py` and `post_run_correction_identity.py` for inspection only; they are not imported or executed. |
| `offline/SUPPLEMENTAL_SOURCES.json` | Source descriptions, relative paths, and SHA-256 identities for every supplemental/recovered file. |
| `validation/` | Package credential-scan disposition, executed verification summary, detailed reports archive, and relocation record. |
| `PACKAGE_STATUS.json` | Machine-readable source, change, validation and limitation record. |

The original ZIP identity and the selected ZIP identity are recorded in [ARCHIVE_SELECTION.json](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/ARCHIVE_SELECTION.json). The current archive preserves 9,661 original manifest-listed members plus the unchanged historical manifest and checksum file. Twelve author-document entries are excluded. Verification checks this selection explicitly. This binds the preserved evidence to the supplied release, but hashes alone cannot prove historical execution.

The original package was not self-contained: its analysis script imported an omitted `revalidate_phase12_run.py`, repair scripts imported an omitted `post_run_correction_identity.py`, the main XSD imported missing `xml.xsd`, and legacy scripts used author-specific absolute paths. The supported entrypoint resolves those packaging problems without editing frozen files. It restores 44 frozen runtime assets and the frozen `element_selection.py`; it sets the frozen evaluator's three path constants at runtime. Unneeded parent package markers are namespace packages, so the full repository's eager imports are not used. The validator verifies its own original implementation manifest on construction. Supplemental files have explicit new identities and are **not asserted to have been bound by the original V20 freeze**. The recovered legacy scripts remain historical source: they are not alternative portable entrypoints.

## What is recomputed

The entrypoint reads the actual ARXML, reruns the frozen XSD/profile validator, checks each generated bundle against the saved post-intervention Phase 1 plan, and reruns the frozen parsed evaluator against the independently represented YAML case obligations and local references. For repairs, it evaluates both the corrupted input and preserved final artifact, and compares final filenames and SHA-256 bytes with the controlled reference bundle. Provider counts, timing, token totals and intervention counts are separately recomputed from the saved ledgers/metadata; those fields are not new observations from model calls.

| Measure | Expected preserved-evidence result |
| --- | --- |
| Generation bundles passing evaluator/profile/saved-plan checks | 60/60 for each |
| Generation pipeline attempts | One per run, 60/60 |
| Generated files | 255 ARXML: 60 components + 195 interfaces; a bundle has 2–7 files |
| XSD checks | 255/255 PASS |
| YAML structural obligations | 2,418 checked, 0 failures |
| Local reference checks | 675 checked, 0 failures |
| Whole-corpus generation decision | 60/60 INCOMPLETE |
| Generation response ledger | 180 responses / 180 logical requests / 184 physical dispatches; 2 continued logical requests |
| Logged generation tokens | 11,967,476 total |
| Logged framework intervention counts | 1,734 applied obligations; 527 recoveries in 49 runs |
| Formal V20 admitted Phase 2 schemas | 120 singleton schemas; unique JSON value matches each saved parsed provider response |
| Controlled repair layers | 85 core fixed-operator cells + 15 substitution cells |
| Corrupted repair inputs | 100/100 fail the evaluator and differ from the reference |
| Preserved repaired outputs | 100/100 pass evaluator/profile and exactly match reference filenames and bytes |
| Whole-corpus repaired-output decision | 100/100 INCOMPLETE |
| Natural-failure repair cells | 0 |
| Repair response ledger | 130 responses; 716,624 logged tokens |

Detailed validation reports preserve the difference between an artifact profile passing and the full constraint corpus being incomplete. `PASS` in this package's summary means the audit checks matched their explicit expected results, including the expected `INCOMPLETE` decisions. It does not mean complete AUTOSAR compliance, industrial integration success, or certification.

## Evidence limits

* The saved Phase 1 `round1_*.json` contains the post-intervention design. The original pre-intervention Phase 1 provider response body, and controlled-repair request/response bodies, were not located in the supplied archives or examined experiment/source/output directories. The response ledgers retain IDs, parameters and usage, but do not retain these bodies or body hashes. This package cannot recover them or independently replay/attribute the logged 1,734 obligations and 527 recoveries to the unavailable raw text. Available Phase 2 parsed raw JSON is retained.
* The 120 singleton finding applies to the **admitted, post-Phase1 schemas of this formal V20 dataset**. It is the configured design, not an implementation defect, and does not establish that Phase 1 is model-free or that all dynamic Phase 2 schemas are singletons. The package does not add or claim a new deterministic baseline experiment.
* The 100 repairs are controlled corruptions of accepted reference bundles. Their exact restoration supports repair of those injected defects under the pinned requirements and operators. It does not estimate a natural failure rate, natural repair effectiveness, or unconstrained model repair ability. The repair verifier uses the preserved reference context and independently parsed YAML obligations; it does not reconstruct absent repair conversation bodies or invent a missing pre-corruption Phase 1 plan.
* The cases are curated, requirement-derived benchmark instances. Independent representation of YAML obligations helps check outputs, but this is not an independently sampled industrial evaluation set. Profile/reference checks and source traceability do not substitute for broader semantic or full-corpus conformance.
* Historical absolute paths inside the unchanged archive/recovered scripts remain provenance strings. The supported offline command maps evidence paths to the newly extracted relative layout. It does not require those historical locations to exist.

The package contains no new model results. These repairs close the offline packaging gap while preserving the limitations of the original evidence.
