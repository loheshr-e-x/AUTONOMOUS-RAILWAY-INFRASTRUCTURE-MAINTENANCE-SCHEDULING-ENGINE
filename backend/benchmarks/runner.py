"""Benchmark the existing solver without changing its search behavior."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import random
import statistics
import sys
import time
from contextlib import ExitStack
from copy import deepcopy
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any
from unittest.mock import patch

from backend.app import data_engine, solver_engine

DEFAULT_SIZES = (10, 25, 50, 100, 200)
DEFAULT_RUNS = 3
DEFAULT_SEED = 20261030
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "results"

INDIVIDUAL_FIELDS = (
    "scenario_size",
    "run_index",
    "seed",
    "instance_sha256",
    "execution_time_sec",
    "total_work_orders",
    "scheduled_work_orders",
    "unscheduled_work_orders",
    "solver_outcome",
    "backtracking_nodes",
    "astar_nodes",
    "candidate_domain_size_before_filtering",
    "candidate_domain_size_after_train_filtering",
    "candidate_domain_size_after_ac3",
    "ac3_pruned_candidates",
    "search_limit_reached",
    "backtracking_limit_reached",
    "astar_limit_reached",
    "objective_score",
    "cold_start",
    "python_version",
    "platform",
    "machine",
    "processor",
    "cpu_count",
    "dependency_versions",
)


def build_instances(seed: int = DEFAULT_SEED) -> tuple[list[Any], list[Any], Any]:
    """Return all available deterministic project work orders and train windows."""
    route_ids = tuple(data_engine.ROUTES)
    work_orders = [
        order
        for route_id in route_ids
        for order in data_engine.get_maintenance_work_orders(route_id)
    ]
    random.Random(seed).shuffle(work_orders)
    trains = [
        train
        for route_id in route_ids
        for train in data_engine.get_train_schedules(route_id)
    ]
    config = {
        "section_ids": sorted(
            section
            for route in data_engine.ROUTES.values()
            for section in route.section_ids
        ),
        "time_horizon_hrs": 24,
        "slot_duration_hrs": 0.5,
        "train_clearance_hrs": 0.0,
        "enable_ac3_pruning": True,
        "enable_simulated_annealing": True,
        "max_search_nodes": 100_000,
        "annealing_iterations": 500,
        "annealing_initial_temperature": 2.0,
        "annealing_cooling_rate": 0.995,
        "workload_balance_weight": 0.1,
        "co_location_reward": 0.5,
        "random_seed": seed,
    }
    return work_orders, trains, config


def instance_digest(
    orders: list[Any], trains: list[Any], config: dict[str, Any]
) -> str:
    payload = {
        "orders": [item.model_dump(mode="json") for item in orders],
        "trains": [item.model_dump(mode="json") for item in trains],
        "config": config,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def dependency_versions() -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for package in ("fastapi", "pydantic", "pytest", "matplotlib", "ortools"):
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = None
    return result


def run_once(
    orders: list[Any],
    trains: list[Any],
    config: dict[str, Any],
    scenario_size: int,
    run_index: int,
    seed: int,
    digest: str,
    include_work_order_ids: bool = False,
) -> dict[str, Any]:
    """Instrument calls around the unchanged solver and return one CSV row."""
    counts = {
        "domain_before": 0,
        "domain_after_train": 0,
        "domain_after_ac3": 0,
        "ac3_pruned": 0,
        "backtracking_nodes": 0,
        "astar_nodes": 0,
        "astar_limit_reached": False,
        "backtracking_limit_reached": False,
    }
    original_candidates = solver_engine._all_start_candidates
    original_filtered = solver_engine._candidate_starts
    original_ac3 = solver_engine._ac3
    original_backtracking = solver_engine._backtracking_search
    original_astar = solver_engine._a_star_search

    def candidates(*args: Any, **kwargs: Any) -> Any:
        result = original_candidates(*args, **kwargs)
        counts["domain_before"] += len(result)
        return result

    def filtered(*args: Any, **kwargs: Any) -> Any:
        result = original_filtered(*args, **kwargs)
        counts["domain_after_train"] += len(result)
        return result

    def ac3(domains: list[list[float]], *args: Any, **kwargs: Any) -> Any:
        before = sum(map(len, domains))
        result = original_ac3(domains, *args, **kwargs)
        after = sum(map(len, domains))
        counts["ac3_pruned"] += before - after
        counts["domain_after_ac3"] += after
        return result

    def backtracking(*args: Any, **kwargs: Any) -> Any:
        result = original_backtracking(*args, **kwargs)
        counts["backtracking_nodes"] += result.explored_nodes
        counts["backtracking_limit_reached"] |= result.limit_reached
        return result

    def astar(*args: Any, **kwargs: Any) -> Any:
        assignment, expanded = original_astar(*args, **kwargs)
        counts["astar_nodes"] += expanded
        call_limit = (
            args[4]
            if len(args) > 4
            else kwargs.get("node_limit", config.get("max_search_nodes", 100_000))
        )
        counts["astar_limit_reached"] |= expanded >= max(1, int(call_limit))
        return assignment, expanded

    input_orders = deepcopy(orders)
    input_trains = deepcopy(trains)
    input_config = deepcopy(config)
    started = time.perf_counter()
    with ExitStack() as stack:
        stack.enter_context(patch.object(solver_engine, "_all_start_candidates", candidates))
        stack.enter_context(patch.object(solver_engine, "_candidate_starts", filtered))
        stack.enter_context(patch.object(solver_engine, "_ac3", ac3))
        stack.enter_context(patch.object(solver_engine, "_backtracking_search", backtracking))
        stack.enter_context(patch.object(solver_engine, "_a_star_search", astar))
        result = solver_engine.solve_maintenance_schedule(
            input_orders, input_trains, input_config
        )
    elapsed = time.perf_counter() - started

    submitted_ids = [item.work_id for item in orders]
    scheduled_ids = [item["work_id"] for item in result["schedule"]]
    unscheduled_ids = result["unscheduled_work_ids"]
    if (
        len(scheduled_ids) != len(set(scheduled_ids))
        or len(unscheduled_ids) != len(set(unscheduled_ids))
        or set(scheduled_ids) & set(unscheduled_ids)
        or set(scheduled_ids) | set(unscheduled_ids) != set(submitted_ids)
        or len(scheduled_ids) + len(unscheduled_ids) != len(submitted_ids)
    ):
        raise ValueError("Solver result does not account for submitted work orders exactly once")

    normalized_orders, normalized_trains, *_ = solver_engine._normalise_inputs(
        orders, trains, config
    )
    index_by_id = {item["work_id"]: index for index, item in enumerate(normalized_orders)}
    assignment = {
        index_by_id[item["work_id"]]: item["start_time_hr"]
        for item in result["schedule"]
    }
    objective = (
        solver_engine._schedule_objective(
            assignment, normalized_orders, normalized_trains, config
        )
        if assignment
        else None
    )
    backtracking_cutoff = bool(counts["backtracking_limit_reached"])
    astar_cutoff = bool(counts["astar_limit_reached"])
    row = {
        "scenario_size": scenario_size,
        "run_index": run_index,
        "seed": seed,
        "instance_sha256": digest,
        "execution_time_sec": elapsed,
        "total_work_orders": len(submitted_ids),
        "scheduled_work_orders": len(scheduled_ids),
        "unscheduled_work_orders": len(unscheduled_ids),
        "solver_outcome": result["solver_outcome"],
        "backtracking_nodes": counts["backtracking_nodes"],
        "astar_nodes": counts["astar_nodes"],
        "candidate_domain_size_before_filtering": counts["domain_before"],
        "candidate_domain_size_after_train_filtering": counts["domain_after_train"],
        "candidate_domain_size_after_ac3": (
            counts["domain_after_ac3"] if input_config["enable_ac3_pruning"] else None
        ),
        "ac3_pruned_candidates": (
            counts["ac3_pruned"] if input_config["enable_ac3_pruning"] else None
        ),
        "search_limit_reached": (
            True
            if (
                backtracking_cutoff
                or astar_cutoff
                or result["solver_outcome"] == "search_limit_reached"
            )
            else False
        ),
        "backtracking_limit_reached": backtracking_cutoff,
        "astar_limit_reached": astar_cutoff,
        "objective_score": objective,
        "cold_start": False,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": __import__("os").cpu_count(),
        "dependency_versions": json.dumps(dependency_versions(), sort_keys=True),
    }
    if include_work_order_ids:
        row["scheduled_work_ids"] = scheduled_ids
        row["unscheduled_work_ids"] = unscheduled_ids
    return row


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    sizes = sorted({row["scenario_size"] for row in rows})
    for size in sizes:
        group = [row for row in rows if row["scenario_size"] == size]
        timings = [float(row["execution_time_sec"]) for row in group]
        total = sum(row["total_work_orders"] for row in group)
        scheduled = sum(row["scheduled_work_orders"] for row in group)
        summaries.append(
            {
                "scenario_size": size,
                "scenario_status": "executed",
                "runs": len(group),
                "execution_time_mean_sec": statistics.mean(timings),
                "execution_time_median_sec": statistics.median(timings),
                "execution_time_stdev_sec": statistics.pstdev(timings),
                "feasibility_rate": sum(row["solver_outcome"] == "success" for row in group)
                / len(group),
                "mean_scheduling_completeness": scheduled / total if total else 0.0,
                "search_limit_runs": sum(row["search_limit_reached"] for row in group),
                "unsupported_reason": "",
            }
        )
    return summaries


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = (
        "scenario_size",
        "scenario_status",
        "runs",
        "execution_time_mean_sec",
        "execution_time_median_sec",
        "execution_time_stdev_sec",
        "feasibility_rate",
        "mean_scheduling_completeness",
        "search_limit_runs",
        "unsupported_reason",
    )
    _write_csv(path, fields, rows)


def _write_svg(path: Path, title: str, ylabel: str, points: list[tuple[int, float]]) -> None:
    width, height = 800, 480
    left, right, top, bottom = 90, 30, 55, 75
    chart_w, chart_h = width - left - right, height - top - bottom
    ymax = max((value for _, value in points), default=1.0) or 1.0
    xmin = min((size for size, _ in points), default=0)
    xmax = max((size for size, _ in points), default=1)

    def x(size: int) -> float:
        return left + ((size - xmin) / max(1, xmax - xmin)) * chart_w

    def y(value: float) -> float:
        return top + chart_h - (value / ymax) * chart_h

    polyline = " ".join(f"{x(size):.1f},{y(value):.1f}" for size, value in points)
    circles = "\n".join(
        f'<circle cx="{x(size):.1f}" cy="{y(value):.1f}" r="5" />'
        for size, value in points
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white"/>
<text x="{width/2}" y="28" text-anchor="middle" font-family="sans-serif" font-size="18">{title}</text>
<line x1="{left}" y1="{top}" x2="{left}" y2="{top+chart_h}" stroke="black"/>
<line x1="{left}" y1="{top+chart_h}" x2="{left+chart_w}" y2="{top+chart_h}" stroke="black"/>
<polyline points="{polyline}" fill="none" stroke="#2463a6" stroke-width="3"/>
{circles}
<text x="{left+chart_w/2}" y="{height-20}" text-anchor="middle" font-family="sans-serif" font-size="14">Work orders</text>
<text x="20" y="{top+chart_h/2}" transform="rotate(-90 20 {top+chart_h/2})" text-anchor="middle" font-family="sans-serif" font-size="14">{ylabel}</text>
{"".join(f'<text x="{x(size):.1f}" y="{top+chart_h+24}" text-anchor="middle" font-family="sans-serif" font-size="12">{size}</text>' for size, _ in points)}
</svg>"""
    path.write_text(svg, encoding="utf-8")


def run_benchmarks(
    output_dir: Path = DEFAULT_OUTPUT,
    runs: int = DEFAULT_RUNS,
    seed: int = DEFAULT_SEED,
    sizes: tuple[int, ...] = DEFAULT_SIZES,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if runs < 1:
        raise ValueError("runs must be at least one")
    orders, trains, config = build_instances(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    available = len(orders)
    rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for size in sizes:
        if size > available:
            summaries.append(
                {
                    "scenario_size": size,
                    "scenario_status": "unsupported",
                    "runs": 0,
                    "execution_time_mean_sec": "",
                    "execution_time_median_sec": "",
                    "execution_time_stdev_sec": "",
                    "feasibility_rate": "",
                    "mean_scheduling_completeness": "",
                    "search_limit_runs": "",
                    "unsupported_reason": (
                        f"Existing generator provides only {available} distinct "
                        "work orders across configured routes; no extra data generated."
                    ),
                }
            )
            continue
        scenario_orders = orders[:size]
        digest = instance_digest(scenario_orders, trains, config)
        rows.extend(
            run_once(
                scenario_orders,
                trains,
                config,
                size,
                run_index,
                seed,
                digest,
            )
            for run_index in range(1, runs + 1)
        )

    summaries.extend(summarize_rows(rows))
    summaries.sort(key=lambda row: row["scenario_size"])
    _write_csv(output_dir / "individual_results.csv", INDIVIDUAL_FIELDS, rows)
    _write_summary_csv(output_dir / "summary_results.csv", summaries)

    executed = [row for row in summaries if row["scenario_status"] == "executed"]
    _write_svg(
        output_dir / "execution_time.svg",
        "Mean solver execution time",
        "Seconds",
        [(row["scenario_size"], row["execution_time_mean_sec"]) for row in executed],
    )
    _write_svg(
        output_dir / "feasibility_rate.svg",
        "Feasibility rate (solver success outcomes)",
        "Rate",
        [(row["scenario_size"], row["feasibility_rate"]) for row in executed],
    )
    _write_svg(
        output_dir / "scheduling_completeness.svg",
        "Mean scheduling completeness",
        "Scheduled / submitted",
        [(row["scenario_size"], row["mean_scheduling_completeness"]) for row in executed],
    )
    return rows, summaries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES)
    args = parser.parse_args()
    rows, summaries = run_benchmarks(
        output_dir=args.output_dir,
        runs=args.runs,
        seed=args.seed,
        sizes=tuple(args.sizes),
    )
    print(f"Wrote {len(rows)} individual runs and {len(summaries)} summary rows to {args.output_dir}")
    for summary in summaries:
        print(
            f"{summary['scenario_size']}: {summary['scenario_status']} "
            f"({summary['runs']} runs)"
        )


if __name__ == "__main__":
    main()
