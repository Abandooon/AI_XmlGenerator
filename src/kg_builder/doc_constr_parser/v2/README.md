# Constraint Pipeline V2

This directory contains the validation-oriented, LLM-API-free constraint
curation pipeline.

The pipeline deliberately separates four source-of-truth layers:

1. `work/source_manifest.jsonl`: immutable source records recovered from the
   annotated AUTOSAR chapters.
2. `work/semantic_curation.jsonl`: semantic decisions made during curation.
3. `work/binding_decisions.jsonl`: metamodel and XML binding decisions.
4. `constraints_v2.json`: the compiled publication artifact.

The source manifest is deterministic. Semantic curation and binding never
rewrite source evidence; they are keyed by the official constraint ID and are
merged only during publication.

The formal compiler derives `validation_plan.json`; retrieval derives
`retrieval_cards.jsonl` and its hash manifest. These outputs are pinned to the
same structured dataset and are checked by the pipeline audit.

No external LLM API is used by this package.

