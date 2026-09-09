"""Validate and deterministically render the ATLAS simplified ASW V3 cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT / "asw_cases_v3.yaml"
DEFAULT_OUTPUT = ROOT / "rendered"


class ManifestError(ValueError):
    """Raised when the source manifest is not internally consistent."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def load_manifest(path: Path = DEFAULT_SOURCE) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ManifestError("manifest_root_must_be_object")
    return value


def event_short_name(runnable_short_name: str) -> str:
    """Return the reproducible technical identity for a runnable's timing event."""
    stem = str(runnable_short_name).strip()
    if stem.startswith("RE_"):
        stem = stem[3:]
    return f"TE_{stem}"


def variable_access_short_name(
    runnable_short_name: str, direction: str, signal: str
) -> str:
    """Return a component-local, collision-resistant variable-access identity."""
    stem = str(runnable_short_name).strip()
    if stem.startswith("RE_"):
        stem = stem[3:]
    operation = {"read": "Read", "write": "Write"}.get(str(direction).lower())
    if operation is None:
        raise ManifestError(f"unsupported_variable_access_direction:{direction}")
    return f"VA_{stem}_{operation}_{str(signal).strip()}"


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ManifestError(code)


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    _require(
        manifest.get("schema_version") == "atlas.autosar.simplified_asw.v3",
        "unsupported_schema_version",
    )
    design = manifest.get("experiment_design") or {}
    cases = manifest.get("cases")
    authoritative_context = manifest.get("authoritative_context") or {}
    catalog = authoritative_context.get("interface_catalog") or {}
    evidence_profile = authoritative_context.get("validation_evidence_profile") or {}
    _require(isinstance(cases, list) and cases, "cases_must_be_nonempty_array")
    _require(isinstance(catalog, dict) and catalog, "interface_catalog_missing")
    init_value = authoritative_context.get("unconnected_required_port_init_value")
    _require(
        isinstance(init_value, (int, float))
        and not isinstance(init_value, bool)
        and math.isfinite(float(init_value)),
        "invalid_unconnected_required_port_init_value",
    )
    _require(
        bool(str(authoritative_context.get("init_value_policy") or "").strip()),
        "init_value_policy_missing",
    )
    _require(
        evidence_profile.get("profile_id") == "autosar_component_arxml_only_v1",
        "invalid_validation_evidence_profile",
    )
    _require(
        evidence_profile.get("manual_evidence_scope_complete") is True,
        "manual_evidence_scope_must_be_complete",
    )
    _require(
        set(evidence_profile.get("manual_capabilities_out_of_scope") or [])
        == {
            "external_antecedent",
            "external_design_evidence",
            "generated_artifact",
            "runtime_evidence",
        },
        "manual_evidence_scope_mismatch",
    )

    case_ids: set[str] = set()
    components: set[str] = set()
    tier_counts = {"minimal": 0, "standard": 0, "full": 0}
    checked_cases: list[dict[str, Any]] = []

    for case in cases:
        _require(isinstance(case, dict), "case_must_be_object")
        case_id = str(case.get("case_id") or "")
        component = str(case.get("component") or "")
        tier = str(case.get("tier") or "")
        _require(case_id and case_id not in case_ids, f"duplicate_or_empty_case_id:{case_id}")
        _require(
            component and component not in components,
            f"duplicate_or_empty_component:{component}",
        )
        _require(tier in tier_counts, f"invalid_tier:{case_id}:{tier}")
        case_ids.add(case_id)
        components.add(component)
        tier_counts[tier] += 1

        provided = case.get("provided_signals") or []
        required_specs = case.get("required_signals") or []
        _require(isinstance(provided, list), f"provided_signals_not_array:{case_id}")
        _require(isinstance(required_specs, list), f"required_signals_not_array:{case_id}")
        _require(len(provided) == len(set(provided)), f"duplicate_provided_signal:{case_id}")

        required: list[str] = []
        for spec in required_specs:
            _require(isinstance(spec, dict), f"required_signal_not_object:{case_id}")
            signal = str(spec.get("signal") or "")
            _require(signal and signal not in required, f"duplicate_required_signal:{case_id}:{signal}")
            required.append(signal)
            timeout = spec.get("alive_timeout_s")
            _require(
                isinstance(timeout, (int, float)) and not isinstance(timeout, bool) and timeout >= 0,
                f"invalid_alive_timeout:{case_id}:{signal}",
            )
            _require(
                spec.get("handle_timeout_type") == "NONE",
                f"unsupported_handle_timeout_type:{case_id}:{signal}",
            )

        for signal in provided:
            _require(signal in catalog, f"unknown_provided_signal:{case_id}:{signal}")
            _require(
                catalog[signal].get("direction") == "provided",
                f"catalog_direction_mismatch:{case_id}:{signal}",
            )
        for signal in required:
            _require(signal in catalog, f"unknown_required_signal:{case_id}:{signal}")
            _require(
                catalog[signal].get("direction") == "required",
                f"catalog_direction_mismatch:{case_id}:{signal}",
            )

        behavior = case.get("internal_behavior")
        runnables = [] if behavior is None else behavior.get("runnables") or []
        _require(isinstance(runnables, list), f"runnables_not_array:{case_id}")
        runnable_names: set[str] = set()
        accesses = 0
        for runnable in runnables:
            _require(isinstance(runnable, dict), f"runnable_not_object:{case_id}")
            name = str(runnable.get("short_name") or "")
            _require(name and name not in runnable_names, f"duplicate_runnable:{case_id}:{name}")
            runnable_names.add(name)
            period = runnable.get("period_s")
            _require(
                isinstance(period, (int, float)) and not isinstance(period, bool) and period > 0,
                f"invalid_period:{case_id}:{name}",
            )
            reads = runnable.get("reads") or []
            writes = runnable.get("writes") or []
            _require(set(reads) <= set(required), f"read_without_r_port:{case_id}:{name}")
            _require(set(writes) <= set(provided), f"write_without_p_port:{case_id}:{name}")
            accesses += len(reads) + len(writes)

        actual_counts = {
            "p_ports": len(provided),
            "r_ports": len(required),
            "runnables": len(runnables),
            "timing_events": len(runnables),
            "variable_accesses": accesses,
        }
        _require(
            actual_counts == case.get("expected_counts"),
            f"expected_count_mismatch:{case_id}:{actual_counts}",
        )
        if tier == "minimal":
            _require(behavior is None, f"minimal_case_has_internal_behavior:{case_id}")
        else:
            _require(behavior is not None, f"nonminimal_case_missing_internal_behavior:{case_id}")

        checked_cases.append(
            {
                "case_id": case_id,
                "case_sha256": canonical_sha256(case),
                "actual_counts": actual_counts,
            }
        )

    _require(
        len(cases) == int(design.get("independent_cases") or -1),
        "independent_case_count_mismatch",
    )
    seeds = design.get("seeds") or []
    repetitions = int(design.get("repetitions_per_case") or 0)
    _require(len(seeds) == repetitions, "seed_count_mismatch")
    _require(len(seeds) == len(set(seeds)), "duplicate_seed")
    _require(
        len(cases) * repetitions == int(design.get("run_count") or -1),
        "run_count_mismatch",
    )
    _require(tier_counts == {"minimal": 6, "standard": 7, "full": 7}, "tier_count_mismatch")

    return {
        "status": "PASS",
        "case_count": len(cases),
        "tier_counts": tier_counts,
        "run_count": len(cases) * repetitions,
        "checked_cases": checked_cases,
    }


def _port_lines(
    case: dict[str, Any],
    catalog: dict[str, Any],
    unconnected_init_value: int | float,
) -> list[str]:
    lines: list[str] = []
    for signal in case.get("provided_signals") or []:
        item = catalog[signal]
        lines.append(
            f"- P-PORT-PROTOTYPE Pp_{signal}: PROVIDED-INTERFACE-TREF "
            f"{item['interface_ref']} (DEST=SENDER-RECEIVER-INTERFACE); "
            f"data element {item['data_element']}."
        )
    for spec in case.get("required_signals") or []:
        signal = spec["signal"]
        item = catalog[signal]
        lines.append(
            f"- R-PORT-PROTOTYPE Rp_{signal}: REQUIRED-INTERFACE-TREF "
            f"{item['interface_ref']} (DEST=SENDER-RECEIVER-INTERFACE); "
            f"data element {item['data_element']}; NONQUEUED-RECEIVER-COM-SPEC "
            f"with ALIVE-TIMEOUT={spec['alive_timeout_s']} seconds and "
            f"HANDLE-TIMEOUT-TYPE={spec['handle_timeout_type']}; because this benchmark "
            "supplies no Composition connector, represent the required port as unconnected "
            "and set INIT-VALUE/NUMERICAL-VALUE-SPECIFICATION/VALUE="
            f"{unconnected_init_value}."
        )
    return lines


def render_prompt(manifest: dict[str, Any], case: dict[str, Any]) -> str:
    authoritative_context = manifest["authoritative_context"]
    catalog = authoritative_context["interface_catalog"]
    unconnected_init_value = authoritative_context[
        "unconnected_required_port_init_value"
    ]
    lines = [
        "Generate one AUTOSAR Classic Platform 4.2.2 ARXML document for the "
        "simplified atomic application software component described below.",
        "This is a component-level benchmark, not a complete ECU configuration.",
        "",
        f"Case ID: {case['case_id']}",
        f"Component: APPLICATION-SW-COMPONENT-TYPE {case['component']}",
        f"Intent: {case['intent']}",
        "",
        "Ports and communication specifications:",
    ]
    lines.extend(
        _port_lines(case, catalog, unconnected_init_value) or ["- No ports."]
    )

    behavior = case.get("internal_behavior")
    if behavior is None:
        lines.extend(
            [
                "",
                "Do not create an SWC-INTERNAL-BEHAVIOR, RUNNABLE-ENTITY, or event.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                f"Internal behavior: SWC-INTERNAL-BEHAVIOR {behavior['short_name']}",
                "Runnables and events:",
            ]
        )
        for runnable in behavior["runnables"]:
            timing_event_name = event_short_name(runnable["short_name"])
            lines.append(
                f"- RUNNABLE-ENTITY {runnable['short_name']} is started by exactly one "
                f"TIMING-EVENT {timing_event_name} with period "
                f"{runnable['period_s']} seconds."
            )
            for signal in runnable["reads"]:
                target = catalog[signal]
                access_name = variable_access_short_name(
                    runnable["short_name"], "read", signal
                )
                lines.append(
                    f"  - Read Rp_{signal}/{target['data_element']} through one "
                    f"DATA-RECEIVE-POINT-BY-ARGUMENTS VARIABLE-ACCESS {access_name} "
                    "with a resolvable "
                    "AUTOSAR-VARIABLE-IREF."
                )
            for signal in runnable["writes"]:
                target = catalog[signal]
                access_name = variable_access_short_name(
                    runnable["short_name"], "write", signal
                )
                lines.append(
                    f"  - Write Pp_{signal}/{target['data_element']} through one "
                    f"DATA-SEND-POINTS VARIABLE-ACCESS {access_name} with a resolvable "
                    "AUTOSAR-VARIABLE-IREF."
                )

    expected = case["expected_counts"]
    lines.extend(
        [
            "",
            "Deterministic obligations:",
            f"- Exactly {expected['p_ports']} P ports, {expected['r_ports']} R ports, "
            f"{expected['runnables']} runnables, {expected['timing_events']} timing "
            f"events, and {expected['variable_accesses']} variable accesses.",
            "- Use the AUTOSAR 4.2.2 namespace, AR-PACKAGES/AR-PACKAGE/ELEMENTS "
            "containment, valid DEST values, valid multiplicities, and XSD element order.",
            "- Treat the interface catalog paths above as definitions supplied by the "
            "same hash-pinned validation context; do not invent alternate interfaces.",
        ]
    )
    if case.get("required_signals"):
        lines.append(
            "- The supplied component-fragment context is authoritative for this benchmark: "
            "every listed R-PORT-PROTOTYPE is unconnected and its "
            "NONQUEUED-RECEIVER-COM-SPEC must contain "
            "INIT-VALUE/NUMERICAL-VALUE-SPECIFICATION/VALUE="
            f"{unconnected_init_value}."
        )
    lines.extend(
        [
            "- Do not add ECU, BSW, system mapping, network, deployment, mode, parameter, "
            "or client-server configuration.",
            "- Return only the complete XML document without Markdown or explanation.",
            "- If the request cannot be represented from the supplied context, fail "
            "explicitly; never substitute default requirements or an unrelated grammar.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_all(
    source: Path = DEFAULT_SOURCE,
    output_dir: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    manifest = load_manifest(source)
    validation = validate_manifest(manifest)
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir = output_dir / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)

    prompts: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    seeds = manifest["experiment_design"]["seeds"]
    for case in manifest["cases"]:
        prompt = render_prompt(manifest, case)
        prompt_path = prompt_dir / f"{case['case_id']}.txt"
        prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
        prompt_hash = sha256_bytes(prompt.encode("utf-8"))
        prompts.append(
            {
                "case_id": case["case_id"],
                "tier": case["tier"],
                "case_sha256": canonical_sha256(case),
                "prompt_sha256": prompt_hash,
                "prompt_file": prompt_path.relative_to(output_dir).as_posix(),
            }
        )
        for repetition, seed in enumerate(seeds, start=1):
            runs.append(
                {
                    "run_id": f"{case['case_id']}-R{repetition}",
                    "case_id": case["case_id"],
                    "tier": case["tier"],
                    "repetition": repetition,
                    "seed": seed,
                    "prompt_sha256": prompt_hash,
                }
            )

    result = {
        "schema_version": "atlas.autosar.simplified_asw.rendered.v1",
        "source_file": source.name,
        "source_sha256": sha256_bytes(source.read_bytes()),
        "source_canonical_sha256": canonical_sha256(manifest),
        "validation": validation,
        "prompt_count": len(prompts),
        "run_count": len(runs),
        "prompts": prompts,
        "runs": runs,
    }
    result["content_sha256"] = canonical_sha256(result)
    manifest_path = output_dir / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    manifest = load_manifest(args.source)
    if args.validate_only:
        print(json.dumps(validate_manifest(manifest), ensure_ascii=False, indent=2))
        return 0
    result = render_all(args.source, args.output_dir)
    print(json.dumps({
        "status": result["validation"]["status"],
        "prompt_count": result["prompt_count"],
        "run_count": result["run_count"],
        "content_sha256": result["content_sha256"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
