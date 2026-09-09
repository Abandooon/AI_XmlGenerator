from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pil_v4_arms
import pil_v4_authorize
import pil_v4_contract as contract
import pil_v4_preflight
import pil_v4_provider
import pil_v4_run
import pil_v4_rescore
import pil_v4_schedule
import pil_v41_render_prompts
from pil_v4_client import Generation
from pil_v4_client import COMMON_SYSTEM_INSTRUCTIONS


def valid_decision(
    *,
    provision: str = "Art.24(1)",
    forum_type: str = "exclusive",
    instrument: str = "BRUSSELS_I_BIS",
) -> dict:
    return {
        "conclusion": "Court_of_X_has_jurisdiction",
        "forum": "France courts",
        "forum_type": forum_type,
        "alternative_forum_types": [],
        "conditional_answer": False,
        "explicit_abstention": False,
        "legal_basis": [{"instrument": instrument, "provision": provision}],
        "reasoning": "The identified provision controls the forum.",
        "missing_facts": [],
    }


class FakeUnifiedClient:
    def __init__(self, decisions: list[dict]) -> None:
        self.decisions = list(decisions)
        self.calls = 0
        self.prompts: list[str] = []
        self.schemas: list[dict | None] = []

    def generate(self, prompt: str, *, schema: dict | None, seed: int) -> Generation:
        self.calls += 1
        self.prompts.append(prompt)
        self.schemas.append(schema)
        decision = self.decisions.pop(0)
        return Generation(
            raw_text=json.dumps(decision),
            parsed=decision if schema is not None else None,
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
            provider_schema_enforced=schema is not None,
            seed=seed,
            provider_response={
                "requested_model": contract.PROVIDER_PROTOCOL["model_name"],
                "response_model": contract.PROVIDER_PROTOCOL["expected_response_model"],
                "seed": seed,
                "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            },
            transport_attempts=({"transport_attempt": 1, "status": "RESPONSE_RECEIVED"},),
        )


class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = contract.load_schema()
        self.rules = contract.load_rules()

    def test_atomic_alternatives_replace_compound_label(self) -> None:
        decision = valid_decision(provision="Art.7(1)(b)", forum_type="special")
        decision["alternative_forum_types"] = ["general"]
        audit = contract.audit_decision(
            decision, schema=self.schema, rules=self.rules,
            allowed_evidence=["BRUSSELS_I_BIS:Art.7(1)(b)"],
        )
        self.assertEqual(audit["status"], "PASS")
        decision["forum_type"] = "special_or_general"
        self.assertEqual(
            contract.audit_decision(decision, schema=self.schema, rules=self.rules, allowed_evidence=None)["status"],
            "FAIL",
        )

    def test_article_29_30_and_31_are_not_conflated(self) -> None:
        decision = valid_decision(provision="Art.29(1)", forum_type="lis_pendens")
        decision["conclusion"] = "Stay_for_first_seised"
        self.assertEqual(contract.audit_decision(
            decision, schema=self.schema, rules=self.rules,
            allowed_evidence=["BRUSSELS_I_BIS:Art.29(1)"],
        )["status"], "PASS")
        decision["legal_basis"] = [{"instrument": "BRUSSELS_I_BIS", "provision": "Art.30(1)"}]
        findings = contract.audit_decision(
            decision, schema=self.schema, rules=self.rules,
            allowed_evidence=["BRUSSELS_I_BIS:Art.30(1)"],
        )
        self.assertEqual(findings["status"], "FAIL")
        self.assertIn("forum_type_basis_mismatch", {item["code"] for item in findings["findings"]})

        related = valid_decision(provision="Art.30(1)", forum_type="related_actions")
        related["conclusion"] = "May_stay_or_decline_for_related_actions"
        self.assertEqual(contract.audit_decision(
            related, schema=self.schema, rules=self.rules,
            allowed_evidence=["BRUSSELS_I_BIS:Art.30(1)"],
        )["status"], "PASS")

    def test_euipo_authority_is_not_encoded_as_a_court(self) -> None:
        decision = valid_decision(
            provision="Art.63(1)", forum_type="exclusive",
            instrument="EU_TRADE_MARK_REGULATION",
        )
        decision["conclusion"] = "Authority_of_X_has_jurisdiction"
        decision["forum"] = "EUIPO"
        self.assertEqual(contract.audit_decision(
            decision, schema=self.schema, rules=self.rules,
            allowed_evidence=["EU_TRADE_MARK_REGULATION:Art.63(1)"],
        )["status"], "PASS")

    def test_correct_alternative_cannot_rescue_a_wrong_primary_forum_type(self) -> None:
        decision = valid_decision(provision="Art.7(1)(b)", forum_type="agreement")
        decision["alternative_forum_types"] = ["special"]
        gold = {
            "conclusion": "Court_of_X_has_jurisdiction",
            "accepted_conclusions": ["Court_of_X_has_jurisdiction"],
            "forum_type": "special",
            "accepted_forum_types": ["special"],
            "conditional_answer": False,
            "required_evidence": ["BRUSSELS_I_BIS:Art.7(1)(b)"],
        }
        compatibility = contract.score_against_gold(decision, gold)
        self.assertFalse(compatibility.forum_type)
        self.assertFalse(compatibility.correct)

    def test_conditional_answer_is_part_of_gold_correctness(self) -> None:
        decision = valid_decision()
        gold = {
            "conclusion": decision["conclusion"],
            "accepted_conclusions": [decision["conclusion"]],
            "forum_type": decision["forum_type"],
            "accepted_forum_types": [decision["forum_type"]],
            "conditional_answer": True,
            "required_evidence": ["BRUSSELS_I_BIS:Art.24(1)"],
        }
        self.assertFalse(contract.score_against_gold(decision, gold).correct)

    def test_soft_json_has_no_fence_repair(self) -> None:
        raw = json.dumps(valid_decision())
        self.assertIsNotNone(contract.strict_json_parse(raw)[0])
        self.assertIsNone(contract.strict_json_parse("```json\n" + raw + "\n```")[0])

    def test_provider_request_uses_the_frozen_protocol(self) -> None:
        captured: dict = {}

        class Completions:
            @staticmethod
            def create(**kwargs):
                captured.update(kwargs)
                return SimpleNamespace(
                    id="fixture", model="gpt-5.6-luna-2026-07-09",
                    usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                    choices=[SimpleNamespace(finish_reason="stop")],
                )

        transport = pil_v4_provider.V4ResponsesTransport(
            api_key="fixture", base_url="https://example.test/v1",
            transport=SimpleNamespace(
                chat=SimpleNamespace(completions=Completions()),
            ),
        )
        response = transport._create_response(
            prompt="facts", instructions="system", seed=104729,
            text={"format": {
                "type": "json_schema", "name": "fixture", "strict": True,
                "schema": {"type": "object", "additionalProperties": False},
            }},
        )
        self.assertEqual(captured["model"], contract.PROVIDER_PROTOCOL["model_name"])
        self.assertEqual(captured["reasoning_effort"], "low")
        self.assertEqual(captured["temperature"], 1.0)
        self.assertEqual(captured["max_completion_tokens"], 128000)
        self.assertEqual(captured["seed"], 104729)
        self.assertEqual(captured["response_format"]["type"], "json_schema")
        self.assertTrue(captured["response_format"]["json_schema"]["strict"])
        self.assertNotIn("tools", captured)
        self.assertEqual(
            transport._response_metadata(response, seed=104729)["usage"],
            {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
        )

    def test_provider_stops_on_response_model_mismatch(self) -> None:
        class Completions:
            @staticmethod
            def create(**kwargs):
                return SimpleNamespace(
                    id="wrong-model", model="different-model",
                    usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
                    choices=[SimpleNamespace(finish_reason="stop")],
                )

        transport = pil_v4_provider.V4ChatCompletionsTransport(
            api_key="fixture", base_url="https://example.test/v1",
            transport=SimpleNamespace(chat=SimpleNamespace(completions=Completions())),
        )
        with self.assertRaises(contract.InfrastructureError) as raised:
            transport._create_response(prompt="facts", instructions="system", seed=104729)
        self.assertEqual(raised.exception.provider_response["response_model"], "different-model")
        self.assertEqual(
            raised.exception.transport_attempts[-1]["status"],
            "RESPONSE_MODEL_MISMATCH",
        )


class ArmTests(unittest.TestCase):
    def setUp(self) -> None:
        provisions = [{
            "evidence_id": "BRUSSELS_I_BIS:Art.24(1)",
            "instrument": "BRUSSELS_I_BIS", "provision": "Art.24(1)",
            "title": "immovable property", "text_en": "Courts at the property location have jurisdiction.",
            "keywords": ["immovable property", "rights in rem"],
        }]
        self.context = pil_v4_arms.ArmContext(
            schema=contract.load_schema(), rules=contract.load_rules(), provisions=provisions,
            retriever=pil_v4_arms.FrozenRetriever(provisions),
        )
        self.case = {"id": 1, "facts_text": "A dispute concerns rights in rem in French immovable property."}

    def unit(self, arm: str) -> dict:
        return {"unit_id": f"1|{arm}|1", "case_id": 1, "arm": arm, "replicate": 1}

    def test_p0_and_p1_share_semantic_json_without_keyword_parser(self) -> None:
        for arm in ("p0", "p1"):
            fake = FakeUnifiedClient([valid_decision()])
            row = pil_v4_arms.run_unit(fake, self.context, self.unit(arm), self.case)
            self.assertEqual(row["schema_status"], "PASS")
            self.assertEqual(row["final_decision"]["forum_type"], "exclusive")
            self.assertEqual(row["external_call_count"], 1)
            self.assertEqual(row["logical_request_count"], 1)
            self.assertEqual(row["transport_request_count"], 1)
            self.assertEqual(row["seed"], 104729)

    def test_p1_and_p2_receive_identical_complete_prompt_contract(self) -> None:
        p1 = FakeUnifiedClient([valid_decision()])
        p2 = FakeUnifiedClient([valid_decision()])
        pil_v4_arms.run_unit(p1, self.context, self.unit("p1"), self.case)
        pil_v4_arms.run_unit(p2, self.context, self.unit("p2"), self.case)
        self.assertEqual(p1.prompts, p2.prompts)
        self.assertIn('"conditional_answer":{"type":"boolean"}', p1.prompts[0])
        self.assertIsNone(p1.schemas[0])
        self.assertEqual(p2.schemas[0], self.context.schema)

    def test_p3_runs_one_bounded_repair(self) -> None:
        invalid = valid_decision(provision="Art.24(1)", forum_type="general")
        repaired = valid_decision()
        fake = FakeUnifiedClient([invalid, repaired])
        row = pil_v4_arms.run_unit(fake, self.context, self.unit("p3"), self.case)
        self.assertTrue(row["repair"]["attempted"])
        self.assertEqual(row["repair"]["status"], "PASS")
        self.assertTrue(row["system_release"])
        self.assertEqual(fake.calls, 2)
        self.assertEqual(row["logical_request_count"], 2)
        self.assertEqual(row["transport_request_count"], 2)
        self.assertEqual(row["repair"]["prompt_cjk_characters"], 0)

    def test_p3_redacts_non_english_prior_output_from_repair_prompt(self) -> None:
        invalid = valid_decision(provision="Art.24(1)", forum_type="general")
        invalid["reasoning"] = "法国法院有管辖权。"
        fake = FakeUnifiedClient([invalid, valid_decision()])
        row = pil_v4_arms.run_unit(fake, self.context, self.unit("p3"), self.case)
        self.assertTrue(row["repair"]["attempted"])
        self.assertNotIn("法国法院", row["repair"]["prompt"])
        self.assertIn("[NON-ENGLISH VALUE REDACTED]", row["repair"]["prompt"])
        self.assertFalse(contract.contains_cjk(row["repair"]["prompt"]))

    def test_initial_infrastructure_failure_retains_exact_prompt(self) -> None:
        class FailingClient:
            @staticmethod
            def generate(prompt, *, schema, seed):
                error = contract.InfrastructureError("fixture outage")
                error.transport_attempts = [{"transport_attempt": 1, "status": "FAILED"}]
                raise error

        with self.assertRaises(contract.InfrastructureError) as raised:
            pil_v4_arms.run_unit(FailingClient(), self.context, self.unit("p1"), self.case)
        error = raised.exception
        self.assertEqual(error.failed_stage, "initial")
        self.assertEqual(
            hashlib.sha256(error.failed_prompt.encode("utf-8")).hexdigest(),
            error.failed_prompt_sha256,
        )
        self.assertEqual(error.logical_requests_observed, 1)

    def test_p3_does_not_repair_a_passing_decision(self) -> None:
        fake = FakeUnifiedClient([valid_decision()])
        row = pil_v4_arms.run_unit(fake, self.context, self.unit("p3"), self.case)
        self.assertFalse(row["repair"]["attempted"])
        self.assertTrue(row["system_release"])
        self.assertEqual(fake.calls, 1)

    def test_retriever_ignores_keywords_in_explicit_exclusion_clause(self) -> None:
        provisions = [
            {"evidence_id": "consumer", "keywords": ["消费者", "选择法院"]},
            {"evidence_id": "domicile", "keywords": ["任何欧盟成员国均无住所"]},
        ]
        retriever = pil_v4_arms.FrozenRetriever(provisions, top_k=1)
        result = retriever.retrieve(
            "乙在任何欧盟成员国均无住所；案情不涉及消费者或选择法院协议。"
        )
        self.assertEqual([item["evidence_id"] for item in result], ["domicile"])


class ScheduleTests(unittest.TestCase):
    def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")

    def _hash(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def make_ready(self, root: Path) -> Path:
        dataset = root / "inference_dataset.jsonl"
        gold = root / "consensus_gold.jsonl"
        kb = root / "kb.jsonl"
        schema = root / "decision_schema_v4.json"
        gold_schema = root / "consensus_gold_schema_v4.json"
        rules = root / "delivery_rules_v4.json"
        parameter_match = root / "PIL_V4_AUTOSAR_V20_PARAMETER_MATCH.json"
        english_manifest = root / "PIL_V41_ENGLISH_INPUT_MANIFEST.json"
        legal_source_audit = root / "PIL_V41_ENGLISH_LEGAL_SOURCE_AUDIT.json"
        translation_acceptance = root / "PIL_V41_TRANSLATION_PARITY_ACCEPTANCE.json"
        rendered_prompts = root / "PIL_V41_RENDERED_PROMPTS.jsonl"
        prepaid_code_audit = root / "PIL_V41_PREPAID_CODE_AUDIT.json"
        self._write_jsonl(dataset, [
            {"id": i, "cluster_id": f"CL-{i:03d}", "facts_text": f"facts {i}", "source_class": "expert"}
            for i in range(1, 61)
        ])
        self._write_jsonl(gold, [
            {"id": i, "cluster_id": f"CL-{i:03d}", "conclusion": contract.ABSTAIN,
             "forum": "none", "forum_type": "none", "alternative_forum_types": [],
             "conditional_answer": True, "explicit_abstention": True,
             "legal_basis": [], "reasoning": "The fixture lacks jurisdiction facts.",
             "missing_facts": ["fixture"], "accepted_conclusions": [contract.ABSTAIN],
             "accepted_forum_types": ["none"], "required_evidence": [],
             "accepted_evidence": [], "review_source_stage": "A1_C1_AGREEMENT"}
            for i in range(1, 61)
        ])
        self._write_jsonl(kb, [
            {"evidence_id": "BRUSSELS_I_BIS:Art.29(1)", "instrument": "BRUSSELS_I_BIS", "provision": "Art.29(1)", "text_zh": "same action"},
            {"evidence_id": "BRUSSELS_I_BIS:Art.30(1)", "instrument": "BRUSSELS_I_BIS", "provision": "Art.30(1)", "text_zh": "related actions"},
            {"evidence_id": "BRUSSELS_I_BIS:Art.31(2)", "instrument": "BRUSSELS_I_BIS", "provision": "Art.31(2)", "text_zh": "chosen court"},
            {"evidence_id": "EU_TRADE_MARK_REGULATION:Art.63(1)", "instrument": "EU_TRADE_MARK_REGULATION", "provision": "Art.63(1)", "text_zh": "EUIPO invalidity"},
        ])
        schema.write_text(json.dumps(contract.load_schema()), encoding="utf-8")
        gold_schema.write_text(
            (contract.ROOT / "schema" / "consensus_gold_schema_v4.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        rules.write_text(json.dumps(contract.load_rules()), encoding="utf-8")
        parameter_match.write_text(
            (contract.ROOT / "PIL_V41_AUTOSAR_V20_PARAMETER_MATCH.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        english_manifest.write_text(
            (contract.ROOT / "PIL_V41_ENGLISH_INPUT_MANIFEST.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        rendered_prompts.write_text(
            (contract.ROOT / "PIL_V41_RENDERED_PROMPTS.jsonl").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        legal_source_audit.write_text(
            (contract.ROOT / "PIL_V41_ENGLISH_LEGAL_SOURCE_AUDIT.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        translation_acceptance.write_text(json.dumps({
            "status": "PASS", "case_rows_accepted": 60,
            "evidence_rows_accepted": 58, "unresolved_rows": 0,
            "accepted_workbook_sha256": "d" * 64,
            "reviewer": "Fixture Reviewer", "review_date": "2026-09-04",
            "provider_calls_before_acceptance": 0,
        }), encoding="utf-8")
        prepaid_code_audit.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
        inputs = {
            "inference_dataset": dataset, "consensus_gold": gold, "knowledge_base": kb,
            "decision_schema": schema, "gold_schema": gold_schema, "delivery_rules": rules,
            "autosar_v20_parameter_match": parameter_match,
            "english_input_manifest": english_manifest,
            "english_legal_source_audit": legal_source_audit,
            "translation_parity_acceptance": translation_acceptance,
            "rendered_prompts": rendered_prompts,
            "prepaid_code_audit": prepaid_code_audit,
        }
        source_preflight = root / "source_preflight.json"
        source_preflight.write_text(
            json.dumps({"content_sha256": "e" * 64}), encoding="utf-8",
        )
        readiness = root / "readiness.json"
        readiness.write_text(json.dumps({
            "schema_version": "atlas.pil.formal_readiness.v4.1",
            "status": "READY_FOR_FORMAL_RUN", "formal_run_enabled": True, "external_calls_authorized": True,
            "review": {
                "reviewer_1_locked": True, "reviewer_2_locked": True, "consensus_complete": True,
                "affected_cases_reconfirmed_after_fact_edits": True,
                "agreement_report_sha256": "a" * 64, "adjudication_record_sha256": "b" * 64,
                "d1_acceptance_sha256": "c" * 64,
            },
            "inputs": {key: {"path": str(path), "sha256": self._hash(path)} for key, path in inputs.items()},
            "implementation": {
                key: {"path": str(path), "sha256": self._hash(path)}
                for key, path in {
                    "preflight": contract.ROOT / "pil_v4_preflight.py",
                    "contract": contract.ROOT / "pil_v4_contract.py",
                    "arms": contract.ROOT / "pil_v4_arms.py",
                    "client": contract.ROOT / "pil_v4_client.py",
                    "provider": contract.ROOT / "pil_v4_provider.py",
                    "schedule": contract.ROOT / "pil_v4_schedule.py",
                    "runner": contract.ROOT / "pil_v4_run.py",
                    "rescore": contract.ROOT / "pil_v4_rescore.py",
                    "authorizer": contract.ROOT / "pil_v4_authorize.py",
                    "prepaid_freezer": contract.ROOT / "pil_v4_freeze_prepaid.py",
                    "prompt_renderer": contract.ROOT / "pil_v41_render_prompts.py",
                    "english_input_builder": contract.ROOT / "build_pil_v41_english_inputs.py",
                    "prepaid_audit": contract.ROOT / "pil_v41_prepaid_audit.py",
                }.items()
            },
            "provider_contract": dict(contract.PROVIDER_PROTOCOL),
            "runtime_environment": contract.runtime_environment(),
            "provider_calls_before_authorization": 0,
            "paid_api_calls_before_authorization": 0,
            "authorization": {
                "api_base_sha256": "a" * 64,
                "authorized_unit_count": 720,
                "confirmation_token_sha256": contract.canonical_sha256(
                    contract.PAID_CONFIRMATION
                ),
                "preflight_path": str(source_preflight),
                "preflight_file_sha256": self._hash(source_preflight),
                "preflight_content_sha256": "e" * 64,
            },
            "required_checks": {
                "inference_dataset_contains_no_gold": True,
                "knowledge_base_checked_against_eur_lex": True,
                "article_29_30_31_distinguished": True,
                "case_count_is_60": True, "gold_case_ids_match_dataset": True,
                "instrument_qualified_evidence_ids": True,
                "consensus_gold_schema_valid": True,
                "retrieval_required_evidence_coverage_complete": True,
                "dependency_clusters_declared": True,
                "implementation_files_hashed": True,
                "provider_contract_frozen": True,
                "autosar_v20_provider_parameters_matched": True,
                "english_model_inputs_verified": True,
                "english_legal_source_audit_passed": True,
                "translation_parity_review_complete": True,
                "translation_review_workbook_hash_verified": True,
                "all_240_primary_prompts_are_english": True,
                "p1_p2_p3_prompt_text_is_identical": True,
                "rendered_prompt_artifact_matches_implementation": True,
                "prepaid_code_audit_passed": True,
                "runtime_environment_complete": True,
                "four_arm_schedule_is_720_units": True, "offline_tests_pass": True,
            },
        }), encoding="utf-8")
        document = json.loads(readiness.read_text(encoding="utf-8"))
        document["content_sha256"] = contract.canonical_sha256(document)
        readiness.write_text(json.dumps(document), encoding="utf-8")
        return readiness

    def test_blocked_template_fails_without_external_calls(self) -> None:
        template = Path(__file__).resolve().parents[1] / "PIL_V4_READINESS_TEMPLATE.json"
        plan = pil_v4_run.plan(template, Path("missing_schedule.json"), Path("missing_ledger.jsonl"))
        self.assertEqual(plan["readiness_status"], "BLOCKED")
        self.assertEqual(plan["external_calls_made"], 0)
        self.assertTrue(plan["blockers"])

    def test_actual_preflight_is_zero_call_and_ready_after_translation_review(self) -> None:
        document = pil_v4_preflight.build(offline_tests_passed=True)
        self.assertEqual(document["status"], "READY_FOR_PAID_AUTHORIZATION")
        self.assertEqual(document["provider_calls"], 0)
        self.assertEqual(document["paid_api_calls"], 0)
        self.assertEqual(document["summary"]["case_count"], 60)
        self.assertEqual(document["summary"]["retrieval_miss_count"], 0)
        self.assertTrue(document["required_checks"]["translation_parity_review_complete"])
        self.assertTrue(document["required_checks"]["translation_review_workbook_hash_verified"])
        self.assertEqual(document["prepaid_blockers"], [])

    def test_all_frozen_primary_prompts_are_english_and_recorded(self) -> None:
        records = pil_v41_render_prompts.build()
        self.assertEqual(len(records), 240)
        self.assertTrue(all(row["language"] == "en" for row in records))
        self.assertTrue(all(row["cjk_characters"] == 0 for row in records))
        self.assertTrue(all(row["system_instructions"] == COMMON_SYSTEM_INSTRUCTIONS for row in records))
        self.assertIn("may rely on your legal knowledge", COMMON_SYSTEM_INSTRUCTIONS)

    def test_authorizer_rejects_missing_explicit_confirmation(self) -> None:
        with self.assertRaises(ValueError):
            pil_v4_authorize.build_formal_readiness(Path("missing.json"), "")

    def test_authorizer_binds_provider_runtime_and_endpoint_without_a_call(self) -> None:
        preflight = {
            "content_sha256": "c" * 64,
            "review": {}, "inputs": {}, "implementation": {},
            "provider_contract": dict(contract.PROVIDER_PROTOCOL),
            "runtime_environment": contract.runtime_environment(),
            "required_checks": {}, "summary": {}, "scope_limits": [],
        }
        endpoint = "https://example.test/v1"
        with tempfile.TemporaryDirectory() as directory:
            preflight_path = Path(directory) / "preflight.json"
            preflight_path.write_text("{}", encoding="utf-8")
            with mock.patch.object(
                pil_v4_authorize, "_load_verified_preflight", return_value=preflight,
            ):
                ready = pil_v4_authorize.build_formal_readiness(
                    preflight_path, pil_v4_authorize.PAID_CONFIRMATION, endpoint,
                )
        self.assertEqual(ready["provider_contract"], contract.PROVIDER_PROTOCOL)
        self.assertEqual(ready["runtime_environment"], contract.runtime_environment())
        self.assertEqual(
            ready["authorization"]["api_base_sha256"],
            hashlib.sha256(endpoint.encode("utf-8")).hexdigest(),
        )

    def test_runner_rejects_changed_provider_or_endpoint_before_calls(self) -> None:
        endpoint = "https://example.test/v1"
        readiness = {
            "provider_contract": dict(contract.PROVIDER_PROTOCOL),
            "authorization": {
                "api_base_sha256": hashlib.sha256(endpoint.encode("utf-8")).hexdigest(),
            },
        }
        client = SimpleNamespace(
            runtime_metadata=dict(contract.PROVIDER_PROTOCOL),
            config=SimpleNamespace(llm_api_url=endpoint),
        )
        pil_v4_run._assert_provider_identity(client, readiness)
        client.runtime_metadata["reasoning_effort"] = "high"
        with self.assertRaises(ValueError):
            pil_v4_run._assert_provider_identity(client, readiness)

    def test_ready_schedule_is_exactly_720_unique_units(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            readiness = self.make_ready(Path(directory))
            schedule = pil_v4_schedule.build_schedule(readiness)
            self.assertEqual(schedule["unit_count"], 720)
            self.assertEqual(len({unit["unit_id"] for unit in schedule["units"]}), 720)
            self.assertEqual(
                {unit["seed"] for unit in schedule["units"]},
                {104729, 130363, 155921},
            )
            pil_v4_schedule.verify_schedule(schedule, readiness)

    def test_ledger_refuses_duplicate_and_reloads_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            readiness = self.make_ready(root)
            schedule = pil_v4_schedule.build_schedule(readiness)
            ledger_path = root / "ledger.jsonl"
            ledger = pil_v4_schedule.RunLedger(ledger_path, schedule, provenance={"model": "fixture"})
            unit = schedule["units"][0]
            ledger.record(unit, {"fixture": True})
            with self.assertRaises(pil_v4_schedule.LedgerIntegrityError):
                ledger.record(unit, {"fixture": True})
            loaded = pil_v4_schedule.RunLedger(ledger_path, schedule, provenance={"model": "fixture"})
            self.assertEqual(loaded.line_count, 1)
            self.assertEqual(len(loaded.pending(schedule)), 719)

    def test_attempt_journal_is_verified_on_reload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            readiness = self.make_ready(root)
            schedule = pil_v4_schedule.build_schedule(readiness)
            ledger_path = root / "ledger.jsonl"
            ledger = pil_v4_schedule.RunLedger(ledger_path, schedule)
            ledger.record_attempt(schedule["units"][0], RuntimeError("fixture outage"))
            loaded = pil_v4_schedule.RunLedger(ledger_path, schedule)
            self.assertEqual(loaded.attempt_count, 1)
            text = loaded.attempt_path.read_text(encoding="utf-8").replace("fixture outage", "edited outage")
            loaded.attempt_path.write_text(text, encoding="utf-8")
            with self.assertRaises(pil_v4_schedule.LedgerIntegrityError):
                pil_v4_schedule.RunLedger(ledger_path, schedule)

    def test_manifest_accounts_for_failed_attempt_tokens_and_requests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            readiness = self.make_ready(root)
            schedule = pil_v4_schedule.build_schedule(readiness)
            ledger = pil_v4_schedule.RunLedger(root / "ledger.jsonl", schedule)
            first, failed = schedule["units"][:2]
            ledger.record(first, {
                "logical_request_count": 1,
                "transport_request_count": 2,
                "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            })
            error = RuntimeError("fixture outage")
            error.logical_requests_observed = 2
            error.completed_stages = [{
                "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5},
                "transport_attempts": [{"transport_attempt": 1}],
            }]
            error.usage = {"input_tokens": 7, "output_tokens": 1, "total_tokens": 8}
            error.transport_attempts = [
                {"transport_attempt": 1}, {"transport_attempt": 2},
            ]
            ledger.record_attempt(failed, error)
            manifest = pil_v4_run._manifest(
                schedule, ledger, readiness_path=readiness, output=root / "run.json",
            )
            self.assertEqual(manifest["request_accounting"]["logical_requests_observed_total"], 3)
            self.assertEqual(manifest["request_accounting"]["transport_requests_observed_total"], 5)
            self.assertEqual(
                manifest["token_accounting"]["observed_total"],
                {"input_tokens": 20, "output_tokens": 8, "total_tokens": 28},
            )
            self.assertEqual(manifest["unresolved_infrastructure_failed_units"], [failed["unit_id"]])


class RescoreTests(unittest.TestCase):
    def test_cluster_bootstrap_keeps_the_case_weighted_estimand(self) -> None:
        result = pil_v4_rescore._bootstrap_difference(
            [1.0, 1.0, -1.0], cluster_ids=["large", "large", "small"],
        )
        self.assertAlmostEqual(result["estimate"], 1.0 / 3.0)
        self.assertEqual(result["clusters"], 2)

    def test_released_delivery_violation_counts_as_error_release(self) -> None:
        decision = valid_decision(provision="Art.24(1)", forum_type="general")
        entry = {
            "case_id": 1,
            "row": {
                "unit_id": "1|p2|1", "id": 1, "mode": "p2", "replicate": 1,
                "final_decision": decision, "retrieved_evidence": ["BRUSSELS_I_BIS:Art.24(1)"],
                "schema_status": "PASS", "system_release": True,
                "repair": {"attempted": False}, "external_call_count": 1,
                "usage": {"total_tokens": 15},
            },
        }
        gold = {
            "id": 1, "cluster_id": "CL-001",
            "conclusion": "Court_of_X_has_jurisdiction",
            "forum_type": "exclusive",
            "accepted_conclusions": ["Court_of_X_has_jurisdiction"],
            "accepted_forum_types": ["exclusive"],
            "required_evidence": ["BRUSSELS_I_BIS:Art.24(1)"],
        }
        scored = pil_v4_rescore.score_row(entry, gold, contract.load_schema(), contract.load_rules())
        self.assertTrue(scored["error_release"])
        self.assertTrue(scored["invalid_artifact_release"])
        self.assertFalse(scored["endpoint_success"])


if __name__ == "__main__":
    unittest.main()
