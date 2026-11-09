"""Run baseline and experimental CP-SAT solvers on identical benchmark inputs."""

from __future__ import annotations

import argparse
import csv
import math
import platform
import statistics
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

from backend.app import cpsat_solver
from backend.benchmarks import runner

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "comparative_results"
DEFAULT_SIZES = (10, 25, 50, 100, 200)
DEFAULT_RUNS = 3
CP_SAT_TIME_LIMIT_SECONDS = 30.0
INDIVIDUAL_FIELDS = (
    "solver",
    "scenario_size",
    "run_index",
    "seed",
    "instance_sha256",
    "execution_time_sec",
    "total_work_orders",
    "scheduled_work_orders",
    "unscheduled_work_orders",
    "solver_outcome",
    "feasible_solution_found",
    "complete_schedule_found",
    "optimality_proven",
    "complete_schedule_proven_infeasible",
    "termination_reason",
    "cp_sat_status",
    "search_nodes",
    "search_conflicts",
    "objective_score",
    "peak_memory_mb",
    "ortools_version",
    "python_version",
    "platform",
)


def _baseline_row(
    result: dict[str, Any], scenario_size: int, run_index: int, seed: int
) -> dict[str, Any]:
    scheduled = result["scheduled_work_orders"]
    total = result["total_work_orders"]
    outcome = result["solver_outcome"]
    return {
        "solver": "baseline",
        "scenario_size": scenario_size,
        "run_index": run_index,
        "seed": seed,
        "instance_sha256": result["instance_sha256"],
        "execution_time_sec": result["execution_time_sec"],
        "total_work_orders": total,
        "scheduled_work_orders": scheduled,
        "unscheduled_work_orders": result["unscheduled_work_orders"],
        "solver_outcome": outcome,
        "feasible_solution_found": scheduled > 0,
        "complete_schedule_found": scheduled == total,
        "optimality_proven": False,
        "complete_schedule_proven_infeasible": outcome == "unschedulable",
        "termination_reason": (
            "NODE_LIMIT_REACHED"
            if result["search_limit_reached"]
            else outcome.upper()
        ),
        "cp_sat_status": "",
        "search_nodes": result["backtracking_nodes"] + result["astar_nodes"],
        "search_conflicts": "",
        "objective_score": result["objective_score"],
        "peak_memory_mb": None,
        "ortools_version": version("ortools"),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }


def _cpsat_row(
    orders: list[Any],
    trains: list[Any],
    config: dict[str, Any],
    scenario_size: int,
    run_index: int,
    seed: int,
    digest: str,
    time_limit_seconds: float,
) -> dict[str, Any]:
    cp_config = dict(config)
    cp_config["cpsat_time_limit_seconds"] = time_limit_seconds
    cpsat_solver._load_cp_sat()
    started = time.perf_counter()
    result = cpsat_solver.solve_maintenance_schedule_cpsat(
        orders, trains, cp_config
    )
    elapsed = time.perf_counter() - started
    scheduled = result["metrics"]["scheduled_requests"]
    total = result["metrics"]["total_requests"]
    stats = result["search_stats"]
    return {
        "solver": "cp_sat",
        "scenario_size": scenario_size,
        "run_index": run_index,
        "seed": seed,
        "instance_sha256": digest,
        "execution_time_sec": elapsed,
        "total_work_orders": total,
        "scheduled_work_orders": scheduled,
        "unscheduled_work_orders": len(result["unscheduled_work_ids"]),
        "solver_outcome": result["solver_outcome"],
        "feasible_solution_found": result["feasible_solution_found"],
        "complete_schedule_found": scheduled == total,
        "optimality_proven": result["optimality_proven"],
        "complete_schedule_proven_infeasible": result[
            "complete_schedule_proven_infeasible"
        ],
        "termination_reason": result["termination_reason"],
        "cp_sat_status": result["cp_sat_status"],
        "search_nodes": stats.get("branches"),
        "search_conflicts": stats.get("conflicts"),
        "objective_score": result["metrics"]["objective_score"],
        "peak_memory_mb": result["peak_memory_mb"],
        "ortools_version": version("ortools"),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for solver_name in ("baseline", "cp_sat"):
        sizes = sorted(
            {row["scenario_size"] for row in rows if row["solver"] == solver_name}
        )
        for size in sizes:
            group = [
                row
                for row in rows
                if row["solver"] == solver_name and row["scenario_size"] == size
            ]
            times = [float(row["execution_time_sec"]) for row in group]
            total = sum(row["total_work_orders"] for row in group)
            scheduled = sum(row["scheduled_work_orders"] for row in group)
            objectives = [
                float(row["objective_score"])
                for row in group
                if row["objective_score"] is not None
            ]
            summaries.append(
                {
                    "solver": solver_name,
                    "scenario_size": size,
                    "scenario_status": "executed",
                    "runs": len(group),
                    "execution_time_mean_sec": statistics.mean(times),
                    "execution_time_median_sec": statistics.median(times),
                    "execution_time_stdev_sec": statistics.pstdev(times),
                    "feasibility_rate": sum(
                        row["complete_schedule_found"] for row in group
                    ) / len(group),
                    "mean_scheduled_work_orders": statistics.mean(
                        row["scheduled_work_orders"] for row in group
                    ),
                    "mean_scheduling_completeness": scheduled / total if total else 0,
                    "optimality_proof_rate": sum(
                        row["optimality_proven"] for row in group
                    ) / len(group),
                    "mean_objective_score": (
                        statistics.mean(objectives) if objectives else None
                    ),
                    "search_limit_runs": sum(
                        row["solver_outcome"] == "search_limit_reached"
                        or row["termination_reason"] == "NODE_LIMIT_REACHED"
                        or row["cp_sat_status"] in ("FEASIBLE", "UNKNOWN")
                        for row in group
                    ),
                    "peak_memory_mb": None,
                    "unsupported_reason": "",
                }
            )
    return summaries


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = (
        "solver",
        "scenario_size",
        "scenario_status",
        "runs",
        "execution_time_mean_sec",
        "execution_time_median_sec",
        "execution_time_stdev_sec",
        "feasibility_rate",
        "mean_scheduled_work_orders",
        "mean_scheduling_completeness",
        "optimality_proof_rate",
        "mean_objective_score",
        "search_limit_runs",
        "peak_memory_mb",
        "unsupported_reason",
    )
    _write_csv(path, fields, rows)


def run_comparison(
    output_dir: Path = DEFAULT_OUTPUT,
    runs: int = DEFAULT_RUNS,
    seed: int = runner.DEFAULT_SEED,
    sizes: tuple[int, ...] = DEFAULT_SIZES,
    cpsat_time_limit_seconds: float = CP_SAT_TIME_LIMIT_SECONDS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if runs < 1:
        raise ValueError("runs must be at least one")
    if not math.isfinite(cpsat_time_limit_seconds) or cpsat_time_limit_seconds <= 0:
        raise ValueError("CP-SAT time limit must be finite and greater than 0")
    orders, trains, config = runner.build_instances(seed)
    available = len(orders)
    output_dir.mkdir(parents=True, exist_ok=True)
    individual: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []

    for size in sizes:
        if size > available:
            unsupported.append(
                {
                    "scenario_size": size,
                    "scenario_status": "unsupported",
                    "runs": 0,
                    "unsupported_reason": (
                        f"Existing generator provides only {available} distinct "
                        "work orders across configured routes."
                    ),
                }
            )
            continue
        scenario_orders = orders[:size]
        digest = runner.instance_digest(scenario_orders, trains, config)
        for run_index in range(1, runs + 1):
            baseline = runner.run_once(
                scenario_orders,
                trains,
                config,
                size,
                run_index,
                seed,
                digest,
            )
            cp_sat = _cpsat_row(
                scenario_orders,
                trains,
                config,
                size,
                run_index,
                seed,
                digest,
                cpsat_time_limit_seconds,
            )
            baseline_row = _baseline_row(baseline, size, run_index, seed)
            if baseline_row["instance_sha256"] != cp_sat["instance_sha256"]:
                raise RuntimeError("The two solvers did not use the same instance digest")
            individual.extend((baseline_row, cp_sat))

    summary = summarize_rows(individual)
    for row in unsupported:
        for solver_name in ("baseline", "cp_sat"):
            summary.append(
                {
                    "solver": solver_name,
                    **row,
                    "execution_time_mean_sec": "",
                    "execution_time_median_sec": "",
                    "execution_time_stdev_sec": "",
                    "feasibility_rate": "",
                    "mean_scheduled_work_orders": "",
                    "mean_scheduling_completeness": "",
                    "optimality_proof_rate": "",
                    "mean_objective_score": "",
                    "search_limit_runs": "",
                    "peak_memory_mb": "",
                }
            )
    summary.sort(key=lambda row: (row["scenario_size"], row["solver"]))
    _write_csv(
        output_dir / "comparison_individual_results.csv",
        INDIVIDUAL_FIELDS,
        individual,
    )
    _write_summary(
        output_dir / "comparison_summary_results.csv",
        summary,
    )
    return individual, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--seed", type=int, default=runner.DEFAULT_SEED)
    parser.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--cpsat-time-limit-seconds",
        type=float,
        default=CP_SAT_TIME_LIMIT_SECONDS,
    )
    args = parser.parse_args()
    rows, summaries = run_comparison(
        output_dir=args.output_dir,
        runs=args.runs,
        seed=args.seed,
        sizes=tuple(args.sizes),
        cpsat_time_limit_seconds=args.cpsat_time_limit_seconds,
    )
    print(
        f"Wrote {len(rows)} paired solver results and {len(summaries)} "
        f"summary rows to {args.output_dir}"
    )


if __name__ == "__main__":
    main()
