from __future__ import annotations

import unittest

from src.validation.v2.context import (
    ValidationContextError,
    build_validation_context,
    normalize_validation_context,
)

DATASET = "a" * 64
VALIDATOR = "c" * 64


class ValidationContextTests(unittest.TestCase):
    def test_manifest_is_deterministic_and_hash_pinned(self) -> None:
        trace = {
            "Controller": {
                "backend": "local-fallback",
                "dataset_sha256": DATASET,
                "result_count": 2,
                "fallback_reason": "Neo4j unavailable",
                "constraint_ids": ["constr_2", "constr_1"],
            }
        }
        first = build_validation_context(trace, expected_dataset_sha256=DATASET)
        second = build_validation_context(trace, expected_dataset_sha256=DATASET)
        self.assertEqual(first, second)
        self.assertEqual(["constr_1", "constr_2"], first["selected_constraint_ids"])
        self.assertEqual("VERIFIED", {
            "status": "VERIFIED" if normalize_validation_context(first, expected_dataset_sha256=DATASET) else ""
        }["status"])
    def test_validator_hash_is_pinned_and_mismatch_fails_closed(self) -> None:
        manifest = build_validation_context(
            {}, expected_dataset_sha256=DATASET,
            expected_validator_sha256=VALIDATOR,
        )
        self.assertEqual(VALIDATOR, manifest["validator_sha256"])
        self.assertEqual(
            manifest,
            normalize_validation_context(
                manifest, expected_dataset_sha256=DATASET,
                expected_validator_sha256=VALIDATOR,
            ),
        )
        with self.assertRaises(ValidationContextError):
            normalize_validation_context(manifest, expected_validator_sha256="d" * 64)


    def test_mixed_dataset_hash_fails_closed(self) -> None:
        with self.assertRaises(ValidationContextError):
            build_validation_context({
                "Controller": {
                    "backend": "neo4j", "dataset_sha256": "b" * 64,
                    "result_count": 0, "constraint_ids": [],
                }
            }, expected_dataset_sha256=DATASET)

    def test_tampered_manifest_is_rejected(self) -> None:
        manifest = build_validation_context({}, expected_dataset_sha256=DATASET)
        manifest["selected_constraint_ids"] = ["constr_fake"]
        with self.assertRaises(ValidationContextError):
            normalize_validation_context(manifest, expected_dataset_sha256=DATASET)

    def test_declared_targets_are_normalized_and_hash_pinned(self) -> None:
        trace = {
            "C": {
                "backend": "neo4j", "dataset_sha256": DATASET,
                "result_count": 1, "constraint_ids": ["constr_1"],
            }
        }
        manifest = build_validation_context(
            trace, expected_dataset_sha256=DATASET,
            declared_constraint_ids=["constr_1"],
            declared_targets={"constr_1": ["Pkg\\Dependency", "/Pkg/Dependency"]},
        )
        self.assertEqual({"constr_1": ["/Pkg/Dependency"]}, manifest["declared_targets"])
        self.assertEqual(manifest, normalize_validation_context(manifest, expected_dataset_sha256=DATASET))

    def test_target_without_declared_constraint_is_rejected(self) -> None:
        with self.assertRaises(ValidationContextError):
            build_validation_context(
                {}, expected_dataset_sha256=DATASET,
                declared_targets={"constr_1": ["/Pkg/Dependency"]},
            )

    def test_tampered_target_is_rejected(self) -> None:
        manifest = build_validation_context({}, expected_dataset_sha256=DATASET)
        manifest["declared_targets"] = {"constr_1": ["/Pkg/Dependency"]}
        with self.assertRaises(ValidationContextError):
            normalize_validation_context(manifest, expected_dataset_sha256=DATASET)


if __name__ == "__main__":
    unittest.main()
