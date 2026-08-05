# XSD content-model enrichment

This package supplements the legacy flattened metadata with the original XSD
`sequence` / `choice` / `all` / `group-ref` structure. Matching is scoped by
the complete parent-container path; `xml_tag`, class name, and
`document_name` are corroborating fields rather than global identities.

Run from the repository root. The default command is read-only:

```powershell
.\.venv\Scripts\python.exe -B -m src.kg_builder.xsd_enrichment.cli
```

Materialize an additive sidecar and an enriched metadata copy:

```powershell
.\.venv\Scripts\python.exe -B -m src.kg_builder.xsd_enrichment.cli `
  --write-sidecar src\kg_builder\output\xsd_content_model_4-2-2.json `
  --metadata-out src\kg_builder\output\unified_metadata_with_xsd_content_model.json `
  --report src\kg_builder\output\xsd_content_model_report.json
```

The input metadata path can never be used as `--metadata-out`. Existing,
different output files and `xsd_*` fields are not replaced unless the
corresponding explicit replace flag is supplied. Repeating the same command
against unchanged inputs is a no-op.

Neo4j application is opt-in:

```powershell
.\.venv\Scripts\python.exe -B -m src.kg_builder.xsd_enrichment.cli `
  --apply-neo4j
```

The Neo4j path performs an exact preflight audit and aborts unless every
metadata entity ID matches exactly one existing `Entity` node. It only uses
`MATCH ... SET n += row.props`; it never deletes or rebuilds nodes or edges.

