from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.validation.v2.context import build_validation_context
from src.validation.v2.engine import ValidationEngine

DATASET = "a" * 64


def rule(
    constraint_id: str,
    plugin: str,
    tags: list[str],
    *,
    exact_targets: bool = False,
) -> dict:
    value = {
        "rule_id": f"{constraint_id}#r1",
        "constraint_id": constraint_id,
        "title": constraint_id,
        "severity": "error",
        "policy": "must",
        "implementation": {"status": "implemented", "plugin": plugin},
        "selector": {"tags": tags, "mode": "any"},
        "parameters": {},
        "completeness": {
            "requires": ["well_formed_xml", "complete_reference_scope"],
            "on_missing": "not_evaluated",
        },
        "dependencies": [],
        "bindings": [],
    }
    if exact_targets:
        value["formal_spec"] = {
            "activation": {
                "requires_validation_context": True,
                "requires_selected_constraint": True,
                "requires_declared_constraint": True,
                "requires_declared_targets": True,
            }
        }
    return value


class RecentPluginBatchTests(unittest.TestCase):
    def validate(
        self,
        xml: str,
        rules: list[dict],
        *,
        targets: dict[str, list[str]] | None = None,
    ) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            context = None
            if targets is not None:
                ids = sorted(targets)
                context = build_validation_context(
                    {
                        "test": {
                            "backend": "test",
                            "dataset_sha256": DATASET,
                            "result_count": len(ids),
                            "constraint_ids": ids,
                        }
                    },
                    expected_dataset_sha256=DATASET,
                    reference_scope="complete",
                    declared_constraint_ids=ids,
                    declared_targets=targets,
                )
            return ValidationEngine(
                {"rules": rules}, expected_dataset_sha256=DATASET
            ).validate([path], validation_context=context)

    @staticmethod
    def service_dependency_xml() -> str:
        return """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <CLIENT-SERVER-INTERFACE><SHORT-NAME>Wrong</SHORT-NAME></CLIENT-SERVER-INTERFACE>
        <R-PORT-PROTOTYPE><SHORT-NAME>Port</SHORT-NAME><REQUIRED-INTERFACE-TREF>/Pkg/Wrong</REQUIRED-INTERFACE-TREF></R-PORT-PROTOTYPE>
        <SWC-SERVICE-DEPENDENCY><SHORT-NAME>Dep</SHORT-NAME><ROLE-BASED-PORT-ASSIGNMENTS>
          <ROLE-BASED-PORT-ASSIGNMENT><ROLE>SecurityAccess</ROLE><PORT-PROTOTYPE-REF>/Pkg/Port</PORT-PROTOTYPE-REF></ROLE-BASED-PORT-ASSIGNMENT>
        </ROLE-BASED-PORT-ASSIGNMENTS></SWC-SERVICE-DEPENDENCY>
        <SWC-SERVICE-DEPENDENCY><SHORT-NAME>Other</SHORT-NAME></SWC-SERVICE-DEPENDENCY>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""

    def test_exact_target_naming_requires_context(self) -> None:
        result = self.validate(
            self.service_dependency_xml(),
            [rule("TPS_SWCT_01627", "service_dependency_interface_name", ["SWC-SERVICE-DEPENDENCY"], exact_targets=True)],
        )
        self.assertEqual("INCOMPLETE", result["decision"])
        self.assertEqual("NOT_EVALUATED", result["rules"][0]["status"])

    def test_exact_target_naming_checks_only_bound_dependency(self) -> None:
        result = self.validate(
            self.service_dependency_xml(),
            [rule("TPS_SWCT_01627", "service_dependency_interface_name", ["SWC-SERVICE-DEPENDENCY"], exact_targets=True)],
            targets={"TPS_SWCT_01627": ["/Pkg/Dep"]},
        )
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(1, result["rules"][0]["applicable_count"])
        self.assertEqual("SecurityAccess_Dep", result["findings"][0]["repair"]["expected"])

    def test_record_value_arity_uses_top_level_elements(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <APPLICATION-RECORD-DATA-TYPE><SHORT-NAME>Rec</SHORT-NAME><ELEMENTS>
          <APPLICATION-RECORD-ELEMENT><SHORT-NAME>A</SHORT-NAME></APPLICATION-RECORD-ELEMENT>
          <APPLICATION-RECORD-ELEMENT><SHORT-NAME>B</SHORT-NAME></APPLICATION-RECORD-ELEMENT>
        </ELEMENTS></APPLICATION-RECORD-DATA-TYPE>
        <APPLICATION-RECORD-DATA-TYPE><SHORT-NAME>Nested</SHORT-NAME><ELEMENTS>
          <APPLICATION-RECORD-ELEMENT><SHORT-NAME>N</SHORT-NAME><TYPE-TREF>/Pkg/Rec</TYPE-TREF></APPLICATION-RECORD-ELEMENT>
        </ELEMENTS></APPLICATION-RECORD-DATA-TYPE>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME><TYPE-TREF>/Pkg/Nested</TYPE-TREF><INIT-VALUE>
          <RECORD-VALUE-SPECIFICATION><FIELDS>
            <RECORD-VALUE-SPECIFICATION><FIELDS><NUMERICAL-VALUE-SPECIFICATION/><NUMERICAL-VALUE-SPECIFICATION/></FIELDS></RECORD-VALUE-SPECIFICATION>
            <NUMERICAL-VALUE-SPECIFICATION/>
          </FIELDS></RECORD-VALUE-SPECIFICATION>
        </INIT-VALUE></VARIABLE-DATA-PROTOTYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(
            xml,
            [rule("constr_1271", "typed_value_shape_cardinality", ["RECORD-VALUE-SPECIFICATION"])],
        )
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(1, result["findings"][0]["evidence"]["expected"])
        self.assertEqual(2, result["findings"][0]["evidence"]["actual"])

    def test_unresolved_local_variable_is_not_evaluated(self) -> None:
        xml = """<AUTOSAR><SWC-INTERNAL-BEHAVIOR><SHORT-NAME>Ib</SHORT-NAME><RUNNABLES>
        <RUNNABLE-ENTITY><SHORT-NAME>R</SHORT-NAME><READ-LOCAL-VARIABLES>
          <VARIABLE-ACCESS><SHORT-NAME>A</SHORT-NAME><ACCESSED-VARIABLE><LOCAL-VARIABLE-REF>/Missing</LOCAL-VARIABLE-REF></ACCESSED-VARIABLE></VARIABLE-ACCESS>
        </READ-LOCAL-VARIABLES></RUNNABLE-ENTITY></RUNNABLES></SWC-INTERNAL-BEHAVIOR></AUTOSAR>"""
        result = self.validate(
            xml,
            [rule("TPS_SWCT_01053", "local_variable_access_reference", ["VARIABLE-ACCESS"])],
        )
        self.assertEqual("INCOMPLETE", result["decision"])
        self.assertEqual("NOT_EVALUATED", result["rules"][0]["status"])


if __name__ == "__main__":
    unittest.main()
