"""Versioned validation-context manifests for generation and validation.

The manifest does not decide whether a rule is true.  It records which
ConstraintV2 records informed generation. Retrieval relevance is kept separate
from explicit user/system intent; only declared use cases or constraint ids can
satisfy an intent-dependent rule.  Dataset identity is always
hash-pinned; conflicting or malformed manifests are rejected fail-closed.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ValidationContextError(ValueError):
    """Raised when a validation-context manifest cannot be trusted."""


def _fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_validation_context(
    retrieval_trace: dict[str, Any] | None,
    *,
    expected_dataset_sha256: str,
    reference_scope: str = "partial",
    declared_use_cases: list[str] | None = None,
    declared_constraint_ids: list[str] | None = None,
    declared_targets: dict[str, list[str]] | None = None,
    declared_parameters: dict[str, dict[str, dict[str, Any]]] | None = None,
    intent_scope: str = "partial",
    declared_capability_scopes: list[dict[str, Any]] | None = None,
    manual_evidence_scope: dict[str, Any] | None = None,
    expected_validator_sha256: str | None = None,
    expected_xsd_serialization_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic manifest from the real Round2 retrieval trace."""
    if not SHA256.fullmatch(str(expected_dataset_sha256 or "")):
        raise ValidationContextError("expected ConstraintV2 dataset SHA-256 is missing or invalid")
    if reference_scope not in {"partial", "complete"}:
        raise ValidationContextError("reference_scope must be 'partial' or 'complete'")
    if intent_scope not in {"partial", "complete"}:
        raise ValidationContextError("intent_scope must be 'partial' or 'complete'")
    if expected_validator_sha256 is not None and not SHA256.fullmatch(str(expected_validator_sha256)):
        raise ValidationContextError("expected validator SHA-256 is invalid")
    if (
        expected_xsd_serialization_manifest_sha256 is not None
        and not SHA256.fullmatch(str(expected_xsd_serialization_manifest_sha256))
    ):
        raise ValidationContextError("expected XSD serialization manifest SHA-256 is invalid")

    scopes: dict[str, dict[str, Any]] = {}
    selected: set[str] = set()
    for scope_name, raw in sorted((retrieval_trace or {}).items()):
        if not isinstance(raw, dict):
            raise ValidationContextError(f"retrieval scope {scope_name!r} is not an object")
        dataset_sha256 = str(raw.get("dataset_sha256") or "")
        if dataset_sha256 != expected_dataset_sha256:
            raise ValidationContextError(
                f"retrieval scope {scope_name!r} dataset hash {dataset_sha256!r} does not match "
                f"the expected ConstraintV2 dataset {expected_dataset_sha256}"
            )
        constraint_ids = sorted({str(item) for item in raw.get("constraint_ids") or [] if str(item)})
        declared_count = raw.get("result_count")
        if declared_count is not None and int(declared_count) != len(constraint_ids):
            raise ValidationContextError(
                f"retrieval scope {scope_name!r} result_count does not match its unique constraint ids"
            )
        selected.update(constraint_ids)
        scopes[str(scope_name)] = {
            "backend": str(raw.get("backend") or "unknown"),
            "dataset_sha256": dataset_sha256,
            "result_count": len(constraint_ids),
            "fallback_reason": str(raw.get("fallback_reason") or ""),
            "constraint_ids": constraint_ids,
        }

    use_cases = sorted({str(item).strip() for item in declared_use_cases or [] if str(item).strip()})
    declared_ids = sorted({str(item).strip() for item in declared_constraint_ids or [] if str(item).strip()})
    missing_declared = sorted(set(declared_ids) - selected)
    if missing_declared:
        raise ValidationContextError(
            "explicit validation constraints were not present in the generation retrieval trace: "
            + ", ".join(missing_declared)
        )

    targets: dict[str, list[str]] = {}
    for raw_id, raw_paths in sorted((declared_targets or {}).items()):
        constraint_id = str(raw_id).strip()
        if constraint_id not in declared_ids:
            raise ValidationContextError(
                f"validation target {constraint_id!r} has no matching explicitly declared constraint"
            )
        if not isinstance(raw_paths, list):
            raise ValidationContextError(f"validation targets for {constraint_id!r} must be an array")
        normalized_paths = sorted({
            "/" + "/".join(part for part in str(path).strip().replace("\\", "/").split("/") if part)
            for path in raw_paths if str(path).strip()
        })
        if not normalized_paths:
            raise ValidationContextError(
                f"validation targets for {constraint_id!r} must contain at least one ARXML short-name path"
            )
        if any(path == "/" for path in normalized_paths):
            raise ValidationContextError(f"validation target for {constraint_id!r} is empty")
        targets[constraint_id] = normalized_paths

    parameters: dict[str, dict[str, dict[str, Any]]] = {}
    for raw_id, raw_target_values in sorted((declared_parameters or {}).items()):
        constraint_id = str(raw_id).strip()
        if constraint_id not in declared_ids:
            raise ValidationContextError(
                f"validation parameters {constraint_id!r} have no matching explicitly declared constraint"
            )
        if not isinstance(raw_target_values, dict):
            raise ValidationContextError(f"validation parameters for {constraint_id!r} must be an object")
        normalized_target_values: dict[str, dict[str, Any]] = {}
        for raw_path, raw_values in sorted(raw_target_values.items()):
            target_path = "/" + "/".join(
                part for part in str(raw_path).strip().replace("\\", "/").split("/") if part
            )
            if target_path not in set(targets.get(constraint_id) or []):
                raise ValidationContextError(
                    f"validation parameters target {target_path!r} is not an exact declared target for {constraint_id!r}"
                )
            if not isinstance(raw_values, dict) or not raw_values:
                raise ValidationContextError(
                    f"validation parameters for {constraint_id!r} target {target_path!r} must be a non-empty object"
                )
            try:
                json.dumps(raw_values, ensure_ascii=False, sort_keys=True, allow_nan=False)
            except (TypeError, ValueError) as error:
                raise ValidationContextError(f"validation parameters are not canonical JSON values: {error}") from error
            normalized_target_values[target_path] = raw_values
        parameters[constraint_id] = normalized_target_values

    capability_scopes: list[dict[str, Any]] = []
    seen_scope_paths: set[str] = set()
    for position, raw_scope in enumerate(declared_capability_scopes or []):
        if not isinstance(raw_scope, dict):
            raise ValidationContextError(
                f"declared_capability_scopes[{position}] must be an object"
            )
        scope_path = "/" + "/".join(
            part
            for part in str(raw_scope.get("scope_path") or "")
            .strip()
            .replace("\\", "/")
            .split("/")
            if part
        )
        if scope_path == "/" or scope_path in seen_scope_paths:
            raise ValidationContextError(
                f"declared_capability_scopes[{position}].scope_path is empty or duplicated"
            )
        seen_scope_paths.add(scope_path)
        raw_capabilities = raw_scope.get("capabilities")
        if not isinstance(raw_capabilities, list):
            raise ValidationContextError(
                f"declared_capability_scopes[{position}].capabilities must be an array"
            )
        capabilities = sorted(
            {str(item).strip() for item in raw_capabilities if str(item).strip()}
        )
        unsupported = sorted(set(capabilities) - {"complete_reference_scope"})
        if not capabilities or unsupported:
            raise ValidationContextError(
                f"declared_capability_scopes[{position}] has unsupported capabilities: "
                + ", ".join(unsupported or ["<empty>"])
            )
        raw_constraint_ids = raw_scope.get("constraint_ids")
        if not isinstance(raw_constraint_ids, list):
            raise ValidationContextError(
                f"declared_capability_scopes[{position}].constraint_ids must be an array"
            )
        scope_constraint_ids = sorted(
            {str(item).strip() for item in raw_constraint_ids if str(item).strip()}
        )
        missing_scope_declarations = sorted(
            set(scope_constraint_ids) - set(declared_ids)
        )
        if not scope_constraint_ids or missing_scope_declarations:
            raise ValidationContextError(
                f"declared_capability_scopes[{position}] has undeclared constraint ids: "
                + ", ".join(missing_scope_declarations or ["<empty>"])
            )
        evidence_sha256 = str(raw_scope.get("evidence_sha256") or "").lower()
        if not SHA256.fullmatch(evidence_sha256):
            raise ValidationContextError(
                f"declared_capability_scopes[{position}].evidence_sha256 is invalid"
            )
        capability_scopes.append(
            {
                "scope_path": scope_path,
                "constraint_ids": scope_constraint_ids,
                "capabilities": capabilities,
                "evidence_sha256": evidence_sha256,
                "evidence_kind": str(
                    raw_scope.get("evidence_kind") or "structured_requirement_context"
                ),
            }
        )
    capability_scopes.sort(key=lambda item: item["scope_path"])

    normalized_manual_scope: dict[str, Any] | None = None
    if manual_evidence_scope is not None:
        if not isinstance(manual_evidence_scope, dict):
            raise ValidationContextError("manual_evidence_scope must be an object")
        if manual_evidence_scope.get("complete") is not True:
            raise ValidationContextError(
                "manual_evidence_scope.complete must be true when the scope is declared"
            )
        raw_excluded = manual_evidence_scope.get("excluded_capabilities")
        if not isinstance(raw_excluded, list):
            raise ValidationContextError(
                "manual_evidence_scope.excluded_capabilities must be an array"
            )
        excluded = sorted(
            {str(item).strip() for item in raw_excluded if str(item).strip()}
        )
        if not excluded:
            raise ValidationContextError(
                "manual_evidence_scope.excluded_capabilities must not be empty"
            )
        evidence_sha256 = str(manual_evidence_scope.get("evidence_sha256") or "").lower()
        if not SHA256.fullmatch(evidence_sha256):
            raise ValidationContextError(
                "manual_evidence_scope.evidence_sha256 is invalid"
            )
        normalized_manual_scope = {
            "profile_id": str(manual_evidence_scope.get("profile_id") or "").strip(),
            "complete": True,
            "excluded_capabilities": excluded,
            "evidence_sha256": evidence_sha256,
        }
        if not normalized_manual_scope["profile_id"]:
            raise ValidationContextError("manual_evidence_scope.profile_id is required")

    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "source": "round2_constraint_retrieval",
        "dataset_sha256": expected_dataset_sha256,
        "model_scope": "generated_bundle",
        "reference_scope": reference_scope,
        "intent_scope": intent_scope,
        "active_purposes": ["generation_context", "automatic_validation", "repair_guidance"],
        "selected_constraint_ids": sorted(selected),
        "declared_use_cases": use_cases,
        "declared_constraint_ids": declared_ids,
        "declared_targets": targets,
        "selection_scopes": scopes,
    }
    if capability_scopes:
        manifest["declared_capability_scopes"] = capability_scopes
    if normalized_manual_scope is not None:
        manifest["manual_evidence_scope"] = normalized_manual_scope
    if expected_validator_sha256 is not None:
        manifest["validator_sha256"] = expected_validator_sha256
    if expected_xsd_serialization_manifest_sha256 is not None:
        manifest["xsd_serialization_manifest_sha256"] = (
            expected_xsd_serialization_manifest_sha256
        )
    if parameters:
        manifest["declared_parameters"] = parameters
    manifest["manifest_sha256"] = _fingerprint(manifest)
    return manifest


def normalize_validation_context(
    value: dict[str, Any] | None,
    *,
    expected_dataset_sha256: str | None = None,
    expected_validator_sha256: str | None = None,
    expected_xsd_serialization_manifest_sha256: str | None = None,
) -> dict[str, Any] | None:
    """Validate and canonicalize an externally supplied context manifest."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValidationContextError("validation_context must be an object")
    if value.get("schema_version") != "1.0":
        raise ValidationContextError("unsupported validation_context schema_version")
    dataset_sha256 = str(value.get("dataset_sha256") or "")
    if not SHA256.fullmatch(dataset_sha256):
        raise ValidationContextError("validation_context dataset_sha256 is missing or invalid")
    if expected_dataset_sha256 and dataset_sha256 != expected_dataset_sha256:
        raise ValidationContextError(
            f"validation_context dataset hash {dataset_sha256} does not match expected {expected_dataset_sha256}"
        )
    reference_scope = str(value.get("reference_scope") or "")
    if reference_scope not in {"partial", "complete"}:
        raise ValidationContextError("validation_context reference_scope is invalid")
    validator_sha256 = str(value.get("validator_sha256") or "")
    if validator_sha256 and not SHA256.fullmatch(validator_sha256):
        raise ValidationContextError("validation_context validator_sha256 is invalid")
    if expected_validator_sha256:
        if not validator_sha256:
            raise ValidationContextError("validation_context validator_sha256 is missing")
        if validator_sha256 != expected_validator_sha256:
            raise ValidationContextError("validation_context validator hash does not match the executable validator")
    serialization_sha256 = str(value.get("xsd_serialization_manifest_sha256") or "")
    if serialization_sha256 and not SHA256.fullmatch(serialization_sha256):
        raise ValidationContextError(
            "validation_context XSD serialization manifest SHA-256 is invalid"
        )
    if expected_xsd_serialization_manifest_sha256:
        if not serialization_sha256:
            raise ValidationContextError(
                "validation_context XSD serialization manifest SHA-256 is missing"
            )
        if serialization_sha256 != expected_xsd_serialization_manifest_sha256:
            raise ValidationContextError(
                "validation_context XSD serialization manifest hash does not match generation"
            )
    scopes = value.get("selection_scopes")
    if not isinstance(scopes, dict):
        raise ValidationContextError("validation_context selection_scopes must be an object")

    rebuilt = build_validation_context(
        scopes,
        expected_dataset_sha256=dataset_sha256,
        reference_scope=reference_scope,
        declared_use_cases=list(value.get("declared_use_cases") or []),
        declared_constraint_ids=list(value.get("declared_constraint_ids") or []),
        declared_targets=dict(value.get("declared_targets") or {}),
        declared_parameters=dict(value.get("declared_parameters") or {}),
        intent_scope=str(value.get("intent_scope") or "partial"),
        declared_capability_scopes=list(
            value.get("declared_capability_scopes") or []
        ),
        manual_evidence_scope=(
            dict(value.get("manual_evidence_scope") or {})
            if value.get("manual_evidence_scope") is not None
            else None
        ),
        expected_validator_sha256=validator_sha256 or None,
        expected_xsd_serialization_manifest_sha256=serialization_sha256 or None,
    )
    declared_ids = sorted({str(item) for item in value.get("selected_constraint_ids") or [] if str(item)})
    if declared_ids != rebuilt["selected_constraint_ids"]:
        raise ValidationContextError("validation_context selected_constraint_ids do not match selection_scopes")
    if value.get("source") != rebuilt["source"]:
        raise ValidationContextError("validation_context source is invalid")
    if value.get("model_scope") != rebuilt["model_scope"]:
        raise ValidationContextError("validation_context model_scope is invalid")
    purposes = sorted({str(item) for item in value.get("active_purposes") or [] if str(item)})
    if purposes != sorted(rebuilt["active_purposes"]):
        raise ValidationContextError("validation_context active_purposes are invalid")
    declared_fingerprint = str(value.get("manifest_sha256") or "")
    if declared_fingerprint != rebuilt["manifest_sha256"]:
        raise ValidationContextError("validation_context manifest_sha256 does not match its content")
    return rebuilt


def activation_reason(rule: dict[str, Any], context: dict[str, Any] | None) -> str | None:
    """Return a fail-closed reason when a rule's explicit intent gate is unmet."""
    activation = (rule.get("formal_spec") or {}).get("activation") or {}
    if not activation:
        return None
    if not isinstance(activation, dict):
        return "Rule activation metadata is malformed."
    if activation.get("requires_validation_context") and context is None:
        return "Rule requires a hash-pinned validation context, but none was provided."
    if activation.get("requires_selected_constraint"):
        if context is None:
            return "Rule requires generation-time selection, but no validation context was provided."
        if rule.get("constraint_id") not in set(context.get("selected_constraint_ids") or []):
            return "Constraint was not selected for this generation context."
    if activation.get("requires_declared_constraint"):
        if context is None:
            return "Rule requires explicit constraint intent, but no validation context was provided."
        if rule.get("constraint_id") not in set(context.get("declared_constraint_ids") or []):
            return "Constraint was retrieved but was not explicitly declared as validation intent."
    if activation.get("requires_declared_targets"):
        if context is None:
            return "Rule requires explicit ARXML target bindings, but no validation context was provided."
        targets = (context.get("declared_targets") or {}).get(rule.get("constraint_id")) or []
        if not targets:
            return (
                "Constraint is declared as validation intent but has no exact ARXML short-name target binding."
            )
    required_use_cases = set(activation.get("required_use_cases") or [])
    declared_use_cases = set((context or {}).get("declared_use_cases") or [])
    missing_use_cases = sorted(required_use_cases - declared_use_cases)
    if missing_use_cases:
        return "Validation context is missing explicitly declared use cases: " + ", ".join(missing_use_cases)
    required_purposes = set(activation.get("required_purposes") or [])
    active_purposes = set((context or {}).get("active_purposes") or [])
    missing = sorted(required_purposes - active_purposes)
    if missing:
        return "Validation context is missing required purposes: " + ", ".join(missing)
    return None
