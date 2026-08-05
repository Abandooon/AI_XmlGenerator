from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.kg_builder.xsd_enrichment.content_model import XsdContentModelExtractor
from src.kg_builder.xsd_enrichment.matcher import MetadataMatcher

XSD = """<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
 xmlns:T="urn:parent-context" targetNamespace="urn:parent-context">
 <xs:group name="OWNER-A"><xs:sequence>
  <xs:element name="TARGET"><xs:complexType><xs:sequence>
   <xs:element name="A-VALUE" type="xs:string"/>
  </xs:sequence></xs:complexType></xs:element>
 </xs:sequence></xs:group>
 <xs:group name="OWNER-B"><xs:sequence>
  <xs:element name="TARGET"><xs:complexType><xs:sequence>
   <xs:element name="B-VALUE" type="xs:string"/>
  </xs:sequence></xs:complexType></xs:element>
 </xs:sequence></xs:group>
</xs:schema>"""


class ParentContextTests(unittest.TestCase):
    def test_same_inner_name_uses_parent_declared_type(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "schema.xsd"
            path.write_text(XSD, encoding="utf-8")
            metadata = {
                "groups": {
                    "OwnerA": {
                        "name": "OwnerA",
                        "annotation": "OWNER-A",
                        "elements": [{"name": "target", "xml_tag": "TARGET", "type": "Target_OwnerA"}],
                    },
                    "OwnerB": {
                        "name": "OwnerB",
                        "annotation": "OWNER-B",
                        "elements": [{"name": "target", "xml_tag": "TARGET", "type": "Target_OwnerB"}],
                    },
                },
                "complexTypes": {},
                "extract_inner_class": {
                    "Target_OwnerA": {
                        "name": "Target_OwnerA",
                        "attributes": [{"name": "aValue", "xml_tag": "A-VALUE", "type": "String"}],
                    },
                    "Target_OwnerB": {
                        "name": "Target_OwnerB",
                        "attributes": [{"name": "bValue", "xml_tag": "B-VALUE", "type": "String"}],
                    },
                },
                "simpleTypes": {},
            }
            matched = MetadataMatcher(metadata).match(XsdContentModelExtractor(path).extract())
            anonymous = [
                owner for owner in matched["owners"]
                if owner.get("owner_kind") == "anonymousComplexType"
            ]
            self.assertEqual(len(anonymous), 2)
            targets = {
                owner["parent_owner_id"]: owner["mapped_target"]["key"]
                for owner in anonymous
            }
            self.assertIn("Target_OwnerA", targets.values())
            self.assertIn("Target_OwnerB", targets.values())
            self.assertNotEqual(*targets.values())


if __name__ == "__main__":
    unittest.main()

