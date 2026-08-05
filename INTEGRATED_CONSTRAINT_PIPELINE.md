# Integrated AUTOSAR constraint pipeline

The project now has one authoritative and traceable flow:

1. source Markdown is parsed into an immutable source manifest;
2. semantic curation adds importance, core status, usages, rule family, and
   validation policy;
3. targets are bound to AUTOSAR classes, attributes, XML tags, and paths;
4. retrieval cards and a hash manifest are generated;
5. the same dataset is projected into existing Neo4j `Constraint` entities as
   `ConstraintV2`, with target, section, and validation-rule relationships;
6. Round2 retrieves from Neo4j and deterministically reranks all cards, with a
   hash-checked local fallback;
7. XSD content models are compiled into a required, hash-pinned serialization
   manifest that preserves exact owner/particle context, sequence, choice, all,
   groups, inheritance, and occurrence metadata;
8. provider JSON is treated as unordered data: an explicit projection map
   reverses schema flattening, then the deterministic serializer emits canonical
   XSD order. Missing, unknown, or ambiguous mappings fail closed; there is no
   runtime XSD/order fallback;
9. every generated ARXML bundle is immediately checked by XSD and the Python
   validation plan. All 554 must-validation rules are implemented; rules that
   require missing intent, exact targets, parameters, reference closure, or
   external evidence remain fail-closed as `NOT_EVALUATED`/`INCOMPLETE`.

Run the full dry-run build:

```powershell
.\.venv\Scripts\python.exe -B -m src.kg_builder.integrated_pipeline
```

Rebuild, idempotently enrich XSD metadata, publish ConstraintV2, and audit the
live database:

```powershell
.\.venv\Scripts\python.exe -B -m src.kg_builder.integrated_pipeline --apply-neo4j
```

Neo4j credentials are read from the project `.env`; no password is stored in
the YAML configuration or logged.
