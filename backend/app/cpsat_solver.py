"""Experimental CP-SAT implementation for comparative scheduling benchmarks."""

from __future__ import annotations

import math
import time
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from . import solver_engine

_TIME_SCALE = 1_000_000
_BALANCE_SCALE = 1_000
_OBJECTIVE_SCALE = 9 * _BALANCE_SCALE**2 * 1_000_000


def _get(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _integer_ticks(value: float, scale: int, label: str) -> int:
    ticks = round(value * scale)
    if not math.isclose(value, ticks / scale, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"{label} must be representable at precision 1/{scale}")
    return int(ticks)


def _load_cp_sat():
    try:
        from ortools.sat.python import cp_model
    except ImportError as exc:
        raise RuntimeError(
            "The experimental CP-SAT solver requires backend/requirements-cpsat.txt"
        ) from exc
    return cp_model


def _extract_assignment(
    cp_solver: Any,
    present_vars: list[Any],
    candidate_vars: list[list[tuple[float, Any]]],
) -> dict[int, float]:
    assignment: dict[int, float] = {}
    for index, present in enumerate(present_vars):
        if cp_solver.BooleanValue(present):
            selected = [
                start
                for start, choice in candidate_vars[index]
                if cp_solver.BooleanValue(choice)
            ]
            if len(selected) != 1:
                raise RuntimeError("CP-SAT returned an invalid work-order assignment")
            assignment[index] = selected[0]
    return assignment


def _build_model(
    cp_model: Any,
    orders: list[dict[str, Any]],
    trains: list[dict[str, Any]],
    horizon: float,
    slot_size: float,
    config: Any,
):
    model = cp_model.CpModel()
    horizon_ticks = _integer_ticks(horizon, _TIME_SCALE, "time_horizon_hrs")

    raw_domains = [
        solver_engine._all_start_candidates(order["duration"], horizon, slot_size)
        for order in orders
    ]
    domains = [
        solver_engine._candidate_starts(order, trains, starts)
        for order, starts in zip(orders, raw_domains)
    ]
    raw_domain_count = sum(map(len, raw_domains))
    candidate_vars: list[list[tuple[float, Any]]] = []
    present_vars: list[Any] = []
    choice_vars_by_order: list[list[Any]] = []
    intervals_by_resource: dict[tuple[str, str, str], list[Any]] = defaultdict(list)

    for index, (order, starts) in enumerate(zip(orders, domains)):
        duration_ticks = _integer_ticks(
            order["duration"], _TIME_SCALE, f"duration for {order['work_id']}"
        )
        _integer_ticks(
            order["duration"],
            _BALANCE_SCALE,
            f"duration for objective workload balance ({order['work_id']})",
        )
        present = model.NewBoolVar(f"scheduled_{index}")
        start_var = model.NewIntVar(0, horizon_ticks, f"start_{index}")
        end_var = model.NewIntVar(
            0, max(horizon_ticks, duration_ticks), f"end_{index}"
        )
        choices: list[tuple[float, Any]] = []
        choice_vars = []
        weighted_starts = []
        for candidate_index, start in enumerate(starts):
            start_ticks = _integer_ticks(
                start, _TIME_SCALE, f"candidate start for {order['work_id']}"
            )
            choice = model.NewBoolVar(f"start_{index}_{candidate_index}")
            choices.append((start, choice))
            choice_vars.append(choice)
            weighted_starts.append(start_ticks * choice)

        model.Add(sum(choice_vars) == present)
        model.Add(start_var == sum(weighted_starts))
        model.Add(end_var == start_var + duration_ticks)
        interval = model.NewOptionalIntervalVar(
            start_var, duration_ticks, end_var, present, f"interval_{index}"
        )
        intervals_by_resource[
            (order["section_id"], order["track_line"], order["department"])
        ].append(interval)
        candidate_vars.append(choices)
        present_vars.append(present)
        choice_vars_by_order.append(choice_vars)

    for intervals in intervals_by_resource.values():
        if len(intervals) > 1:
            model.AddNoOverlap(intervals)

    for left in range(len(orders)):
        order_left = orders[left]
        for right in range(left + 1, len(orders)):
            order_right = orders[right]
            if (
                order_left["section_id"] != order_right["section_id"]
                or order_left["track_line"] != order_right["track_line"]
                or order_left["department"] == order_right["department"]
            ):
                continue
            for start_left, choice_left in candidate_vars[left]:
                for start_right, choice_right in candidate_vars[right]:
                    if not solver_engine._compatible(
                        left, start_left, right, start_right, orders
                    ):
                        model.AddBoolOr([choice_left.Not(), choice_right.Not()])

    co_location_groups: dict[
        tuple[str, str, float, float], list[Any]
    ] = defaultdict(list)
    for index, choices in enumerate(candidate_vars):
        order = orders[index]
        for start, choice in choices:
            key = (
                order["section_id"],
                order["track_line"],
                start,
                round(start + order["duration"], 6),
            )
            co_location_groups[key].append(choice)

    merge_vars = []
    for group_index, choices in enumerate(co_location_groups.values()):
        if len(choices) < 2:
            continue
        active = model.NewBoolVar(f"co_location_group_{group_index}")
        model.Add(sum(choices) >= active)
        for choice in choices:
            model.Add(active >= choice)
        merge_vars.append(sum(choices) - active)

    disruption_terms = []
    for index, choices in enumerate(candidate_vars):
        for start, choice in choices:
            cost = solver_engine._disruption_cost(index, start, orders, trains)
            disruption_terms.append(round(cost * _OBJECTIVE_SCALE) * choice)

    departments = sorted({order["department"] for order in orders})
    balance_terms = []
    for department_index, department in enumerate(departments):
        shift_loads = []
        duration_ticks = [
            _integer_ticks(
                order["duration"],
                _BALANCE_SCALE,
                f"duration for objective workload balance ({order['work_id']})",
            )
            for order in orders
        ]
        department_max = sum(
            duration_ticks[index]
            for index, order in enumerate(orders)
            if order["department"] == department
        )
        for shift in range(3):
            load = model.NewIntVar(
                0, department_max, f"load_{department_index}_{shift}"
            )
            load_terms = [
                duration_ticks[index] * choice
                for index, choices in enumerate(candidate_vars)
                if orders[index]["department"] == department
                for start, choice in choices
                if min(2, int(start // 8)) == shift
            ]
            model.Add(load == sum(load_terms))
            square = model.NewIntVar(
                0,
                department_max**2,
                f"load_square_{department_index}_{shift}",
            )
            model.AddMultiplicationEquality(square, [load, load])
            shift_loads.append((load, square))

        total_load = model.NewIntVar(
            0, department_max, f"department_total_{department_index}"
        )
        model.Add(total_load == sum(load for load, _ in shift_loads))
        total_square = model.NewIntVar(
            0, department_max**2, f"department_total_square_{department_index}"
        )
        model.AddMultiplicationEquality(total_square, [total_load, total_load])
        balance_terms.append(
            3 * sum(square for _, square in shift_loads) - total_square
        )

    balance_weight = float(_get(config, "workload_balance_weight", 0.1))
    co_location_reward = float(_get(config, "co_location_reward", 0.5))
    if not math.isfinite(balance_weight) or not math.isfinite(co_location_reward):
        raise ValueError("Objective weights must be finite")
    balance_coefficient = round(balance_weight * 1_000_000)
    merge_coefficient = round(co_location_reward * _OBJECTIVE_SCALE)
    objective = (
        sum(disruption_terms)
        + balance_coefficient * sum(balance_terms)
        - merge_coefficient * sum(merge_vars)
    )

    urgency_order = sorted(
        range(len(orders)),
        key=lambda index: (orders[index]["urgency"], orders[index]["work_id"]),
    )
    decision_vars = [
        variable
        for index in urgency_order
        for variable in (present_vars[index], *choice_vars_by_order[index])
    ]
    model.AddDecisionStrategy(
        decision_vars,
        cp_model.CHOOSE_FIRST,
        cp_model.SELECT_MAX_VALUE,
    )
    return (
        model,
        candidate_vars,
        present_vars,
        objective,
        raw_domain_count,
        sum(map(len, domains)),
    )


def solve_maintenance_schedule_cpsat(
    work_orders: Sequence[Any],
    train_schedules: Sequence[Any],
    config: Any,
) -> dict[str, Any]:
    """Solve using CP-SAT; this module is experimental and not used by the API."""
    started_at = time.perf_counter()
    (
        orders,
        trains,
        horizon,
        slot_size,
        _enable_ac3,
        _enable_annealing,
    ) = solver_engine._normalise_inputs(work_orders, train_schedules, config)
    submitted_ids = [order["work_id"] for order in orders]
    if not orders:
        return {
            "status": "no_work",
            "solver_outcome": "no_work",
            "schedule": [],
            "unscheduled_work_ids": [],
            "metrics": {
                "total_requests": 0,
                "scheduled_requests": 0,
                "solver_execution_time_sec": time.perf_counter() - started_at,
                "objective_score": None,
                "scaled_objective_value": None,
                "objective_integer_scale": _OBJECTIVE_SCALE,
            },
            "feasible_solution_found": False,
            "complete_schedule_proven_infeasible": False,
            "optimality_proven": False,
            "termination_reason": "NO_WORK",
            "cp_sat_status": "NOT_RUN",
            "search_stats": {},
            "peak_memory_mb": None,
        }

    cp_model = _load_cp_sat()
    time_limit = float(_get(config, "cpsat_time_limit_seconds", 30.0))
    if not math.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("cpsat_time_limit_seconds must be finite and greater than 0")
    (
        model,
        candidate_vars,
        present_vars,
        objective,
        raw_domain_count,
        domain_count,
    ) = _build_model(cp_model, orders, trains, horizon, slot_size, config)
    model.Maximize(sum(present_vars))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max(
        1e-9, time_limit - (time.perf_counter() - started_at)
    )
    solver.parameters.random_seed = int(_get(config, "random_seed", 7))
    solver.parameters.num_search_workers = 1
    solver.parameters.search_branching = cp_model.FIXED_SEARCH
    first_status = solver.Solve(model)
    first_status_name = solver.StatusName(first_status)
    total_branches = solver.NumBranches()
    total_conflicts = solver.NumConflicts()
    first_assignment: dict[int, float] = {}
    if first_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        first_assignment = _extract_assignment(solver, present_vars, candidate_vars)
    max_scheduled = len(first_assignment)
    coverage_proven = first_status == cp_model.OPTIMAL
    final_assignment = dict(first_assignment)
    final_status_name = first_status_name
    objective_proven = False
    scaled_objective_value = None

    if coverage_proven:
        model.Add(sum(present_vars) == max_scheduled)
        model.ClearObjective()
        model.Minimize(objective)
        remaining_time = time_limit - (time.perf_counter() - started_at)
        if remaining_time > 1e-9:
            objective_solver = cp_model.CpSolver()
            objective_solver.parameters.max_time_in_seconds = remaining_time
            objective_solver.parameters.random_seed = int(_get(config, "random_seed", 7))
            objective_solver.parameters.num_search_workers = 1
            objective_solver.parameters.search_branching = cp_model.FIXED_SEARCH
            objective_status = objective_solver.Solve(model)
            total_branches += objective_solver.NumBranches()
            total_conflicts += objective_solver.NumConflicts()
            final_status_name = objective_solver.StatusName(objective_status)
            if objective_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                final_assignment = _extract_assignment(
                    objective_solver, present_vars, candidate_vars
                )
                scaled_objective_value = objective_solver.ObjectiveValue()
            objective_proven = objective_status == cp_model.OPTIMAL
            solver = objective_solver
        else:
            final_status_name = "TIME_LIMIT_AFTER_COVERAGE_PROOF"

    if first_status == cp_model.MODEL_INVALID:
        raise RuntimeError(f"CP-SAT rejected the generated model: {solver.ResponseStats()}")

    scheduled_ids = {orders[index]["work_id"] for index in final_assignment}
    unscheduled_ids = [
        work_id for work_id in submitted_ids if work_id not in scheduled_ids
    ]
    if (
        len(scheduled_ids) != len(final_assignment)
        or len(scheduled_ids) + len(unscheduled_ids) != len(submitted_ids)
        or set(unscheduled_ids) & scheduled_ids
    ):
        raise RuntimeError("CP-SAT result does not account for work orders exactly once")

    windows: dict[tuple[str, str, float, float], list[str]] = defaultdict(list)
    for index, start in final_assignment.items():
        order = orders[index]
        windows[
            (
                order["section_id"],
                order["track_line"],
                start,
                round(start + order["duration"], 6),
            )
        ].append(order["work_id"])
    schedule = []
    for index, start in sorted(
        final_assignment.items(), key=lambda item: (item[1], orders[item[0]]["work_id"])
    ):
        order = orders[index]
        colocated = windows[
            (
                order["section_id"],
                order["track_line"],
                start,
                round(start + order["duration"], 6),
            )
        ]
        schedule.append(
            {
                "work_id": order["work_id"],
                "department": order["department"],
                "section_id": order["section_id"],
                "track_line": order["track_line"],
                "start_time_hr": round(start, 6),
                "end_time_hr": round(start + order["duration"], 6),
                "co_located_with": sorted(
                    work_id for work_id in colocated if work_id != order["work_id"]
                ),
                "heavy_equipment": order["heavy_equipment"],
            }
        )

    if final_assignment:
        objective_score = solver_engine._schedule_objective(
            final_assignment, orders, trains, config
        )
    else:
        objective_score = None

    complete_schedule_proven_infeasible = coverage_proven and max_scheduled < len(orders)
    if len(final_assignment) == len(orders):
        status = "success"
        outcome = "success"
    elif coverage_proven:
        status = "partial" if final_assignment else "unschedulable"
        outcome = "partial" if final_assignment else "unschedulable"
    elif first_status == cp_model.INFEASIBLE:
        status = "unschedulable"
        outcome = "unschedulable"
        complete_schedule_proven_infeasible = True
    else:
        status = "search_limit_reached"
        outcome = "search_limit_reached"

    return {
        "status": status,
        "solver_outcome": outcome,
        "schedule": schedule,
        "unscheduled_work_ids": unscheduled_ids,
        "metrics": {
            "total_requests": len(orders),
            "scheduled_requests": len(final_assignment),
            "solver_execution_time_sec": time.perf_counter() - started_at,
            "objective_score": objective_score,
            "scaled_objective_value": scaled_objective_value,
            "objective_integer_scale": _OBJECTIVE_SCALE,
            "candidate_domain_total_before_train_filtering": raw_domain_count,
            "candidate_domain_total_after_train_filtering": domain_count,
        },
        "feasible_solution_found": bool(final_assignment),
        "complete_schedule_proven_infeasible": complete_schedule_proven_infeasible,
        "optimality_proven": objective_proven,
        "termination_reason": (
            final_status_name
            if coverage_proven
            else first_status_name
        ),
        "cp_sat_status": final_status_name,
        "coverage_optimality_proven": coverage_proven,
        "search_stats": {
            "branches": total_branches,
            "conflicts": total_conflicts,
            "wall_time_sec": solver.WallTime(),
        },
        "peak_memory_mb": None,
    }
