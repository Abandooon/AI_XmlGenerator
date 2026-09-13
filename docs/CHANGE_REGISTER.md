# Manuscript and navigation changes

| Change | Current location |
| --- | --- |
| Publish the English main text and Appendices A–D as one LaTeX manuscript | [PDF and source](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/current/README.md) |
| Describe automatic constraint extraction and metamodel linking, with human resolution of failed or ambiguous links | Section 3.3; Appendix A.2; [implementation guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md) |
| Separate domain preparation from the evaluated model-generation runs | Sections 4.1–4.2; Appendix A.2 |
| Report the 554-rule plan as configured rules, with checks executed according to the task and artifact | Section 4.2.2; Appendix A.2 |
| Keep publication-state implementation details in the repository | [ICM evidence](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md#stored-publication-states) |
| Link every normalized reviewer comment to manuscript labels, appendices and inspectable materials | [Artifact crosswalk](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/PAPER_ARTIFACT_CROSSWALK.md), [response matrix](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/REVIEW_RESPONSE_MATRIX.md) |
| Provide direct routes to prompts, schemas, generated ARXML/XMI/JSON and statistical calculations | [Evidence map](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md), [statistical analysis](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/STATISTICAL_ANALYSIS.md) |
| Make the current integrated manuscript distinct from historical drafts | [Paper navigation](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/README.md) |

This revision changes manuscript presentation, supporting navigation and the offline reviewer adapters. Original experimental inputs, outputs, code snapshots and result values remain unchanged. It includes no new model calls. The release manifest identifies the final file set; Git identifies the repository commits.

The [execution audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/publication_review/COMMAND_AUDIT.md) covers all 20 active commands, external-output regression checks, independent ICM and figure checks, and [428 specified manuscript numbers](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/PAPER_DATA_CROSSCHECK.md). The [original concern mapping](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/COMMENT_SOURCE_MAP.md) identifies the source of each of the 31 response items.
