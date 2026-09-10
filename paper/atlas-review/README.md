# ATLAS: manuscript, code and reviewer evidence

This release contains the current Chinese methodology, experiment and appendix chapters, their figures, four original experimental tracks, and the completed second-model railway supplement. The original experiment outputs remain unchanged. The Terra supplement contains new model calls; this synchronization performs offline review only.

Start with [the current chapters](paper/README.md), [claim boundaries](docs/EVIDENCE_AND_CLAIMS.md), and [the self-review findings](docs/SELF_REVIEW.md). The ATLAS branch contains this release at its root. The api_rag branch contains the identical release under `paper/atlas-review/`; development code outside that directory is not the frozen experimental implementation.

| Track | Task set | Supported result |
|---|---|---|
| [AUTOSAR](experiments/autosar/README.md) | 20 authored cases × 3 repetitions; separate controlled faults | 60/60 accepted bundles in the declared scope; core repair 85/85, substitutions 15/15 separately |
| [Local vLLM–AUTOSAR](experiments/vllm/README.md) | 20 cases × 3 repetitions × U/G/A | Structural acceptance 45/60, 60/60, 60/60; all 60 audited runs record decoding intervention |
| [PIL](experiments/pil/README.md) | 60 cases × 3 repetitions × four conditions | Narrow composite endpoint 73/96/101/143 of 180; not full legal accuracy |
| [Railway, Luna](experiments/railway/README.md) | 24 tasks × 3 repetitions; separate controlled faults | G0/GS/GF 23/29/51 of 72; controlled S/V/F 129/140/141 of 144 |
| [Railway, Terra](experiments/railway_terra/README.md) | Same 24 tasks, one fixed seed | G0/GS/GF 18/22/22 of 24; paired Luna subset 6/8/13 of 24; exploratory comparison |

## Offline review

Use Python 3.12, Node.js 22+ for PIL, and Java 8 for the railway native runtime. Install the pinned requirements in a fresh Python environment. Dependency installation may require the Internet; the review requires no model API, model weights, GPU or Neo4j service.

```sh
python -m venv .venv
# Activate .venv using your platform's normal command.
python -m pip install -r requirements-lock.txt
python verify_release.py --integrity-only
python verify_release.py --track all --work-dir ../atlas-review-output --node node --java java --jobs 4
```

Use an empty output directory outside this release and allow several GiB of free space. The individual choices are `autosar`, `vllm`, `pil`, `railway`, and `railway_terra`. Pass the Java 8 executable explicitly if another Java version is the default. The Terra entry reconstructs four lossless archive parts, verifies the original archive and its sealed contents, then executes the independent native audit. The original archive SHA-256 is preserved. The supplied entry accepts caller Python and Java 8; qualification was performed on Windows, not on every operating system.

New review reports have new identities when paths or timing metadata differ. Retained expected failures remain failures: agreement with a recorded verdict does not mean that an artifact passed. [Validation evidence](validation/CURRENT_REVIEW.json) records this release's checks.

## Scope and publication status

ATLAS starts from an existing or externally supplied explicit metamodel and constraints expressible through supported generation restrictions and executable post-generation checks. Its ICM construction connects metamodel entities, structured constraints and their uses. Custom validators were developed manually with LLM assistance; arbitrary metamodel induction or verifier synthesis is not claimed.

The revised chapters are included. The original complete paper is retained as source context, not presented as the revised submission. English whole-paper integration, final response-letter page/line references, bibliography/figure unification and compilation remain pending. No submission or message to reviewers was sent.

See [the change register](docs/CHANGE_REGISTER.md), [reviewer evidence map](docs/REVIEWER_EVIDENCE_MAP.md), [provenance](docs/PROVENANCE.md) and [access](docs/ACCESS.md). Historical run identifiers are retained for traceability, not used as the paper's research-condition names.

## License

The existing [Apache 2.0 license](LICENSE) is retained for repository-authored code. Third-party material retains its original terms; see [attribution](docs/THIRD_PARTY_NOTICES.md). No model weights or live API credentials are included in this curated release.
