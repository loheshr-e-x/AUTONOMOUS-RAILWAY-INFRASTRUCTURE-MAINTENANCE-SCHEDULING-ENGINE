import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.benchmarks import task12_runner


class Task12BenchmarkTests(unittest.TestCase):
    def test_seeded_instances_are_deterministic_and_distinct_by_seed(self):
        first = task12_runner.build_seeded_instance(41, 5)
        repeat = task12_runner.build_seeded_instance(41, 5)
        other_seed = task12_runner.build_seeded_instance(42, 5)

        self.assertEqual(first[3], repeat[3])
        self.assertNotEqual(first[3], other_seed[3])
        self.assertEqual(len(first[0]), 5)
        with self.assertRaises(ValueError):
            task12_runner.build_seeded_instance(41, 91)

    def test_execution_order_alternates_and_both_solvers_share_digest(self):
        baseline_rows = []
        cp_rows = []

        def fake_baseline(*args, **kwargs):
            row = {
                "solver": "baseline",
                "workload_size": args[3],
                "repetition": args[4],
                "seed": args[5],
                "instance_id": f"n{args[3]}-r{args[4]}-s{args[5]}",
                "instance_sha256": args[6],
                "total_work_orders": 1,
                "execution_time_sec": 1.0,
                "execution_time_censored": False,
                "scheduled_work_orders": 1,
                "unscheduled_work_orders": 0,
                "schedule_completeness_pct": 100.0,
                "solver_outcome": "success",
                "termination_reason": "SUCCESS",
                "feasible_solution_found": True,
                "complete_schedule_found": True,
                "infeasibility_proven": False,
                "optimality_proven": False,
                "coverage_optimality_proven": False,
                "objective_score": 1.0,
                "time_limit_sec": None,
                "run_order": args[8],
            }
            baseline_rows.append(row)
            return row

        def fake_cp(*args, **kwargs):
            row = {
                "solver": "cp_sat",
                "workload_size": args[3],
                "repetition": args[4],
                "seed": args[5],
                "instance_id": f"n{args[3]}-r{args[4]}-s{args[5]}",
                "instance_sha256": args[6],
                "total_work_orders": 1,
                "execution_time_sec": 0.5,
                "execution_time_censored": False,
                "scheduled_work_orders": 1,
                "unscheduled_work_orders": 0,
                "schedule_completeness_pct": 100.0,
                "solver_outcome": "success",
                "termination_reason": "OPTIMAL",
                "feasible_solution_found": True,
                "complete_schedule_found": True,
                "infeasibility_proven": False,
                "optimality_proven": True,
                "coverage_optimality_proven": True,
                "objective_score": 1.0,
                "time_limit_sec": args[7],
                "run_order": args[8],
            }
            cp_rows.append(row)
            return row

        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(
                    task12_runner,
                    "run_baseline_bounded",
                    side_effect=fake_baseline,
                ),
                patch.object(task12_runner, "_run_cp_sat", side_effect=fake_cp),
                patch.object(
                    task12_runner, "_constraint_equivalence_rows", return_value=[]
                ),
                patch.object(
                    task12_runner, "_exhaustive_validation_rows", return_value=[]
                ),
                patch.object(task12_runner, "_write_charts_from_csv"),
                patch.object(task12_runner.cpsat_solver, "_load_cp_sat"),
            ):
                result = task12_runner.run_task12(
                    output_dir=Path(temp_dir) / "results",
                    repetitions=2,
                    base_seed=5,
                    sizes=(1,),
                    time_limits=(5.0, 10.0),
                )

        self.assertEqual([row["run_order"] for row in baseline_rows], [
            "baseline_then_cp_sat", "cp_sat_then_baseline"
        ])
        self.assertEqual(len(result["paired"]), 4)
        self.assertEqual(
            {row["instance_sha256"] for row in baseline_rows},
            {row["instance_sha256"] for row in cp_rows},
        )
        self.assertEqual({row["time_limit_sec"] for row in cp_rows}, {5.0, 10.0})

    def test_timeout_is_censored_and_not_counted_as_infeasible(self):
        rows = [
            {
                "solver": "baseline",
                "workload_size": 5,
                "time_limit_sec": None,
                "execution_time_sec": 3.0,
                "execution_time_censored": True,
                "solver_outcome": "timeout",
                "termination_reason": "TIMEOUT",
                "scheduled_work_orders": None,
                "total_work_orders": 5,
                "complete_schedule_found": None,
                "feasible_solution_found": None,
                "optimality_proven": False,
                "objective_score": None,
            },
            {
                "solver": "cp_sat",
                "workload_size": 5,
                "time_limit_sec": 5.0,
                "execution_time_sec": 5.0,
                "execution_time_censored": False,
                "solver_outcome": "search_limit_reached",
                "termination_reason": "FEASIBLE",
                "scheduled_work_orders": 4,
                "total_work_orders": 5,
                "complete_schedule_found": False,
                "feasible_solution_found": True,
                "optimality_proven": False,
                "objective_score": 2.0,
            },
        ]

        summary = task12_runner._rows_for_summary(rows)
        baseline = next(row for row in summary if row["solver"] == "baseline")
        cp_sat = next(row for row in summary if row["solver"] == "cp_sat")
        pairs = task12_runner._paired_rows(
            [
                {
                    **rows[0],
                    "repetition": 1,
                    "seed": 1,
                    "instance_id": "id",
                    "instance_sha256": "digest",
                    "run_order": "baseline_then_cp_sat",
                    "schedule_completeness_pct": None,
                    "infeasibility_proven": False,
                    "coverage_optimality_proven": False,
                    "scheduled_work_ids": None,
                    "unscheduled_work_ids": None,
                    "objective_scale_description": "",
                    "solver_objective_value": None,
                    "solver_objective_integer_scale": None,
                    "timeout_limit_sec": 3.0,
                },
                {
                    **rows[1],
                    "repetition": 1,
                    "seed": 1,
                    "instance_id": "id",
                    "instance_sha256": "digest",
                    "run_order": "baseline_then_cp_sat",
                    "schedule_completeness_pct": 80.0,
                    "infeasibility_proven": False,
                    "coverage_optimality_proven": False,
                    "scheduled_work_ids": "[]",
                    "unscheduled_work_ids": "[]",
                    "objective_scale_description": "",
                    "solver_objective_value": None,
                    "solver_objective_integer_scale": None,
                    "timeout_limit_sec": 5.0,
                },
            ]
        )

        self.assertEqual(baseline["censored_timeout_runs"], 1)
        self.assertIsNone(baseline["full_schedule_success_rate"])
        self.assertEqual(cp_sat["feasible_solution_rate"], 1.0)
        self.assertIsNone(pairs[0]["runtime_speedup_baseline_over_cp_sat"])
        self.assertTrue(pairs[0]["timeout_or_censoring_present"])

    def test_completed_baseline_records_external_timeout_configuration(self):
        config = {
            "time_horizon_hrs": 24,
            "enable_ac3_pruning": True,
            "enable_simulated_annealing": True,
        }
        result = {
            "total_work_orders": 1,
            "scheduled_work_orders": 1,
            "unscheduled_work_orders": 0,
            "solver_outcome": "success",
            "search_limit_reached": False,
            "objective_score": 1.0,
            "scheduled_work_ids": ["A"],
            "unscheduled_work_ids": [],
            "backtracking_nodes": 2,
            "astar_nodes": 3,
            "candidate_domain_size_before_filtering": 1,
            "candidate_domain_size_after_train_filtering": 1,
            "candidate_domain_size_after_ac3": 1,
            "ac3_pruned_candidates": 0,
            "execution_time_sec": 0.1,
        }

        row = task12_runner._baseline_result_row(
            result, 1, 1, 9, "digest", config, "baseline_then_cp_sat", 120.0
        )

        self.assertEqual(row["timeout_limit_sec"], 120.0)
        self.assertEqual(
            json.loads(row["solver_configuration"])[
                "baseline_external_timeout_seconds"
            ],
            120.0,
        )
        self.assertIn("ortools", json.loads(row["dependency_versions"]))

    def test_pairing_uses_same_instance_and_records_differences(self):
        baseline = {
            "solver": "baseline", "workload_size": 5, "repetition": 1,
            "seed": 4, "instance_id": "a", "instance_sha256": "same",
            "time_limit_sec": None, "run_order": "baseline_then_cp_sat",
            "execution_time_sec": 10.0, "execution_time_censored": False,
            "scheduled_work_orders": 4, "schedule_completeness_pct": 80.0,
            "objective_score": 3.0, "optimality_proven": False,
        }
        cp_sat = {
            **baseline, "solver": "cp_sat", "time_limit_sec": 5.0,
            "execution_time_sec": 2.0, "scheduled_work_orders": 5,
            "schedule_completeness_pct": 100.0, "objective_score": 2.0,
            "optimality_proven": True,
        }

        pair = task12_runner._paired_rows([baseline, cp_sat])[0]

        self.assertEqual(pair["runtime_speedup_baseline_over_cp_sat"], 5.0)
        self.assertEqual(pair["scheduled_count_difference_cp_sat_minus_baseline"], 1)
        self.assertEqual(pair["completeness_difference_percentage_points"], 20.0)
        self.assertEqual(pair["objective_difference_cp_sat_minus_baseline"], -1.0)
        self.assertFalse(pair["objective_comparison_interpretable"])

    def test_independent_exhaustive_reference_cases_and_equivalence_matrix(self):
        reference = task12_runner._exhaustive_validation_rows()
        matrix = task12_runner._constraint_equivalence_rows()

        self.assertEqual(len(reference), 3)
        self.assertTrue(all(row["cpsat_matches_reference"] for row in reference))
        constraint_cases = [
            row for row in matrix if row["scheduled_count_matches_expected"] is not None
        ]
        self.assertTrue(
            all(row["scheduled_count_matches_expected"] for row in constraint_cases)
        )
        self.assertTrue(
            next(
                row
                for row in matrix
                if row["case"] == "missing_required_duration"
            )["validation_behavior_matches"]
        )
        self.assertTrue(
            any(not row["same_solver_outcome"] for row in constraint_cases)
        )
        self.assertIn(
            "maintenance_heavy_opposite_line_overlap",
            {row["case"] for row in matrix},
        )
        self.assertIn(
            "missing_required_duration",
            {row["case"] for row in matrix},
        )

    def test_charts_are_generated_from_saved_csv_outputs(self):
        rows = [
            {
                "solver": "baseline",
                "workload_size": 5,
                "repetition": 1,
                "seed": 1,
                "time_limit_sec": None,
                "execution_time_sec": 1.0,
                "execution_time_censored": False,
                "scheduled_work_orders": 5,
                "total_work_orders": 5,
                "complete_schedule_found": True,
                "feasible_solution_found": True,
                "optimality_proven": False,
                "objective_score": 1.0,
                "solver_outcome": "success",
                "termination_reason": "SUCCESS",
                "cp_sat_status": "",
                "instance_sha256": "same",
                "instance_id": "id",
                "run_order": "baseline_then_cp_sat",
                "schedule_completeness_pct": 100.0,
                "infeasibility_proven": False,
                "coverage_optimality_proven": False,
                "scheduled_work_ids": '["A"]',
                "unscheduled_work_ids": "[]",
                "objective_scale_description": "",
                "solver_objective_value": 1.0,
                "solver_objective_integer_scale": None,
                "search_nodes_or_branches": 10,
                "search_conflicts": None,
                "candidate_domain_before_filtering": 1,
                "candidate_domain_after_train_filtering": 1,
                "candidate_domain_after_ac3": 1,
                "ac3_pruned_candidates": 0,
                "memory_peak_mb": None,
                "python_version": "3.12",
                "platform": "test",
                "machine": "test",
                "processor": "test",
                "cpu_count": 1,
                "ortools_version": "",
                "termination_detail": "",
                "timeout_limit_sec": None,
                "solver_configuration": "{}",
                "schedule_horizon_hours": 24,
            },
            {
                "solver": "cp_sat",
                "workload_size": 5,
                "repetition": 1,
                "seed": 1,
                "time_limit_sec": 5.0,
                "execution_time_sec": 0.5,
                "execution_time_censored": False,
                "scheduled_work_orders": 5,
                "total_work_orders": 5,
                "complete_schedule_found": True,
                "feasible_solution_found": True,
                "optimality_proven": True,
                "objective_score": 0.8,
                "solver_outcome": "success",
                "termination_reason": "OPTIMAL",
                "cp_sat_status": "OPTIMAL",
                "instance_sha256": "same",
                "instance_id": "id",
                "run_order": "baseline_then_cp_sat",
                "schedule_completeness_pct": 100.0,
                "infeasibility_proven": False,
                "coverage_optimality_proven": True,
                "scheduled_work_ids": '["A"]',
                "unscheduled_work_ids": "[]",
                "objective_scale_description": "scaled",
                "solver_objective_value": 800.0,
                "solver_objective_integer_scale": 1000,
                "timeout_limit_sec": 5.0,
                "search_nodes_or_branches": 5,
                "search_conflicts": 0,
                "candidate_domain_before_filtering": 1,
                "candidate_domain_after_train_filtering": 1,
                "candidate_domain_after_ac3": None,
                "ac3_pruned_candidates": None,
                "memory_peak_mb": None,
                "python_version": "3.12",
                "platform": "test",
                "machine": "test",
                "processor": "test",
                "cpu_count": 1,
                "ortools_version": "9.14.6206",
                "termination_detail": "OPTIMAL",
                "solver_configuration": "{}",
                "schedule_horizon_hours": 24,
            },
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            task12_runner._write_csv(output_dir / "individual_results.csv", rows)
            task12_runner._write_csv(
                output_dir / "summary_results.csv",
                task12_runner._rows_for_summary(rows),
            )
            task12_runner._write_csv(
                output_dir / "paired_comparisons.csv",
                task12_runner._paired_rows(rows),
            )

            task12_runner._write_charts_from_csv(output_dir)

            charts = list((output_dir / "charts").glob("*.png"))
            self.assertEqual(len(charts), 6)
            self.assertTrue(all(chart.stat().st_size > 0 for chart in charts))

    def test_csv_writer_preserves_fields_present_only_in_later_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "rows.csv"
            empty_path = Path(temp_dir) / "empty.csv"

            task12_runner._write_csv(
                path,
                [{"case": "regular"}, {"case": "validation", "validation_behavior_matches": True}],
            )
            task12_runner._write_csv(empty_path, [], ("first", "optional"))

            with path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))
            with empty_path.open(newline="", encoding="utf-8") as file:
                empty_reader = csv.reader(file)
                self.assertEqual(next(empty_reader), ["first", "optional"])
            self.assertEqual(rows[1]["validation_behavior_matches"], "True")
            self.assertEqual(rows[0]["validation_behavior_matches"], "")

    def test_constraint_csv_preserves_heterogeneous_validation_row_fields(self):
        rows = task12_runner._constraint_equivalence_rows()
        validation = next(row for row in rows if row["case"] == "missing_required_duration")
        validation["optional_diagnostic"] = "preserved"

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "constraint.csv"
            task12_runner._write_csv(
                path, rows, task12_runner.CONSTRAINT_FIELDS
            )
            with path.open(newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                written = list(reader)
                self.assertIn("validation_behavior_matches", reader.fieldnames)
                self.assertIn("optional_diagnostic", reader.fieldnames)

        regular = next(row for row in written if row["case"] != "missing_required_duration")
        written_validation = next(
            row for row in written if row["case"] == "missing_required_duration"
        )
        self.assertEqual(regular["validation_behavior_matches"], "")
        self.assertEqual(written_validation["validation_behavior_matches"], "True")
        self.assertEqual(written_validation["optional_diagnostic"], "preserved")

    def test_csv_write_failure_preserves_previous_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "results.csv"
            path.write_text("previous results\n", encoding="utf-8")

            with patch.object(task12_runner.csv, "DictWriter", side_effect=OSError("write failed")):
                with self.assertRaisesRegex(OSError, "write failed"):
                    task12_runner._write_csv(path, [{"value": "new"}])

            self.assertEqual(path.read_text(encoding="utf-8"), "previous results\n")
            self.assertEqual(list(Path(temp_dir).glob(".results.csv.*.tmp")), [])

    def test_directory_publish_failure_restores_previous_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "results"
            staging = root / ".results.run"
            output.mkdir()
            staging.mkdir()
            (output / "summary.csv").write_text("old\n", encoding="utf-8")
            (staging / "summary.csv").write_text("new\n", encoding="utf-8")
            real_replace = task12_runner.os.replace
            calls = 0

            def replace_with_failure(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("publish failed")
                real_replace(source, target)

            with patch.object(
                task12_runner.os, "replace", side_effect=replace_with_failure
            ):
                with self.assertRaisesRegex(OSError, "publish failed"):
                    task12_runner._publish_output_directory(staging, output)

            self.assertEqual((output / "summary.csv").read_text(encoding="utf-8"), "old\n")
            self.assertTrue(staging.exists())

    def test_successful_publish_preserves_previous_output_backup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "results"
            staging = root / ".results.run"
            output.mkdir()
            staging.mkdir()
            (output / "summary.csv").write_text("old\n", encoding="utf-8")
            (staging / "summary.csv").write_text("new\n", encoding="utf-8")

            backup = task12_runner._publish_output_directory(staging, output)

            self.assertEqual((output / "summary.csv").read_text(encoding="utf-8"), "new\n")
            self.assertIsNotNone(backup)
            self.assertEqual(
                (backup / "summary.csv").read_text(encoding="utf-8"), "old\n"
            )

    def test_previous_output_is_recovered_if_publish_was_interrupted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "results"
            backup = root / ".results.previous-interrupted"
            backup.mkdir()
            (backup / "summary.csv").write_text("old\n", encoding="utf-8")

            restored_from = task12_runner._restore_previous_output_if_missing(output)

            self.assertEqual(restored_from, backup)
            self.assertEqual((output / "summary.csv").read_text(encoding="utf-8"), "old\n")
            self.assertFalse(backup.exists())

    def test_failed_run_keeps_incremental_checkpoint_and_previous_results(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "results"
            output.mkdir()
            (output / "summary_results.csv").write_text(
                "previous complete summary\n", encoding="utf-8"
            )
            baseline_row = {
                "solver": "baseline",
                "workload_size": 1,
                "repetition": 1,
                "seed": 12,
                "instance_id": "n1-r1-s12",
                "instance_sha256": "digest",
                "execution_time_sec": 1.0,
                "execution_time_censored": False,
                "time_limit_sec": None,
                "scheduled_work_orders": 1,
                "unscheduled_work_orders": 0,
                "schedule_completeness_pct": 100.0,
                "solver_outcome": "success",
                "termination_reason": "SUCCESS",
                "feasible_solution_found": True,
                "complete_schedule_found": True,
                "infeasibility_proven": False,
                "optimality_proven": False,
                "coverage_optimality_proven": False,
                "objective_score": 1.0,
                "run_order": "baseline_then_cp_sat",
            }
            with (
                patch.object(task12_runner.cpsat_solver, "_load_cp_sat"),
                patch.object(
                    task12_runner,
                    "run_baseline_bounded",
                    return_value=baseline_row,
                ),
                patch.object(
                    task12_runner,
                    "_run_cp_sat",
                    side_effect=RuntimeError("simulated solver failure"),
                ),
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "simulated solver failure"
                ) as caught:
                    task12_runner.run_task12(
                        output_dir=output,
                        repetitions=1,
                        base_seed=12,
                        sizes=(1,),
                        time_limits=(5.0,),
                    )

            self.assertEqual(
                (output / "summary_results.csv").read_text(encoding="utf-8"),
                "previous complete summary\n",
            )
            checkpoints = list(root.glob(".results.run-*"))
            self.assertEqual(len(checkpoints), 1)
            state = json.loads(
                (checkpoints[0] / "run_state.json").read_text(encoding="utf-8")
            )
            self.assertEqual(state["status"], "failed")
            self.assertEqual(state["completed_solver_rows"], 1)
            with (checkpoints[0] / "individual_results.csv").open(
                newline="", encoding="utf-8"
            ) as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["solver"], "baseline")
            self.assertIn(str(checkpoints[0]), str(caught.exception.__notes__))


if __name__ == "__main__":
    unittest.main()
