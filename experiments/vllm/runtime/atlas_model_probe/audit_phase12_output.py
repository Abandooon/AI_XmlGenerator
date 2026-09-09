"""Parsed structural and reference audit for the ASW-STD-07 Phase 1/2 output."""

from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from lxml import etree


NS = "http://autosar.org/schema/r4.0"
N = {"ar": NS}
XSD = Path(r"E:\git projects\AI_XmlGenerator\src\validation\data\AUTOSAR_4-2-2.xsd")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(root: etree._Element, xpath: str) -> list[str]:
    return [str(value).strip() for value in root.xpath(xpath, namespaces=N)]


def _number_equal(value: str, expected: str) -> bool:
    try:
        return Decimal(value) == Decimal(expected)
    except InvalidOperation:
        return False


def _obligation(code: str, expected: Any, actual: Any, passed: bool) -> dict[str, Any]:
    return {
        "code": code,
        "status": "PASS" if passed else "FAIL",
        "expected": expected,
        "actual": actual,
    }


def _identity_paths(roots: list[etree._Element]) -> set[str]:
    paths: set[str] = set()

    def visit(node: etree._Element, parent_path: str) -> None:
        short = node.find(f"{{{NS}}}SHORT-NAME")
        current = parent_path
        if short is not None and short.text and short.text.strip():
            current = f"{parent_path}/{short.text.strip()}"
            paths.add(current)
        for child in node:
            if etree.QName(child).localname != "SHORT-NAME":
                visit(child, current)

    for root in roots:
        for package in root.xpath("/ar:AUTOSAR/ar:AR-PACKAGES/ar:AR-PACKAGE", namespaces=N):
            short = package.find(f"{{{NS}}}SHORT-NAME")
            if short is None or not short.text:
                continue
            package_path = f"/{short.text.strip()}"
            paths.add(package_path)
            for element in package.xpath("./ar:ELEMENTS/*", namespaces=N):
                visit(element, package_path)
    return paths


def audit(component: Path, interfaces: list[Path], validation: Path) -> dict[str, Any]:
    parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False)
    component_root = etree.parse(str(component), parser).getroot()
    interface_roots = [etree.parse(str(path), parser).getroot() for path in interfaces]
    roots = [component_root, *interface_roots]

    xsd_parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
    schema = etree.XMLSchema(etree.parse(str(XSD), xsd_parser))
    xsd_results = []
    for path in [component, *interfaces]:
        document = etree.parse(str(path), parser)
        valid = schema.validate(document)
        errors = [str(error) for error in schema.error_log]
        xsd_results.append({
            "file": str(path),
            "sha256": sha256_file(path),
            "status": "PASS" if valid else "FAIL",
            "errors": errors,
        })

    obligations: list[dict[str, Any]] = []
    checks = (
        ("p_port_count", "1", "count(//ar:P-PORT-PROTOTYPE)"),
        ("r_port_count", "1", "count(//ar:R-PORT-PROTOTYPE)"),
        ("runnable_count", "1", "count(//ar:RUNNABLE-ENTITY)"),
        ("timing_event_count", "1", "count(//ar:TIMING-EVENT)"),
        ("variable_access_count", "2", "count(//ar:VARIABLE-ACCESS)"),
    )
    for code, expected, xpath in checks:
        actual = str(int(component_root.xpath(xpath, namespaces=N)))
        obligations.append(_obligation(code, expected, actual, actual == expected))

    exact_text_checks = (
        (
            "p_port_name",
            "Pp_MCU03_NRF_IdcSamp",
            "//ar:P-PORT-PROTOTYPE/ar:SHORT-NAME/text()",
        ),
        ("r_port_name", "Rp_HCU01_TqCmd", "//ar:R-PORT-PROTOTYPE/ar:SHORT-NAME/text()"),
        (
            "provided_interface_path",
            "/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp",
            "//ar:P-PORT-PROTOTYPE/ar:PROVIDED-INTERFACE-TREF/text()",
        ),
        (
            "required_interface_path",
            "/COM_Interface/SR_Interface_HCU01_TqCmd",
            "//ar:R-PORT-PROTOTYPE/ar:REQUIRED-INTERFACE-TREF/text()",
        ),
        (
            "internal_behavior_name",
            "IB_Com_Std_TimeoutExplicit",
            "//ar:SWC-INTERNAL-BEHAVIOR/ar:SHORT-NAME/text()",
        ),
        (
            "runnable_name",
            "RE_Com_Std_TimeoutExplicit",
            "//ar:RUNNABLE-ENTITY/ar:SHORT-NAME/text()",
        ),
        (
            "handle_timeout_type",
            "NONE",
            "//ar:NONQUEUED-RECEIVER-COM-SPEC/ar:HANDLE-TIMEOUT-TYPE/text()",
        ),
    )
    for code, expected, xpath in exact_text_checks:
        actual = _text(component_root, xpath)
        obligations.append(_obligation(code, [expected], actual, actual == [expected]))

    count_checks = (
        (
            "nonqueued_receiver_com_spec_count",
            1,
            "count(//ar:R-PORT-PROTOTYPE/ar:REQUIRED-COM-SPECS/ar:NONQUEUED-RECEIVER-COM-SPEC)",
        ),
        (
            "read_access_count",
            1,
            "count(//ar:DATA-RECEIVE-POINT-BY-ARGUMENTS/ar:VARIABLE-ACCESS)",
        ),
        ("write_access_count", 1, "count(//ar:DATA-SEND-POINTS/ar:VARIABLE-ACCESS)"),
        (
            "receiver_numerical_init_value_count",
            1,
            "count(//ar:NONQUEUED-RECEIVER-COM-SPEC/ar:INIT-VALUE/"
            "ar:NUMERICAL-VALUE-SPECIFICATION/ar:VALUE)",
        ),
    )
    for code, expected, xpath in count_checks:
        actual = int(component_root.xpath(xpath, namespaces=N))
        obligations.append(_obligation(code, expected, actual, actual == expected))

    numeric_checks = (
        ("alive_timeout_seconds", "0.1", "//ar:NONQUEUED-RECEIVER-COM-SPEC/ar:ALIVE-TIMEOUT/text()"),
        ("timing_period_seconds", "0.01", "//ar:TIMING-EVENT/ar:PERIOD/text()"),
        (
            "receiver_init_numerical_value",
            "0",
            "//ar:NONQUEUED-RECEIVER-COM-SPEC/ar:INIT-VALUE/"
            "ar:NUMERICAL-VALUE-SPECIFICATION/ar:VALUE/text()",
        ),
    )
    for code, expected, xpath in numeric_checks:
        actual = _text(component_root, xpath)
        passed = len(actual) == 1 and _number_equal(actual[0], expected)
        obligations.append(_obligation(code, [expected], actual, passed))

    identities = _identity_paths(roots)
    reference_results = []
    for root, source in zip(roots, [component, *interfaces]):
        for ref in root.xpath("//*[substring(local-name(), string-length(local-name()) - 3) = '-REF' or substring(local-name(), string-length(local-name()) - 4) = '-TREF']"):
            target = str(ref.text or "").strip()
            if target.startswith("/AUTOSAR_Platform/"):
                status = "NOT_EVALUATED"
                reason = "external data-type catalog is outside this partial bundle"
            elif target in identities:
                status = "PASS"
                reason = "resolved in generated bundle"
            else:
                status = "FAIL"
                reason = "target path is absent from generated bundle"
            reference_results.append({
                "source_file": str(source),
                "tag": etree.QName(ref).localname,
                "dest": ref.get("DEST"),
                "target": target,
                "status": status,
                "reason": reason,
            })

    validation_report = json.loads(validation.read_text(encoding="utf-8"))
    structural_failures = [item for item in obligations if item["status"] == "FAIL"]
    local_reference_failures = [
        item for item in reference_results if item["status"] == "FAIL"
    ]
    external_references = [
        item for item in reference_results if item["status"] == "NOT_EVALUATED"
    ]
    decision = "PASS"
    if structural_failures or local_reference_failures or any(
        item["status"] != "PASS" for item in xsd_results
    ):
        decision = "FAIL"
    elif external_references or validation_report.get("decision") != "PASS":
        decision = "INCOMPLETE"

    return {
        "schema_version": "atlas.phase12.parsed-audit.v1",
        "case_id": "ASW-STD-07",
        "decision": decision,
        "promotable": decision == "PASS",
        "xsd_path": str(XSD),
        "xsd_sha256": sha256_file(XSD),
        "xsd": xsd_results,
        "structural_obligations": obligations,
        "structural_failure_count": len(structural_failures),
        "reference_integrity": reference_results,
        "local_reference_failure_count": len(local_reference_failures),
        "external_reference_not_evaluated_count": len(external_references),
        "v2": {
            "decision": validation_report.get("decision"),
            "summary": validation_report.get("summary"),
            "validator_sha256": validation_report.get("validator_sha256"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", type=Path, required=True)
    parser.add_argument("--interface", type=Path, action="append", required=True)
    parser.add_argument("--validation", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.component, args.interface, args.validation)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
