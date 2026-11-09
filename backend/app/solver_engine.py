"""Constraint-based maintenance block scheduling."""

from __future__ import annotations

import heapq
import math
import random
import time
from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import count
from typing import Any


def _get(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _overlaps(start_a: float, end_a: float, start_b: float, end_b: float) -> bool:
    return start_a < end_b and start_b < end_a


def _get_track_line(value: Any) -> str:
    return str(_enum_value(_get(value, "track_line", "DOWN_LINE")))


# Local-time weighting: daylight closures (06:00-22:00) hurt most, the
# 01:00-05:00 night window is free, the remaining hours are a mild shoulder.
_DAYLIGHT_START, _DAYLIGHT_END = 6.0, 22.0
_NIGHT_START, _NIGHT_END = 1.0, 5.0
_DAYLIGHT_WEIGHT, _SHOULDER_WEIGHT = 1.0, 0.25


def _time_of_day_cost(start: float, end: float) -> float:
    """Per-hour penalty integrated over [start, end): daylight > shoulder > night."""
    daylight = max(0.0, min(end, _DAYLIGHT_END) - max(start, _DAYLIGHT_START))
    night = max(0.0, min(end, _NIGHT_END) - max(start, _NIGHT_START))
    shoulder = (end - start) - daylight - night
    return _DAYLIGHT_WEIGHT * daylight + _SHOULDER_WEIGHT * shoulder


def _work_order_value(work_order: Any, name: str) -> Any:
    value = _get(work_order, name)
    if value is None:
        raise ValueError(f"Work order is missing required field '{name}'")
    return _enum_value(value)


def _normalise_inputs(
    work_orders: Sequence[Any],
    train_schedules: Sequence[Any],
    config: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float, float, bool, bool]:
    horizon = float(_get(config, "time_horizon_hrs", 24))
    if not math.isfinite(horizon) or not 0 < horizon <= 24:
        raise ValueError("time_horizon_hrs must be greater than 0 and no more than 24")

    slot_size = float(_get(config, "slot_duration_hrs", 0.5))
    if not math.isfinite(slot_size) or slot_size <= 0:
        raise ValueError("slot_duration_hrs must be greater than 0")

    orders: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for source in work_orders:
        work_id = str(_work_order_value(source, "work_id"))
        if work_id in seen_ids:
            raise ValueError(f"Duplicate work_id: {work_id}")
        seen_ids.add(work_id)

        duration = float(_work_order_value(source, "duration_hrs"))
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError(f"Work order {work_id} has an invalid duration")

        orders.append(
            {
                "work_id": work_id,
                "department": str(_work_order_value(source, "department")),
                "section_id": str(_work_order_value(source, "section_id")),
                "track_line": str(_get_track_line(source)),
                "heavy_equipment": bool(_get(source, "heavy_equipment", False)),
                "duration": duration,
                "urgency": int(_work_order_value(source, "urgency")),
                "co_location_allowed": bool(
                    _get(source, "co_location_allowed", True)
                ),
            }
        )

    trains: list[dict[str, Any]] = []
    clearance = float(_get(config, "train_clearance_hrs", 0.0))
    if not math.isfinite(clearance) or clearance < 0:
        raise ValueError("train_clearance_hrs cannot be negative")
    for source in train_schedules:
        start = float(_get(source, "start_time_hr"))
        end = float(_get(source, "end_time_hr"))
        if not math.isfinite(start) or not math.isfinite(end) or end <= start:
            raise ValueError("Train occupancy windows must have end_time_hr > start_time_hr")
        trains.append(
            {
                "section_id": str(_get(source, "section_id")),
                "track_line": str(_get_track_line(source)),
                "start": max(0.0, start - clearance),
                "end": min(horizon, end + clearance),
            }
        )

    configured_sections = _get(config, "section_ids")
    if configured_sections is not None:
        selected_sections = {str(section_id) for section_id in configured_sections}
        out_of_scope = sorted(
            order["section_id"]
            for order in orders
            if order["section_id"] not in selected_sections
        )
        if out_of_scope:
            raise ValueError(
                "Work orders contain sections outside config.section_ids: "
                + ", ".join(sorted(set(out_of_scope)))
            )

    return (
        orders,
        trains,
        horizon,
        slot_size,
        bool(_get(config, "enable_ac3_pruning", True)),
        bool(_get(config, "enable_simulated_annealing", True)),
    )


def _all_start_candidates(
    duration: float, horizon: float, slot_size: float
) -> list[float]:
    latest_start = horizon - duration
    if latest_start < -1e-9:
        return []

    starts = []
    step_count = int(math.floor(latest_start / slot_size + 1e-9))
    for step in range(step_count + 1):
        starts.append(round(step * slot_size, 6))
    if not starts or latest_start - starts[-1] > 1e-9:
        starts.append(round(latest_start, 6))
    return starts


def _candidate_starts(
    order: dict[str, Any],
    trains: list[dict[str, Any]],
    starts: list[float],
) -> list[float]:
    return [
        start
        for start in starts
        if not any(
            train["section_id"] == order["section_id"]
            and (
                train["track_line"] == order["track_line"]
                # Heavy equipment also needs the adjacent track line clear.
                or (
                    order["heavy_equipment"]
                    and train["track_line"] != order["track_line"]
                )
            )
            and _overlaps(
                start,
                start + order["duration"],
                train["start"],
                train["end"],
            )
            for train in trains
        )
    ]


def _can_co_locate(order_a: dict[str, Any], order_b: dict[str, Any]) -> bool:
    return (
        order_a["section_id"] == order_b["section_id"]
        and order_a["track_line"] == order_b["track_line"]
        and order_a["department"] != order_b["department"]
        and order_a["co_location_allowed"]
        and order_b["co_location_allowed"]
    )


def _compatible(
    index_a: int,
    start_a: float,
    index_b: int,
    start_b: float,
    orders: list[dict[str, Any]],
) -> bool:
    order_a, order_b = orders[index_a], orders[index_b]
    if order_a["section_id"] != order_b["section_id"]:
        return True
    if order_a["track_line"] != order_b["track_line"]:
        return True
    end_a = start_a + order_a["duration"]
    end_b = start_b + order_b["duration"]
    if not _overlaps(start_a, end_a, start_b, end_b):
        return True

    same_department = order_a["department"] == order_b["department"]
    same_window = abs(start_a - start_b) < 1e-9 and abs(end_a - end_b) < 1e-9
    if same_department:
        return False
    return same_window and _can_co_locate(order_a, order_b)


def _ac3(
    domains: list[list[float]],
    orders: list[dict[str, Any]],
) -> None:
    neighbors: dict[int, list[int]] = defaultdict(list)
    for left in range(len(orders)):
        for right in range(left + 1, len(orders)):
            a, b = orders[left], orders[right]
            if a["track_line"] != b["track_line"]:
                continue
            if a["section_id"] == b["section_id"]:
                neighbors[left].append(right)
                neighbors[right].append(left)

    queue = deque(
        (left, right) for left, adjacent in neighbors.items() for right in adjacent
    )
    while queue:
        left, right = queue.popleft()
        revised = [
            start_left
            for start_left in domains[left]
            if any(
                _compatible(left, start_left, right, start_right, orders)
                for start_right in domains[right]
            )
        ]
        if len(revised) == len(domains[left]):
            continue
        domains[left] = revised
        if not revised:
            return
        queue.extend((other, left) for other in neighbors[left] if other != right)


def _disruption_cost(
    index: int,
    start: float,
    orders: list[dict[str, Any]],
    trains: list[dict[str, Any]],
) -> float:
    order = orders[index]
    end = start + order["duration"]
    cost = _time_of_day_cost(start, end)
    for train in trains:
        if (
            train["section_id"] != order["section_id"]
            or train["track_line"] != order["track_line"]
        ):
            continue
        gap = train["start"] - end if train["start"] >= end else start - train["end"]
        if 0 <= gap < 2.0:
            cost += (2.0 - gap) / 2.0
    return cost


def _available_starts(
    index: int,
    domains: list[list[float]],
    assignment: dict[int, float],
    orders: list[dict[str, Any]],
) -> list[float]:
    return [
        start
        for start in domains[index]
        if all(
            _compatible(index, start, assigned_index, assigned_start, orders)
            for assigned_index, assigned_start in assignment.items()
        )
    ]


def _mrv_variable(
    unassigned: set[int],
    domains: list[list[float]],
    assignment: dict[int, float],
    orders: list[dict[str, Any]],
) -> tuple[int, list[float]]:
    options = [
        (index, _available_starts(index, domains, assignment, orders))
        for index in unassigned
    ]
    return min(
        options,
        key=lambda item: (
            len(item[1]),
            orders[item[0]]["urgency"],
            orders[item[0]]["work_id"],
        ),
    )


@dataclass(frozen=True)
class _BacktrackingResult:
    assignment: dict[int, float] | None
    complete: bool
    exhausted: bool
    limit_reached: bool
    explored_nodes: int


def _backtracking_search(
    domains: list[list[float]],
    orders: list[dict[str, Any]],
    trains: list[dict[str, Any]],
    node_limit: int,
) -> _BacktrackingResult:
    nodes = 0

    def search(
        assignment: dict[int, float], unassigned: set[int]
    ) -> tuple[dict[int, float] | None, bool, bool]:
        nonlocal nodes
        if not unassigned:
            return assignment, True, False
        if nodes >= node_limit:
            return None, False, True
        nodes += 1

        index, options = _mrv_variable(unassigned, domains, assignment, orders)
        options.sort(
            key=lambda start: (
                _disruption_cost(index, start, orders, trains),
                start,
            )
        )
        for start in options:
            next_assignment = dict(assignment)
            next_assignment[index] = start
            result, exhausted, limit_reached = search(
                next_assignment, unassigned - {index}
            )
            if result is not None:
                return result, False, False
            if limit_reached:
                return None, False, True
            if not exhausted:
                return None, False, False
        return None, True, False

    assignment, exhausted, limit_reached = search({}, set(range(len(orders))))
    return _BacktrackingResult(
        assignment=assignment,
        complete=assignment is not None,
        exhausted=exhausted,
        limit_reached=limit_reached,
        explored_nodes=nodes,
    )


def _a_star_search(
    domains: list[list[float]],
    orders: list[dict[str, Any]],
    trains: list[dict[str, Any]],
    initial: dict[int, float],
    node_limit: int,
) -> tuple[dict[int, float], int]:
    """Search feasible assignments by f(n)=disruption-so-far+critical-work heuristic."""
    if not orders:
        return {}, 0

    serial = count()
    start_state: tuple[tuple[int, float], ...] = ()
    critical = sum(order["urgency"] == 1 for order in orders)
    frontier: list[tuple[float, float, int, tuple[tuple[int, float], ...]]] = [
        (float(critical), 0.0, next(serial), start_state)
    ]
    best_cost = sum(
        _disruption_cost(index, start, orders, trains)
        for index, start in initial.items()
    )
    best_assignment = dict(initial)
    visited: dict[tuple[tuple[int, float], ...], float] = {start_state: 0.0}
    expanded = 0

    while frontier and expanded < node_limit:
        _, g_cost, _, state = heapq.heappop(frontier)
        if g_cost > visited.get(state, math.inf):
            continue
        assignment = dict(state)
        if len(assignment) == len(orders):
            if g_cost < best_cost:
                best_cost = g_cost
                best_assignment = assignment
            continue
        expanded += 1

        unassigned = set(range(len(orders))) - assignment.keys()
        index, options = _mrv_variable(unassigned, domains, assignment, orders)
        options.sort(
            key=lambda start: (
                _disruption_cost(index, start, orders, trains),
                start,
            )
        )
        for start in options:
            next_cost = g_cost + _disruption_cost(index, start, orders, trains)
            next_state = tuple(sorted((*state, (index, start))))
            if next_cost >= visited.get(next_state, math.inf):
                continue
            visited[next_state] = next_cost
            remaining_critical = sum(
                orders[remaining]["urgency"] == 1
                for remaining in unassigned
                if remaining != index
            )
            heuristic = float(remaining_critical) + sum(
                min(
                    (
                        _time_of_day_cost(s, s + orders[r]["duration"])
                        for s in domains[r]
                    ),
                    default=0.0,
                )
                for r in unassigned
                if r != index
            )
            heapq.heappush(
                frontier,
                (
                    next_cost + heuristic,
                    next_cost,
                    next(serial),
                    next_state,
                ),
            )

    return best_assignment, expanded


def _is_valid_schedule(
    assignment: dict[int, float], orders: list[dict[str, Any]]
) -> bool:
    return all(
        _compatible(left, start_left, right, start_right, orders)
        for left, start_left in assignment.items()
        for right, start_right in assignment.items()
        if left < right
    )


def _schedule_objective(
    assignment: dict[int, float],
    orders: list[dict[str, Any]],
    trains: list[dict[str, Any]],
    config: Any,
) -> float:
    cost = sum(
        _disruption_cost(index, start, orders, trains)
        for index, start in assignment.items()
    )

    shift_loads: dict[tuple[str, int], float] = defaultdict(float)
    for index, start in assignment.items():
        order = orders[index]
        shift = min(2, int(start // 8))
        shift_loads[(order["department"], shift)] += order["duration"]
    departments = {order["department"] for order in orders}
    imbalance = 0.0
    for department in departments:
        loads = [shift_loads[(department, shift)] for shift in range(3)]
        mean = sum(loads) / len(loads)
        imbalance += sum((load - mean) ** 2 for load in loads) / len(loads)

    windows: dict[tuple[str, str, float, float], list[int]] = defaultdict(list)
    for index, start in assignment.items():
        order = orders[index]
        windows[
            (
                order["section_id"],
                order["track_line"],
                start,
                round(start + order["duration"], 6),
            )
        ].append(index)
    merges = sum(len(group) - 1 for group in windows.values() if len(group) > 1)

    return (
        cost
        + float(_get(config, "workload_balance_weight", 0.1)) * imbalance
        - float(_get(config, "co_location_reward", 0.5)) * merges
    )


def _simulated_annealing(
    initial: dict[int, float],
    domains: list[list[float]],
    orders: list[dict[str, Any]],
    trains: list[dict[str, Any]],
    config: Any,
) -> dict[int, float]:
    current = dict(initial)
    if len(current) < 2:
        return current

    best = dict(current)
    current_cost = _schedule_objective(current, orders, trains, config)
    best_cost = current_cost
    rng = random.Random(int(_get(config, "random_seed", 7)))
    iterations = max(0, int(_get(config, "annealing_iterations", 500)))
    initial_temperature = max(
        1e-6, float(_get(config, "annealing_initial_temperature", 2.0))
    )
    cooling_rate = float(_get(config, "annealing_cooling_rate", 0.995))
    cooling_rate = min(0.9999, max(0.8, cooling_rate))

    for iteration in range(iterations):
        index = rng.choice(tuple(current))
        candidates = domains[index]
        if len(candidates) < 2:
            continue
        new_start = rng.choice(candidates)
        if new_start == current[index]:
            continue

        neighbor = dict(current)
        neighbor[index] = new_start
        if not _is_valid_schedule(neighbor, orders):
            continue

        neighbor_cost = _schedule_objective(neighbor, orders, trains, config)
        temperature = initial_temperature * (cooling_rate**iteration)
        delta = neighbor_cost - current_cost
        if delta < 0 or rng.random() < math.exp(-delta / temperature):
            current = neighbor
            current_cost = neighbor_cost
            if current_cost < best_cost:
                best = dict(current)
                best_cost = current_cost

    return best


def _partial_schedule(
    domains: list[list[float]],
    orders: list[dict[str, Any]],
    trains: list[dict[str, Any]],
) -> dict[int, float]:
    assignment: dict[int, float] = {}
    remaining = set(range(len(orders)))
    while remaining:
        index, options = _mrv_variable(remaining, domains, assignment, orders)
        if options:
            start = min(
                options,
                key=lambda candidate: (
                    _disruption_cost(index, candidate, orders, trains),
                    candidate,
                ),
            )
            assignment[index] = start
        remaining.remove(index)
    return assignment


def solve_maintenance_schedule(
    work_orders: Sequence[Any],
    train_schedules: Sequence[Any],
    config: Any,
) -> dict[str, Any]:
    """Return a schema-compatible block schedule using CSP, A*, and local search."""
    started_at = time.perf_counter()
    (
        orders,
        trains,
        horizon,
        slot_size,
        enable_ac3,
        enable_annealing,
    ) = _normalise_inputs(work_orders, train_schedules, config)

    if not orders:
        return {
            "status": "no_work",
            "solver_outcome": "no_work",
            "schedule": [],
            "unscheduled_work_ids": [],
            "metrics": {
                "total_requests": 0,
                "scheduled_requests": 0,
                "search_space_pruned_pct": 0.0,
                "fol_rule_compliance_pct": None,
                "co_location_merges_count": 0,
                "solver_execution_time_sec": round(time.perf_counter() - started_at, 6),
            },
            "audit_trail": [],
        }

    search_limit = max(1, int(_get(config, "max_search_nodes", 100000)))
    assignment: dict[int, float] = {}
    search_limit_reached = False
    infeasibility_proven = False
    initial_domain_size = 0
    filtered_domain_size_total = 0
    remaining_domain_size = 0
    ac3_pruned_count = 0
    domains_nonempty_after_ac3: bool | None = True if orders else None
    # UP_LINE and DOWN_LINE are independent CSPs: prune and search each separately.
    for line in sorted({order["track_line"] for order in orders}):
        line_indexes = [i for i, order in enumerate(orders) if order["track_line"] == line]
        line_orders = [orders[i] for i in line_indexes]
        line_trains = [t for t in trains if t["track_line"] == line]
        raw_domains = [
            _all_start_candidates(order["duration"], horizon, slot_size)
            for order in line_orders
        ]
        initial_domain_size += sum(map(len, raw_domains))
        domains = [
            _candidate_starts(order, trains, raw_domain)
            for order, raw_domain in zip(line_orders, raw_domains)
        ]
        filtered_domain_size = sum(map(len, domains))
        filtered_domain_size_total += filtered_domain_size
        if enable_ac3:
            _ac3(domains, line_orders)
            ac3_pruned_count += filtered_domain_size - sum(map(len, domains))
        domains_nonempty_after_ac3 &= all(domains)
        remaining_domain_size += sum(map(len, domains))

        backtracking_result = _backtracking_search(
            domains, line_orders, line_trains, search_limit
        )
        line_assignment = backtracking_result.assignment
        if line_assignment is not None:
            line_assignment, _ = _a_star_search(
                domains, line_orders, line_trains, line_assignment, search_limit
            )
        else:
            search_limit_reached |= backtracking_result.limit_reached
            infeasibility_proven |= backtracking_result.exhausted
            line_assignment = _partial_schedule(domains, line_orders, line_trains)
        if enable_annealing and line_assignment:
            line_assignment = _simulated_annealing(
                line_assignment, domains, line_orders, line_trains, config
            )
        for local, start in line_assignment.items():
            assignment[line_indexes[local]] = start

    pruned_pct = (
        100.0 * (initial_domain_size - remaining_domain_size) / initial_domain_size
        if initial_domain_size
        else 0.0
    )

    schedule: list[dict[str, Any]] = []
    audit_trail: list[dict[str, Any]] = []
    colocated_groups: dict[tuple[str, str, float, float], list[str]] = defaultdict(list)
    for index, start in assignment.items():
        order = orders[index]
        end = round(start + order["duration"], 6)
        colocated_groups[
            (order["section_id"], order["track_line"], start, end)
        ].append(order["work_id"])

    for index, start in sorted(
        assignment.items(), key=lambda item: (item[1], orders[item[0]]["work_id"])
    ):
        order = orders[index]
        end = round(start + order["duration"], 6)
        colocated = colocated_groups[
            (order["section_id"], order["track_line"], start, end)
        ]
        other_ids = sorted(work_id for work_id in colocated if work_id != order["work_id"])
        schedule.append(
            {
                "work_id": order["work_id"],
                "department": order["department"],
                "section_id": order["section_id"],
                "track_line": order["track_line"],
                "start_time_hr": round(start, 6),
                "end_time_hr": end,
                "co_located_with": other_ids,
                "heavy_equipment": order["heavy_equipment"],
            }
        )

    audit_trail.append(
        {
            "rule_name": "AC3DomainPruning",
            "predicate_evaluated": (
                "all_candidate_domains_nonempty_after_ac3"
                if enable_ac3
                else "ac3_enabled"
            ),
            "passed": (
                domains_nonempty_after_ac3
                if enable_ac3
                else None
            ),
            "explanation": (
                f"AC-3 removed {ac3_pruned_count} of "
                f"{filtered_domain_size_total} "
                "candidate starts remaining after train-conflict filtering."
                if enable_ac3
                else "AC-3 pruning was disabled; feasibility was checked during search."
            ),
        }
    )

    merges = sum(len(group) - 1 for group in colocated_groups.values() if len(group) > 1)
    scheduled_count = len(schedule)
    total_count = len(orders)
    unscheduled_work_ids = [
        order["work_id"]
        for index, order in enumerate(orders)
        if index not in assignment
    ]
    if scheduled_count == total_count:
        status = "success"
        solver_outcome = "success"
    elif infeasibility_proven:
        status = "partial" if scheduled_count else "unschedulable"
        solver_outcome = "unschedulable"
    elif search_limit_reached:
        status = "search_limit_reached"
        solver_outcome = "search_limit_reached"
    else:
        status = "partial" if scheduled_count else "search_limit_reached"
        solver_outcome = status

    return {
        "status": status,
        "solver_outcome": solver_outcome,
        "schedule": schedule,
        "unscheduled_work_ids": unscheduled_work_ids,
        "metrics": {
            "total_requests": total_count,
            "scheduled_requests": scheduled_count,
            "search_space_pruned_pct": round(pruned_pct, 2),
            "fol_rule_compliance_pct": None,
            "co_location_merges_count": merges,
            "solver_execution_time_sec": round(time.perf_counter() - started_at, 6),
        },
        "audit_trail": audit_trail,
    }
