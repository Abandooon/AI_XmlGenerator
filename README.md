# Manuscript, implementation and reviewer evidence

The [integrated Chinese manuscript](paper/current/latex/main.pdf) contains the main text, references and Appendices A–D. Its [LaTeX source](paper/current/latex/main.tex), [bibliography](paper/current/latex/references.bib) and [figures](paper/current/latex/figures/) are supplied together.

| Read or inspect | Entry point |
| --- | --- |
| Manuscript and source files | [Current paper](paper/current/README.md) |
| Paper → appendix → evidence → reviewer comment | [Artifact crosswalk](docs/PAPER_ARTIFACT_CROSSWALK.md) |
| Responses to all 31 normalized comments | [Response matrix](paper/REVIEW_RESPONSE_MATRIX.md) |
| Requirements, prompts, schemas and generated artifacts | [Evidence map](docs/REVIEWER_EVIDENCE_MAP.md) |
| Constraint extraction, automatic linking and ICM | [ICM guide](docs/ICM_EVIDENCE.md) |
| Statistical definitions and complete calculations | [Statistical analysis](docs/STATISTICAL_ANALYSIS.md) |
| Source attribution and access | [Provenance](docs/PROVENANCE.md), [access guide](docs/ACCESS.md) |

## Experimental tracks

| Paper location | Package | Task set and main result |
| --- | --- | --- |
| Section 4.2; Appendix A | [AUTOSAR](experiments/autosar/README.md) | 20 requirements × 3 runs; 60/60 accepted bundles; 85 core and 15 substitution repair cells |
| Section 4.3; Appendix B | [AUTOSAR–vLLM](experiments/vllm/README.md) | 20 cases × 3 repetitions × three conditions; structural acceptance 45/60, 60/60, 60/60 |
| Section 4.4; Appendix C | [Railway](experiments/railway/README.md) | 24 tasks × 3 repetitions; initial generation/self-repair/validation-feedback repair: 23/29/51 of 72 |
| Section 4.4.3; Appendix C.3 | [Railway second model](experiments/railway_terra/README.md) | Same 24 tasks and one seed; Terra 18/22/22 and Luna 6/8/13 of 24 |
| Section 4.5; Appendix D | [Private international law (PIL)](experiments/pil/README.md) | 60 cases × 3 repetitions × four conditions; composite endpoint 73/96/101/143 of 180 |

Domain preparation supplies the metamodel representation, source-linked constraints, generation mappings and validators. The generation experiments use those prepared resources to construct and check instance models or structured decisions. The complete input, output and analysis records are retained in the corresponding packages.

## Offline review

Use Python 3.12, Node.js 22 or newer for PIL, and Java 8 for the railway native runtime. Install the pinned dependencies, then run:

```sh
python -m venv .venv
# Activate the environment using your platform's normal command.
python -m pip install -r requirements-lock.txt
python verify_release.py --integrity-only
python verify_release.py --track all --work-dir ../review-output --node node --java java --jobs 4
```

Use an empty output directory outside the release and allow several GiB of free space. Individual track choices are `autosar`, `vllm`, `railway`, `railway_terra` and `pil`. These commands review saved inputs and outputs without model API calls, GPU access, model weights or a Neo4j service. A focused ICM inspection is available as `python -B inspection/check_icm_evidence.py`.

The ATLAS branch contains this reviewer tree at its root; api_rag contains the same tree under `paper/atlas-review/`. The [access guide](docs/ACCESS.md) provides the branch-specific links. Release manifests identify files, and delivery receipts identify the corresponding commits and standalone archive. Earlier manuscript sources are listed separately in [paper/README.md](paper/README.md).

Repository-authored code retains its [Apache 2.0 license](LICENSE). See [third-party notices](docs/THIRD_PARTY_NOTICES.md) for other materials.
