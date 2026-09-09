"""In-process validation service for an ARXML bundle produced by Round2."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any

from .context import ValidationContextError, build_validation_context, normalize_validation_context
from .engine import ValidationEngine
from .implementation_manifest import validate_manifest
from .repair import build_repair_payload
from src.kg_builder.xsd_enrichment.serialization_manifest import (
    load_serialization_manifest,
)

SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


class GeneratedArxmlValidationService:
    def __init__(
        self,
        *,
        plan_path: Path,
        xsd_path: Path | None,
        reference_scope: str = "partial",
        dataset_sha256: str | None = None,
        validator_sha256: str | None = None,
        xsd_serialization_manifest_sha256: str | None = None,
    ) -> None:
        self.plan_path = plan_path.resolve()
        self.xsd_path = xsd_path.resolve() if xsd_path else None
        self.reference_scope = reference_scope
        self.dataset_sha256 = dataset_sha256
        self.validator_sha256 = validator_sha256
        self.xsd_serialization_manifest_sha256 = xsd_serialization_manifest_sha256
        self.engine = ValidationEngine.from_plan_file(
            self.plan_path,
            reference_scope=reference_scope,
            expected_dataset_sha256=dataset_sha256,
        )

    @classmethod
    def from_config(cls, config: Any) -> "GeneratedArxmlValidationService | None":
        validation = getattr(config, "validation", None)
        if validation is not None and not bool(getattr(validation, "enabled", True)):
            return None
        project_root = Path(__file__).resolve().parents[3]
        plan_value = getattr(validation, "plan_path", "") if validation is not None else ""
        xsd_value = getattr(validation, "xsd_path", "") if validation is not None else ""
        serialization_value = (
            getattr(validation, "xsd_serialization_manifest_path", "")
            if validation is not None
            else ""
        )
        xsd_enabled = bool(getattr(validation, "xsd_enabled", True)) if validation is not None else True
        scope = str(getattr(validation, "reference_scope", "partial") or "partial")
        plan_path = Path(plan_value) if plan_value else project_root / "src/generate_formal_constraints/v2/validation_plan.json"
        xsd_path = Path(xsd_value) if xsd_value else project_root / "src/validation/data/AUTOSAR_4-2-2.xsd"
        serialization_path = (
            Path(serialization_value)
            if serialization_value
            else project_root / "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json"
        )
        if not plan_path.is_absolute():
            plan_path = project_root / plan_path
        if not xsd_path.is_absolute():
            xsd_path = project_root / xsd_path
        if not serialization_path.is_absolute():
            serialization_path = project_root / serialization_path
        if not plan_path.is_file():
            raise FileNotFoundError(f"Validation plan not found: {plan_path}")
        if not xsd_path.is_file():
            raise FileNotFoundError(f"AUTOSAR XSD not found: {xsd_path}")
        serialization_manifest = load_serialization_manifest(
            serialization_path,
            xsd_path=xsd_path,
        )
        retrieval_manifest = project_root / "src/llm_generation/knowledge/v2/retrieval_manifest.json"
        if not retrieval_manifest.is_file():
            raise FileNotFoundError(f"ConstraintV2 retrieval manifest not found: {retrieval_manifest}")
        dataset_sha256 = str(
            json.loads(retrieval_manifest.read_text(encoding="utf-8-sig")).get("dataset_sha256") or ""
        )
        validator_manifest_path = project_root / "src/validation/v2/validator_manifest.json"
        validator_manifest = validate_manifest(
            validator_manifest_path,
            plan_path=plan_path,
            xsd_path=xsd_path if xsd_enabled else None,
            dataset_manifest_path=retrieval_manifest,
            xsd_serialization_manifest_path=serialization_path,
        )
        return cls(
            plan_path=plan_path,
            xsd_path=xsd_path if xsd_enabled else None,
            reference_scope=scope,
            dataset_sha256=dataset_sha256,
            validator_sha256=str(validator_manifest["validator_sha256"]),
            xsd_serialization_manifest_sha256=str(
                serialization_manifest["manifest_sha256"]
            ),
        )

    def build_validation_context(
        self,
        retrieval_trace: dict[str, Any] | None,
        *,
        declared_use_cases: list[str] | None = None,
        declared_constraint_ids: list[str] | None = None,
        declared_targets: dict[str, list[str]] | None = None,
        declared_parameters: dict[str, dict[str, dict[str, Any]]] | None = None,
        intent_scope: str = "partial",
        declared_capability_scopes: list[dict[str, Any]] | None = None,
        manual_evidence_scope: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.dataset_sha256:
            raise ValueError("validation service has no hash-pinned ConstraintV2 dataset")
        return build_validation_context(
            retrieval_trace,
            expected_dataset_sha256=self.dataset_sha256,
            reference_scope=self.reference_scope,
            declared_use_cases=declared_use_cases,
            declared_constraint_ids=declared_constraint_ids,
            declared_targets=declared_targets,
            declared_parameters=declared_parameters,
            intent_scope=intent_scope,
            declared_capability_scopes=declared_capability_scopes,
            manual_evidence_scope=manual_evidence_scope,
            expected_validator_sha256=self.validator_sha256,
            expected_xsd_serialization_manifest_sha256=
                self.xsd_serialization_manifest_sha256,
        )

    @staticmethod
    def _filename(kind: str, name: str) -> str:
        safe = SAFE_NAME.sub("_", name).strip("._") or "unnamed"
        digest = hashlib.sha256(f"{kind}/{name}".encode("utf-8")).hexdigest()[:8]
        return f"{kind}_{safe}_{digest}.arxml"

    @staticmethod
    def _replace_files(report: dict, file_names: dict[str, str]) -> None:
        report["inputs"] = [file_names.get(str(Path(item).resolve()), item) for item in report.get("inputs", [])]
        for finding in report.get("findings", []):
            location = finding.get("location") or {}
            raw = location.get("file")
            if raw:
                location["file"] = file_names.get(str(Path(raw).resolve()), raw)
        for rule in report.get("rules", []):
            for violation in rule.get("violations", []):
                location = violation.get("location") or {}
                raw = location.get("file")
                if raw:
                    location["file"] = file_names.get(str(Path(raw).resolve()), raw)
        for review in report.get("manual_review", []):
            for location in review.get("locations", []):
                raw = location.get("file")
                if raw:
                    location["file"] = file_names.get(str(Path(raw).resolve()), raw)

    def validate_bundle(
        self,
        bundle: dict[str, Any],
        validation_context: dict[str, Any] | None = None,
    ) -> dict:
        try:
            context = normalize_validation_context(
                validation_context,
                expected_dataset_sha256=self.dataset_sha256,
                expected_validator_sha256=self.validator_sha256,
            expected_xsd_serialization_manifest_sha256=
                self.xsd_serialization_manifest_sha256,
            )
        except ValidationContextError as error:
            return self.engine._context_error_report([], error)
        documents: list[tuple[str, str]] = []
        for kind in ("components", "interfaces"):
            for name, xml_text in sorted((bundle.get(kind) or {}).items()):
                if isinstance(xml_text, str) and xml_text.strip():
                    documents.append((f"{kind}/{name}.arxml", xml_text))
        if not documents:
            return {
                "schema_version": "2.0",
                "decision": "ERROR",
                "valid": False,
                "reference_scope": self.reference_scope,
                "validation_context": self.engine._context_report(context),
                "inputs": [],
                "summary": {
                    "PASS": 0, "FAIL": 0, "NOT_APPLICABLE": 0,
                    "NOT_EVALUATED": 0, "ERROR": 1,
                    "finding_count": 0, "must_not_evaluated": 0,
                    "manual_review_applicable": 0,
                    "manual_review_not_applicable": 0,
                },
                "findings": [],
                "repair": build_repair_payload([]),
                "manual_review": [],
                "artifact_profile": self.engine._error_artifact_profile(
                    context, "Round2 did not produce any ARXML documents."
                ),
                "rules": [],
                "notes": ["Round2 did not produce any ARXML documents."],
            }

        with tempfile.TemporaryDirectory(prefix="arxml-validation-") as directory:
            root = Path(directory)
            paths: list[Path] = []
            file_names: dict[str, str] = {}
            for logical_name, xml_text in documents:
                kind, name = logical_name.split("/", 1)
                path = root / self._filename(kind, name.removesuffix(".arxml"))
                path.write_text(xml_text, encoding="utf-8")
                paths.append(path)
                file_names[str(path.resolve())] = logical_name
            report = self.engine.validate(paths, self.xsd_path, context)
            self._replace_files(report, file_names)
        repair = report.get("repair") or {}
        for action in repair.get("actions", []):
            raw = action.get("file")
            if raw:
                action["file"] = file_names.get(str(Path(raw).resolve()), raw)
        remapped: dict[str, list[dict]] = {}
        for file_name, actions in (repair.get("by_file") or {}).items():
            logical = file_names.get(str(Path(file_name).resolve()), file_name)
            remapped[logical] = actions
        if repair:
            repair["by_file"] = remapped
            # Rebuild the prompt after temporary paths have been normalized.
            normalized = build_repair_payload(
                report.get("findings", []), report.get("rules")
            )
            repair["llm_prompt"] = normalized["llm_prompt"]
        report["plan"] = str(self.plan_path)
        report["xsd"] = str(self.xsd_path) if self.xsd_path else None
        report["validator_sha256"] = self.validator_sha256
        return report
