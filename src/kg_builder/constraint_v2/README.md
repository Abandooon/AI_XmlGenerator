# ConstraintV2 Neo4j model

`constraints_v2.json` remains the version-controlled source of truth. This
package publishes an idempotent graph projection that upgrades matching legacy
`Constraint` entities in place and adds `ConstraintV2`, `ConstraintTargetV2`,
`ValidationRuleV2`, `DocumentSectionV2`, and `ConstraintDatasetV2` data.

The publication is hash-pinned. Generation only reads a Neo4j dataset whose
hash and record count match the local retrieval manifest; otherwise hybrid mode
falls back to the same local cards and records the reason.

Dry-run:

```powershell
.\.venv\Scripts\python.exe -B -m src.kg_builder.constraint_v2.cli
```

Publish and audit:

```powershell
.\.venv\Scripts\python.exe -B -m src.kg_builder.constraint_v2.cli --apply-neo4j
.\.venv\Scripts\python.exe -B -m src.kg_builder.constraint_v2.cli --audit-only
```
