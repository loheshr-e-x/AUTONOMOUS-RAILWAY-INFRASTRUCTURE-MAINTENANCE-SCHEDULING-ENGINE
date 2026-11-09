import unittest

from backend.app.schemas.contracts import MaintenanceWorkOrder, UrgencyLevel
from backend.benchmarks.runner import (
    build_instances,
    instance_digest,
    run_once,
    summarize_rows,
)
from backend.benchmarks.compare import summarize_rows as summarize_comparison_rows


def order(work_id: str) -> MaintenanceWorkOrder:
    return MaintenanceWorkOrder(
        work_id=work_id,
        department="ENGINEERING",
        section_id="S1",
        track_line="UP_LINE",
        defect_type="benchmark fixture",
        duration_hrs=1.0,
        urgency=UrgencyLevel.MEDIUM,
    )


def config(horizon: int = 2, **updates):
    values = {
        "section_ids": ["S1"],
        "time_horizon_hrs": horizon,
        "enable_ac3_pruning": True,
        "enable_simulated_annealing": False,
    }
    values.update(updates)
    return values


class BenchmarkRunnerTests(unittest.TestCase):
    def test_scenario_generation_is_reproducible(self):
        first_orders, first_trains, first_config = build_instances(seed=31)
        next_orders, next_trains, next_config = build_instances(seed=31)

        self.assertEqual(
            instance_digest(first_orders, first_trains, first_config),
            instance_digest(next_orders, next_trains, next_config),
        )
        self.assertEqual(len(first_orders), 90)
        self.assertEqual(len({item.work_id for item in first_orders}), 90)

    def test_run_collects_solver_metrics_and_exact_accounting(self):
        orders = [order("W-1")]
        trains = []
        run = run_once(
            orders, trains, config(), 1, 1, 17,
            instance_digest(orders, trains, config()),
        )

        self.assertEqual(run["total_work_orders"], 1)
        self.assertEqual(run["scheduled_work_orders"], 1)
        self.assertEqual(run["unscheduled_work_orders"], 0)
        self.assertEqual(run["solver_outcome"], "success")
        self.assertGreaterEqual(run["backtracking_nodes"], 1)
        self.assertGreaterEqual(run["candidate_domain_size_before_filtering"], 1)
        self.assertIsNotNone(run["candidate_domain_size_after_ac3"])
        self.assertIsNotNone(run["ac3_pruned_candidates"])
        self.assertIsNotNone(run["objective_score"])
        self.assertFalse(run["cold_start"])

    def test_aggregate_statistics_use_population_standard_deviation(self):
        rows = [
            {"scenario_size": 10, "execution_time_sec": 1.0,
             "solver_outcome": "success", "scheduled_work_orders": 10,
             "total_work_orders": 10, "search_limit_reached": False},
            {"scenario_size": 10, "execution_time_sec": 3.0,
             "solver_outcome": "partial", "scheduled_work_orders": 5,
             "total_work_orders": 10, "search_limit_reached": True},
        ]

        summary = summarize_rows(rows)[0]

        self.assertEqual(summary["execution_time_mean_sec"], 2.0)
        self.assertEqual(summary["execution_time_median_sec"], 2.0)
        self.assertEqual(summary["execution_time_stdev_sec"], 1.0)
        self.assertEqual(summary["feasibility_rate"], 0.5)
        self.assertEqual(summary["mean_scheduling_completeness"], 0.75)
        self.assertEqual(summary["search_limit_runs"], 1)

    def test_no_work_outcome_is_measured_without_fabricated_domain_metrics(self):
        run = run_once([], [], config(), 0, 1, 17, "empty")

        self.assertEqual(run["solver_outcome"], "no_work")
        self.assertEqual(run["total_work_orders"], 0)
        self.assertEqual(run["scheduled_work_orders"], 0)
        self.assertEqual(run["unscheduled_work_orders"], 0)
        self.assertIsNone(run["objective_score"])
        self.assertEqual(run["candidate_domain_size_before_filtering"], 0)

    def test_partial_and_unschedulable_results_keep_ids_accounted(self):
        orders = [order(f"W-{index}") for index in range(3)]
        cfg = config(horizon=2, enable_ac3_pruning=False)
        run = run_once(orders, [], cfg, 3, 1, 17, "partial")

        self.assertEqual(run["solver_outcome"], "unschedulable")
        self.assertEqual(run["scheduled_work_orders"], 2)
        self.assertEqual(run["unscheduled_work_orders"], 1)

        impossible = [order("W-IMPOSSIBLE")]
        occupied = [{
            "train_no": "T-1", "section_id": "S1", "track_line": "UP_LINE",
            "start_time_hr": 0.0, "end_time_hr": 2.0,
        }]
        failed = run_once(
            impossible, occupied, config(horizon=2), 1, 1, 17, "impossible"
        )
        self.assertEqual(failed["solver_outcome"], "unschedulable")
        self.assertEqual(failed["unscheduled_work_orders"], 1)

    def test_search_limit_outcome_is_preserved_in_benchmark_metrics(self):
        orders = [order(f"W-{index}") for index in range(3)]
        run = run_once(
            orders,
            [],
            config(horizon=2, enable_ac3_pruning=False, max_search_nodes=1),
            3,
            1,
            17,
            "limited",
        )

        self.assertEqual(run["solver_outcome"], "search_limit_reached")
        self.assertTrue(run["search_limit_reached"])
        self.assertTrue(run["backtracking_limit_reached"])
        self.assertEqual(
            run["scheduled_work_orders"] + run["unscheduled_work_orders"], 3
        )

    def test_comparison_summary_reports_feasibility_and_proof_rate(self):
        rows = [
            {
                "solver": "baseline",
                "scenario_size": 10,
                "execution_time_sec": 2.0,
                "total_work_orders": 10,
                "scheduled_work_orders": 10,
                "complete_schedule_found": True,
                "optimality_proven": False,
                "objective_score": 4.0,
                "solver_outcome": "success",
                "termination_reason": "SUCCESS",
                "cp_sat_status": "",
            },
            {
                "solver": "cp_sat",
                "scenario_size": 10,
                "execution_time_sec": 1.0,
                "total_work_orders": 10,
                "scheduled_work_orders": 8,
                "complete_schedule_found": False,
                "optimality_proven": True,
                "objective_score": 3.0,
                "solver_outcome": "partial",
                "termination_reason": "OPTIMAL",
                "cp_sat_status": "OPTIMAL",
            },
        ]

        summary = summarize_comparison_rows(rows)

        baseline = next(row for row in summary if row["solver"] == "baseline")
        cpsat = next(row for row in summary if row["solver"] == "cp_sat")
        self.assertEqual(baseline["feasibility_rate"], 1.0)
        self.assertEqual(baseline["optimality_proof_rate"], 0.0)
        self.assertEqual(cpsat["feasibility_rate"], 0.0)
        self.assertEqual(cpsat["mean_scheduling_completeness"], 0.8)
        self.assertEqual(cpsat["optimality_proof_rate"], 1.0)

    def test_astar_limit_is_reported_even_when_a_complete_schedule_exists(self):
        orders = [order("W-1")]
        run = run_once(
            orders,
            [],
            config(horizon=1, max_search_nodes=1),
            1,
            1,
            17,
            "astar-limited",
        )

        self.assertEqual(run["solver_outcome"], "success")
        self.assertTrue(run["astar_limit_reached"])
        self.assertTrue(run["search_limit_reached"])
        self.assertFalse(run["backtracking_limit_reached"])


if __name__ == "__main__":
    unittest.main()
