"""Independent, unweighted objective-component calculations."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .schemas.scenario_contracts import (
    ObjectiveComponent,
    ScenarioAssignment,
    ScenarioComparisonRequest,
    ScenarioObjectiveComponents,
    ScheduleValidationResult,
)


_DAYLIGHT_START, _DAYLIGHT_END = 6.0, 22.0
_NIGHT_START, _NIGHT_END = 1.0, 5.0


def _unavailable(explanation: str) -> ObjectiveComponent:
    return ObjectiveComponent(available=False, value=None, explanation=explanation)


def _available(value: float | int, explanation: str) -> ObjectiveComponent:
    return ObjectiveComponent(available=True, value=value, explanation=explanation)


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _time_of_day_cost(start: float, end: float) -> float:
    daylight = max(0.0, min(end, _DAYLIGHT_END) - max(start, _DAYLIGHT_START))
    night = max(0.0, min(end, _NIGHT_END) - max(start, _NIGHT_START))
    shoulder = (end - start) - daylight - night
    return daylight + 0.25 * shoulder


def evaluate_objective_components(
    scenario: ScenarioComparisonRequest,
    schedule: Iterable[ScenarioAssignment],
    validation: ScheduleValidationResult,
) -> ScenarioObjectiveComponents:
    rows = list(schedule)
    if not validation.valid:
        unavailable = _unavailable(
            "Unavailable because the independent schedule validation found errors."
        )
        return ScenarioObjectiveComponents(
            time_of_day_train_gap=unavailable,
            department_workload_imbalance=unavailable,
            co_location_merge_count=unavailable,
            schedule_stability=_unavailable(
                "The current model has no schedule-stability objective component."
            ),
            utilization=_unavailable(
                "The current model has no utilization objective component."
            ),
        )

    config = scenario.solver_configuration
    orders = {order.work_id: order for order in scenario.work_orders}
    time_cost = 0.0
    for row in rows:
        order = orders[row.work_id]
        start, end = row.start_time_hr, row.end_time_hr
        time_cost += _time_of_day_cost(start, end)
        for train in scenario.train_windows:
            if (
                train.section_id != order.section_id
                or _enum_value(train.track_line) != _enum_value(order.track_line)
            ):
                continue
            train_start = max(0.0, train.start_time_hr - config.train_clearance_hrs)
            train_end = min(
                config.time_horizon_hrs,
                train.end_time_hr + config.train_clearance_hrs,
            )
            gap = (
                train_start - end
                if train_start >= end
                else start - train_end
            )
            if 0 <= gap < 2.0:
                time_cost += (2.0 - gap) / 2.0

    departments = {_enum_value(order.department) for order in scenario.work_orders}
    shift_loads: dict[tuple[Any, int], float] = defaultdict(float)
    for row in rows:
        order = orders[row.work_id]
        shift = min(2, int(row.start_time_hr // 8))
        shift_loads[(_enum_value(order.department), shift)] += order.duration_hrs

    imbalance = 0.0
    for department in departments:
        loads = [shift_loads[(department, shift)] for shift in range(3)]
        mean = sum(loads) / 3
        imbalance += sum((load - mean) ** 2 for load in loads) / 3

    colocated_groups: dict[tuple[str, str, float, float], int] = defaultdict(int)
    for row in rows:
        key = (
            row.section_id,
            _enum_value(row.track_line),
            row.start_time_hr,
            round(row.end_time_hr, 6),
        )
        colocated_groups[key] += 1
    merges = sum(count - 1 for count in colocated_groups.values() if count > 1)

    return ScenarioObjectiveComponents(
        time_of_day_train_gap=_available(
            time_cost,
            "Unweighted sum of the current time-of-day and same-line train-gap costs.",
        ),
        department_workload_imbalance=_available(
            imbalance,
            "Unweighted sum of per-department three-shift workload variance.",
        ),
        co_location_merge_count=_available(
            merges,
            "Raw co-location merge count; no reward weight is applied.",
        ),
        schedule_stability=_unavailable(
            "The current model has no schedule-stability objective component."
        ),
        utilization=_unavailable(
            "The current model has no utilization objective component."
        ),
    )
