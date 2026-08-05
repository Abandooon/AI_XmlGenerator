from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.kg_builder.xsd_enrichment.content_model import XsdContentModelExtractor
from src.kg_builder.xsd_enrichment.matcher import MetadataMatcher, build_enriched_metadata

SYNTHETIC_XSD = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:T="urn:atlas:test"
           targetNamespace="urn:atlas:test">
  <xs:group name="PARENT-A">
    <xs:sequence>
      <xs:element name="VALUE" type="xs:string"/>
      <xs:element name="ITEMS" minOccurs="0">
        <xs:complexType>
          <xs:choice minOccurs="0" maxOccurs="unbounded">
            <xs:element name="ENTRY" type="xs:string"/>
          </xs:choice>
        </xs:complexType>
      </xs:element>
      <xs:group ref="T:SHARED" minOccurs="0"/>
    </xs:sequence>
  </xs:group>
  <xs:group name="PARENT-B">
    <xs:sequence>
      <xs:element name="VALUE" type="xs:int"/>
    </xs:sequence>
  </xs:group>
  <xs:group name="SHARED">
    <xs:choice>
      <xs:element name="LEFT" type="xs:string"/>
      <xs:element name="RIGHT" type="xs:string"/>
    </xs:choice>
  </xs:group>
  <xs:complexType name="PARENT-A">
    <xs:sequence><xs:group ref="T:PARENT-A"/></xs:sequence>
  </xs:complexType>
</xs:schema>
"""


def synthetic_metadata() -> dict:
    return {
        "groups": {
            "ParentA": {
                "name": "ParentA",
                "annotation": "PARENT-A",
                "description": "keep me",
                "elements": [
                    {"name": "value", "xml_tag": "VALUE", "type": "String"},
                    {
                        "name": "items",
                        "xml_tag": "ENTRY",
                        "xml_wrapper_tag": "ITEMS",
                        "type": "String",
                    },
                ],
            },
            "ParentB": {
                "name": "ParentB",
                "annotation": "PARENT-B",
                "elements": [{"name": "value", "xml_tag": "VALUE", "type": "Integer"}],
            },
            "Shared": {
                "name": "Shared",
                "annotation": "SHARED",
                "elements": [
                    {"name": "left", "xml_tag": "LEFT", "type": "String"},
                    {"name": "right", "xml_tag": "RIGHT", "type": "String"},
                ],
            },
        },
        "complexTypes": {},
        "extract_inner_class": {},
        "simpleTypes": {},
    }


class XsdEnrichmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.xsd_path = Path(self.temporary.name) / "schema.xsd"
        self.xsd_path.write_text(SYNTHETIC_XSD, encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _matched(self) -> tuple[dict, dict]:
        metadata = synthetic_metadata()
        extracted = XsdContentModelExtractor(self.xsd_path).extract()
        return metadata, MetadataMatcher(metadata, domain="AUTOSAR", version="4-2-2").match(extracted)

    def test_preserves_choice_group_ref_and_parent_container(self) -> None:
        metadata, matched = self._matched()
        owners = {owner["owner_id"]: owner for owner in matched["owners"]}
        parent_a = next(
            owner for owner in owners.values()
            if owner.get("owner_kind") == "group" and owner.get("name") == "PARENT-A"
        )
        parent_b = next(
            owner for owner in owners.values()
            if owner.get("owner_kind") == "group" and owner.get("name") == "PARENT-B"
        )
        shared = next(
            owner for owner in owners.values()
            if owner.get("owner_kind") == "group" and owner.get("name") == "SHARED"
        )

        self.assertEqual(parent_a["declared_model"]["kind"], "sequence")
        self.assertEqual(shared["declared_model"]["kind"], "choice")
        group_ref = parent_a["declared_model"]["children"][2]
        self.assertEqual(group_ref["kind"], "group-ref")
        self.assertIn("children", parent_a["effective_model"]["children"][2])

        value_a = parent_a["declared_model"]["children"][0]
        value_b = parent_b["declared_model"]["children"][0]
        self.assertEqual(value_a["match"]["owner_key"], "ParentA")
        self.assertEqual(value_b["match"]["owner_key"], "ParentB")
        self.assertEqual(value_a["match"]["xml_tag"], value_b["match"]["xml_tag"])
        self.assertNotEqual(value_a["match"]["owner_entity_id"], value_b["match"]["owner_entity_id"])
        self.assertEqual(metadata["groups"]["ParentA"]["description"], "keep me")

    def test_wrapper_is_matched_inside_its_parent_context(self) -> None:
        _, matched = self._matched()
        parent_a = next(
            owner for owner in matched["owners"]
            if owner.get("owner_kind") == "group" and owner.get("name") == "PARENT-A"
        )
        wrapper_particle = parent_a["declared_model"]["children"][1]
        self.assertEqual(wrapper_particle["match"]["status"], "flattened_wrapper")

        anonymous = next(
            owner for owner in matched["owners"]
            if owner.get("owner_id") == wrapper_particle["anonymous_owner_id"]
        )
        self.assertEqual(anonymous["match"]["status"], "flattened_wrapper")
        entry = anonymous["declared_model"]["children"][0]
        self.assertEqual(entry["match"]["status"], "matched")
        self.assertEqual(entry["match"]["xml_wrapper_tag"], "ITEMS")
        self.assertIn("element:ITEMS@", anonymous["container_path"][-1])

    def test_metadata_enrichment_is_additive_and_idempotent(self) -> None:
        metadata, matched = self._matched()
        enriched, first = build_enriched_metadata(metadata, matched)
        self.assertGreater(first["records_changed"], 0)
        self.assertEqual(enriched["groups"]["ParentA"]["description"], "keep me")
        self.assertIn("xsd_group_model_json", enriched["groups"]["ParentA"])
        self.assertEqual(
            json.loads(enriched["groups"]["ParentA"]["xsd_group_model_json"])["kind"],
            "sequence",
        )

        enriched_again, second = build_enriched_metadata(enriched, matched)
        self.assertEqual(second["fields_changed"], 0)
        self.assertEqual(enriched_again, enriched)

    def test_existing_xsd_field_is_not_overwritten_without_explicit_replace(self) -> None:
        metadata, matched = self._matched()
        metadata["groups"]["ParentA"]["xsd_group_model_json"] = "different"
        enriched, report = build_enriched_metadata(metadata, matched, replace_existing=False)
        self.assertEqual(enriched["groups"]["ParentA"]["xsd_group_model_json"], "different")
        self.assertTrue(
            any(item["category"] == "existing_xsd_field_conflict" for item in report["conflicts"])
        )

    def test_schema_only_scalar_wrapper_and_typed_choice_are_audited_matches(self) -> None:
        xsd = """<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
 xmlns:T="urn:typed-model" targetNamespace="urn:typed-model">
 <xs:simpleType name="LIMIT-VALUE--SIMPLE"><xs:restriction base="xs:string"/></xs:simpleType>
 <xs:complexType name="LIMIT-VALUE"><xs:simpleContent>
  <xs:extension base="T:LIMIT-VALUE--SIMPLE"/>
 </xs:simpleContent></xs:complexType>
 <xs:group name="CHILD"><xs:sequence/></xs:group>
 <xs:complexType name="CHILD"><xs:sequence><xs:group ref="T:CHILD"/></xs:sequence></xs:complexType>
 <xs:group name="PARENT"><xs:choice>
  <xs:element name="CHILD" type="T:CHILD"/>
 </xs:choice></xs:group>
</xs:schema>"""
        path = Path(self.temporary.name) / "typed-model.xsd"
        path.write_text(xsd, encoding="utf-8")
        metadata = {
            "groups": {
                "Child": {"name": "Child", "xml_tag": "CHILD", "elements": []},
                "Parent": {"name": "Parent", "xml_tag": "PARENT", "elements": []},
            },
            "complexTypes": {},
            "extract_inner_class": {},
            "simpleTypes": {
                "LimitValueSimple": {
                    "name": "LimitValueSimple",
                    "xml_tag": "LIMIT-VALUE--SIMPLE",
                }
            },
        }

        matched = MetadataMatcher(metadata).match(XsdContentModelExtractor(path).extract())
        self.assertEqual(matched["conflicts"], [])
        self.assertEqual(matched["stats"]["owners_schema_only"], 1)
        scalar = next(owner for owner in matched["owners"] if owner.get("name") == "LIMIT-VALUE")
        self.assertEqual(scalar["match"]["status"], "schema_only")
        self.assertEqual(scalar["match"]["base_simple_type"], "LIMIT-VALUE--SIMPLE")
        parent = next(
            owner for owner in matched["owners"]
            if owner.get("owner_kind") == "group" and owner.get("name") == "PARENT"
        )
        child = parent["declared_model"]["children"][0]
        self.assertEqual(child["match"]["status"], "matched")
        self.assertEqual(child["match"]["mode"], "typed_model_element")
        self.assertEqual(child["match"]["model_target"]["key"], "Child")

    def test_typed_model_particle_requires_unique_target(self) -> None:
        xsd = """<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
 xmlns:T="urn:typed-ambiguous" targetNamespace="urn:typed-ambiguous">
 <xs:group name="CHILD"><xs:sequence/></xs:group>
 <xs:group name="PARENT"><xs:choice><xs:element name="CHILD" type="T:CHILD"/></xs:choice></xs:group>
</xs:schema>"""
        path = Path(self.temporary.name) / "typed-ambiguous.xsd"
        path.write_text(xsd, encoding="utf-8")
        metadata = {
            "groups": {
                "ChildA": {"name": "Child", "xml_tag": "CHILD", "elements": []},
                "ChildB": {"name": "Child", "xml_tag": "CHILD", "elements": []},
                "Parent": {"name": "Parent", "xml_tag": "PARENT", "elements": []},
            },
            "complexTypes": {}, "extract_inner_class": {}, "simpleTypes": {},
        }
        matched = MetadataMatcher(metadata).match(XsdContentModelExtractor(path).extract())
        self.assertTrue(any(item["category"] == "owner_ambiguous" for item in matched["conflicts"]))
        self.assertTrue(any(item["category"] == "particle_type_ambiguous" for item in matched["conflicts"]))


if __name__ == "__main__":
    unittest.main()

