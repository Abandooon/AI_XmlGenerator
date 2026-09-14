# Material locations and maintenance

The ATLAS branch is the reviewer-facing implementation and evidence release. The api_rag branch contains its byte-identical copy under `paper/atlas-review/` alongside the development source tree.

| Material | Canonical entry |
| --- | --- |
| Domain preparation, ICM records and element binding | [ICM evidence](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md) |
| Requirements, prompts, schemas, model outputs and checks | [Evidence map](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md) |
| Experimental counts and aggregation | [Data index](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/EXPERIMENT_DATA.md) |
| Executable verification | [Supported commands](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md) |
| Verification execution records | [Command audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/COMMAND_AUDIT.md), [subsequent railway audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/review_closure_2026-09-14/RAILWAY_AUDIT.md) |
| Figure data and plotting source | [Figure guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/analysis/figures/README.md) |
| English explanations of retained preparation records | [English reading guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ENGLISH_REVIEW_GUIDE.md) |
| Frozen archive selection and original identities | [Provenance](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/PROVENANCE.md) |

Manuscript sources, submission PDFs, decision letters and author responses are maintained by the authors outside this release. They are not required to execute its checks.

Frozen archives, request and response records, manifests, generated artifacts, expert adjudications, source snapshots and qualified verification reports are retained evidence. A historical date or a repeated artifact does not by itself make such a file redundant: source identities, shared initial candidates and independent checks may depend on it. The release manifest binds their current locations and bytes.

Fresh replay outputs, extracted working copies, virtual environments, IDE settings and ordinary runtime logs do not belong in the release. The supported commands write new outputs outside it. On api_rag, local IDE preferences and runtime logs are ignored; removing their tracked copies does not change the frozen experiment evidence. Git history is retained.

Changes to the reviewer export should update both branch locations and their release manifest. The manifest and navigation checks in the command list verify the resulting file set and references.
