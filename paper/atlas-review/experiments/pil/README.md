# PIL V4.1 reviewer package

This package supports offline inspection and recomputation of a bounded, four-arm structured-decision experiment. It contains all **720 original final records**, their initial/repair response text and accounting, the unchanged historical scoring code, a versioned gold-derivation correction, and three targeted expert findings. It does not require API credentials, GPU access, Neo4j, the authors' repository, or new model responses.

## Verify with one offline command

Prerequisites: Python 3.11 or later, Node.js 18 or later available as `node`, and the Python dependencies in `requirements.txt`. In an environment that needs setup, install those dependencies before disconnecting from the network, or use a local wheel cache. The listed versions describe the tested verification environment; the original generation protocol remains in the frozen evidence.

From this directory:

```sh
python -B tools/verify.py
```

The command uses package-relative inputs. It checks file identities, the 720-row ledger chain and schedule, all 720 prompt instances and 784 recorded transport request hashes, 782 unique response IDs, response parsing and token totals. It reproduces every historical score, regenerates corrected gold for all 60 cases, reproduces the 720 corrected scores and paired statistics, binds the three expert findings, and executes the 27 original PIL tests plus 7 export tests and 8 article-boundary checks. Tests use fake clients; network access is blocked in Python. The verifier also rejects experiment-file access outside the package and its output/runtime directories.

One original preflight test follows a workstation-specific translation-workbook locator. The test adapter rebases only that locator in memory to the bundled workbook after verifying its accepted SHA-256. The test source, frozen JSON file, expert judgments and scoring logic remain byte-preserved. This path adapter is recorded in the verification report.

Outputs go to `verification/latest/`; evidence files are not overwritten. An alternative output directory may be passed with `--work-dir` (alias `--output-dir`). An explicit Node executable may be passed with `--node`, or selected by prepending its directory to `PATH`. The main result is `verification_report.json`, accompanied by the unit-test log and independently regenerated corrected gold. `verification/relocation/` records the separate relocation check performed for this export.

## Layout and entry points

| Directory | Role |
|---|---|
| `frozen/formal/` | Original 720-unit ledger, schedule, run manifest, analysis and readiness record. |
| `frozen/prepaid_freeze/` | Byte-preserved facts, original gold, provision paraphrases, schemas, rules, prompts, generation/scoring sources, PIL tests and review provenance. |
| `corrections/data/` and `corrections/expected/` | Erratum1 corrected gold and retained recomputation results. Original model outputs and the scorer are unchanged. |
| `corrections/code/correct_gold.mjs` | Portable correction entry point. It executes only the audited pure `requiredEvidence` function extracted from the retained revised builder source. |
| `corrections/provenance/` | Revised legacy builder stored as text for inspection and pure-function extraction; the full builder is not executed. |
| `expert_supplement/` | Author clarification, hash-bound targeted adjudications, future field definitions and the expected 720-row opinion association. |
| `tools/verify.py`, `tools/review_join.py`, `tests/` | Portable verification and opinion-binding adapters with additional negative controls. |

The original `frozen/prepaid_freeze/data/consensus_gold_v4.jsonl` and `frozen/prepaid_freeze/provenance/build_pil_v4_inputs.mjs` are **historical evidence**, not corrected derivation inputs or recommended execution entry points. The former is deliberately used to reproduce historical scores. The full legacy builder contains historical workstation paths and depends on older authoring inputs; do not use it to rebuild this export. Archived absolute path strings in original manifests, review records or source snapshots are provenance only and are never followed by the supported offline verifier.

For corrected derivation alone, without running the full verification:

```sh
node corrections/code/correct_gold.mjs --output verification/corrected_gold.jsonl
```

Generation modules are retained to explain the experiment; this reviewer export does not configure or authorize a fresh paid run. Personal provider configuration and the cross-experiment workstation registry are absent.

`frozen/SOURCE_ARCHIVE_MANIFEST.json` is the original manifest. `frozen/SOURCE_SELECTION.json` accounts for all its 61 payload entries: 57 retain their original bytes; four unrelated workbench/registry files are excluded. This export is not represented as an exact copy of the entire original archive. `PACKAGE_MANIFEST.json` independently inventories this review package's immutable payload. Generated verification reports and package-status metadata are excluded from that payload inventory to permit repeat execution; the parent release may inventory them separately.

## What the results mean

The 60 synthetic scenarios are not real legal cases or a probability sample. The four arms share the semantic JSON contract and the requested model; P1--P3 have identical main prompt text and evidence. P0 has no retrieved provisions; P1 adds retrieval; P2 adds provider-side strict schema; P3 adds deterministic auditing, at most one repair, and fail-closed release. The 58-provision store was selected using accepted evidence for these same cases, and retrieval was developed on the case set. Gold labels were not given to the model during generation. This is a case-tailored study, not a held-out legal retrieval benchmark.

The primary endpoint combines schema/delivery validity, actual system release, and four frozen gold obligations: conclusion, accepted forum type, required-evidence intersection and conditional flag. It does **not** certify free-text court/country identification, reasoning, or substantive missing facts. Original and corrected endpoint counts remain **73, 96, 101 and 143 out of 180** for P0--P3. These are contract-compatible endpoint counts, not complete legal-answer accuracy.

Erratum1 fixes an Article 6/62 prefix collision. Re-deriving all 60 cases changes only case19's required evidence from `BRUSSELS_I_BIS:Art.62(1)` to `BRUSSELS_I_BIS:Art.6(1)`. Across all 720 rescored records, only the 12 evidence-obligation flags for that case change from false to true. The four endpoint totals, full summaries and paired comparisons do not change. All old evidence remains available.

P3 has 180 delivery-valid records including four normalized fail-closed records, 176 actual releases, and 143 endpoint successes. It attempts 62 repairs: 58 are released; 40 recover gold compatibility and are released; 42 repaired units finally meet the endpoint; three repairs induce a gold error. These quantities measure different events. P3--P2 estimates the combined audit/one-repair/release policy. Provider metadata and response IDs support the retained local accounting; a proxy-reported model name does not independently authenticate upstream model identity.

## Human review and the targeted supplement

The author confirmed on 9 September 2026 that **Xinyue Yang** designed the cases, and **Xinyue Yang and Yirui Wang** acted as human experts. They initially reviewed separately without seeing one another's judgments, then discussed disagreements. Codex assisted with filling review materials. Independence here refers to the separate initial judgments, not independence of both reviewers from case authorship. The clarification date is not a newly asserted historical signature date. Some byte-preserved historical filenames use a different spelling; they have not been silently renamed or rewritten.

On the same date, the author supplied targeted post-run expert findings about three stored answers. These are not represented as a new independently blinded review of all 720 outputs:

| Unit | Targeted finding | Historical endpoint |
|---|---|---|
| `19\|p3\|1` | Substantive explanation acceptable, with a flag-level ambiguity. Future encoding evaluates the selected conclusion itself: referral to national law is already established, so its canonical flag is false. | Fails the frozen four-field criterion; the model's original true flag is preserved. |
| `42\|p1\|1` | Unacceptable inference from Dutch domicile to Amsterdam-specific jurisdiction. | Passes the machine endpoint, demonstrating a real semantic coverage limit. |
| `42\|p3\|1` | Conditionally acceptable based on the later qualifications; specific jurisdiction and exclusive effect are not established. Consumer protection under Articles 19 and 25(4) still matters. | Passes the machine endpoint. |

Each finding is bound to the exact ledger entry and complete final-decision hash. The association preserves **3 targeted opinions and 717 records without an opinion in this new assessment layer**. It does not erase any historical gold review. `full_legal_accuracy` is explicitly null; no 3-answer aggregate is presented as corpus-wide accuracy.

The clarified field descriptions in `expert_supplement/protocol/` are for a future protocol. They were not retrospectively inserted into the prompts used for this batch, and do not loosen arbitrary true/false matching. A claim about generation under clarified prompts would require a separately frozen run; recording this clarification and correcting deterministic scoring inputs require no new generation.

## Source and scope notes

Legal source identifiers and URLs are retained in `frozen/prepaid_freeze/PIL_V41_ENGLISH_LEGAL_SOURCE_AUDIT.json`. Brussels I bis was frozen to consolidated text `02012R1215-20150226`; the supplied English provision entries are paraphrases. The relevant primary source is [EUR-Lex Regulation 1215/2012, consolidated 26 February 2015](https://eur-lex.europa.eu/eli/reg/2012/1215/2015-02-26/eng). The EU trade-mark source version is also recorded in the source audit. Historical Chinese review material is preserved for provenance; the 60 formal case prompts and English evidence used in the experiment are separately supplied.

The aborted 132-unit V4 design-audit batch is excluded in full, as documented in the retained abort record. Its outputs are not mixed into the formal 720-unit schedule. This export verifies the retained formal run; it does not generate new answers or certify that all free-text legal conclusions are correct. It supports within-corpus effects for a shallow structured-decision contract, not full engineering-artifact transfer or general legal validity.

Paper copies, manuscript-edit backups, conversation logs, private provider configuration, and unrelated experiment registries are intentionally excluded. The source-selection record and package manifest document the boundary of the export.
