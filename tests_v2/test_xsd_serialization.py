from __future__ import annotations

import json
import tempfile
import unittest
from collections import OrderedDict
from pathlib import Path
from xml.etree.ElementTree import Element, tostring

from src.kg_builder.xsd_enrichment.serialization_manifest import (
    XsdSerializationManifestError,
    load_serialization_manifest,
)
from src.llm_generation.core.xsd_serializer import (
    DeterministicXsdSerializer,
    XsdSerializationError,
    apply_projection_map,
)
from src.validation.v2.context import (
    ValidationContextError,
    build_validation_context,
    normalize_validation_context,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
XSD = PROJECT_ROOT / "src/validation/data/AUTOSAR_4-2-2.xsd"
MANIFEST = (
    PROJECT_ROOT
    / "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json"
)


class XsdSerializationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.serializer = DeterministicXsdSerializer.from_files(
            MANIFEST,
            xsd_path=XSD,
        )

    @staticmethod
    def projection_map() -> dict:
        return {
            "schema_version": "1.0",
            "rules": [
                {
                    "source": ["SWC-INTERNAL-BEHAVIOR"],
                    "target": ["INTERNAL-BEHAVIORS", "SWC-INTERNAL-BEHAVIOR"],
                },
                {
                    "source": [
                        "INTERNAL-BEHAVIORS",
                        "SWC-INTERNAL-BEHAVIOR",
                        "RUNNABLE-ENTITY",
                    ],
                    "target": [
                        "INTERNAL-BEHAVIORS",
                        "SWC-INTERNAL-BEHAVIOR",
                        "RUNNABLES",
                        "RUNNABLE-ENTITY",
                    ],
                },
            ],
        }

    def test_projection_is_explicit_and_conflicts_fail_closed(self) -> None:
        payload = {
            "SWC-INTERNAL-BEHAVIOR": {
                "SHORT-NAME": "Behavior",
                "RUNNABLE-ENTITY": [{"SHORT-NAME": "Runnable"}],
            }
        }
        projected = apply_projection_map(payload, self.projection_map())
        behavior = projected["INTERNAL-BEHAVIORS"]["SWC-INTERNAL-BEHAVIOR"]
        self.assertNotIn("RUNNABLE-ENTITY", behavior)
        self.assertEqual(
            "Runnable",
            behavior["RUNNABLES"]["RUNNABLE-ENTITY"][0]["SHORT-NAME"],
        )

        conflict = {
            "SWC-INTERNAL-BEHAVIOR": {},
            "INTERNAL-BEHAVIORS": {"SWC-INTERNAL-BEHAVIOR": {}},
        }
        with self.assertRaises(XsdSerializationError):
            apply_projection_map(conflict, self.projection_map())

    def test_real_swc_internal_behavior_order_is_key_order_independent(self) -> None:
        first = OrderedDict([
            ("SUPPORTS-MULTIPLE-INSTANTIATION", "false"),
            ("RUNNABLES", {}),
            ("HANDLE-TERMINATION-AND-RESTART", "CAN-BE-TERMINATED-AND-RESTARTED"),
            ("EVENTS", {}),
            ("SHORT-NAME", "Behavior"),
        ])
        second = OrderedDict(reversed(list(first.items())))

        outputs = []
        for payload in (first, second):
            root = Element("SWC-INTERNAL-BEHAVIOR")
            self.serializer.append_payload(
                root,
                payload,
                root_element="SWC-INTERNAL-BEHAVIOR",
            )
            outputs.append(tostring(root, encoding="unicode"))
            self.assertEqual(
                [
                    "SHORT-NAME",
                    "EVENTS",
                    "HANDLE-TERMINATION-AND-RESTART",
                    "RUNNABLES",
                    "SUPPORTS-MULTIPLE-INSTANTIATION",
                ],
                [child.tag for child in root],
            )
        self.assertEqual(outputs[0], outputs[1])

    def test_unknown_or_ambiguous_structure_never_preserves_llm_order(self) -> None:
        root = Element("SWC-INTERNAL-BEHAVIOR")
        with self.assertRaises(XsdSerializationError):
            self.serializer.append_payload(
                root,
                {"SHORT-NAME": "Behavior", "NOT-IN-XSD": "value"},
                root_element="SWC-INTERNAL-BEHAVIOR",
            )

    def test_manifest_is_hash_pinned_to_xsd(self) -> None:
        loaded = load_serialization_manifest(MANIFEST, xsd_path=XSD)
        self.assertEqual(64, len(loaded["manifest_sha256"]))
        with tempfile.TemporaryDirectory() as directory:
            wrong_xsd = Path(directory) / "wrong.xsd"
            wrong_xsd.write_text("<schema/>", encoding="utf-8")
            with self.assertRaises(XsdSerializationManifestError):
                load_serialization_manifest(MANIFEST, xsd_path=wrong_xsd)

    def test_validation_context_pins_serialization_manifest(self) -> None:
        dataset = "a" * 64
        validator = "b" * 64
        serialization = "c" * 64
        context = build_validation_context(
            {},
            expected_dataset_sha256=dataset,
            expected_validator_sha256=validator,
            expected_xsd_serialization_manifest_sha256=serialization,
        )
        self.assertEqual(
            serialization,
            context["xsd_serialization_manifest_sha256"],
        )
        self.assertEqual(
            context,
            normalize_validation_context(
                context,
                expected_dataset_sha256=dataset,
                expected_validator_sha256=validator,
                expected_xsd_serialization_manifest_sha256=serialization,
            ),
        )
        with self.assertRaises(ValidationContextError):
            normalize_validation_context(
                context,
                expected_xsd_serialization_manifest_sha256="d" * 64,
            )


if __name__ == "__main__":
    unittest.main()
