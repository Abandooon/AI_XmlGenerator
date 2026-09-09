"""Run one fail-closed AUTOSAR generation probe against a selected model.

The script reads the existing ATLAS API configuration without printing or
persisting credentials. Probe artifacts contain only hashes of endpoint/config
context, never the endpoint URL or API key.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml
from dotenv import dotenv_values
from jsonschema import Draft202012Validator
from lxml import etree
from openai import OpenAI


ATLAS_ROOT = Path(r"E:\git projects\AI_XmlGenerator")
OUTPUT_ROOT = Path(r"E:\54239\Documents\atlas_model_probe\outputs")
CONFIG_PATH = ATLAS_ROOT / "config" / "llm_api_config.yaml"
PLAN_PATH = ATLAS_ROOT / "src" / "generate_formal_constraints" / "v2" / "validation_plan.json"
XSD_PATH = ATLAS_ROOT / "src" / "validation" / "data" / "AUTOSAR_4-2-2.xsd"
RETRIEVAL_MANIFEST = (
    ATLAS_ROOT / "src" / "llm_generation" / "knowledge" / "v2" / "retrieval_manifest.json"
)

MODELS = ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol")
REASONING_EFFORT = "medium"
MAX_OUTPUT_TOKENS = 16_384
PROBE_PROTOCOL = "autosar-component-fragment-v2"

# Prices are the user's endpoint prices from the supplied screenshot, including
# its displayed x1.5 multiplier. They are not asserted to be OpenAI list prices.
ENDPOINT_PRICES_USD_PER_MTOK = {
    "gpt-5.6-luna": {"input": 0.20 * 1.5, "output": 1.20 * 1.5},
    "gpt-5.6-terra": {"input": 2.00 * 1.5, "output": 12.00 * 1.5},
    "gpt-5.6-sol": {"input": 5.00 * 1.5, "output": 30.00 * 1.5},
}

PROMPT = """Generate one self-contained AUTOSAR Classic Platform 4.2.2 ARXML document for a deliberately simplified atomic application software component. This is a tool-chain benchmark, not a complete ECU configuration.

Required model content:
1. One APPLICATION-SW-COMPONENT-TYPE named ASW_TemperatureMonitor.
2. One SENDER-RECEIVER-INTERFACE named If_RawTemperature with one VARIABLE-DATA-PROTOTYPE named RawTemperature.
3. One SENDER-RECEIVER-INTERFACE named If_TemperatureStatus with one VARIABLE-DATA-PROTOTYPE named TemperatureStatus.
4. One R-PORT-PROTOTYPE named Rp_RawTemperature, typed by /Interfaces/If_RawTemperature.
5. One P-PORT-PROTOTYPE named Pp_TemperatureStatus, typed by /Interfaces/If_TemperatureStatus.
6. One SWC-INTERNAL-BEHAVIOR named Ib_TemperatureMonitor and one RUNNABLE-ENTITY named Re_TemperatureMonitor.
7. A TIMING-EVENT that starts Re_TemperatureMonitor every 0.01 seconds.
8. The runnable shall read Rp_RawTemperature/RawTemperature and write Pp_TemperatureStatus/TemperatureStatus using AUTOSAR variable-access structures.
9. The required port shall contain a NONQUEUED-RECEIVER-COM-SPEC for RawTemperature with a numerical INIT-VALUE of 0, ALIVE-TIMEOUT 0.1 seconds, and HANDLE-TIMEOUT-TYPE NONE, where permitted by AUTOSAR 4.2.2.
10. Include any minimal application/implementation data-type declarations needed for resolvable TYPE-TREF references.

Use the AUTOSAR 4.2.2 namespace and normal AR-PACKAGES/AR-PACKAGE/ELEMENTS containment. Preserve valid reference paths, DEST values, multiplicities, and XSD element order. Do not add ECU, BSW, system mapping, network, or deployment configuration. Do not use Markdown fences.

Return the complete ARXML in the arxml field. Record only genuinely necessary modeling assumptions in assumptions. If a requested semantic detail cannot be represented without information not supplied above, record it in unresolved instead of silently inventing external configuration."""

OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["arxml", "assumptions", "unresolved"],
    "properties": {
        "arxml": {"type": "string"},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "unresolved": {"type": "array", "items": {"type": "string"}},
    },
}

EXPECTED_MARKERS = (
    "APPLICATION-SW-COMPONENT-TYPE",
    "ASW_TemperatureMonitor",
    "SENDER-RECEIVER-INTERFACE",
    "If_RawTemperature",
    "RawTemperature",
    "If_TemperatureStatus",
    "TemperatureStatus",
    "R-PORT-PROTOTYPE",
    "Rp_RawTemperature",
    "P-PORT-PROTOTYPE",
    "Pp_TemperatureStatus",
    "SWC-INTERNAL-BEHAVIOR",
    "Ib_TemperatureMonitor",
    "RUNNABLE-ENTITY",
    "Re_TemperatureMonitor",
    "TIMING-EVENT",
    "VARIABLE-ACCESS",
    "NONQUEUED-RECEIVER-COM-SPEC",
    "ALIVE-TIMEOUT",
    "HANDLE-TIMEOUT-TYPE",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))


def normalize_base_url(value: str) -> str:
    url = str(value or "").strip().rstrip("/")
    if not url:
        raise ValueError("The configured API base URL is empty.")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if not url.endswith("/v1"):
        url += "/v1"
    return url


def load_transport() -> tuple[OpenAI, str]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    llm = config.get("llm") or {}
    dotenv = dotenv_values(ATLAS_ROOT / ".env")
    api_key = str(
        os.environ.get("ATLAS_LLM_API_KEY")
        or os.environ.get("PIL_LLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("LLM_API_KEY")
        or dotenv.get("ATLAS_LLM_API_KEY")
        or dotenv.get("PIL_LLM_API_KEY")
        or dotenv.get("OPENAI_API_KEY")
        or dotenv.get("LLM_API_KEY")
        or dotenv.get("API_KEY")
        or llm.get("api_key")
        or ""
    ).strip()
    base_url = normalize_base_url(
        str(os.environ.get("ATLAS_LLM_API_URL") or llm.get("llm_api_url") or "")
    )
    if not api_key:
        raise ValueError("The ATLAS API key is not configured.")
    parsed = urlsplit(base_url)
    endpoint_identity = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    client = OpenAI(api_key=api_key, base_url=base_url, max_retries=1, timeout=240.0)
    return client, sha256_bytes(endpoint_identity.encode("utf-8"))


def output_text(response: Any) -> str:
    status = str(getattr(response, "status", "") or "")
    if status and status != "completed":
        raise RuntimeError(f"response_status_{status}")
    direct = str(getattr(response, "output_text", "") or "")
    if direct:
        return direct
    for item in list(getattr(response, "output", None) or []):
        if getattr(item, "type", None) != "message":
            continue
        for content in list(getattr(item, "content", None) or []):
            if getattr(content, "type", None) == "refusal":
                raise RuntimeError("model_refusal")
            if getattr(content, "type", None) == "output_text":
                text = str(getattr(content, "text", "") or "")
                if text:
                    return text
    raise RuntimeError("response_has_no_output_text")


def usage_dict(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    total_tokens = int(
        getattr(usage, "total_tokens", input_tokens + output_tokens)
        or input_tokens + output_tokens
    )
    return {"input": input_tokens, "output": output_tokens, "total": total_tokens}


def estimated_cost(model: str, usage: dict[str, int]) -> float:
    rates = ENDPOINT_PRICES_USD_PER_MTOK[model]
    return round(
        usage["input"] * rates["input"] / 1_000_000
        + usage["output"] * rates["output"] / 1_000_000,
        8,
    )


def marker_evaluation(arxml: str) -> dict[str, Any]:
    present = [marker for marker in EXPECTED_MARKERS if marker in arxml]
    missing = [marker for marker in EXPECTED_MARKERS if marker not in arxml]
    return {
        "expected": len(EXPECTED_MARKERS),
        "present": len(present),
        "coverage": round(len(present) / len(EXPECTED_MARKERS), 4),
        "missing": missing,
    }


def deterministic_validation(arxml: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "xml_parse": "FAIL",
        "xsd": "NOT_EVALUATED",
        "xsd_errors": [],
        "v2_decision": "NOT_EVALUATED",
        "v2_summary": {},
    }
    parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False, huge_tree=True)
    try:
        etree.fromstring(arxml.encode("utf-8"), parser)
        result["xml_parse"] = "PASS"
    except Exception as exc:
        result["xml_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"
        return result

    try:
        import xmlschema

        schema = xmlschema.XMLSchema(str(XSD_PATH))
        errors = list(schema.iter_errors(arxml))
        result["xsd_errors"] = [str(error)[:1000] for error in errors[:20]]
        result["xsd"] = "PASS" if not errors else "FAIL"
    except Exception as exc:
        result["xsd"] = "ERROR"
        result["xsd_errors"] = [f"{type(exc).__name__}: {str(exc)[:1000]}"]

    try:
        if str(ATLAS_ROOT) not in sys.path:
            sys.path.insert(0, str(ATLAS_ROOT))
        from src.validation.v2.service import GeneratedArxmlValidationService

        retrieval = json.loads(RETRIEVAL_MANIFEST.read_text(encoding="utf-8-sig"))
        service = GeneratedArxmlValidationService(
            plan_path=PLAN_PATH,
            xsd_path=XSD_PATH,
            # This probe deliberately produces only a component fragment and
            # excludes its containing Composition/System. Cross-document rules
            # must therefore remain NOT_EVALUATED instead of becoming false
            # FAIL findings under a fabricated complete scope.
            reference_scope="partial",
            dataset_sha256=str(retrieval.get("dataset_sha256") or ""),
        )
        report = service.validate_bundle(
            {"components": {"autosar_model_probe": arxml}, "interfaces": {}},
            validation_context=None,
        )
        result["v2_decision"] = str(report.get("decision") or "ERROR")
        result["v2_summary"] = report.get("summary") or {}
        result["v2_findings"] = (report.get("findings") or [])[:50]
    except Exception as exc:
        result["v2_decision"] = "ERROR"
        result["v2_error"] = f"{type(exc).__name__}: {str(exc)[:1000]}"
    return result


def run_model(model: str) -> Path:
    if model not in MODELS:
        raise ValueError(f"Unsupported probe model: {model}")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    client, endpoint_sha256 = load_transport()
    schema_name = "autosar_probe_" + canonical_sha256(OUTPUT_SCHEMA)[:16]
    started = time.perf_counter()
    response = client.responses.create(
        model=model,
        instructions=(
            "Act as an AUTOSAR Classic 4.2.2 modeling assistant. Return only the "
            "strictly schema-conforming result. Do not claim that a model is XSD-valid "
            "unless its content actually follows the requested AUTOSAR structures."
        ),
        input=PROMPT,
        reasoning={"effort": REASONING_EFFORT},
        store=False,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        truncation="disabled",
        text={
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "strict": True,
                "schema": OUTPUT_SCHEMA,
            }
        },
    )
    latency = time.perf_counter() - started
    raw = output_text(response)
    data = json.loads(raw)
    schema_errors = list(Draft202012Validator(OUTPUT_SCHEMA).iter_errors(data))
    if schema_errors:
        raise RuntimeError("authoritative_output_schema_validation_failed")
    arxml = str(data["arxml"])
    usage = usage_dict(response)
    artifact = {
        "manifest_version": "1.0",
        "probe_protocol": PROBE_PROTOCOL,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "reasoning_effort": REASONING_EFFORT,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "response_id": str(getattr(response, "id", "") or ""),
        "response_status": str(getattr(response, "status", "") or ""),
        "latency_seconds": round(latency, 6),
        "usage": usage,
        "endpoint_price_usd_per_mtok_with_displayed_multiplier": ENDPOINT_PRICES_USD_PER_MTOK[model],
        "estimated_endpoint_cost_usd": estimated_cost(model, usage),
        "endpoint_identity_sha256": endpoint_sha256,
        "prompt": PROMPT,
        "prompt_sha256": sha256_bytes(PROMPT.encode("utf-8")),
        "output_schema": OUTPUT_SCHEMA,
        "output_schema_sha256": canonical_sha256(OUTPUT_SCHEMA),
        "plan_sha256": sha256_file(PLAN_PATH),
        "xsd_sha256": sha256_file(XSD_PATH),
        "sdk": {"name": "openai", "version": importlib.metadata.version("openai")},
        "structured_output": {
            "status": "PASS",
            "assumptions": list(data.get("assumptions") or []),
            "unresolved": list(data.get("unresolved") or []),
        },
        "arxml_sha256": sha256_bytes(arxml.encode("utf-8")),
        "arxml_character_count": len(arxml),
        "requirement_markers": marker_evaluation(arxml),
        "validation": deterministic_validation(arxml),
        "arxml": arxml,
    }
    path = OUTPUT_ROOT / f"{PROBE_PROTOCOL}__{model}.json"
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def summarize() -> Path:
    rows: list[dict[str, Any]] = []
    for model in MODELS:
        path = OUTPUT_ROOT / f"{PROBE_PROTOCOL}__{model}.json"
        if not path.is_file():
            rows.append({"model": model, "status": "MISSING"})
            continue
        artifact = json.loads(path.read_text(encoding="utf-8"))
        validation = artifact.get("validation") or {}
        rows.append(
            {
                "model": model,
                "status": "COMPLETE",
                "latency_seconds": artifact.get("latency_seconds"),
                "usage": artifact.get("usage"),
                "estimated_endpoint_cost_usd": artifact.get("estimated_endpoint_cost_usd"),
                "marker_coverage": (artifact.get("requirement_markers") or {}).get("coverage"),
                "missing_markers": (artifact.get("requirement_markers") or {}).get("missing"),
                "assumption_count": len((artifact.get("structured_output") or {}).get("assumptions") or []),
                "unresolved_count": len((artifact.get("structured_output") or {}).get("unresolved") or []),
                "xml_parse": validation.get("xml_parse"),
                "xsd": validation.get("xsd"),
                "xsd_error_count_recorded": len(validation.get("xsd_errors") or []),
                "v2_decision": validation.get("v2_decision"),
                "v2_summary": validation.get("v2_summary"),
                "artifact": str(path),
                "artifact_sha256": sha256_file(path),
            }
        )
    summary = {
        "manifest_version": "1.0",
        "probe_protocol": PROBE_PROTOCOL,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "probe_models": list(MODELS),
        "prompt_sha256": sha256_bytes(PROMPT.encode("utf-8")),
        "output_schema_sha256": canonical_sha256(OUTPUT_SCHEMA),
        "row_count": len(rows),
        "complete": all(row.get("status") == "COMPLETE" for row in rows),
        "rows": rows,
    }
    path = OUTPUT_ROOT / "summary.json"
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MODELS)
    parser.add_argument("--summarize", action="store_true")
    args = parser.parse_args()
    if args.summarize:
        print(summarize())
        return 0
    if not args.model:
        parser.error("--model is required unless --summarize is used")
    print(run_model(args.model))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
