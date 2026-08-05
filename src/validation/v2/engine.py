"""Validation-plan executor with explicit PASS/FAIL/NOT_EVALUATED/ERROR states."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lxml import etree

from .arxml_index import ArxmlIndex
from .context import ValidationContextError, activation_reason, normalize_validation_context
from .plugins import REGISTRY
from .repair import build_repair_payload


class ValidationEngine:
    def __init__(
        self,
        plan: dict,
        reference_scope: str = "complete",
        expected_dataset_sha256: str | None = None,
    ) -> None:
        if reference_scope not in {"complete", "partial"}:
            raise ValueError("reference_scope must be 'complete' or 'partial'")
        self.plan = plan
        self.reference_scope = reference_scope
        self.expected_dataset_sha256 = expected_dataset_sha256

    @classmethod
    def from_plan_file(
        cls,
        path: Path,
        reference_scope: str = "complete",
        expected_dataset_sha256: str | None = None,
    ) -> "ValidationEngine":
        return cls(
            json.loads(path.read_text(encoding="utf-8")),
            reference_scope,
            expected_dataset_sha256,
        )

    def validate(
        self,
        arxml_paths: list[Path],
        xsd_path: Path | None = None,
        validation_context: dict | None = None,
    ) -> dict:
        try:
            context = normalize_validation_context(
                validation_context,
                expected_dataset_sha256=self.expected_dataset_sha256,
            )
        except ValidationContextError as error:
            return self._context_error_report(arxml_paths, error)
        syntax_findings = self._xml_syntax_findings(arxml_paths)
        if syntax_findings:
            return self._syntax_error_report(arxml_paths, syntax_findings, context)
        try:
            index = ArxmlIndex(arxml_paths)
        except Exception as error:
            return self._engine_error(arxml_paths, error, context)

        capabilities = {"well_formed_xml", "metamodel"}
        if context is not None:
            capabilities.add("validation_context")
            if context.get("declared_use_cases") or context.get("declared_constraint_ids") or context.get("declared_targets"):
                capabilities.add("generation_intent")
        if self.reference_scope == "complete":
            capabilities.add("complete_reference_scope")
        results: list[dict] = []
        if xsd_path is not None:
            xsd_result = self._validate_xsd(index, xsd_path)
            results.append(xsd_result)
            if xsd_result["status"] == "PASS":
                capabilities.add("xsd")

        for rule in self.plan.get("rules", []):
            results.append(self._evaluate_rule(index, rule, capabilities, context))

        findings: list[dict] = []
        fingerprints: dict[str, dict] = {}
        for result in results:
            for violation in result.get("violations", []):
                fingerprint_source = json.dumps({
                    "message": violation.get("message"),
                    "location": violation.get("location"),
                    "evidence": violation.get("evidence"),
                }, sort_keys=True, ensure_ascii=False)
                fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
                if fingerprint not in fingerprints:
                    item = dict(violation)
                    item["fingerprint"] = fingerprint
                    item["rule_ids"] = [result["rule_id"]]
                    item["constraint_ids"] = [result.get("constraint_id")]
                    item["severity"] = result.get("severity", "error")
                    item["rule_title"] = result.get("title", "")
                    fingerprints[fingerprint] = item
                    findings.append(item)
                else:
                    item = fingerprints[fingerprint]
                    item["rule_ids"].append(result["rule_id"])
                    constraint_id = result.get("constraint_id")
                    if constraint_id not in item["constraint_ids"]:
                        item["constraint_ids"].append(constraint_id)

        manual_reviews: list[dict] = []
        for review in (self.plan.get("manual_review") or {}).get("reviews", []):
            tags = list(review.get("selector_tags") or [])
            selected = index.select_any(tags) if tags else list(index.roots)
            if tags and not selected:
                continue
            manual_reviews.append({
                **review,
                "status": "MANUAL_REVIEW",
                "applicable_count": len(selected),
                "locations": [index.location(item) for item in selected],
            })

        counts = {status: sum(item["status"] == status for item in results) for status in ("PASS", "FAIL", "NOT_EVALUATED", "ERROR")}
        must_incomplete = [item for item in results if item.get("policy") == "must" and item["status"] == "NOT_EVALUATED"]
        if counts["ERROR"]:
            decision = "ERROR"
        elif counts["FAIL"]:
            decision = "FAIL"
        elif must_incomplete or manual_reviews:
            decision = "INCOMPLETE"
        else:
            decision = "PASS"
        return {
            "schema_version": "2.0",
            "decision": decision,
            "valid": decision == "PASS",
            "reference_scope": self.reference_scope,
            "validation_context": self._context_report(context),
            "inputs": [str(path.resolve()) for path in arxml_paths],
            "summary": {**counts, "finding_count": len(findings), "must_not_evaluated": len(must_incomplete), "manual_review_applicable": len(manual_reviews)},
            "findings": findings,
            "repair": build_repair_payload(findings),
            "manual_review": manual_reviews,
            "rules": results,
        }

    def _evaluate_rule(
        self,
        index: ArxmlIndex,
        rule: dict,
        capabilities: set[str],
        validation_context: dict | None = None,
    ) -> dict:
        base = {
            "rule_id": rule["rule_id"],
            "constraint_id": rule["constraint_id"],
            "policy": rule["policy"],
            "severity": rule["severity"],
            "title": rule["title"],
        }
        selector = rule.get("selector", {})
        selected = index.select_any(selector.get("tags", [])) if selector.get("mode") != "global" else [root for root in index.roots]

        inactive_reason = activation_reason(rule, validation_context)
        if inactive_reason:
            return {
                **base, "status": "NOT_EVALUATED",
                "applicable_count": len(selected), "checked_count": 0,
                "violations": [], "notes": [inactive_reason],
            }

        activation = (rule.get("formal_spec") or {}).get("activation") or {}
        if activation.get("requires_declared_targets"):
            target_paths = (validation_context or {}).get("declared_targets", {}).get(rule["constraint_id"], [])
            resolved: list = []
            target_errors: list[str] = []
            selector_tags = set(selector.get("tags") or [])
            for target_path in target_paths:
                resolution = index.resolve(target_path)
                if resolution.status != "resolved" or resolution.element is None:
                    target_errors.append(
                        f"Declared target {target_path} is {resolution.status}; exactly one ARXML element is required."
                    )
                    continue
                target_tag = resolution.element.tag.rsplit("}", 1)[-1]
                if selector.get("mode") != "global" and selector_tags and target_tag not in selector_tags:
                    target_errors.append(
                        f"Declared target {target_path} has tag {target_tag}, outside the rule selector."
                    )
                    continue
                if all(item is not resolution.element for item in resolved):
                    resolved.append(resolution.element)
            if target_errors:
                return {
                    **base, "status": "NOT_EVALUATED",
                    "applicable_count": len(target_paths), "checked_count": 0,
                    "violations": [], "notes": target_errors,
                }
            selected = resolved

        if selector.get("mode") != "global" and not selected:
            return {
                **base, "status": "PASS", "applicable_count": 0,
                "checked_count": 0, "violations": [],
                "notes": ["No applicable ARXML elements."],
            }

        missing = sorted(set(rule.get("completeness", {}).get("requires", [])) - capabilities)
        if missing:
            return {**base, "status": "NOT_EVALUATED", "applicable_count": len(selected), "checked_count": 0, "violations": [], "notes": ["Missing capabilities: " + ", ".join(missing)]}
        implementation = rule.get("implementation", {})
        if implementation.get("status") != "implemented" or not implementation.get("plugin"):
            return {**base, "status": "NOT_EVALUATED", "applicable_count": len(selected), "checked_count": 0, "violations": [], "notes": [implementation.get("reason") or "Rule is not implemented."]}
        function = REGISTRY.get(implementation["plugin"])
        if function is None:
            return {**base, "status": "ERROR", "applicable_count": len(selected), "checked_count": 0, "violations": [], "notes": [f"Unknown plugin {implementation['plugin']}"]}
        try:
            runtime_rule = dict(rule)
            runtime_rule["_validation_context"] = validation_context
            report = function(index, runtime_rule, selected)
        except Exception as error:
            return {**base, "status": "ERROR", "applicable_count": len(selected), "checked_count": 0, "violations": [], "notes": [f"{type(error).__name__}: {error}"]}
        if report.violations:
            status = "FAIL"
        elif report.incomplete_reasons:
            status = "NOT_EVALUATED"
        else:
            status = "PASS"
        return {
            **base,
            "status": status,
            "applicable_count": len(selected),
            "checked_count": report.checked,
            "violations": report.violations,
            "observations": report.observations,
            "notes": report.incomplete_reasons,
        }

    def _validate_xsd(self, index: ArxmlIndex, xsd_path: Path) -> dict:
        base = {"rule_id": "XSD#r1", "constraint_id": "XSD", "policy": "must", "severity": "error", "title": "AUTOSAR XSD validation"}
        try:
            schema = etree.XMLSchema(etree.parse(str(xsd_path)))
            violations: list[dict] = []
            for tree, path in zip(index.trees, index.paths):
                if schema.validate(tree):
                    continue
                for entry in schema.error_log:
                    violations.append({
                        "message": entry.message,
                        "location": {
                            "file": str(path), "line": entry.line,
                            "column": entry.column, "xml_path": entry.path,
                            "tag": None,
                        },
                        "repair": {
                            "action": "repair_xsd_structure",
                            "target": entry.path,
                            "instruction": entry.message,
                        },
                    })
            return {**base, "status": "FAIL" if violations else "PASS", "applicable_count": len(index.trees), "checked_count": len(index.trees), "violations": violations, "notes": []}
        except Exception as error:
            return {**base, "status": "ERROR", "applicable_count": len(index.trees), "checked_count": 0, "violations": [], "notes": [f"{type(error).__name__}: {error}"]}

    @staticmethod
    def _xml_syntax_findings(arxml_paths: list[Path]) -> list[dict]:
        """Collect parser diagnostics from every input instead of stopping at file one."""
        findings: list[dict] = []
        parser_options = {
            "resolve_entities": False,
            "no_network": True,
            "huge_tree": True,
            "recover": False,
        }
        for path in arxml_paths:
            parser = etree.XMLParser(**parser_options)
            try:
                etree.parse(str(path), parser)
            except (OSError, etree.XMLSyntaxError) as error:
                entries = list(getattr(error, "error_log", ()) or parser.error_log)
                if not entries:
                    entries = [error]
                for entry in entries:
                    line = getattr(entry, "line", None)
                    column = getattr(entry, "column", None)
                    message = str(getattr(entry, "message", None) or entry)
                    finding = {
                        "message": message,
                        "location": {
                            "file": str(path.resolve()),
                            "line": line,
                            "column": column,
                            "xml_path": None,
                            "tag": None,
                        },
                        "repair": {
                            "action": "repair_xml_syntax",
                            "target": f"line {line}, column {column}",
                            "instruction": message,
                        },
                        "evidence": {"parser": "lxml", "column": column},
                    }
                    fingerprint_source = json.dumps(
                        {"message": message, "location": finding["location"]},
                        sort_keys=True,
                        ensure_ascii=False,
                    )
                    finding["fingerprint"] = hashlib.sha256(
                        fingerprint_source.encode("utf-8")
                    ).hexdigest()[:16]
                    finding["rule_ids"] = ["XML#well-formed"]
                    finding["constraint_ids"] = ["XML"]
                    finding["severity"] = "error"
                    finding["rule_title"] = "XML well-formedness"
                    findings.append(finding)
        return findings

    def _syntax_error_report(
        self,
        arxml_paths: list[Path],
        findings: list[dict],
        validation_context: dict | None = None,
    ) -> dict:
        return {
            "schema_version": "2.0",
            "decision": "ERROR",
            "valid": False,
            "reference_scope": self.reference_scope,
            "validation_context": self._context_report(validation_context),
            "inputs": [str(path.resolve()) for path in arxml_paths],
            "summary": {
                "PASS": 0,
                "FAIL": 0,
                "NOT_EVALUATED": 0,
                "ERROR": 1,
                "finding_count": len(findings),
                "must_not_evaluated": 0,
                "manual_review_applicable": 0,
            },
            "findings": findings,
            "repair": build_repair_payload(findings),
            "manual_review": [],
            "rules": [{
                "rule_id": "XML#well-formed",
                "constraint_id": "XML",
                "policy": "must",
                "severity": "error",
                "title": "XML well-formedness",
                "status": "ERROR",
                "applicable_count": len(arxml_paths),
                "checked_count": len(arxml_paths),
                "violations": findings,
                "notes": [
                    "Semantic and XSD validation were not run because malformed XML cannot be indexed safely."
                ],
            }],
        }

    @staticmethod
    def _context_report(context: dict | None) -> dict:
        if context is None:
            return {"status": "NOT_PROVIDED", "manifest": None}
        return {
            "status": "VERIFIED",
            "dataset_sha256": context["dataset_sha256"],
            "manifest_sha256": context["manifest_sha256"],
            "selected_constraint_count": len(context.get("selected_constraint_ids") or []),
            "manifest": context,
        }

    def _context_error_report(self, arxml_paths: list[Path], error: Exception) -> dict:
        message = f"Validation context integrity failure: {error}"
        finding = {
            "message": message,
            "location": {"file": None, "line": None, "column": None, "xml_path": None, "tag": None},
            "evidence": {"expected_dataset_sha256": self.expected_dataset_sha256},
            "repair": {
                "action": "regenerate_validation_context",
                "target": "validation_context",
                "instruction": "Re-run hash-pinned constraint retrieval and regenerate the validation-context manifest.",
            },
            "fingerprint": hashlib.sha256(message.encode("utf-8")).hexdigest()[:16],
            "rule_ids": ["CONTEXT#integrity"],
            "constraint_ids": ["CONTEXT"],
            "severity": "error",
            "rule_title": "Validation-context integrity",
        }
        return {
            "schema_version": "2.0", "decision": "ERROR", "valid": False,
            "reference_scope": self.reference_scope,
            "validation_context": {"status": "ERROR", "manifest": None, "error": str(error)},
            "inputs": [str(path.resolve()) for path in arxml_paths],
            "summary": {
                "PASS": 0, "FAIL": 0, "NOT_EVALUATED": 0, "ERROR": 1,
                "finding_count": 1, "must_not_evaluated": 0, "manual_review_applicable": 0,
            },
            "findings": [finding], "repair": build_repair_payload([finding]),
            "manual_review": [],
            "rules": [{
                "rule_id": "CONTEXT#integrity", "constraint_id": "CONTEXT",
                "policy": "must", "severity": "error", "title": "Validation-context integrity",
                "status": "ERROR", "applicable_count": 1, "checked_count": 0,
                "violations": [finding], "notes": [str(error)],
            }],
        }

    def _engine_error(
        self,
        arxml_paths: list[Path],
        error: Exception,
        validation_context: dict | None = None,
    ) -> dict:
        return {
            "schema_version": "2.0", "decision": "ERROR", "valid": False,
            "reference_scope": self.reference_scope,
            "validation_context": self._context_report(validation_context),
            "inputs": [str(path.resolve()) for path in arxml_paths],
            "summary": {"PASS": 0, "FAIL": 0, "NOT_EVALUATED": 0, "ERROR": 1, "finding_count": 0, "must_not_evaluated": 0},
            "findings": [],
            "repair": build_repair_payload([]),
            "manual_review": [],
            "rules": [{"rule_id": "ENGINE#r1", "constraint_id": "ENGINE", "policy": "must", "severity": "error", "title": "ARXML loading", "status": "ERROR", "applicable_count": 0, "checked_count": 0, "violations": [], "notes": [f"{type(error).__name__}: {error}"]}],
        }
