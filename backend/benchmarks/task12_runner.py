"""Reproducible, bounded comparative evaluation for Task 12."""

from __future__ import annotations

import argparse
import csv
import json
import math
import multiprocessing
import os
import platform
import statistics
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from backend.app import cpsat_solver, solver_engine
from backend.benchmarks import compare, runner

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "task12_results"
DEFAULT_SIZES = (10, 25, 50)
DEFAULT_REPETITIONS = 10
DEFAULT_SEED = 20261030
DEFAULT_CP_SAT_LIMITS = (5.0, 10.0, 30.0, 60.0)
DEFAULT_BASELINE_TIMEOUT_SECONDS = 120.0
BASELINE_CONFIG = {
    "enable_ac3_pruning": True,
    "enable_simulated_annealing": True,
    "max_search_nodes": 100_000,
}

INDIVIDUAL_FIELDS = (
    "solver",
    "workload_size",
    "repetition",
    "seed",
    "instance_id",
    "instance_sha256",
    "schedule_horizon_hours",
    "solver_configuration",
    "run_order",
    "execution_time_sec",
    "execution_time_censored",
    "timeout_limit_sec",
    "time_limit_sec",
    "total_work_orders",
    "scheduled_work_orders",
    "unscheduled_work_orders",
    "schedule_completeness_pct",
    "solver_outcome",
    "termination_reason",
    "feasible_solution_found",
    "complete_schedule_found",
    "infeasibility_proven",
    "optimality_proven",
    "coverage_optimality_proven",
    "objective_score",
    "solver_objective_value",
    "solver_objective_integer_scale",
    "objective_scale_description",
    "scheduled_work_ids",
    "unscheduled_work_ids",
    "search_nodes_or_branches",
    "search_conflicts",
    "candidate_domain_before_filtering",
    "candidate_domain_after_train_filtering",
    "candidate_domain_after_ac3",
    "ac3_pruned_candidates",
    "memory_peak_mb",
    "python_version",
    "platform",
    "machine",
    "processor",
    "cpu_count",
    "dependency_versions",
    "ortools_version",
    "termination_detail",
)

SUMMARY_FIELDS = (
    "solver",
    "workload_size",
    "time_limit_sec",
    "runs",
    "completed_runs",
    "censored_timeout_runs",
    "runtime_mean_sec_including_censored_observations",
    "runtime_median_sec_including_censored_observations",
    "runtime_stdev_sec_including_censored_observations",
    "runtime_min_sec",
    "runtime_max_sec",
    "runtime_mean_completed_only_sec",
    "mean_scheduled_work_orders",
    "mean_completeness_pct",
    "full_schedule_success_rate",
    "feasible_solution_rate",
    "optimality_proof_rate",
    "mean_objective_score",
    "search_limit_runs",
)

PAIRED_FIELDS = (
    "workload_size",
    "repetition",
    "seed",
    "instance_id",
    "instance_sha256",
    "time_limit_sec",
    "run_order",
    "baseline_runtime_sec",
    "baseline_runtime_censored",
    "cp_sat_runtime_sec",
    "cp_sat_runtime_censored",
    "runtime_speedup_baseline_over_cp_sat",
    "scheduled_count_difference_cp_sat_minus_baseline",
    "completeness_difference_percentage_points",
    "objective_difference_cp_sat_minus_baseline",
    "baseline_optimality_proven",
    "cp_sat_optimality_proven",
    "objective_comparison_interpretable",
    "timeout_or_censoring_present",
)

CONSTRAINT_FIELDS = (
    "case",
    "expected_scheduled",
    "baseline_scheduled",
    "cpsat_scheduled",
    "baseline_status",
    "cpsat_status",
    "baseline_outcome",
    "cpsat_outcome",
    "same_status",
    "same_solver_outcome",
    "classification",
    "scheduled_count_matches_expected",
    "detail",
    "validation_behavior_matches",
)

EXHAUSTIVE_FIELDS = (
    "scenario",
    "work_order_count",
    "reference_maximum_scheduled",
    "reference_objective_score",
    "feasible_assignments_examined",
    "cpsat_scheduled",
    "cpsat_objective_score",
    "cpsat_status",
    "cpsat_optimality_proven",
    "cpsat_matches_reference",
    "baseline_scheduled",
    "baseline_objective_score",
    "limitation",
)


def build_seeded_instance(
    seed: int, workload_size: int
) -> tuple[list[Any], list[Any], dict[str, Any], str]:
    orders, trains, config = runner.build_instances(seed)
    if workload_size < 1:
        raise ValueError("workload_size must be positive")
    if workload_size > len(orders):
        raise ValueError(
            f"Requested {workload_size} work orders, but the existing generator "
            f"provides only {len(orders)}"
        )
    selected = orders[:workload_size]
    digest = runner.instance_digest(selected, trains, config)
    return selected, trains, config, digest


def _baseline_worker(connection: Any, payload: dict[str, Any]) -> None:
    try:
        from backend.benchmarks import runner as baseline_runner

        connection.send(("ready", None))
        row = baseline_runner.run_once(
            payload["orders"],
            payload["trains"],
            payload["config"],
            payload["workload_size"],
            payload["repetition"],
            payload["seed"],
            payload["digest"],
            include_work_order_ids=True,
        )
        connection.send(("result", row))
    except BaseException as exc:
        try:
            connection.send(("error", f"{type(exc).__name__}: {exc}"))
        except (BrokenPipeError, EOFError):
            pass
    finally:
        connection.close()


def run_baseline_bounded(
    orders: list[Any],
    trains: list[Any],
    config: dict[str, Any],
    workload_size: int,
    repetition: int,
    seed: int,
    digest: str,
    timeout_seconds: float,
    run_order: str,
    startup_timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("baseline timeout must be finite and greater than 0")
    context = multiprocessing.get_context("spawn")
    receive, send = context.Pipe(duplex=False)
    payload = {
        "orders": orders,
        "trains": trains,
        "config": config,
        "workload_size": workload_size,
        "repetition": repetition,
        "seed": seed,
        "digest": digest,
    }
    process = context.Process(target=_baseline_worker, args=(send, payload))
    process.start()
    send.close()
    try:
        if not receive.poll(startup_timeout_seconds):
            process.terminate()
            process.join()
            raise TimeoutError("Baseline worker did not initialize before startup timeout")
        kind, payload_result = receive.recv()
        if kind == "error":
            raise RuntimeError(f"Baseline worker failed: {payload_result}")
        if kind != "ready":
            raise RuntimeError(f"Unexpected baseline worker message: {kind}")
        started = time.monotonic()
        if receive.poll(timeout_seconds):
            kind, payload_result = receive.recv()
            if kind == "error":
                raise RuntimeError(f"Baseline worker failed: {payload_result}")
            if kind != "result":
                raise RuntimeError(f"Unexpected baseline worker message: {kind}")
            return _baseline_result_row(
                payload_result,
                workload_size,
                repetition,
                seed,
                digest,
                config,
                run_order,
                timeout_seconds,
            )

        elapsed = time.monotonic() - started
        process.terminate()
        process.join()
        return _timeout_row(
            "baseline",
            workload_size,
            repetition,
            seed,
            digest,
            config,
            run_order,
            elapsed,
            timeout_seconds,
            "Baseline child process reached the external wall-clock bound.",
        )
    finally:
        receive.close()
        if process.is_alive():
            process.terminate()
        process.join()


def _base_row(
    solver_name: str,
    workload_size: int,
    repetition: int,
    seed: int,
    digest: str,
    config: dict[str, Any],
    run_order: str,
) -> dict[str, Any]:
    return {
        "solver": solver_name,
        "workload_size": workload_size,
        "repetition": repetition,
        "seed": seed,
        "instance_id": f"n{workload_size}-r{repetition}-s{seed}",
        "instance_sha256": digest,
        "schedule_horizon_hours": config["time_horizon_hrs"],
        "solver_configuration": json.dumps(config, sort_keys=True),
        "run_order": run_order,
        "execution_time_censored": False,
        "timeout_limit_sec": None,
        "time_limit_sec": None,
        "total_work_orders": workload_size,
        "scheduled_work_orders": None,
        "unscheduled_work_orders": None,
        "schedule_completeness_pct": None,
        "solver_outcome": "timeout",
        "termination_reason": "TIMEOUT",
        "feasible_solution_found": None,
        "complete_schedule_found": None,
        "infeasibility_proven": False,
        "optimality_proven": False,
        "coverage_optimality_proven": False,
        "objective_score": None,
        "solver_objective_value": None,
        "solver_objective_integer_scale": None,
        "objective_scale_description": "",
        "scheduled_work_ids": None,
        "unscheduled_work_ids": None,
        "search_nodes_or_branches": None,
        "search_conflicts": None,
        "candidate_domain_before_filtering": None,
        "candidate_domain_after_train_filtering": None,
        "candidate_domain_after_ac3": None,
        "ac3_pruned_candidates": None,
        "memory_peak_mb": None,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": __import__("os").cpu_count(),
        "dependency_versions": json.dumps(
            runner.dependency_versions(), sort_keys=True
        ),
        "ortools_version": "",
        "termination_detail": "",
    }


def _timeout_row(
    solver_name: str,
    workload_size: int,
    repetition: int,
    seed: int,
    digest: str,
    config: dict[str, Any],
    run_order: str,
    elapsed: float,
    timeout_seconds: float,
    detail: str,
) -> dict[str, Any]:
    row = _base_row(
        solver_name, workload_size, repetition, seed, digest, config, run_order
    )
    row.update(
        {
            "execution_time_sec": elapsed,
            "execution_time_censored": True,
            "timeout_limit_sec": timeout_seconds,
            "solver_configuration": json.dumps(
                {**config, "baseline_external_timeout_seconds": timeout_seconds},
                sort_keys=True,
            ),
            "termination_detail": detail,
        }
    )
    return row


def _baseline_result_row(
    result: dict[str, Any],
    workload_size: int,
    repetition: int,
    seed: int,
    digest: str,
    config: dict[str, Any],
    run_order: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    row = _base_row(
        "baseline", workload_size, repetition, seed, digest, config, run_order
    )
    total = result["total_work_orders"]
    scheduled = result["scheduled_work_orders"]
    config_text = dict(config)
    config_text.update(BASELINE_CONFIG)
    config_text["baseline_external_timeout_seconds"] = timeout_seconds
    row.update(
        {
            "solver_configuration": json.dumps(config_text, sort_keys=True),
            "timeout_limit_sec": timeout_seconds,
            "execution_time_sec": result["execution_time_sec"],
            "scheduled_work_orders": scheduled,
            "unscheduled_work_orders": result["unscheduled_work_orders"],
            "schedule_completeness_pct": (
                100.0 * scheduled / total if total else None
            ),
            "solver_outcome": result["solver_outcome"],
            "termination_reason": (
                "NODE_LIMIT_REACHED"
                if result["search_limit_reached"]
                else result["solver_outcome"].upper()
            ),
            "feasible_solution_found": scheduled > 0,
            "complete_schedule_found": scheduled == total,
            "infeasibility_proven": (
                result["solver_outcome"] == "unschedulable"
            ),
            "objective_score": result["objective_score"],
            "solver_objective_value": result["objective_score"],
            "objective_scale_description": (
                "Baseline floating-point objective; no global optimality proof exposed."
            ),
            "scheduled_work_ids": json.dumps(result["scheduled_work_ids"]),
            "unscheduled_work_ids": json.dumps(result["unscheduled_work_ids"]),
            "search_nodes_or_branches": (
                result["backtracking_nodes"] + result["astar_nodes"]
            ),
            "candidate_domain_before_filtering": (
                result["candidate_domain_size_before_filtering"]
            ),
            "candidate_domain_after_train_filtering": (
                result["candidate_domain_size_after_train_filtering"]
            ),
            "candidate_domain_after_ac3": result["candidate_domain_size_after_ac3"],
            "ac3_pruned_candidates": result["ac3_pruned_candidates"],
        }
    )
    return row


def _run_cp_sat(
    orders: list[Any],
    trains: list[Any],
    config: dict[str, Any],
    workload_size: int,
    repetition: int,
    seed: int,
    digest: str,
    time_limit: float,
    run_order: str,
) -> dict[str, Any]:
    cp_config = dict(config)
    cp_config["cpsat_time_limit_seconds"] = time_limit
    started = time.perf_counter()
    result = cpsat_solver.solve_maintenance_schedule_cpsat(
        orders, trains, cp_config
    )
    elapsed = time.perf_counter() - started
    row = _base_row(
        "cp_sat", workload_size, repetition, seed, digest, cp_config, run_order
    )
    scheduled = result["metrics"]["scheduled_requests"]
    total = result["metrics"]["total_requests"]
    stats = result["search_stats"]
    row.update(
        {
            "solver_configuration": json.dumps(
                {
                    **config,
                    "cpsat_time_limit_seconds": time_limit,
                    "num_search_workers": 1,
                    "search_branching": "FIXED_SEARCH",
                },
                sort_keys=True,
            ),
            "execution_time_sec": elapsed,
            "timeout_limit_sec": time_limit,
            "time_limit_sec": time_limit,
            "scheduled_work_orders": scheduled,
            "unscheduled_work_orders": len(result["unscheduled_work_ids"]),
            "schedule_completeness_pct": (
                100.0 * scheduled / total if total else None
            ),
            "solver_outcome": result["solver_outcome"],
            "termination_reason": result["termination_reason"],
            "feasible_solution_found": result["feasible_solution_found"],
            "complete_schedule_found": scheduled == total,
            "infeasibility_proven": result[
                "complete_schedule_proven_infeasible"
            ],
            "optimality_proven": result["optimality_proven"],
            "coverage_optimality_proven": result.get(
                "coverage_optimality_proven", False
            ),
            "objective_score": result["metrics"]["objective_score"],
            "solver_objective_value": result["metrics"].get(
                "scaled_objective_value"
            ),
            "solver_objective_integer_scale": result["metrics"].get(
                "objective_integer_scale"
            ),
            "objective_scale_description": (
                "CP-SAT uses integer-scaled disruption, workload-balance, and "
                "co-location terms; reported score is recalculated by the "
                "baseline floating-point objective."
            ),
            "scheduled_work_ids": json.dumps(
                [item["work_id"] for item in result["schedule"]]
            ),
            "unscheduled_work_ids": json.dumps(result["unscheduled_work_ids"]),
            "search_nodes_or_branches": stats.get("branches"),
            "search_conflicts": stats.get("conflicts"),
            "candidate_domain_before_filtering": result["metrics"].get(
                "candidate_domain_total_before_train_filtering"
            ),
            "candidate_domain_after_train_filtering": result["metrics"].get(
                "candidate_domain_total_after_train_filtering"
            ),
            "ortools_version": __import__("ortools").__version__,
            "termination_detail": result["cp_sat_status"],
        }
    )
    return row


def _enumerate_reference(
    work_orders: list[dict[str, Any]],
    trains: list[dict[str, Any]],
    horizon: float,
    slot_size: float,
    clearance: float = 0.0,
) -> dict[str, Any]:
    """Independent tiny-instance enumerator; deliberately avoids solver helpers."""
    domains: list[list[float]] = []
    normalized_trains = []
    for train in trains:
        normalized_trains.append(
            {
                "section": train["section_id"],
                "line": train.get("track_line", "DOWN_LINE"),
                "start": max(0.0, train["start_time_hr"] - clearance),
                "end": min(horizon, train["end_time_hr"] + clearance),
            }
        )
    for order in work_orders:
        duration = float(order["duration_hrs"])
        latest = horizon - duration
        candidates = []
        candidate_starts = []
        if latest >= -1e-9:
            step_count = math.floor(latest / slot_size + 1e-9)
            candidate_starts = [
                round(tick * slot_size, 6) for tick in range(step_count + 1)
            ]
            if (
                not candidate_starts
                or latest - candidate_starts[-1] > 1e-9
            ):
                candidate_starts.append(round(latest, 6))
        for start in candidate_starts:
            blocked = any(
                train["section"] == order["section_id"]
                and (
                    train["line"] == order.get("track_line", "DOWN_LINE")
                    or (
                        order.get("heavy_equipment", False)
                        and train["line"] != order.get("track_line", "DOWN_LINE")
                    )
                )
                and start < train["end"]
                and train["start"] < start + duration
                for train in normalized_trains
            )
            if not blocked:
                candidates.append(start)
        domains.append(candidates)

    departments = {str(order["department"]) for order in work_orders}
    best_count = -1
    best_score = math.inf
    best_assignment: dict[int, float] = {}
    examined = 0

    def time_cost(start: float, end: float) -> float:
        daylight = max(0.0, min(end, 22.0) - max(start, 6.0))
        night = max(0.0, min(end, 5.0) - max(start, 1.0))
        return daylight + 0.25 * ((end - start) - daylight - night)

    def valid_pair(left: int, start_left: float, right: int, start_right: float) -> bool:
        a, b = work_orders[left], work_orders[right]
        if a["section_id"] != b["section_id"] or a.get(
            "track_line", "DOWN_LINE"
        ) != b.get("track_line", "DOWN_LINE"):
            return True
        end_left = start_left + float(a["duration_hrs"])
        end_right = start_right + float(b["duration_hrs"])
        if not (start_left < end_right and start_right < end_left):
            return True
        if a["department"] == b["department"]:
            return False
        exact = math.isclose(start_left, start_right, abs_tol=1e-9) and math.isclose(
            end_left, end_right, abs_tol=1e-9
        )
        return exact and a.get("co_location_allowed", True) and b.get(
            "co_location_allowed", True
        )

    def objective(assignment: dict[int, float]) -> float:
        score = 0.0
        shift_loads: dict[tuple[str, int], float] = {}
        windows: dict[tuple[str, str, float, float], list[int]] = {}
        for index, start in assignment.items():
            order = work_orders[index]
            duration = float(order["duration_hrs"])
            end = start + duration
            line = order.get("track_line", "DOWN_LINE")
            score += time_cost(start, end)
            for train in normalized_trains:
                if train["section"] != order["section_id"] or train["line"] != line:
                    continue
                gap = (
                    train["start"] - end
                    if train["start"] >= end
                    else start - train["end"]
                )
                if 0 <= gap < 2:
                    score += (2 - gap) / 2
            shift = min(2, int(start // 8))
            key = (str(order["department"]), shift)
            shift_loads[key] = shift_loads.get(key, 0.0) + duration
            group_key = (
                order["section_id"],
                line,
                start,
                round(end, 6),
            )
            windows.setdefault(group_key, []).append(index)
        imbalance = 0.0
        for department in departments:
            loads = [
                shift_loads.get((department, shift), 0.0) for shift in range(3)
            ]
            mean = sum(loads) / 3
            imbalance += sum((load - mean) ** 2 for load in loads) / 3
        merges = sum(len(group) - 1 for group in windows.values() if len(group) > 1)
        return (
            score
            + 0.1 * imbalance
            - 0.5 * merges
        )

    def enumerate_index(index: int, assignment: dict[int, float]) -> None:
        nonlocal best_count, best_score, best_assignment, examined
        if index == len(work_orders):
            examined += 1
            count = len(assignment)
            score = objective(assignment)
            if count > best_count or (count == best_count and score < best_score - 1e-12):
                best_count = count
                best_score = score
                best_assignment = dict(assignment)
            return
        enumerate_index(index + 1, assignment)
        for start in domains[index]:
            if all(
                valid_pair(index, start, other, other_start)
                for other, other_start in assignment.items()
            ):
                assignment[index] = start
                enumerate_index(index + 1, assignment)
                del assignment[index]

    enumerate_index(0, {})
    return {
        "maximum_scheduled": best_count,
        "objective_score": None if best_count == 0 else best_score,
        "assignment": best_assignment,
        "feasible_assignments_examined": examined,
    }


def _constraint_equivalence_rows() -> list[dict[str, Any]]:
    cases = [
        {
            "case": "same_resource_overlap_same_department",
            "orders": [
                {"work_id": "A", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 1.0, "urgency": 2},
                {"work_id": "B", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 1.0, "urgency": 2},
            ],
            "horizon": 1.0,
            "train": [],
            "expected_scheduled": 1,
            "classification": "equivalent",
            "detail": "Same department cannot overlap within the same section and track.",
        },
        {
            "case": "same_resource_nonoverlap",
            "orders": [
                {"work_id": "A", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 0.5, "urgency": 2},
                {"work_id": "B", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 0.5, "urgency": 2},
            ],
            "horizon": 1.0,
            "train": [],
            "expected_scheduled": 2,
            "classification": "equivalent",
            "detail": "Adjacent non-overlapping intervals are accepted.",
        },
        {
            "case": "different_sections_overlap",
            "orders": [
                {"work_id": "A", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 1.0, "urgency": 2},
                {"work_id": "B", "department": "ENGINEERING", "section_id": "S2",
                 "track_line": "UP_LINE", "duration_hrs": 1.0, "urgency": 2},
            ],
            "horizon": 1.0,
            "train": [],
            "expected_scheduled": 2,
            "classification": "equivalent",
            "detail": "Different sections have independent baseline resources.",
        },
        {
            "case": "different_track_lines_overlap",
            "orders": [
                {"work_id": "A", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 1.0, "urgency": 2},
                {"work_id": "B", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "DOWN_LINE", "duration_hrs": 1.0, "urgency": 2},
            ],
            "horizon": 1.0,
            "train": [],
            "expected_scheduled": 2,
            "classification": "equivalent",
            "detail": "Different track lines are independent maintenance resources.",
        },
        {
            "case": "cross_department_exact_colocation",
            "orders": [
                {"work_id": "A", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 1.0, "urgency": 2},
                {"work_id": "B", "department": "SIGNALLING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 1.0, "urgency": 2},
            ],
            "horizon": 1.0,
            "train": [],
            "expected_scheduled": 2,
            "classification": "equivalent",
            "detail": "Cross-department overlap is allowed for identical windows when both allow co-location.",
        },
        {
            "case": "cross_department_partial_overlap",
            "orders": [
                {"work_id": "A", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 1.0, "urgency": 2},
                {"work_id": "B", "department": "SIGNALLING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 0.5, "urgency": 2},
            ],
            "horizon": 1.0,
            "train": [],
            "expected_scheduled": 1,
            "classification": "equivalent",
            "detail": "Cross-department non-identical overlap is rejected.",
        },
        {
            "case": "heavy_equipment_adjacent_train",
            "orders": [
                {"work_id": "A", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "heavy_equipment": True,
                 "duration_hrs": 1.0, "urgency": 2},
            ],
            "horizon": 1.0,
            "train": [{"train_no": "T", "section_id": "S1",
                       "track_line": "DOWN_LINE", "start_time_hr": 0.0,
                       "end_time_hr": 1.0}],
            "expected_scheduled": 0,
            "classification": "equivalent",
            "detail": "Heavy equipment is filtered against train occupancy on the other line.",
        },
        {
            "case": "maintenance_heavy_opposite_line_overlap",
            "orders": [
                {"work_id": "A", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "heavy_equipment": True,
                 "duration_hrs": 1.0, "urgency": 2},
                {"work_id": "B", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "DOWN_LINE", "duration_hrs": 1.0, "urgency": 2},
            ],
            "horizon": 1.0,
            "train": [],
            "expected_scheduled": 2,
            "classification": "baseline_limitation",
            "detail": "Baseline does not prohibit heavy-equipment maintenance from overlapping maintenance on the adjacent line.",
        },
    ]
    rows = []
    for case in cases:
        cfg = {
            "section_ids": ["S1", "S2"],
            "time_horizon_hrs": case["horizon"],
            "slot_duration_hrs": 0.5,
            "enable_ac3_pruning": True,
            "enable_simulated_annealing": False,
            "max_search_nodes": 100_000,
            "random_seed": 1,
        }
        expected = case["expected_scheduled"]
        baseline = solver_engine.solve_maintenance_schedule(
            case["orders"], case["train"], cfg
        )
        cpsat = cpsat_solver.solve_maintenance_schedule_cpsat(
            case["orders"],
            case["train"],
            {**cfg, "cpsat_time_limit_seconds": 5.0},
        )
        rows.append(
            {
                "case": case["case"],
                "expected_scheduled": expected,
                "baseline_scheduled": len(baseline["schedule"]),
                "cpsat_scheduled": len(cpsat["schedule"]),
                "baseline_status": baseline["status"],
                "cpsat_status": cpsat["status"],
                "baseline_outcome": baseline["solver_outcome"],
                "cpsat_outcome": cpsat["solver_outcome"],
                "same_status": baseline["status"] == cpsat["status"],
                "same_solver_outcome": (
                    baseline["solver_outcome"] == cpsat["solver_outcome"]
                ),
                "classification": case["classification"],
                "scheduled_count_matches_expected": (
                    len(baseline["schedule"]) == len(cpsat["schedule"]) == expected
                ),
                "detail": case["detail"],
            }
        )
    invalid_order = {
        "work_id": "MISSING-DURATION",
        "department": "ENGINEERING",
        "section_id": "S1",
        "track_line": "UP_LINE",
        "urgency": 2,
    }
    results = []
    for solve in (
        lambda: solver_engine.solve_maintenance_schedule(
            [invalid_order], [], {
                "section_ids": ["S1"], "time_horizon_hrs": 1,
                "enable_simulated_annealing": False,
            }
        ),
        lambda: cpsat_solver.solve_maintenance_schedule_cpsat(
            [invalid_order], [], {
                "section_ids": ["S1"], "time_horizon_hrs": 1,
                "enable_simulated_annealing": False,
                "cpsat_time_limit_seconds": 5,
            }
        ),
    ):
        try:
            solve()
            results.append("accepted")
        except (TypeError, ValueError) as exc:
            results.append(f"rejected: {type(exc).__name__}")
    rows.append(
        {
            "case": "missing_required_duration",
            "expected_scheduled": None,
            "baseline_scheduled": None,
            "cpsat_scheduled": None,
            "baseline_status": None,
            "cpsat_status": None,
            "baseline_outcome": results[0],
            "cpsat_outcome": results[1],
            "same_status": None,
            "same_solver_outcome": results[0] == results[1],
            "classification": "equivalent_validation",
            "scheduled_count_matches_expected": None,
            "validation_behavior_matches": results[0] == results[1]
            and results[0].startswith("rejected"),
            "detail": (
                "Both implementations use the baseline normalizer and reject a "
                "work order without duration_hrs."
            ),
        }
    )
    return rows


def _exhaustive_validation_rows() -> list[dict[str, Any]]:
    scenarios = [
        {
            "name": "feasible_two_nonoverlapping",
            "orders": [
                {"work_id": "A", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 0.5, "urgency": 2,
                 "co_location_allowed": True},
                {"work_id": "B", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 0.5, "urgency": 2,
                 "co_location_allowed": True},
            ],
            "trains": [],
            "horizon": 1.0,
        },
        {
            "name": "infeasible_train_blocks_all_windows",
            "orders": [
                {"work_id": "A", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 0.5, "urgency": 1,
                 "co_location_allowed": True},
            ],
            "trains": [
                {"train_no": "T", "section_id": "S1", "track_line": "UP_LINE",
                 "start_time_hr": 0.0, "end_time_hr": 1.0}
            ],
            "horizon": 1.0,
        },
        {
            "name": "partial_two_full_horizon_conflict",
            "orders": [
                {"work_id": "A", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 1.0, "urgency": 1,
                 "co_location_allowed": True},
                {"work_id": "B", "department": "ENGINEERING", "section_id": "S1",
                 "track_line": "UP_LINE", "duration_hrs": 1.0, "urgency": 2,
                 "co_location_allowed": True},
            ],
            "trains": [],
            "horizon": 1.0,
        },
    ]
    rows = []
    for scenario in scenarios:
        cfg = {
            "section_ids": ["S1"],
            "time_horizon_hrs": scenario["horizon"],
            "slot_duration_hrs": 0.5,
            "enable_ac3_pruning": True,
            "enable_simulated_annealing": False,
            "max_search_nodes": 100_000,
            "random_seed": 1,
        }
        reference = _enumerate_reference(
            scenario["orders"],
            scenario["trains"],
            scenario["horizon"],
            cfg["slot_duration_hrs"],
        )
        cp_result = cpsat_solver.solve_maintenance_schedule_cpsat(
            scenario["orders"],
            scenario["trains"],
            {**cfg, "cpsat_time_limit_seconds": 5.0},
        )
        baseline_result = solver_engine.solve_maintenance_schedule(
            scenario["orders"], scenario["trains"], cfg
        )
        cp_score = cp_result["metrics"]["objective_score"]
        cp_count = cp_result["metrics"]["scheduled_requests"]
        cp_valid = (
            cp_count == reference["maximum_scheduled"]
            and cp_result["optimality_proven"]
            and (
                reference["objective_score"] is None
                or math.isclose(
                    cp_score, reference["objective_score"], abs_tol=1e-9
                )
            )
        )
        rows.append(
            {
                "scenario": scenario["name"],
                "work_order_count": len(scenario["orders"]),
                "reference_maximum_scheduled": reference["maximum_scheduled"],
                "reference_objective_score": reference["objective_score"],
                "feasible_assignments_examined": reference[
                    "feasible_assignments_examined"
                ],
                "cpsat_scheduled": cp_count,
                "cpsat_objective_score": cp_score,
                "cpsat_status": cp_result["cp_sat_status"],
                "cpsat_optimality_proven": cp_result["optimality_proven"],
                "cpsat_matches_reference": cp_valid,
                "baseline_scheduled": len(baseline_result["schedule"]),
                "baseline_objective_score": (
                    solver_engine._schedule_objective(
                        {
                            index: next(
                                item["start_time_hr"]
                                for item in baseline_result["schedule"]
                                if item["work_id"] == order["work_id"]
                            )
                            for index, order in enumerate(scenario["orders"])
                            if any(
                                item["work_id"] == order["work_id"]
                                for item in baseline_result["schedule"]
                            )
                        },
                        solver_engine._normalise_inputs(
                            scenario["orders"], scenario["trains"], cfg
                        )[0],
                        solver_engine._normalise_inputs(
                            scenario["orders"], scenario["trains"], cfg
                        )[1],
                        cfg,
                    )
                    if baseline_result["schedule"]
                    else None
                ),
                "limitation": (
                    "Exhaustive check covers only this finite small instance and "
                    "uses an independently written feasibility/objective evaluator."
                ),
            }
        )
    return rows


def _rows_for_summary(individual: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int, float | None], list[dict[str, Any]]] = {}
    for row in individual:
        key = (row["solver"], row["workload_size"], row.get("time_limit_sec"))
        groups.setdefault(key, []).append(row)
    summaries = []
    for (solver_name, size, limit), group in sorted(
        groups.items(), key=lambda item: (item[0][1], item[0][0], item[0][2] or 0)
    ):
        times = [
            float(row["execution_time_sec"])
            for row in group
            if row["execution_time_sec"] is not None
        ]
        completed = [row for row in group if not row["execution_time_censored"]]
        scheduled_values = [
            row["scheduled_work_orders"]
            for row in completed
            if row["scheduled_work_orders"] is not None
        ]
        complete_flags = [
            row["complete_schedule_found"]
            for row in completed
            if row["complete_schedule_found"] is not None
        ]
        feasible_flags = [
            row["feasible_solution_found"]
            for row in completed
            if row["feasible_solution_found"] is not None
        ]
        proven_flags = [
            row["optimality_proven"]
            for row in completed
            if row["optimality_proven"] is not None
        ]
        objective_values = [
            float(row["objective_score"])
            for row in completed
            if row["objective_score"] is not None
        ]
        denominators = [
            row["total_work_orders"]
            for row in completed
            if row["scheduled_work_orders"] is not None
        ]
        summaries.append(
            {
                "solver": solver_name,
                "workload_size": size,
                "time_limit_sec": limit,
                "runs": len(group),
                "completed_runs": len(completed),
                "censored_timeout_runs": sum(
                    row["execution_time_censored"] for row in group
                ),
                "runtime_mean_sec_including_censored_observations": (
                    statistics.mean(times) if times else None
                ),
                "runtime_median_sec_including_censored_observations": (
                    statistics.median(times) if times else None
                ),
                "runtime_stdev_sec_including_censored_observations": (
                    statistics.pstdev(times) if times else None
                ),
                "runtime_min_sec": min(times) if times else None,
                "runtime_max_sec": max(times) if times else None,
                "runtime_mean_completed_only_sec": (
                    statistics.mean(
                        float(row["execution_time_sec"]) for row in completed
                    )
                    if completed
                    else None
                ),
                "mean_scheduled_work_orders": (
                    statistics.mean(scheduled_values) if scheduled_values else None
                ),
                "mean_completeness_pct": (
                    100
                    * sum(scheduled_values)
                    / sum(denominators)
                    if denominators
                    else None
                ),
                "full_schedule_success_rate": (
                    sum(complete_flags) / len(complete_flags)
                    if complete_flags
                    else None
                ),
                "feasible_solution_rate": (
                    sum(feasible_flags) / len(feasible_flags)
                    if feasible_flags
                    else None
                ),
                "optimality_proof_rate": (
                    sum(proven_flags) / len(proven_flags)
                    if proven_flags
                    else None
                ),
                "mean_objective_score": (
                    statistics.mean(objective_values) if objective_values else None
                ),
                "search_limit_runs": sum(
                    row["solver_outcome"] == "search_limit_reached"
                    or row["termination_reason"] in ("NODE_LIMIT_REACHED", "FEASIBLE", "UNKNOWN")
                    for row in completed
                ),
            }
        )
    return summaries


def _paired_rows(individual: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline_by_instance = {
        (row["workload_size"], row["seed"]): row
        for row in individual
        if row["solver"] == "baseline"
    }
    pairs = []
    for cp_row in individual:
        if cp_row["solver"] != "cp_sat":
            continue
        baseline_row = baseline_by_instance[
            (cp_row["workload_size"], cp_row["seed"])
        ]
        base_complete = (
            not baseline_row["execution_time_censored"]
            and not cp_row["execution_time_censored"]
        )
        base_sched = baseline_row["scheduled_work_orders"]
        cp_sched = cp_row["scheduled_work_orders"]
        pairs.append(
            {
                "workload_size": cp_row["workload_size"],
                "repetition": cp_row["repetition"],
                "seed": cp_row["seed"],
                "instance_id": cp_row["instance_id"],
                "instance_sha256": cp_row["instance_sha256"],
                "time_limit_sec": cp_row["time_limit_sec"],
                "run_order": cp_row["run_order"],
                "baseline_runtime_sec": baseline_row["execution_time_sec"],
                "baseline_runtime_censored": baseline_row["execution_time_censored"],
                "cp_sat_runtime_sec": cp_row["execution_time_sec"],
                "cp_sat_runtime_censored": cp_row["execution_time_censored"],
                "runtime_speedup_baseline_over_cp_sat": (
                    baseline_row["execution_time_sec"] / cp_row["execution_time_sec"]
                    if base_complete
                    and cp_row["execution_time_sec"]
                    and baseline_row["execution_time_sec"] is not None
                    else None
                ),
                "scheduled_count_difference_cp_sat_minus_baseline": (
                    cp_sched - base_sched
                    if base_sched is not None and cp_sched is not None
                    else None
                ),
                "completeness_difference_percentage_points": (
                    cp_row["schedule_completeness_pct"]
                    - baseline_row["schedule_completeness_pct"]
                    if cp_row["schedule_completeness_pct"] is not None
                    and baseline_row["schedule_completeness_pct"] is not None
                    else None
                ),
                "objective_difference_cp_sat_minus_baseline": (
                    cp_row["objective_score"] - baseline_row["objective_score"]
                    if cp_row["objective_score"] is not None
                    and baseline_row["objective_score"] is not None
                    else None
                ),
                "baseline_optimality_proven": baseline_row["optimality_proven"],
                "cp_sat_optimality_proven": cp_row["optimality_proven"],
                "objective_comparison_interpretable": (
                    cp_row["optimality_proven"]
                    and baseline_row["optimality_proven"]
                ),
                "timeout_or_censoring_present": (
                    baseline_row["execution_time_censored"]
                    or cp_row["execution_time_censored"]
                ),
            }
        )
    return pairs


def _write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fieldnames: tuple[str, ...] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(
        dict.fromkeys(
            [
                *(fieldnames or ()),
                *(key for row in rows for key in row),
            ]
        )
    )
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            newline="",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            if columns:
                writer = csv.DictWriter(
                    file, fieldnames=columns, restval="", extrasaction="raise"
                )
                writer.writeheader()
                writer.writerows(rows)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(value, file, sort_keys=True, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def _restore_previous_output_if_missing(output_dir: Path) -> Path | None:
    if output_dir.exists():
        return None
    backups = sorted(
        output_dir.parent.glob(f".{output_dir.name}.previous-*"),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    if not backups:
        return None
    os.replace(backups[0], output_dir)
    return backups[0]


def _publish_output_directory(staging_dir: Path, output_dir: Path) -> Path | None:
    backup_dir = None
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        if output_dir.exists():
            if not any(output_dir.iterdir()):
                output_dir.rmdir()
            else:
                backup_dir = output_dir.parent / (
                    f".{output_dir.name}.previous-{uuid.uuid4().hex}"
                )
                os.replace(output_dir, backup_dir)
        os.replace(staging_dir, output_dir)
    except BaseException:
        if backup_dir is not None and backup_dir.exists() and not output_dir.exists():
            os.replace(backup_dir, output_dir)
        raise
    return backup_dir


def _write_charts_from_csv(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    import pandas as pd

    individual = pd.read_csv(output_dir / "individual_results.csv")
    summary = pd.read_csv(output_dir / "summary_results.csv")
    paired = pd.read_csv(output_dir / "paired_comparisons.csv")
    chart_dir = output_dir / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)

    def save(name: str) -> Any:
        plt.tight_layout()
        plt.savefig(chart_dir / name, dpi=150)
        plt.close()

    runtime_summary = summary[summary["runtime_mean_sec_including_censored_observations"].notna()]
    cp_rows = individual[individual["solver"] == "cp_sat"]
    cp_limits = sorted(cp_rows["time_limit_sec"].dropna().unique().tolist())
    plt.figure(figsize=(9, 5))
    baseline = runtime_summary[runtime_summary["solver"] == "baseline"]
    baseline_limits = individual.loc[
        individual["solver"] == "baseline", "timeout_limit_sec"
    ].dropna().unique()
    baseline_label = "Baseline"
    if len(baseline_limits) == 1:
        baseline_label += f" ({baseline_limits[0]:g}s external cap)"
    plt.plot(
        baseline["workload_size"],
        baseline["runtime_mean_sec_including_censored_observations"],
        marker="o",
        label=baseline_label,
    )
    for limit in cp_limits:
        group = runtime_summary[
            (runtime_summary["solver"] == "cp_sat")
            & (runtime_summary["time_limit_sec"] == limit)
        ]
        if not group.empty:
            plt.plot(
                group["workload_size"],
                group["runtime_mean_sec_including_censored_observations"],
                marker="o",
                label=f"CP-SAT {limit:g}s limit",
            )
    plt.title("Runtime by workload size and solver configuration")
    plt.xlabel("Submitted work orders")
    plt.ylabel("Observed wall time (seconds; timeouts are censored at cap)")
    plt.legend()
    save("runtime_vs_workload.png")

    values, labels = [], []
    for size in sorted(individual["workload_size"].dropna().unique()):
        baseline_values = individual[
            (individual["solver"] == "baseline")
            & (individual["workload_size"] == size)
        ]["execution_time_sec"].dropna().tolist()
        if baseline_values:
            values.append(baseline_values)
            labels.append(f"Baseline n={size}")
        for limit in cp_limits:
            cp_values = cp_rows[
                (cp_rows["workload_size"] == size)
                & (cp_rows["time_limit_sec"] == limit)
            ]["execution_time_sec"].dropna().tolist()
            if cp_values:
                values.append(cp_values)
                labels.append(f"CP {limit:g}s n={size}")
    plt.figure(figsize=(max(10, len(labels) * 0.6), 6))
    if values:
        plt.boxplot(values, tick_labels=labels, showfliers=True)
    plt.xticks(rotation=70, ha="right")
    plt.title("Observed runtime distributions by solver, workload, and limit")
    plt.xlabel("Solver configuration")
    plt.ylabel("Observed wall time (seconds; capped runs retained)")
    save("runtime_distribution.png")

    plt.figure(figsize=(9, 5))
    for solver_name, label in (("baseline", "Baseline"), ("cp_sat", "CP-SAT")):
        group = summary[summary["solver"] == solver_name]
        if not group.empty:
            plt.plot(
                group["workload_size"],
                group["mean_completeness_pct"],
                marker="o",
                label=label,
            )
    plt.ylim(0, 105)
    plt.title("Mean schedule completeness by workload size")
    plt.xlabel("Submitted work orders")
    plt.ylabel("Scheduled / submitted (%)")
    plt.legend()
    save("completeness_vs_workload.png")

    plt.figure(figsize=(9, 5))
    proof = summary[
        (summary["solver"] == "cp_sat")
        & summary["time_limit_sec"].notna()
    ]
    for limit in sorted(proof["time_limit_sec"].dropna().unique()):
        group = proof[proof["time_limit_sec"] == limit]
        plt.plot(
            group["workload_size"],
            100 * group["optimality_proof_rate"],
            marker="o",
            label=f"{limit:g}s",
        )
    plt.ylim(0, 105)
    plt.title("CP-SAT objective optimality proof rate by time limit")
    plt.xlabel("Submitted work orders")
    plt.ylabel("Runs with objective proof (%)")
    plt.legend(title="CP-SAT time limit")
    save("cpsat_optimality_proof_rate.png")

    plt.figure(figsize=(9, 5))
    for solver_name, label in (("baseline", "Baseline"), ("cp_sat", "CP-SAT")):
        group = summary[summary["solver"] == solver_name]
        if not group.empty:
            plt.plot(
                group["workload_size"],
                100 * group["full_schedule_success_rate"],
                marker="o",
                label=label,
            )
    plt.ylim(0, 105)
    plt.title("Full-schedule feasibility rate by workload size")
    plt.xlabel("Submitted work orders")
    plt.ylabel("Runs scheduling every submitted work order (%)")
    plt.legend()
    save("full_schedule_feasibility_rate.png")

    plt.figure(figsize=(9, 5))
    usable = paired[
        paired["objective_difference_cp_sat_minus_baseline"].notna()
    ]
    if not usable.empty:
        for proven, label, marker in (
            (True, "CP objective proven", "o"),
            (False, "CP objective unproven", "x"),
        ):
            group = usable[
                usable["cp_sat_optimality_proven"].astype(bool) == proven
            ]
            plt.scatter(
                group["baseline_runtime_sec"],
                group["objective_difference_cp_sat_minus_baseline"],
                marker=marker,
                label=label,
            )
    plt.axhline(0, color="black", linewidth=1)
    plt.title("Paired objective-score differences (CP-SAT minus baseline)")
    plt.xlabel("Baseline runtime (seconds)")
    plt.ylabel("Objective difference (lower is better; proof flags govern interpretation)")
    plt.legend()
    save("paired_objective_difference.png")


def run_task12(
    output_dir: Path = DEFAULT_OUTPUT,
    repetitions: int = DEFAULT_REPETITIONS,
    base_seed: int = DEFAULT_SEED,
    sizes: tuple[int, ...] = DEFAULT_SIZES,
    time_limits: tuple[float, ...] = DEFAULT_CP_SAT_LIMITS,
    baseline_timeout_seconds: float = DEFAULT_BASELINE_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    if repetitions < 1:
        raise ValueError("repetitions must be at least one")
    if not time_limits or any(
        not math.isfinite(limit) or limit <= 0 for limit in time_limits
    ):
        raise ValueError("CP-SAT time limits must be finite and positive")
    cpsat_solver._load_cp_sat()
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    _restore_previous_output_if_missing(output_dir)
    staging_dir = output_dir.parent / (
        f".{output_dir.name}.run-{uuid.uuid4().hex}"
    )
    staging_dir.mkdir()
    state_path = staging_dir / "run_state.json"
    run_state = {
        "status": "running",
        "output_dir": str(output_dir),
        "repetitions": repetitions,
        "base_seed": base_seed,
        "sizes": list(sizes),
        "time_limits": list(time_limits),
        "baseline_timeout_seconds": baseline_timeout_seconds,
        "completed_solver_rows": 0,
    }
    individual: list[dict[str, Any]] = []
    _write_json(state_path, run_state)

    def record_result(row: dict[str, Any]) -> None:
        individual.append(row)
        run_state["completed_solver_rows"] = len(individual)
        _write_csv(
            staging_dir / "individual_results.csv",
            individual,
            INDIVIDUAL_FIELDS,
        )
        _write_json(state_path, run_state)

    try:
        for size in sizes:
            for repetition in range(1, repetitions + 1):
                seed = base_seed + repetition - 1
                orders, trains, config, digest = build_seeded_instance(seed, size)
                order_label = (
                    "baseline_then_cp_sat"
                    if repetition % 2 == 1
                    else "cp_sat_then_baseline"
                )
                if repetition % 2 == 1:
                    baseline = run_baseline_bounded(
                        orders,
                        trains,
                        config,
                        size,
                        repetition,
                        seed,
                        digest,
                        baseline_timeout_seconds,
                        order_label,
                    )
                    record_result(baseline)
                for limit in time_limits:
                    record_result(
                        _run_cp_sat(
                            orders,
                            trains,
                            config,
                            size,
                            repetition,
                            seed,
                            digest,
                            limit,
                            order_label,
                        )
                    )
                if repetition % 2 == 0:
                    baseline = run_baseline_bounded(
                        orders,
                        trains,
                        config,
                        size,
                        repetition,
                        seed,
                        digest,
                        baseline_timeout_seconds,
                        order_label,
                    )
                    record_result(baseline)

        summaries = _rows_for_summary(individual)
        paired = _paired_rows(individual)
        constraint_rows = _constraint_equivalence_rows()
        exhaustive_rows = _exhaustive_validation_rows()
        _write_csv(
            staging_dir / "individual_results.csv",
            individual,
            INDIVIDUAL_FIELDS,
        )
        _write_csv(staging_dir / "summary_results.csv", summaries, SUMMARY_FIELDS)
        _write_csv(staging_dir / "paired_comparisons.csv", paired, PAIRED_FIELDS)
        _write_csv(
            staging_dir / "constraint_equivalence_results.csv",
            constraint_rows,
            CONSTRAINT_FIELDS,
        )
        _write_csv(
            staging_dir / "exhaustive_validation_results.csv",
            exhaustive_rows,
            EXHAUSTIVE_FIELDS,
        )
        _write_charts_from_csv(staging_dir)
        run_state["status"] = "completed"
        _write_json(state_path, run_state)
        previous_output = _publish_output_directory(staging_dir, output_dir)
    except BaseException as exc:
        run_state["status"] = "failed"
        run_state["error"] = f"{type(exc).__name__}: {exc}"
        try:
            _write_json(state_path, run_state)
        except Exception as checkpoint_error:
            exc.add_note(
                f"Could not update checkpoint state: {checkpoint_error}"
            )
        exc.add_note(f"Incremental run checkpoint retained at: {staging_dir}")
        raise

    return {
        "individual": individual,
        "summary": summaries,
        "paired": paired,
        "constraint_equivalence": constraint_rows,
        "exhaustive_validation": exhaustive_rows,
        "output_dir": str(output_dir),
        "previous_output_backup": (
            str(previous_output) if previous_output is not None else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--base-seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES)
    parser.add_argument(
        "--cpsat-time-limits",
        type=float,
        nargs="+",
        default=DEFAULT_CP_SAT_LIMITS,
    )
    parser.add_argument(
        "--baseline-timeout-seconds",
        type=float,
        default=DEFAULT_BASELINE_TIMEOUT_SECONDS,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run_task12(
        output_dir=args.output_dir,
        repetitions=args.repetitions,
        base_seed=args.base_seed,
        sizes=tuple(args.sizes),
        time_limits=tuple(args.cpsat_time_limits),
        baseline_timeout_seconds=args.baseline_timeout_seconds,
    )
    print(
        f"Created {len(result['individual'])} individual results, "
        f"{len(result['paired'])} paired comparisons, "
        f"{len(result['constraint_equivalence'])} constraint cases, and "
        f"{len(result['exhaustive_validation'])} exhaustive checks."
    )


if __name__ == "__main__":
    main()
