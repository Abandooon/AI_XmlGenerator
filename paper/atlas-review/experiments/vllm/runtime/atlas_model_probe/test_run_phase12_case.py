from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from experiment_freeze import ExperimentFreezeError
from run_phase12_case import (
    _case_run_definition,
    _load_runtime_environment,
    _preflight_formal_neo4j,
    _requirement,
    main,
)
from run_asw_v3_experiment import (
    build_heldout_schedule,
    build_schedule,
    canonical_sha256,
    verify_schedule,
)


class Phase12RunnerTests(unittest.TestCase):
    @staticmethod
    def frozen_identity():
        return {
            "manifest_path": "offline-test-freeze.json",
            "manifest_file_sha256": "1" * 64,
            "manifest_sha256": "2" * 64,
            "experiment_contract_sha256": "3" * 64,
            "neo4j_context_sha256": "4" * 64,
        }

    def test_formal_contract_is_luna_only_and_provider_compatible(self):
        contract = json.loads(
            (Path(__file__).resolve().parent / "FORMAL_EXPERIMENT_CONTRACT.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(["gpt-5.6-luna"], contract["models"])
        self.assertFalse(contract["study_design"]["cross_model_comparison"])
        self.assertEqual(
            {"round1": 1.0, "interface": 1.0, "round2": 1.0},
            contract["generation"]["temperature"],
        )
        self.assertEqual(1.0, contract["repair_experiment"]["temperature"])
        self.assertEqual("low", contract["generation"]["reasoning_effort"])
        self.assertFalse(contract["generation"]["stream_responses"])
        self.assertEqual(
            1, contract["generation"]["provider_max_attempts_per_call"]
        )
        registration = contract["generation"]["provider_registration"]
        self.assertEqual("gpt-5.6-luna", registration["requested_model"])
        self.assertEqual(180.0, registration["request_timeout_seconds"])
        self.assertEqual(1, registration["max_attempts_per_call"])
        self.assertEqual(64, len(registration["provider_endpoint_sha256"]))
        self.assertEqual(
            "direct_no_environment_proxy",
            registration["transport_route_policy"],
        )
        self.assertEqual(
            registration["transport_route_policy"],
            contract["generation"]["transport_route_policy"],
        )
        self.assertEqual(
            ["full_experiment_root", "generation_root"],
            contract["generation"]["orchestration"][
                "operator_stop_sentinel_locations"
            ],
        )

    def test_runtime_environment_accepts_existing_api_key_alias(self):
        with patch.dict(os.environ, {"API_KEY": "sentinel"}, clear=True), patch(
            "run_phase12_case.load_dotenv"
        ):
            _load_runtime_environment()
            self.assertEqual("sentinel", os.environ["LLM_API_KEY"])

    def test_case_index_repetition_and_seed_come_from_manifest(self):
        definition = _case_run_definition("ASW-STD-07", 2)
        self.assertEqual(13, definition["case_index"])
        self.assertEqual(130363, definition["seed"])
        self.assertEqual("standard", definition["case"]["tier"])

    def test_heldout_runtime_is_the_exact_reviewed_source_not_a_second_fixture(self):
        definition = _case_run_definition("ASW-HO-FULL-02", 3, "heldout")
        self.assertEqual("heldout", definition["cohort"])
        self.assertEqual(155921, definition["seed"])
        self.assertEqual("EXTENSION", definition["case"]["structural_role"])
        self.assertEqual(64, len(definition["case_sha256"]))
        requirement = _requirement("ASW-HO-FULL-02", 155921, "heldout")
        self.assertEqual(6, len(requirement["interface_data_type_bindings"]))
        self.assertEqual(
            {"/DataTypes/Impl_Float32", "/DataTypes/Impl_UInt8"},
            {
                item["type_ref"]
                for item in requirement["interface_data_type_bindings"]
            },
        )
        self.assertIn("TYPE-TREF /DataTypes/Impl_Float32", requirement["description"])
        self.assertIn(
            "/DataTypes/Impl_Float32",
            {item["scope_path"] for item in requirement["declared_capability_scopes"]},
        )

    def test_heldout_schedule_is_separate_balanced_and_case_level(self):
        with patch(
            "run_asw_v3_experiment.verify_freeze_manifest",
            return_value=self.frozen_identity(),
        ):
            schedule = build_heldout_schedule(["gpt-5.6-luna"], "off")
        self.assertEqual(12, schedule["case_count"])
        self.assertEqual(36, schedule["pipeline_run_count"])
        self.assertEqual("case", schedule["unit_of_analysis"])
        self.assertEqual(
            {"REPLICATION": 6, "EXTENSION": 6},
            schedule["structural_role_case_counts"],
        )
        self.assertTrue(all(run["cohort"] == "heldout" for run in schedule["runs"]))
        self.assertEqual(36, len({run["run_id"] for run in schedule["runs"]}))

    def test_standard_case_declares_exact_artifact_context(self):
        requirement = _requirement("ASW-STD-07", 104729)
        self.assertEqual(104729, requirement["generation_seed"])
        self.assertEqual("complete", requirement["intent_scope"])
        self.assertEqual(
            ["TPS_SWCT_01519", "constr_1100"],
            requirement["declared_constraint_ids"],
        )
        obligations = requirement["generation_value_obligations"]
        contracts = requirement["generation_requirement_contracts"]
        self.assertTrue(all(item["requirement_id"] for item in obligations))
        self.assertEqual(
            len(obligations),
            sum(item["expected_obligation_count"] for item in contracts),
        )
        obligation = next(
            item
            for item in obligations
            if "authoritative_subtree_path" in item
        )
        self.assertEqual(
            "Rp_HCU01_TqCmd", obligation["anchors"][0]["short_name"]
        )
        self.assertEqual(0, obligation["value"])
        self.assertEqual("#TEXT", obligation["path"][-1])
        self.assertEqual("INIT-VALUE", obligation["authoritative_subtree_path"][-1])
        data_reference = next(
            item
            for item in obligations
            if item["path"][-2:] == ["DATA-ELEMENT-REF", "#TEXT"]
        )
        self.assertEqual(
            "/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_TqCmd",
            data_reference["value"],
        )
        self.assertTrue(
            all(
                scope["constraint_ids"] == requirement["declared_constraint_ids"]
                for scope in requirement["declared_capability_scopes"]
            )
        )

    def test_minimal_provided_only_case_does_not_claim_periodic_or_rport_intent(self):
        requirement = _requirement("ASW-MIN-01", 104729)
        self.assertEqual([], requirement["declared_constraint_ids"])
        self.assertEqual({}, requirement["declared_targets"])
        self.assertFalse(
            any(
                "authoritative_subtree_path" in item
                for item in requirement["generation_value_obligations"]
            )
        )
        self.assertEqual(2, len(requirement["generation_value_obligations"]))
        self.assertEqual(
            ["sender_receiver_communication"], requirement["declared_use_cases"]
        )

    def test_full_case_compiles_runnable_event_and_access_relationships(self):
        requirement = _requirement("ASW-FULL-06", 104729)
        obligations = requirement["generation_value_obligations"]
        contracts = {
            item["requirement_id"]: item
            for item in requirement["generation_requirement_contracts"]
        }
        self.assertEqual(61, len(obligations))
        self.assertEqual(5, len(contracts))
        self.assertEqual(
            1,
            contracts["asw.component.internal_behavior"]["expected_obligation_count"],
        )
        self.assertEqual(
            24,
            contracts["asw.component.variable_accesses"]["expected_obligation_count"],
        )
        behavior_identity = next(
            item
            for item in obligations
            if item["requirement_id"] == "asw.component.internal_behavior"
        )
        self.assertEqual("IB_Com_Full_ThreeRates", behavior_identity["value"])
        periods = [
            item
            for item in obligations
            if item["path"][-2:] == ["PERIOD", "#TEXT"]
        ]
        self.assertEqual([0.005, 0.01, 0.02], [item["value"] for item in periods])
        self.assertEqual(
            ["TE_Com_Torque", "TE_Com_Shift", "TE_Com_Poweroff"],
            [item["anchors"][0]["short_name"] for item in periods],
        )
        access_port_refs = [
            item
            for item in obligations
            if item["path"][-2:] == ["PORT-PROTOTYPE-REF", "#TEXT"]
        ]
        self.assertEqual(6, len(access_port_refs))
        self.assertTrue(all(len(item["anchors"]) == 2 for item in access_port_refs))
        torque_read = next(
            item
            for item in access_port_refs
            if item["value"].endswith("/Rp_HCU01_TqCmd")
        )
        self.assertEqual(
            ["RE_Com_Torque", "VA_Com_Torque_Read_HCU01_TqCmd"],
            [anchor["short_name"] for anchor in torque_read["anchors"]],
        )

    def test_luna_qualification_schedule_has_60_unique_pipeline_runs(self):
        with patch(
            "run_asw_v3_experiment.verify_freeze_manifest",
            return_value=self.frozen_identity(),
        ):
            schedule = build_schedule(["gpt-5.6-luna"], "off")
        self.assertEqual(60, schedule["pipeline_run_count"])
        self.assertEqual(60, len({item["run_id"] for item in schedule["runs"]}))
        self.assertEqual(
            {104729, 130363, 155921},
            {item["seed"] for item in schedule["runs"]},
        )
        self.assertTrue(schedule["freeze_manifest_sha256"])
        self.assertTrue(schedule["experiment_contract_sha256"])
        self.assertTrue(all(item["case_sha256"] for item in schedule["runs"]))

    def test_formal_schedule_rejects_subset_or_repair_enabled(self):
        with patch(
            "run_asw_v3_experiment.verify_freeze_manifest",
            return_value=self.frozen_identity(),
        ):
            with self.assertRaisesRegex(ValueError, "models must exactly match"):
                build_schedule([], "off")
            with self.assertRaisesRegex(ValueError, "repair mode"):
                build_schedule(["gpt-5.6-luna"], "on")

    def test_formal_schedule_rejects_rehashed_semantic_mutation(self):
        with patch(
            "run_asw_v3_experiment.verify_freeze_manifest",
            return_value=self.frozen_identity(),
        ):
            schedule = build_schedule(["gpt-5.6-luna"], "off")
            schedule["runs"][0]["seed"] = 1
            unsigned = {
                key: value for key, value in schedule.items()
                if key != "content_sha256"
            }
            schedule["content_sha256"] = canonical_sha256(unsigned)
            with self.assertRaisesRegex(ValueError, "differs from frozen"):
                verify_schedule(schedule)

    def test_formal_freeze_failure_precedes_credential_loading(self):
        arguments = [
            "run_phase12_case.py",
            "--model", "gpt-5.6-luna",
            "--case-id", "ASW-MIN-01",
            "--freeze-manifest", "missing.json",
            "--expected-freeze-sha256", "a" * 64,
            "--expected-schedule-sha256", "b" * 64,
        ]
        with patch("sys.argv", arguments), patch(
            "run_phase12_case.verify_freeze_manifest",
            side_effect=ExperimentFreezeError("frozen input mismatch"),
        ), patch("run_phase12_case._load_runtime_environment") as load_environment:
            with self.assertRaisesRegex(ExperimentFreezeError, "frozen input mismatch"):
                main()
        load_environment.assert_not_called()

    def test_formal_neo4j_preflight_rejects_missing_credentials(self):
        class KnowledgeGraph:
            neo4j_password = ""

        class Config:
            knowledge_graph = KnowledgeGraph()

        with self.assertRaisesRegex(RuntimeError, "requires configured credentials"):
            _preflight_formal_neo4j(Config(), "a" * 64, 1085, {})


if __name__ == "__main__":
    unittest.main()
