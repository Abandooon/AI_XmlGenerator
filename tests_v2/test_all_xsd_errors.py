from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.validation.v2.engine import ValidationEngine


class AllXsdErrorsTests(unittest.TestCase):
    def test_xsd_errors_are_collected_from_every_well_formed_file(self) -> None:
        schema_text = """<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
        <xsd:element name="AUTOSAR"><xsd:complexType><xsd:sequence>
        <xsd:element name="A" type="xsd:int"/>
        </xsd:sequence></xsd:complexType></xsd:element></xsd:schema>"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            xsd = root / "model.xsd"
            first = root / "first.arxml"
            second = root / "second.arxml"
            xsd.write_text(schema_text, encoding="utf-8")
            first.write_text("<AUTOSAR><B/></AUTOSAR>", encoding="utf-8")
            second.write_text("<AUTOSAR><A>not-an-int</A><C/></AUTOSAR>", encoding="utf-8")
            report = ValidationEngine({"rules": []}).validate([first, second], xsd)
        self.assertEqual("FAIL", report["decision"])
        self.assertGreaterEqual(report["summary"]["finding_count"], 2)
        files = {Path(item["location"]["file"]).name for item in report["findings"]}
        self.assertEqual({"first.arxml", "second.arxml"}, files)
        self.assertEqual(report["summary"]["finding_count"], report["repair"]["action_count"])


if __name__ == "__main__":
    unittest.main()
