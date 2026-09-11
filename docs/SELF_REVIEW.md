# Manuscript and evidence alignment review

This revision aligns the [current manuscript](../paper/current/README.md) with existing experimental packages and adds English reviewer navigation. It introduces no new model calls and does not alter original experiment files.

| Review item | Current reading location | Evidence and interpretation |
| --- | --- | --- |
| Requirement origin and input language | Section 4.2.1; Appendix A.1 | [Requirement source guide](../paper/sources/AUTOSAR_REQUIREMENT_PROVENANCE_AND_DESIGN.md), [ICM/language evidence](ICM_EVIDENCE.md); distinguish normative text, requirements, extraction prompts, generation prompts and comments |
| Extraction, object binding and checker construction | Section 4.2.2; Appendix A.2 | [ICM evidence](ICM_EVIDENCE.md); stored constraints, element links and executable rules are different quantities |
| Concrete generation and repair examples | Appendices A.4, C.4 and D.3 | [Archive/member index](REVIEWER_EVIDENCE_MAP.md); examples use existing ARXML, XMI and decision JSON |
| Main railway comparisons and second model | Section 4.4; Table C3 and Appendix C.3/Table C4 | [Statistical analysis](STATISTICAL_ANALYSIS.md), [Luna package](../experiments/railway/README.md), [Terra package](../experiments/railway_terra/README.md) |
| PIL decision fields and expert examples | Section 4.5; Appendix D.2–D.4 | [PIL package](../experiments/pil/README.md); reference compatibility differs from a full legal evaluation |
| Current versus historical documents | [Current paper](../paper/current/README.md), [historical context](../paper/README.md) | Earlier chapter numbers and response anchors are not current navigation |

AUTOSAR task acceptance checks case requirements as well as the produced artifact. Controlled repair is separate from formal generation. Railway repair acceptance preserves task obligations and protected content. Both Terra repair branches reach 22/24, with different success sets; the single-seed comparison does not establish a consistent advantage over self-repair. Statistical intervals and paired tests answer different questions, explained in [STATISTICAL_ANALYSIS.md](STATISTICAL_ANALYSIS.md).

Custom validators were developed with human interpretation and LLM assistance; existing XSD, EMF and VIATRA capabilities were reused. Source availability or a passed artifact check does not establish extraction accuracy. See [claim boundaries](EVIDENCE_AND_CLAIMS.md).

Earlier executed checks remain at [CURRENT_REVIEW.json](../validation/CURRENT_REVIEW.json) and [retained review records](../validation/self_review/). Their identities and timestamps are preserved; this document does not turn an earlier execution into a new test run. Final response-letter page and line anchors must come from the final integrated manuscript. [Remote access](ACCESS.md) for this revision is not confirmed.
