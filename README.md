# Manuscript, implementation and reviewer evidence

Start with the [current manuscript and appendix](paper/current/README.md). The current Chinese manuscript uses four experimental sections and Appendices A–D. The [paper-to-evidence index](docs/REVIEWER_EVIDENCE_MAP.md) connects those locations to requirements, ICM records, prompts, generation schemas, original artifacts, statistics and offline checks.

| Read or inspect | Entry point |
| --- | --- |
| Current manuscript | [Word](paper/current/manuscript.docx), [Markdown](paper/current/manuscript.md) |
| Current appendix | [Word](paper/current/appendix.docx), [Markdown](paper/current/appendix.md) |
| Constraint extraction, ICM and language evidence | [ICM evidence guide](docs/ICM_EVIDENCE.md) |
| Statistical definitions and complete analyses | [Statistical analysis](docs/STATISTICAL_ANALYSIS.md) |
| Paper locations and original evidence | [Reviewer evidence map](docs/REVIEWER_EVIDENCE_MAP.md) |
| Changes and interpretation | [Change register](docs/CHANGE_REGISTER.md), [self-review](docs/SELF_REVIEW.md), [claim boundaries](docs/EVIDENCE_AND_CLAIMS.md) |

## Experimental tracks

| Current paper location | Package | Task set and main result |
| --- | --- | --- |
| Section 4.2; Appendix A | [AUTOSAR](experiments/autosar/README.md) | 20 requirements × 3 runs; 60/60 accepted bundles; 85 core and 15 substitution repair cells reported separately |
| Section 4.3; Appendix B | [AUTOSAR–vLLM](experiments/vllm/README.md) | 20 cases × 3 repetitions × U/G/A; structural acceptance 45/60, 60/60, 60/60 |
| Section 4.4; Appendix C | [Railway](experiments/railway/README.md) | 24 tasks × 3 repetitions; G0/GS/GF 23/29/51 of 72 |
| Section 4.4.3; Appendix C.3 | [Railway second model](experiments/railway_terra/README.md) | Same 24 tasks, one fixed seed; Terra 18/22/22 and Luna 6/8/13 of 24 |
| Section 4.5; Appendix D | [PIL](experiments/pil/README.md) | 60 cases × 3 repetitions × four conditions; composite endpoint 73/96/101/143 of 180 |

No new model calls were made for this manuscript and navigation revision. Original experiment files remain in their existing packages. Historical run names are retained as source identifiers.

## Offline review

Use Python 3.12, Node.js 22 or newer for PIL, and Java 8 for the railway native runtime. Install the pinned dependencies before running the offline checks.

```sh
python -m venv .venv
# Activate the environment using your platform's normal command.
python -m pip install -r requirements-lock.txt
python verify_release.py --integrity-only
python verify_release.py --track all --work-dir ../review-output --node node --java java --jobs 4
```

Use an empty output directory outside the release and allow several GiB of free space. Individual track choices are `autosar`, `vllm`, `railway`, `railway_terra` and `pil`. The review checks retained inputs and outputs; it does not require a model API, GPU, model weights or a Neo4j service. Each package README describes its prerequisites and replay scope. Earlier measured results remain under [validation](validation/); their dates and source identities determine which revision they cover.

The intended repository layout is the reviewer tree at the ATLAS branch root and the same tree under `paper/atlas-review/` on api_rag. Development code outside that directory and [historical paper material](paper/README.md) are separate from the current manuscript. Use the branch-specific links and access instructions in [access and branch navigation](docs/ACCESS.md); the delivery receipt identifies the synchronized commits.

Repository-authored code retains its [Apache 2.0 license](LICENSE). See [third-party notices](docs/THIRD_PARTY_NOTICES.md) for other materials.
