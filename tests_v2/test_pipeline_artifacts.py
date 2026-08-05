from __future__ import annotations

import json
import unittest
from pathlib import Path

import src.validation.v2  # noqa: F401 - imports additional plugin registrations
from src.validation.v2.plugins import REGISTRY


class PipelineArtifactTest(unittest.TestCase):
    def test_every_implemented_plan_plugin_is_registered(self) -> None:
        root = Path(__file__).parents[1]
        plan = json.loads(
            (root / "src" / "generate_formal_constraints" / "v2" / "validation_plan.json").read_text(encoding="utf-8")
        )
        missing = sorted({
            rule["implementation"]["plugin"]
            for rule in plan["rules"]
            if rule["implementation"]["status"] == "implemented"
            and rule["implementation"]["plugin"] not in REGISTRY
        })
        self.assertEqual([], missing)

    def test_pipeline_audit_is_valid(self) -> None:
        root = Path(__file__).parents[1]
        audit = json.loads(
            (root / "src" / "generate_formal_constraints" / "v2" / "pipeline_audit.json").read_text(encoding="utf-8")
        )
        self.assertTrue(audit["valid"], audit["errors"])
        self.assertEqual(audit["counts"]["source"], audit["counts"]["constraints"])
        self.assertEqual(0, audit["counts"]["must_binding_failures"])

    def test_every_rule_has_a_hash_pinned_qualification_record(self) -> None:
        root = Path(__file__).parents[1]
        audit = json.loads(
            (root / "src/generate_formal_constraints/v2/compiled_rule_audit.json").read_text(encoding="utf-8")
        )
        self.assertTrue(audit["valid"], audit["errors"])
        self.assertEqual(554, audit["counts"]["must_validate"])
        self.assertEqual(554, audit["counts"]["qualified_rules"])
        self.assertEqual(400, audit["counts"]["python_rules"])
        self.assertEqual(154, audit["counts"]["dsl_rules"])
        self.assertTrue(all(item["qualified"] and item["plugin_module_sha256"] for item in audit["rules"]))

    def test_production_entry_forwards_all_declared_validation_context_fields(self) -> None:
        root = Path(__file__).parents[1]
        entry_source = (root / "llm_rag_generator_auto.py").read_text(encoding="utf-8")
        round2_source = (
            root / "src" / "llm_generation" / "core" / "round2_generator.py"
        ).read_text(encoding="utf-8")
        names = (
            "declared_use_cases",
            "declared_constraint_ids",
            "declared_targets",
            "declared_parameters",
        )
        for name in names:
            self.assertIn(name, entry_source)
            self.assertIn(f'declarations["{name}"]', round2_source)
        self.assertIn("_validation_declarations(custom_requirements)", round2_source)
        self.assertIn("declared_use_cases must be an array", round2_source)
        self.assertIn("declared_targets must be an object", round2_source)

    def test_round2_xml_converter_requires_compiled_xsd_serialization(self) -> None:
        root = Path(__file__).parents[1]
        source = (
            root / "src" / "llm_generation" / "core" / "round2_generator.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("def _xsd_sequence_order", source)
        self.assertNotIn("order = self._xsd_sequence_order(parent.tag)", source)
        self.assertIn("DeterministicXsdSerializer.from_files", source)
        self.assertIn("apply_projection_map", source)

        manifest = json.loads(
            (
                root
                / "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual("xsd_serialization_manifest", manifest["artifact_kind"])
        self.assertEqual(4080, manifest["stats"]["owners"])
        self.assertEqual(64, len(manifest["manifest_sha256"]))


if __name__ == "__main__":
    unittest.main()
