"""Deterministic, credential-free schema client for full-context offline E2E.

This client is test infrastructure.  It executes the same Round1/Round2 and
typed-repair schema contracts as the provider client, but derives responses
only from the frozen ASW requirement manifest and the schema passed by the
real runner.  It never opens a network connection.
"""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from precheck_all_asw_requirements import (
    canonical_component_instance,
    canonical_component_plan,
    canonical_interface_instance,
    interface_plans,
)


ROOT = Path(__file__).resolve().parent
REQUIREMENTS_ROOT = Path(r"E:\54239\Documents\atlas_autosar_requirements_v3")
REQUIREMENTS_PATH = REQUIREMENTS_ROOT / "asw_cases_v3.yaml"
SCRIPTED_ENDPOINT = "offline://atlas-v16-scripted-schema-client"
SCRIPTED_ENDPOINT_SHA256 = hashlib.sha256(SCRIPTED_ENDPOINT.encode("utf-8")).hexdigest()


def _find_unique(value: Any, key: str) -> Any:
    found: list[Any] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if key in node:
                found.append(node[key])
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return found[0] if len(found) == 1 else None


def _value_for_schema(schema: dict[str, Any], source: Any = None) -> Any:
    """Project a reference value into one strict schema, filling only gaps."""

    if "const" in schema:
        return deepcopy(schema["const"])
    if schema.get("enum"):
        if source in schema["enum"]:
            return deepcopy(source)
        return deepcopy(schema["enum"][0])
    kind = schema.get("type")
    if kind == "object":
        properties = schema.get("properties") or {}
        output: dict[str, Any] = {}
        source_by_identity = (
            {
                str(item.get("SHORT-NAME")): item
                for item in source
                if isinstance(item, dict) and item.get("SHORT-NAME")
            }
            if isinstance(source, list)
            else {}
        )
        for key, child_schema in properties.items():
            child_source = None
            if isinstance(source, dict) and key in source:
                child_source = source[key]
            elif key in source_by_identity:
                child_source = source_by_identity[key]
            elif source is not None:
                child_source = _find_unique(source, key)
            output[key] = _value_for_schema(child_schema, child_source)
        return output
    if kind == "array":
        items = schema.get("items") or {}
        if isinstance(source, list) and source:
            return [_value_for_schema(items, item) for item in source]
        minimum = int(schema.get("minItems") or 0)
        return [_value_for_schema(items) for _ in range(minimum)]
    if kind == "string":
        if isinstance(source, (str, int, float)):
            return str(source)
        return "offline_scripted_value"
    if kind == "integer":
        if isinstance(source, (int, float)) and not isinstance(source, bool):
            return int(source)
        return int(schema.get("minimum") or 0)
    if kind == "number":
        if isinstance(source, (int, float)) and not isinstance(source, bool):
            return source
        return schema.get("minimum", 0.0)
    if kind == "boolean":
        return bool(source) if isinstance(source, bool) else False
    if source is not None:
        return deepcopy(source)
    return None


class ScriptedAutosarClient:
    """A strict-schema fake with the audit surface of the concrete client."""

    def __init__(
        self,
        case_id: str,
        *,
        cohort: str = "primary",
        requested_model: str = "gpt-5.6-luna",
        fail_stage: str | None = None,
    ) -> None:
        import sys

        if cohort == "primary":
            sys.path.insert(0, str(REQUIREMENTS_ROOT))
            from render_cases import (
                event_short_name,
                load_manifest,
                variable_access_short_name,
            )

            manifest = load_manifest(REQUIREMENTS_PATH)
        elif cohort == "heldout":
            from heldout_v3_runtime import (
                event_short_name,
                load_manifest,
                variable_access_short_name,
            )

            manifest = load_manifest()
        else:
            raise ValueError(f"unsupported scripted AUTOSAR cohort: {cohort!r}")
        cases = {item["case_id"]: item for item in manifest["cases"]}
        if case_id not in cases:
            raise ValueError(f"unknown scripted ASW case: {case_id}")
        self.case_id = case_id
        self.cohort = cohort
        self.case = cases[case_id]
        self.manifest = manifest
        self.requested_model = requested_model
        self.fail_stage = fail_stage
        self.call_count = 0
        self.success_count = 0
        self.error_count = 0
        self.response_audit: list[dict[str, Any]] = []
        self.pipeline_phase = "unassigned"
        self.transport_route_policy = "offline_scripted_no_network"
        self.last_raw_schema_payload: dict[str, Any] | None = None
        self.last_raw_schema_status = "NOT_EVALUATED"
        self._event_short_name = event_short_name
        self._variable_access_short_name = variable_access_short_name

    def _stage_and_source(self, schema: dict[str, Any]) -> tuple[str, Any]:
        properties = schema.get("properties") or {}
        if "component_plan" in properties:
            component = canonical_component_plan(self.case)
            interfaces = interface_plans(self.case, self.manifest)
            source = {
                "system_analysis": {},
                "component_plan": [component],
                "interface_plan": interfaces,
                "component_generation_order": [self.case["component"]],
                "connection_topology": {},
                "architecture_rationale": {},
            }
            return "round1", source
        if "patches" in properties:
            return "repair", None
        if "SENDER-RECEIVER-INTERFACE" in properties:
            plans = interface_plans(self.case, self.manifest)
            return "interface", canonical_interface_instance(plans)
        if "APPLICATION-SW-COMPONENT-TYPE" in properties:
            return (
                "component",
                canonical_component_instance(
                    self.case,
                    self.manifest,
                    event_short_name=self._event_short_name,
                    variable_access_short_name=self._variable_access_short_name,
                ),
            )
        return "repair_value", None

    def _audit(
        self,
        *,
        stage: str,
        seed: int | None,
        temperature: float | None,
        max_retries: int | None,
        status: str,
    ) -> None:
        audit = {
            "schema_version": "atlas.offline_scripted_provider_audit.v1",
            "credentials_included": False,
            "actual_paid_provider_call": False,
            "stage": stage,
            "provider_call_id": f"offline-{self.case_id}-{self.call_count:03d}",
            "pipeline_phase": self.pipeline_phase,
            "logical_call_index": self.call_count,
            "sdk_attempt": 1,
            "status": status,
            "requested_model": self.requested_model,
            "response_model": "offline-scripted-schema-client",
            "response_id": f"offline-{self.case_id}-{self.call_count:03d}",
            "created": 0,
            "system_fingerprint": "deterministic-requirement-xsd-reference",
            "service_tier": "offline",
            "finish_reason": "stop" if status == "PASS" else "scripted_failure",
            "transport": "offline_scripted_nonstream",
            "response_format": "strict_json_schema",
            "seed": seed,
            "temperature": temperature,
            "reasoning_effort": "low",
            "max_completion_tokens": 128000,
            "request_timeout_seconds": 180.0,
            "max_attempts": int(max_retries or 1),
            "provider_endpoint_sha256": SCRIPTED_ENDPOINT_SHA256,
            "transport_route_policy": self.transport_route_policy,
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
            },
        }
        self.response_audit.append(audit)
        audit_path = os.environ.get("ATLAS_PROVIDER_AUDIT_PATH")
        if audit_path:
            path = Path(audit_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(audit, sort_keys=True) + "\n")

    def generate_with_schema(
        self,
        *,
        prompt: str,
        schema: dict[str, Any],
        seed: int | None = None,
        temperature: float | None = None,
        max_retries: int | None = None,
        document_files: Any = None,
        **_kwargs: Any,
    ) -> tuple[dict[str, Any], int, int, int]:
        del prompt, document_files
        self.call_count += 1
        stage, source = self._stage_and_source(schema)
        if self.fail_stage == stage:
            self.error_count += 1
            self.last_raw_schema_payload = None
            self.last_raw_schema_status = "NOT_EVALUATED"
            self._audit(
                stage=stage,
                seed=seed,
                temperature=temperature,
                max_retries=max_retries,
                status="SCRIPTED_FAILURE",
            )
            raise RuntimeError(f"SCRIPTED_{stage.upper()}_FAILURE")
        response = _value_for_schema(schema, source)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(response),
            key=lambda error: list(error.absolute_path),
        )
        self.last_raw_schema_payload = deepcopy(response)
        self.last_raw_schema_status = "PASS" if not errors else "RAW_FAIL"
        if errors:
            self.error_count += 1
            self._audit(
                stage=stage,
                seed=seed,
                temperature=temperature,
                max_retries=max_retries,
                status="RAW_FAIL",
            )
            raise ValueError(f"scripted response schema failure: {errors[0].message}")
        self.success_count += 1
        self._audit(
            stage=stage,
            seed=seed,
            temperature=temperature,
            max_retries=max_retries,
            status="PASS",
        )
        return response, 0, 0, 0
