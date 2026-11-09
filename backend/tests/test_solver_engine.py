import unittest

from backend.app.solver_engine import (
    _backtracking_search,
    solve_maintenance_schedule,
)


def order(
    work_id,
    section_id="S1",
    track_line="UP_LINE",
    department="ENGINEERING",
    heavy_equipment=False,
):
    return {
        "work_id": work_id,
        "department": department,
        "section_id": section_id,
        "track_line": track_line,
        "heavy_equipment": heavy_equipment,
        "duration_hrs": 1.0,
        "urgency": 2,
        "co_location_allowed": True,
    }


def config(sections, **updates):
    values = {
        "section_ids": sections,
        "time_horizon_hrs": 1,
        "enable_ac3_pruning": True,
        "enable_simulated_annealing": False,
    }
    values.update(updates)
    return values


class SolverEngineTests(unittest.TestCase):
    def test_same_line_work_in_different_sections_can_overlap(self):
        result = solve_maintenance_schedule(
            [order("W-1", section_id="S1"), order("W-2", section_id="S2")],
            [],
            config(["S1", "S2"]),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            {item["work_id"]: item["start_time_hr"] for item in result["schedule"]},
            {"W-1": 0.0, "W-2": 0.0},
        )

    def test_heavy_equipment_is_filtered_against_adjacent_trains_both_directions(self):
        cases = (
            ("UP_LINE", "DOWN_LINE"),
            ("DOWN_LINE", "UP_LINE"),
        )
        for work_line, train_line in cases:
            with self.subTest(work_line=work_line):
                train = {
                    "train_no": "T-1",
                    "section_id": "S1",
                    "track_line": train_line,
                    "start_time_hr": 0.0,
                    "end_time_hr": 1.0,
                }
                result = solve_maintenance_schedule(
                    [order("W-1", track_line=work_line, heavy_equipment=True)],
                    [train],
                    config(["S1"]),
                )

                self.assertEqual(result["status"], "unschedulable")
                self.assertEqual(result["schedule"], [])

    def test_ac3_audit_does_not_claim_to_run_when_disabled(self):
        result = solve_maintenance_schedule(
            [order("W-1")],
            [],
            config(["S1"], enable_ac3_pruning=False),
        )

        ac3_entry = next(
            entry for entry in result["audit_trail"]
            if entry["rule_name"] == "AC3DomainPruning"
        )
        self.assertIsNone(ac3_entry["passed"])
        self.assertEqual(ac3_entry["predicate_evaluated"], "ac3_enabled")

    def test_ac3_audit_is_unevaluated_without_work_orders(self):
        result = solve_maintenance_schedule([], [], config([]))

        self.assertEqual(result["status"], "no_work")
        self.assertEqual(result["solver_outcome"], "no_work")
        self.assertEqual(result["schedule"], [])
        self.assertEqual(result["unscheduled_work_ids"], [])
        self.assertEqual(result["audit_trail"], [])
        self.assertEqual(result["metrics"]["scheduled_requests"], 0)
        self.assertEqual(result["metrics"]["total_requests"], 0)

    def test_backtracking_reports_proven_exhaustion(self):
        result = _backtracking_search(
            domains=[[]],
            orders=[{"work_id": "W-1", "urgency": 1}],
            trains=[],
            node_limit=10,
        )

        self.assertFalse(result.complete)
        self.assertTrue(result.exhausted)
        self.assertFalse(result.limit_reached)
        self.assertEqual(result.explored_nodes, 1)

    def test_backtracking_reports_node_limit_without_claiming_exhaustion(self):
        orders = [
            {"work_id": f"W-{index}", "urgency": 1, "duration": 1.0,
             "section_id": "S1", "track_line": "UP_LINE",
             "department": "ENGINEERING", "co_location_allowed": True}
            for index in range(3)
        ]
        result = _backtracking_search(
            domains=[[0.0, 0.5, 1.0] for _ in orders],
            orders=orders,
            trains=[],
            node_limit=1,
        )

        self.assertFalse(result.complete)
        self.assertFalse(result.exhausted)
        self.assertTrue(result.limit_reached)
        self.assertEqual(result.explored_nodes, 1)

    def test_exhausted_infeasible_work_order_is_unschedulable(self):
        train = {
            "train_no": "T-1",
            "section_id": "S1",
            "track_line": "UP_LINE",
            "start_time_hr": 0.0,
            "end_time_hr": 1.0,
        }
        result = solve_maintenance_schedule(
            [order("W-1")], [train], config(["S1"])
        )

        self.assertEqual(result["status"], "unschedulable")
        self.assertEqual(result["solver_outcome"], "unschedulable")
        self.assertEqual(result["unscheduled_work_ids"], ["W-1"])
        self.assertEqual(result["schedule"], [])

    def test_partial_greedy_fallback_lists_every_omitted_id(self):
        orders = [order(f"W-{index}") for index in range(3)]
        result = solve_maintenance_schedule(
            orders,
            [],
            config(
                ["S1"],
                time_horizon_hrs=2,
                enable_ac3_pruning=False,
                max_search_nodes=100,
            ),
        )
        scheduled = [item["work_id"] for item in result["schedule"]]
        unscheduled = result["unscheduled_work_ids"]

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["solver_outcome"], "unschedulable")
        self.assertEqual(len(scheduled), 2)
        self.assertEqual(len(unscheduled), 1)
        self.assertEqual(set(scheduled) | set(unscheduled), {o["work_id"] for o in orders})
        self.assertFalse(set(scheduled) & set(unscheduled))
        self.assertEqual(len(scheduled + unscheduled), len(set(scheduled + unscheduled)))

    def test_search_cutoff_is_not_reported_as_unschedulable(self):
        orders = [order(f"W-{index}") for index in range(3)]
        result = solve_maintenance_schedule(
            orders,
            [],
            config(
                ["S1"],
                time_horizon_hrs=2,
                enable_ac3_pruning=False,
                max_search_nodes=1,
            ),
        )

        self.assertEqual(result["status"], "search_limit_reached")
        self.assertEqual(result["solver_outcome"], "search_limit_reached")
        self.assertEqual(len(result["schedule"]), 2)
        self.assertEqual(len(result["unscheduled_work_ids"]), 1)

    def test_per_line_combination_preserves_work_order_accounting(self):
        orders = [
            order("W-UP", track_line="UP_LINE"),
            order("W-DOWN", track_line="DOWN_LINE"),
        ]
        result = solve_maintenance_schedule(
            orders, [], config(["S1"])
        )

        scheduled = [item["work_id"] for item in result["schedule"]]
        accounted = scheduled + result["unscheduled_work_ids"]
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["solver_outcome"], "success")
        self.assertEqual(set(accounted), {"W-UP", "W-DOWN"})
        self.assertEqual(len(accounted), len(set(accounted)))
        self.assertEqual(result["unscheduled_work_ids"], [])

    def test_ac3_audit_separates_train_filtering_from_ac3_pruning(self):
        train = {
            "train_no": "T-1",
            "section_id": "S1",
            "track_line": "UP_LINE",
            "start_time_hr": 0.0,
            "end_time_hr": 1.0,
        }
        result = solve_maintenance_schedule(
            [order("W-1")],
            [train],
            config(["S1"], time_horizon_hrs=2),
        )

        ac3_entry = next(
            entry for entry in result["audit_trail"]
            if entry["rule_name"] == "AC3DomainPruning"
        )
        self.assertTrue(ac3_entry["passed"])
        self.assertIn("AC-3 removed 0 of 1", ac3_entry["explanation"])
        self.assertEqual(result["metrics"]["search_space_pruned_pct"], 66.67)


if __name__ == "__main__":
    unittest.main()
