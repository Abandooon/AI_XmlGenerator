from __future__ import annotations

import copy
import unittest

from controlled_repair_v16 import (
    EXPECTED_CORE_DENOMINATORS,
    build_mutation_schedule,
    load_requirements,
    verify_mutation_schedule,
)


class ControlledRepairV16DesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.requirements = load_requirements()
        cls.schedule = build_mutation_schedule(cls.requirements)

    def test_design_is_20_by_5_with_separate_85_and_15_layers(self):
        self.assertEqual(20, self.schedule["case_count"])
        self.assertEqual(100, self.schedule["design_cell_count"])
        self.assertEqual(100, self.schedule["scheduled_task_count"])
        self.assertEqual(85, self.schedule["core_fixed_operator_task_count"])
        self.assertEqual(15, self.schedule["substitution_task_count"])
        self.assertEqual(100, len(self.schedule["applicability_ledger"]))
        self.assertEqual(100, len(self.schedule["tasks"]))

    def test_core_denominators_exclude_but_ledger_retains_not_applicable(self):
        self.assertEqual(
            EXPECTED_CORE_DENOMINATORS,
            self.schedule["core_repair_rate_denominators"],
        )
        self.assertEqual(
            {
                "empty_init_value": 3,
                "wrong_init_value": 3,
                "missing_event_behavior_path": 6,
                "missing_required_comspec": 3,
                "wrong_xsd_order": 0,
            },
            self.schedule["not_applicable_counts"],
        )
        self.assertEqual(
            15,
            sum(
                row["applicability"] == "NOT_APPLICABLE"
                for row in self.schedule["applicability_ledger"]
            ),
        )

    def test_every_not_applicable_cell_has_a_predeclared_actual_task(self):
        substituted = [
            task
            for task in self.schedule["tasks"]
            if task["analysis_layer"] == "substitution"
        ]
        self.assertEqual(15, len(substituted))
        self.assertTrue(
            all(task["effective_mutation"] != task["base_operator"] for task in substituted)
        )
        self.assertEqual(100, len({task["task_id"] for task in self.schedule["tasks"]}))
        self.assertEqual(
            {
                "empty_provided_interface_ref",
                "wrong_provided_interface_ref",
                "missing_provided_port",
                "missing_component_short_name",
                "missing_required_interface_ref",
            },
            {task["effective_mutation"] for task in substituted},
        )

    def test_schedule_is_deterministic_and_tamper_evident(self):
        self.assertEqual(self.schedule, build_mutation_schedule(self.requirements))
        self.assertIs(self.schedule, verify_mutation_schedule(self.schedule, self.requirements))
        tampered = copy.deepcopy(self.schedule)
        tampered["tasks"][0]["effective_mutation"] = "selected_from_a_run"
        with self.assertRaisesRegex(ValueError, "differs from requirements"):
            verify_mutation_schedule(tampered, self.requirements)


if __name__ == "__main__":
    unittest.main()
