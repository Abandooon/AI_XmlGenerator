"""CLI for dry-run-first XSD content-model enrichment."""

from __future__ import annotations

import argparse
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .content_model import XsdContentModelExtractor, canonical_json, sha256_file
from .matcher import MetadataMatcher, build_enriched_metadata, metadata_sha256
from .neo4j_apply import KgUpdateConflict, apply_updates, collect_updates
from .serialization_manifest import build_serialization_manifest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_XSD = PROJECT_ROOT / "src/kg_builder/uml_metadata_parser/input/AUTOSAR_4-2-2.xsd"
DEFAULT_METADATA = PROJECT_ROOT / "src/kg_builder/data/unified_metadata_with_inlines.json"
DEFAULT_SERIALIZATION_MANIFEST = (
    PROJECT_ROOT / "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json"
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract and safely apply parent-aware XSD content models (dry-run by default)."
    )
    parser.add_argument("--xsd", type=Path, default=DEFAULT_XSD)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--domain", default="AUTOSAR")
    parser.add_argument("--version", default="4-2-2")
    parser.add_argument("--expected-xsd-sha256")
    parser.add_argument("--expected-metadata-sha256")
    parser.add_argument("--write-sidecar", type=Path)
    parser.add_argument("--serialization-manifest", type=Path)
    parser.add_argument("--metadata-out", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--replace-output",
        action="store_true",
        help="Allow replacing a different sidecar/report/output file. Input metadata is never overwritten.",
    )
    parser.add_argument(
        "--replace-existing-xsd",
        action="store_true",
        help="Allow replacing existing, different xsd_* fields in the output/KG.",
    )
    parser.add_argument("--apply-neo4j", action="store_true")
    parser.add_argument("--neo4j-uri")
    parser.add_argument("--neo4j-user")
    parser.add_argument("--neo4j-password")
    parser.add_argument("--fail-on-conflict", action="store_true")
    return parser.parse_args(argv)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"JSON file does not exist: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _write_json_idempotent(path: Path, value: Any, *, replace: bool) -> str:
    path = path.resolve()
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path.exists():
        current = path.read_text(encoding="utf-8")
        try:
            if canonical_json(json.loads(current)) == canonical_json(value):
                return "noop"
        except json.JSONDecodeError:
            pass
        if not replace:
            raise FileExistsError(
                f"Refusing to replace different output {path}; pass --replace-output explicitly"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)
    return "written"


def run(args: argparse.Namespace) -> dict[str, Any]:
    xsd_path = args.xsd.resolve()
    metadata_path = args.metadata.resolve()
    if args.metadata_out and args.metadata_out.resolve() == metadata_path:
        raise ValueError("Input metadata is never overwritten; choose a different --metadata-out path")

    actual_xsd_hash = sha256_file(xsd_path)
    if args.expected_xsd_sha256 and args.expected_xsd_sha256.lower() != actual_xsd_hash:
        raise RuntimeError(
            "XSD source hash mismatch: "
            f"expected {args.expected_xsd_sha256.lower()}, got {actual_xsd_hash}"
        )

    metadata = _read_json(metadata_path)
    source_metadata_hash = sha256_file(metadata_path)
    if (
        args.expected_metadata_sha256
        and args.expected_metadata_sha256.lower() != source_metadata_hash
    ):
        raise RuntimeError(
            "Metadata source hash mismatch: "
            f"expected {args.expected_metadata_sha256.lower()}, got {source_metadata_hash}"
        )
    content_document = XsdContentModelExtractor(xsd_path).extract()
    serialization_manifest = build_serialization_manifest(
        xsd_path,
        content_document=content_document,
    )
    matched = MetadataMatcher(
        metadata,
        domain=args.domain,
        version=args.version,
    ).match(content_document)
    enriched, enrichment_report = build_enriched_metadata(
        metadata,
        matched,
        replace_existing=args.replace_existing_xsd,
    )

    matched["artifact"] = {
        "path": str(metadata_path),
        "sha256": source_metadata_hash,
        "enriched_semantic_sha256": metadata_sha256(enriched),
    }
    matched["enrichment"] = enrichment_report
    try:
        kg_rows = collect_updates(enriched, domain=args.domain, version=args.version)
        kg_preflight = {"status": "ready", "update_targets": len(kg_rows), "conflicts": []}
    except KgUpdateConflict as exc:
        kg_rows = []
        kg_preflight = {
            "status": "blocked",
            "update_targets": 0,
            "conflicts": exc.conflicts,
            "conflict_count": len(exc.conflicts),
        }
    matched["kg_preflight"] = kg_preflight

    actions: dict[str, Any] = {"mode": "apply-neo4j" if args.apply_neo4j else "dry-run"}
    if args.write_sidecar:
        actions["sidecar"] = _write_json_idempotent(
            args.write_sidecar,
            matched,
            replace=args.replace_output,
        )
    if args.serialization_manifest:
        actions["serialization_manifest"] = _write_json_idempotent(
            args.serialization_manifest,
            serialization_manifest,
            replace=args.replace_output,
        )
    if args.metadata_out:
        actions["metadata"] = _write_json_idempotent(
            args.metadata_out,
            enriched,
            replace=args.replace_output,
        )

    if args.apply_neo4j:
        load_dotenv(PROJECT_ROOT / ".env")
        uri = args.neo4j_uri or os.getenv("NEO4J_URI") or "neo4j://127.0.0.1:7687"
        user = args.neo4j_user or os.getenv("NEO4J_USER") or "neo4j"
        password = args.neo4j_password or os.getenv("NEO4J_PASSWORD") or os.getenv("NEO4J_PWD")
        if not password:
            raise ValueError("Neo4j password is not configured")
        if kg_preflight["status"] != "ready":
            raise RuntimeError("Neo4j enrichment blocked by KG entity-id collisions")
        actions["neo4j"] = apply_updates(
            uri=uri,
            user=user,
            password=password,
            rows=kg_rows,
            replace_existing=args.replace_existing_xsd,
        )

    compact_enrichment = {
        key: deepcopy(value)
        for key, value in enrichment_report.items()
        if key not in {"conflicts", "warnings"}
    }
    compact_enrichment["conflict_sample"] = deepcopy(
        (enrichment_report.get("conflicts") or [])[:10]
    )
    compact_enrichment["warning_sample"] = deepcopy(
        (enrichment_report.get("warnings") or [])[:10]
    )
    summary = {
        "source": deepcopy(matched.get("source")),
        "artifact": deepcopy(matched.get("artifact")),
        "stats": deepcopy(matched.get("stats")),
        "enrichment": compact_enrichment,
        "kg_preflight": deepcopy(kg_preflight),
        "serialization_manifest": {
            "path": str((args.serialization_manifest or DEFAULT_SERIALIZATION_MANIFEST).resolve()),
            "xsd_sha256": serialization_manifest["xsd"]["sha256"],
            "content_model_sha256": serialization_manifest["content_model_sha256"],
            "manifest_sha256": serialization_manifest["manifest_sha256"],
            "owner_count": serialization_manifest["stats"]["owners"],
        },
        "actions": actions,
    }
    if args.report:
        report_payload = deepcopy(summary)
        report_payload.pop("actions", None)
        actions["report"] = _write_json_idempotent(
            args.report,
            report_payload,
            replace=args.replace_output,
        )
    if args.fail_on_conflict and (
        matched.get("conflicts") or enrichment_report.get("conflicts")
    ):
        raise RuntimeError(
            "Conflicts were found; inspect the dry-run/sidecar report before applying enrichment"
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run(args)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

