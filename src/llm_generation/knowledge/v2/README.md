# Constraint retrieval V2

`constraints_v2.json` is the version-controlled source of truth. The build
produces `retrieval_cards.jsonl` plus `retrieval_manifest.json`; the manifest
hash pins one exact retrieval dataset.

At runtime `GenerationConstraintAdapterV2` extracts tags and paths from the
actual Round1 plan and generated JSON Schema. In `hybrid` mode it:

1. requires a ready Neo4j `ConstraintDatasetV2` with the same hash and count;
2. loads cards from Neo4j and expands matches through Class inheritance and
   Attribute relationships;
3. applies the shared deterministic ranker to the complete card set;
4. falls back to the hash-verified local cards only when Neo4j is unavailable
   or stale, recording the reason in the Round2 statistics.

Scoring uses exact XML path, property tag, class tag, graph hierarchy, purpose,
validation policy, importance, review quality, and query-term overlap. A
per-rule-family quota prevents one overloaded class from consuming the prompt.

Rebuild all derived artifacts:

```powershell
.\.venv\Scripts\python.exe -B src\generate_formal_constraints\v2\run_pipeline.py
```

Publish/audit Neo4j:

```powershell
.\.venv\Scripts\python.exe -B -m src.kg_builder.constraint_v2.cli --apply-neo4j
.\.venv\Scripts\python.exe -B -m src.kg_builder.constraint_v2.cli --audit-only
```
