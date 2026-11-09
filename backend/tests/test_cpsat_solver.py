import unittest
from unittest.mock import patch

from ortools.sat.python import cp_model

from backend.app import solver_engine
from backend.app.cpsat_solver import solve_maintenance_schedule_cpsat


def order(
    work_id,
    *,
    duration=1.0,
    section_id="S1",
    track_line="UP_LINE",
    department="ENGINEERING",
    heavy_equipment=False,
    urgency=2,
    co_location_allowed=True,
):
    return {
        "work_id": work_id,
        "department": department,
        "section_id": section_id,
        "track_line": track_line,
        "heavy_equipment": heavy_equipment,
        "duration_hrs": duration,
        "urgency": urgency,
        "co_location_allowed": co_location_allowed,
    }


def config(horizon=2, **updates):
    values = {
        "section_ids": ["S1"],
        "time_horizon_hrs": horizon,
        "slot_duration_hrs": 0.5,
        "enable_ac3_pruning": True,
        "enable_simulated_annealing": False,
        "cpsat_time_limit_seconds": 5.0,
        "random_seed": 13,
    }
    values.update(updates)
    return values


class CpsatSolverTests(unittest.TestCase):
    def test_empty_input_is_no_work_without_claiming_optimality(self):
        result = solve_maintenance_schedule_cpsat([], [], config())

        self.assertEqual(result["status"], "no_work")
        self.assertEqual(result["solver_outcome"], "no_work")
        self.assertEqual(result["schedule"], [])
        self.assertEqual(result["unscheduled_work_ids"], [])
        self.assertFalse(result["optimality_proven"])
        self.assertEqual(result["termination_reason"], "NO_WORK")

    def test_simple_feasible_schedule_reports_solution_and_proof(self):
        result = solve_maintenance_schedule_cpsat([order("W-1")], [], config())

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["solver_outcome"], "success")
        self.assertEqual([item["work_id"] for item in result["schedule"]], ["W-1"])
        self.assertEqual(result["unscheduled_work_ids"], [])
        self.assertTrue(result["feasible_solution_found"])
        self.assertTrue(result["optimality_proven"])

    def test_proven_infeasibility_with_no_schedulable_orders(self):
        train = {
            "train_no": "T-1",
            "section_id": "S1",
            "track_line": "UP_LINE",
            "start_time_hr": 0.0,
            "end_time_hr": 1.0,
        }
        result = solve_maintenance_schedule_cpsat(
            [order("W-1")], [train], config(horizon=1)
        )

        self.assertEqual(result["status"], "unschedulable")
        self.assertEqual(result["solver_outcome"], "unschedulable")
        self.assertEqual(result["schedule"], [])
        self.assertEqual(result["unscheduled_work_ids"], ["W-1"])
        self.assertTrue(result["complete_schedule_proven_infeasible"])

    def test_train_occupancy_conflict_is_not_scheduled(self):
        train = {
            "train_no": "T-1",
            "section_id": "S1",
            "track_line": "UP_LINE",
            "start_time_hr": 0.0,
            "end_time_hr": 1.0,
        }
        result = solve_maintenance_schedule_cpsat(
            [order("W-1")], [train], config(horizon=2)
        )

        assignment = result["schedule"][0]
        self.assertGreaterEqual(assignment["start_time_hr"], 1.0)
        self.assertEqual(result["solver_outcome"], "success")

    def test_same_track_department_conflicts_match_baseline_feasibility(self):
        orders = [order("W-1"), order("W-2")]
        cfg = config(horizon=1)
        experimental = solve_maintenance_schedule_cpsat(orders, [], cfg)
        baseline = solver_engine.solve_maintenance_schedule(orders, [], cfg)

        self.assertEqual(experimental["status"], "partial")
        self.assertTrue(experimental["complete_schedule_proven_infeasible"])
        self.assertEqual(
            len(experimental["schedule"]), len(baseline["schedule"])
        )
        self.assertEqual(len(experimental["unscheduled_work_ids"]), 1)

    def test_adjacent_track_heavy_equipment_conflicts_with_train(self):
        train = {
            "train_no": "T-1",
            "section_id": "S1",
            "track_line": "DOWN_LINE",
            "start_time_hr": 0.0,
            "end_time_hr": 1.0,
        }
        result = solve_maintenance_schedule_cpsat(
            [order("W-1", heavy_equipment=True)],
            [train],
            config(horizon=1),
        )

        self.assertEqual(result["status"], "unschedulable")
        self.assertEqual(result["unscheduled_work_ids"], ["W-1"])

    def test_partial_schedule_accounts_for_every_work_order(self):
        orders = [order(f"W-{index}") for index in range(3)]
        result = solve_maintenance_schedule_cpsat(
            orders, [], config(horizon=2)
        )

        scheduled = [item["work_id"] for item in result["schedule"]]
        unscheduled = result["unscheduled_work_ids"]
        self.assertEqual(result["status"], "partial")
        self.assertEqual(len(scheduled), 2)
        self.assertEqual(len(unscheduled), 1)
        self.assertEqual(set(scheduled) | set(unscheduled), {item["work_id"] for item in orders})
        self.assertFalse(set(scheduled) & set(unscheduled))
        self.assertEqual(len(scheduled + unscheduled), len(set(scheduled + unscheduled)))

    def test_colocation_exception_matches_baseline_and_objective(self):
        orders = [
            order("W-ENG", department="ENGINEERING"),
            order("W-SIG", department="SIGNALLING"),
        ]
        result = solve_maintenance_schedule_cpsat(orders, [], config(horizon=1))
        normalized_orders, normalized_trains, *_ = solver_engine._normalise_inputs(
            orders, [], config(horizon=1)
        )
        indexes = {
            item["work_id"]: index for index, item in enumerate(normalized_orders)
        }
        assignment = {
            indexes[item["work_id"]]: item["start_time_hr"]
            for item in result["schedule"]
        }

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["schedule"][0]["start_time_hr"], result["schedule"][1]["start_time_hr"])
        self.assertEqual(
            result["metrics"]["objective_score"],
            solver_engine._schedule_objective(
                assignment, normalized_orders, normalized_trains, config(horizon=1)
            ),
        )

    def test_time_limit_without_incumbent_is_not_reported_as_infeasible(self):
        class TimedOutSolver:
            def __init__(self):
                self.parameters = type("Parameters", (), {})()

            def Solve(self, _model):
                return cp_model.UNKNOWN

            @staticmethod
            def StatusName(_status):
                return "UNKNOWN"

            @staticmethod
            def NumBranches():
                return 0

            @staticmethod
            def NumConflicts():
                return 0

            @staticmethod
            def WallTime():
                return 0.0

        with patch.object(cp_model, "CpSolver", TimedOutSolver):
            result = solve_maintenance_schedule_cpsat(
                [order("W-1")], [], config()
            )

        self.assertEqual(result["status"], "search_limit_reached")
        self.assertEqual(result["solver_outcome"], "search_limit_reached")
        self.assertEqual(result["unscheduled_work_ids"], ["W-1"])
        self.assertFalse(result["complete_schedule_proven_infeasible"])
        self.assertFalse(result["optimality_proven"])

    def test_feasible_incumbent_is_not_mislabeled_as_optimal(self):
        class FeasibleSolver:
            def __init__(self):
                self.parameters = type("Parameters", (), {})()

            def Solve(self, model):
                self.values = {
                    variable.name: int(
                        variable.name in {"scheduled_0", "start_0_0"}
                    )
                    for variable in model.Proto().variables
                }
                return cp_model.FEASIBLE

            def BooleanValue(self, variable):
                return bool(self.values[variable.Name()])

            @staticmethod
            def ObjectiveValue():
                return 0.0

            @staticmethod
            def StatusName(_status):
                return "FEASIBLE"

            @staticmethod
            def NumBranches():
                return 0

            @staticmethod
            def NumConflicts():
                return 0

            @staticmethod
            def WallTime():
                return 0.0

        with patch.object(cp_model, "CpSolver", FeasibleSolver):
            result = solve_maintenance_schedule_cpsat(
                [order("W-1")], [], config(horizon=1)
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["solver_outcome"], "success")
        self.assertTrue(result["feasible_solution_found"])
        self.assertFalse(result["optimality_proven"])
        self.assertEqual(result["cp_sat_status"], "FEASIBLE")


if __name__ == "__main__":
    unittest.main()
