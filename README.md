# ATLAS: reviewer code and evidence

This branch contains the four admitted experimental tracks and offline review tools for the ATLAS revision. Start with this file, then the README in each experiment. The historical model outputs are preserved; the September 9 corrections concern replay, scoring, provenance and explanation. No model experiment was rerun to create this release.

| Track | Retained experiment | Result supported by this evidence |
|---|---|---|
| [AUTOSAR](experiments/autosar/README.md) | V20, 20 cases × 3 repetitions; 100 separately scheduled controlled repair cells | 60/60 accepted artifact bundles; repair 85/85 core and 15/15 substitution, reported separately |
| [Local vLLM–AUTOSAR](experiments/vllm/README.md) | V6.3.4, 20 cases × 3 repetitions × U/G/A | U 45/60, G 60/60, A 60/60; identical G/A outputs |
| [PIL](experiments/pil/README.md) | V4.1, 60 cases × 3 repetitions × P0/P1/P2/P3; Erratum1 and targeted expert supplement | Narrow endpoint counts 73/96/101/143 of 180; these are not full legal accuracy |
| [Railway](experiments/railway/README.md) | V5, 747 actions and 891 endpoints | G0/GS/GF 23/29/51 of 72; R S/V/F 129/140/141 of 144 |

## Run an offline review

Use Python 3.12, Node.js 22+ for the PIL gold derivation, and Java 8 for the Railway EMF/VIATRA runtime. Create a fresh Python environment and install the pinned requirements. Installing dependencies may need the Internet; replay requires no model API, model weights, GPU or Neo4j service.

```sh
python -m venv .venv
# Activate .venv using your platform's normal command.
python -m pip install -r requirements-lock.txt
python verify_release.py --integrity-only
python verify_release.py --track all --work-dir ../atlas-review-output --node node --java java
```

Use an empty output directory and allow several GiB of free space for decompression and validation. Add `--jobs 4` to run the four independent tracks concurrently. `--track autosar`, `vllm`, `pil`, or `railway` runs one track. `--java` should point to a Java 8 executable when another Java version is the system default. The verifier does not call a model; new validation reports receive new identities when paths or timing metadata differ. The per-track instructions identify the original generation and analysis code for inspection. `requirements.txt` lists direct dependencies; `requirements-lock.txt` also pins the transitive versions used in the clean-environment review.

## What changed

- Railway's corrected scorer validates the actual submitted XMI bytes with the native loader. Projection data is used separately for task and preservation checks. It no longer validates a newly serialized substitute for the submitted artifact.
- AUTOSAR and vLLM have portable offline entry points with packaged dependencies and explicit source identity checks.
- PIL includes the Article 6/62 derivation fix, a complete rescore of the retained 720 units and three separately recorded expert assessments. Historical outputs were not replaced.
- Unrelated development files and superseded experiment trees were removed from this branch's current tree. The source development checkout and historical Git commits are preserved.

Read [evidence and claim boundaries](docs/EVIDENCE_AND_CLAIMS.md), [the change register](docs/CHANGE_REGISTER.md), [the reviewer evidence map](docs/REVIEWER_EVIDENCE_MAP.md) and [provenance conventions](docs/PROVENANCE.md). Machine-readable manifests and verification results accompany each track.

This is an experimental review release. The manuscript, existing paper PDFs and TeX sources were not edited in this release. Whole-paper integration, final response-letter page/line references, compilation and submission are separate pending work.

The GitHub repository is private at release preparation. For external review, the author can provide the standalone release ZIP or authorized repository access; see [access details](docs/ACCESS.md).

## License and attribution

The existing repository [Apache 2.0 license](LICENSE) is retained for repository-authored code. Third-party assets retain their original terms; see [third-party attribution](docs/THIRD_PARTY_NOTICES.md). A bundled specification, dependency or generated evidence file is not relicensed by the repository license.
