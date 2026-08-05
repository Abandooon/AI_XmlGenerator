import json
import unittest

from src.kg_builder.xsd_enrichment.content_model import canonical_json
from src.kg_builder.xsd_enrichment.neo4j_apply import KgUpdateConflict, collect_updates


def _model(owner_id: str, element: str) -> dict:
    effective = {
        "kind": "sequence",
        "children": [{"kind": "element", "element_name": element}],
    }
    return {
        "owner_id": owner_id,
        "owner_kind": "group" if owner_id.endswith("group") else "anonymousComplexType",
        "container_path": [f"element:{element}"],
        "declared_model": effective,
        "effective_model": effective,
        "declared_model_sha256": owner_id + "-declared",
        "effective_model_sha256": owner_id + "-effective",
    }


def _record(name: str, model: dict, extra_field: str) -> dict:
    return {
        "name": name,
        "xsd_content_models_json": canonical_json([model]),
        "xsd_owner_ids_json": canonical_json([model["owner_id"]]),
        "xsd_source_sha256": "source-hash",
        "xsd_model_sha256": model["owner_id"],
        "xsd_model_version": "1",
        extra_field: canonical_json(model["declared_model"]),
        "xsd_effective_model_json": canonical_json(model["effective_model"]),
    }


class Neo4jMergeTests(unittest.TestCase):
    def test_same_name_legacy_split_keeps_both_parent_contexts(self):
        group_model = _model("owner-group", "GROUP-CHILD")
        inner_model = _model("owner-inner", "INNER-CHILD")
        metadata = {
            "groups": {
                "Target": _record("Target", group_model, "xsd_group_model_json"),
            },
            "extract_inner_class": {
                "Target": _record("Target", inner_model, "xsd_complex_type_model_json"),
            },
        }

        rows = collect_updates(metadata, domain="AUTOSAR", version="4-2-2")

        self.assertEqual(len(rows), 1)
        props = rows[0]["props"]
        models = json.loads(props["xsd_content_models_json"])
        self.assertEqual({item["owner_id"] for item in models}, {"owner-group", "owner-inner"})
        self.assertNotIn("xsd_effective_model_json", props)
        self.assertIn("xsd_group_model_json", props)
        self.assertIn("xsd_complex_type_model_json", props)

    def test_different_names_with_same_slug_remain_a_conflict(self):
        model = _model("owner-group", "CHILD")
        metadata = {
            "groups": {"A-B": _record("A-B", model, "xsd_group_model_json")},
            "extract_inner_class": {
                "A_B": _record("A_B", model, "xsd_complex_type_model_json"),
            },
        }

        with self.assertRaises(KgUpdateConflict):
            collect_updates(metadata, domain="AUTOSAR", version="4-2-2")

    def test_same_owner_with_different_models_remains_a_conflict(self):
        first = _model("same-owner", "FIRST")
        second = _model("same-owner", "SECOND")
        metadata = {
            "groups": {"Target": _record("Target", first, "xsd_group_model_json")},
            "extract_inner_class": {
                "Target": _record("Target", second, "xsd_complex_type_model_json"),
            },
        }

        with self.assertRaises(KgUpdateConflict):
            collect_updates(metadata, domain="AUTOSAR", version="4-2-2")


if __name__ == "__main__":
    unittest.main()
