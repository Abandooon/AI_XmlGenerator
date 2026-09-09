"""Local fail-closed regression tests for the ATLAS U/G/A V6 repairs."""

from __future__ import annotations

import base64
import copy
import json
import pathlib
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from execution_schema_v027 import build_witness_matrix, harden_execution_schema
from probe_xgrammar_execution_schemas_v027 import resolve_model_vocab_size
from probe_xgrammar_regressions_v028 import (
    EXACT_V4_REJECTIONS,
    PINNED_XGRAMMAR_VERSION,
)
from qwen35_prompt_v026 import build_final_ir_instruction
from run_uga_schedule_v026 import classify_output
from strict_vllm_client_v026 import VllmExperimentConfig
from strict_vllm_uga_client_v026 import build_uga_completion_payload
from token_evidence_v027 import decode_token_ids, encode_token_ids
from verify_uga_qualification_v026 import main as qualification_main


class TokenEvidenceTests(unittest.TestCase):
    def test_large_sequence_round_trips_exactly(self) -> None:
        token_ids = [index % 151_643 for index in range(65_536)]
        evidence = encode_token_ids(token_ids)
        self.assertEqual(decode_token_ids(evidence), token_ids)

    def test_tampered_count_fails_closed(self) -> None:
        evidence = encode_token_ids([1, 2, 3])
        evidence["token_count"] = 4
        with self.assertRaisesRegex(ValueError, "count_mismatch"):
            decode_token_ids(evidence)

    def test_tampered_hash_fails_closed(self) -> None:
        evidence = encode_token_ids([1, 2, 3])
        evidence["token_ids_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash_mismatch"):
            decode_token_ids(evidence)

    def test_noncanonical_payload_fails_closed(self) -> None:
        import zlib

        evidence = encode_token_ids([1, 2, 3])
        evidence["data"] = base64.b64encode(zlib.compress(b"[1, 2, 3]")).decode(
            "ascii"
        )
        with self.assertRaisesRegex(ValueError, "not_canonical"):
            decode_token_ids(evidence)


class StableAuditRequestPayloadTests(unittest.TestCase):
    def config(self) -> VllmExperimentConfig:
        return VllmExperimentConfig(
            endpoint="http://127.0.0.1:8000/v1/completions",
            model="/model/Qwen3.5-9B",
            temperature=0.0,
            top_p=1.0,
            max_tokens=16_384,
            max_model_len=131_072,
        )

    def test_a_arm_carries_stable_external_audit_id(self) -> None:
        payload = build_uga_completion_payload(
            self.config(),
            arm="A",
            prompt="prompt",
            schema={"type": "object"},
            seed=1,
            request_id="experiment-001-a",
        )
        self.assertEqual(
            payload["structured_outputs"]["atlas_audit_request_id"],
            "cmpl-experiment-001-a-0",
        )

    def test_g_arm_does_not_claim_an_audit_identity(self) -> None:
        payload = build_uga_completion_payload(
            self.config(),
            arm="G",
            prompt="prompt",
            schema={"type": "object"},
            seed=1,
            request_id="experiment-001-g",
        )
        self.assertNotIn(
            "atlas_audit_request_id", payload["structured_outputs"]
        )


class TerminationAndCollectorTests(unittest.TestCase):
    def test_classification_rejects_two_json_values(self) -> None:
        result = classify_output("{} {}", {"type": "object"})
        self.assertEqual(result["single_json_value_decision"], "FAIL")

    def test_classification_accepts_one_json_value_and_whitespace(self) -> None:
        result = classify_output("  {}\n", {"type": "object"})
        self.assertEqual(result["single_json_value_decision"], "PASS")

    def test_qualification_cli_writes_fail_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            output = root / "qualification.json"
            argv = [
                "verify",
                "--contract",
                str(root / "missing-contract.json"),
                "--schedule",
                str(root / "missing-schedule.json"),
                "--run-root",
                str(root / "run"),
                "--audit-root",
                str(root / "audit"),
                "--postprocess-root",
                str(root / "post"),
                "--audit-verifier",
                str(root / "missing-audit.py"),
                "--output",
                str(output),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(qualification_main(), 2)
            manifest = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(manifest["decision"], "FAIL")
        self.assertFalse(manifest["paper_result_admissible"])

    def test_xgrammar_correctness_build_and_exact_failures_are_pinned(self) -> None:
        self.assertEqual(PINNED_XGRAMMAR_VERSION, "0.2.6rc1")
        self.assertEqual(
            EXACT_V4_REJECTIONS["005.json"]["first_rejected_token_index"],
            599,
        )
        self.assertEqual(
            EXACT_V4_REJECTIONS["007.json"]["first_rejected_token_index"],
            1214,
        )

    def test_prompt_resolves_legacy_xml_output_conflict(self) -> None:
        instruction = build_final_ir_instruction(
            requirement_text="Build AUTOSAR. Return only XML.",
            schema_text='{"type":"object"}',
        )
        self.assertIn("legacy XML-only task", instruction)
        self.assertTrue(
            instruction.endswith(
                "Do not emit XML, Markdown fences, self-correction, "
                "explanation, or a second JSON value."
            )
        )

    def test_v6_overlay_enforces_lossless_root_grammar_stop(self) -> None:
        bundle_root = pathlib.Path(__file__).resolve().parents[1]
        backend = (
            bundle_root
            / "vllm_overlay"
            / "overlay"
            / "vllm"
            / "v1"
            / "structured_output"
            / "backend_xgrammar.py"
        ).read_text(encoding="utf-8")
        scheduler = (
            bundle_root
            / "vllm_overlay"
            / "overlay"
            / "vllm"
            / "v1"
            / "core"
            / "sched"
            / "scheduler.py"
        ).read_text(encoding="utf-8")
        output_processor = (
            bundle_root
            / "vllm_overlay"
            / "overlay"
            / "vllm"
            / "v1"
            / "engine"
            / "output_processor.py"
        ).read_text(encoding="utf-8")
        launcher = (bundle_root / "tools" / "launch_vllm_qwen35_v026.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("terminate_without_stop_token=True", backend)
        self.assertIn("elif advance_token_ids and grammar.is_terminated():", scheduler)
        self.assertIn("request.status = RequestStatus.FINISHED_STOPPED", scheduler)
        self.assertIn(
            "request.stop_reason = STRUCTURED_OUTPUT_TERMINATED_STOP_REASON",
            scheduler,
        )
        self.assertIn("should_exclude_stop_token_from_output", output_processor)
        self.assertIn("STRUCTURED_OUTPUT_TERMINATED_STOP_REASON", output_processor)
        self.assertIn('"disable_any_whitespace": True', launcher)

    def test_v6_deployment_and_contract_pin_the_correctness_stack(self) -> None:
        bundle_root = pathlib.Path(__file__).resolve().parents[1]
        bootstrap = (bundle_root / "bootstrap_no_docker.sh").read_text(
            encoding="utf-8"
        )
        contract_builder = (
            bundle_root / "tools" / "build_uga_contract_v026.py"
        ).read_text(encoding="utf-8")
        probe = (
            bundle_root / "tools" / "probe_xgrammar_regressions_v028.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "97c1f669592a4934ceb51697e26610c110902accfb4078548d5958d82dd341a9",
            bootstrap,
        )
        self.assertIn('"apache-tvm-ffi==0.1.10"', bootstrap)
        self.assertIn('uv pip check --python "${venv_root}/bin/python"', bootstrap)
        self.assertIn("xgrammar_regression_model_path_mismatch", contract_builder)
        self.assertIn("xgrammar_regression_exact_replay_mismatch", contract_builder)
        self.assertIn("detokenization_regression_exact_cases_mismatch", contract_builder)
        self.assertIn(
            "preserve_grammar_completion_payload_token",
            contract_builder,
        )
        self.assertIn("nccl_regression_rank_evidence_mismatch", contract_builder)
        self.assertIn('"NCCL_CUMEM_HOST_ENABLE": "0"', contract_builder)
        self.assertIn('not item["accepted_all"]', probe)

    def test_qualification_verifier_builds_frozen_file_inventories(self) -> None:
        bundle_root = pathlib.Path(__file__).resolve().parents[1]
        verifier = (
            bundle_root / "tools" / "verify_uga_qualification_v026.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "result_files = [\n        run_root / name",
            verifier,
        )
        self.assertIn(
            "postprocess_files = [\n        postprocess_root / name",
            verifier,
        )
        self.assertIn("qualification_verifier_file_sha256", verifier)


class XGrammarProbeConfigTests(unittest.TestCase):
    def test_qwen35_nested_text_vocab_is_resolved(self) -> None:
        config = SimpleNamespace(
            text_config=SimpleNamespace(vocab_size=248_320)
        )
        self.assertEqual(resolve_model_vocab_size(config), 248_320)

    def test_plain_vocab_is_resolved(self) -> None:
        self.assertEqual(
            resolve_model_vocab_size(SimpleNamespace(vocab_size=151_936)),
            151_936,
        )

    def test_disagreeing_vocab_sizes_fail_closed(self) -> None:
        config = SimpleNamespace(
            vocab_size=100,
            text_config=SimpleNamespace(vocab_size=101),
        )
        with self.assertRaisesRegex(RuntimeError, "model_vocab_size_disagrees"):
            resolve_model_vocab_size(config)


class ExecutionSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_root = pathlib.Path(__file__).resolve().parents[1] / "source_assets"
        cls.manifest = json.loads(
            (cls.source_root / "SOURCE_ASSET_MANIFEST.json").read_text(
                encoding="utf-8"
            )
        )

    def test_all_twenty_schemas_are_finite_and_witnessed(self) -> None:
        for record in self.manifest["records"]:
            with self.subTest(case_id=record["case_id"]):
                source_schema = json.loads(
                    (self.source_root / record["schema_path"]).read_text(
                        encoding="utf-8"
                    )
                )
                requirement = (
                    self.source_root / record["requirement_path"]
                ).read_text(encoding="utf-8")
                schema, report = harden_execution_schema(
                    source_schema,
                    requirement,
                    case_id=record["case_id"],
                )
                self.assertLess(
                    report["execution_schema_character_count"],
                    report["source_schema_character_count"],
                )
                self.assertGreater(len(report["array_bounds"]), 0)
                self.assertEqual(build_witness_matrix(schema)["decision"], "PASS")

    def test_array_cardinality_mutation_in_requirement_fails_closed(self) -> None:
        record = next(
            item for item in self.manifest["records"] if item["case_id"] == "ASW-STD-04"
        )
        source_schema = json.loads(
            (self.source_root / record["schema_path"]).read_text(encoding="utf-8")
        )
        requirement = (self.source_root / record["requirement_path"]).read_text(
            encoding="utf-8"
        )
        mutated = requirement.replace("Exactly 2 P ports", "Exactly 9 P ports")
        with self.assertRaisesRegex(ValueError, "p_port_count_disagrees"):
            harden_execution_schema(
                source_schema,
                mutated,
                case_id=record["case_id"],
            )


if __name__ == "__main__":
    unittest.main()
