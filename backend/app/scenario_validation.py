"""Canonical inputs and independent validation for experimental scenarios."""

from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal
from typing import Any, Iterable

from pydantic import ValidationError

from .schemas.scenario_contracts import (
    MODEL_VERSION,
    ScenarioAssignment,
    ScenarioComparisonRequest,
    ScheduleValidationResult,
    ValidationFinding,
)


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _multiple_of(value: float, scale: int) -> bool:
    scaled = Decimal(str(value)) * scale
    return scaled == scaled.to_integral_value()


def canonical_scenario_digest(scenario: ScenarioComparisonRequest) -> str:
    """Hash solver-relevant inputs; presentation metadata is intentionally excluded."""
    snapshot = {
        "model_version": scenario.model_version,
        "work_orders": [
            order.model_dump(mode="json") for order in scenario.work_orders
        ],
        "train_windows": [
            train.model_dump(mode="json") for train in scenario.train_windows
        ],
        "solver_configuration": scenario.solver_configuration.model_dump(mode="json"),
    }
    encoded = json.dumps(
        snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_scenario_input(
    scenario: ScenarioComparisonRequest,
    valid_section_ids: set[str] | None = None,
) -> ScheduleValidationResult:
    findings: list[ValidationFinding] = []
    if scenario.model_version != MODEL_VERSION:
        findings.append(
            ValidationFinding(
                code="UNSUPPORTED_MODEL_VERSION",
                message=f"Supported model version is {MODEL_VERSION}.",
            )
        )

    order_ids = [order.work_id for order in scenario.work_orders]
    duplicate_order_ids = sorted(
        work_id for work_id in set(order_ids) if order_ids.count(work_id) > 1
    )
    for work_id in duplicate_order_ids:
        findings.append(
            ValidationFinding(
                code="DUPLICATE_WORK_ORDER_ID",
                work_order_ids=[work_id],
                message=f"Work-order ID {work_id!r} appears more than once.",
            )
        )

    selected_sections = set(scenario.solver_configuration.section_ids)
    if len(selected_sections) != len(scenario.solver_configuration.section_ids):
        findings.append(
            ValidationFinding(
                code="DUPLICATE_SELECTED_SECTION",
                message="Selected section IDs must be unique.",
            )
        )

    order_sections = {order.section_id for order in scenario.work_orders}
    train_sections = {train.section_id for train in scenario.train_windows}
    outside_selection = sorted((order_sections | train_sections) - selected_sections)
    if outside_selection:
        findings.append(
            ValidationFinding(
                code="SECTION_OUTSIDE_SCENARIO",
                message=(
                    "Work orders and train windows must use selected sections: "
                    + ", ".join(outside_selection)
                ),
            )
        )

    if valid_section_ids is not None:
        unknown = sorted(
            (selected_sections | order_sections | train_sections) - valid_section_ids
        )
        if unknown:
            findings.append(
                ValidationFinding(
                    code="UNKNOWN_SECTION",
                    message="Unknown section ID(s): " + ", ".join(unknown),
                )
            )

    config = scenario.solver_configuration
    precision_values: list[tuple[str, float, int]] = [
        ("time_horizon_hrs", config.time_horizon_hrs, 1_000_000),
        ("slot_duration_hrs", config.slot_duration_hrs, 1_000_000),
        ("train_clearance_hrs", config.train_clearance_hrs, 1_000_000),
        ("workload_balance_weight", config.workload_balance_weight, 1_000_000),
        ("co_location_reward", config.co_location_reward, 9_000_000_000_000),
    ]
    precision_values.extend(
        (f"duration for {order.work_id}", order.duration_hrs, 1_000)
        for order in scenario.work_orders
    )
    precision_values.extend(
        (f"train start for {train.train_no}", train.start_time_hr, 1_000_000)
        for train in scenario.train_windows
    )
    precision_values.extend(
        (f"train end for {train.train_no}", train.end_time_hr, 1_000_000)
        for train in scenario.train_windows
    )
    for label, value, scale in precision_values:
        if not _multiple_of(value, scale):
            findings.append(
                ValidationFinding(
                    code="UNSUPPORTED_NUMERIC_PRECISION",
                    message=(
                        f"{label} must be representable at precision 1/{scale}; "
                        "the value will not be rounded."
                    ),
                )
            )

    if config.time_horizon_hrs > 24:
        findings.append(
            ValidationFinding(
                code="HORIZON_OUT_OF_RANGE",
                message="time_horizon_hrs must not exceed 24.",
            )
        )
    for train in scenario.train_windows:
        if train.end_time_hr <= train.start_time_hr:
            findings.append(
                ValidationFinding(
                    code="INVALID_TRAIN_INTERVAL",
                    message=f"Train {train.train_no!r} must have end time after start.",
                )
            )

    return ScheduleValidationResult(valid=not findings, findings=findings)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _overlaps(start_a: float, end_a: float, start_b: float, end_b: float) -> bool:
    return start_a < end_b and start_b < end_a


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _candidate_starts_for_order(
    scenario: ScenarioComparisonRequest,
    order: Any,
) -> list[float]:
    """Rebuild the simulation candidate domain without importing solver helpers."""
    config = scenario.solver_configuration
    latest_start = config.time_horizon_hrs - order.duration_hrs
    if latest_start < -1e-9:
        return []

    step_count = math.floor(
        latest_start / config.slot_duration_hrs + 1e-9
    )
    starts = [
        round(step * config.slot_duration_hrs, 6)
        for step in range(step_count + 1)
    ]
    if not starts or latest_start - starts[-1] > 1e-9:
        starts.append(round(latest_start, 6))

    clearance = config.train_clearance_hrs
    filtered: list[float] = []
    for start in starts:
        end = start + order.duration_hrs
        blocked = False
        for train in scenario.train_windows:
            if train.section_id != order.section_id:
                continue
            same_line = _enum_value(train.track_line) == _enum_value(
                order.track_line
            )
            if not (same_line or (order.heavy_equipment and not same_line)):
                continue
            train_start = max(0.0, train.start_time_hr - clearance)
            train_end = min(
                config.time_horizon_hrs,
                train.end_time_hr + clearance,
            )
            if _overlaps(start, end, train_start, train_end):
                blocked = True
                break
        if not blocked:
            filtered.append(start)
    return filtered


def validate_schedule(
    scenario: ScenarioComparisonRequest,
    schedule: Iterable[ScenarioAssignment | dict[str, Any]],
    unscheduled_work_ids: Iterable[str],
) -> ScheduleValidationResult:
    """Check returned assignments without using either solver's compatibility helpers."""
    findings: list[ValidationFinding] = []
    orders = {order.work_id: order for order in scenario.work_orders}
    schedule_rows = list(schedule)
    unscheduled_ids = list(unscheduled_work_ids)
    scheduled_ids = [_field(row, "work_id") for row in schedule_rows]

    seen_schedule_ids: set[str] = set()
    valid_rows: list[tuple[ScenarioAssignment, Any]] = []
    for row in schedule_rows:
        raw_id = _field(row, "work_id")
        work_id = raw_id if isinstance(raw_id, str) else None
        if work_id is None:
            findings.append(
                ValidationFinding(
                    code="MISSING_ASSIGNMENT_ID",
                    message="Every assignment must contain a string work_id.",
                )
            )
            continue
        if work_id in seen_schedule_ids:
            findings.append(
                ValidationFinding(
                    code="DUPLICATE_SCHEDULED_ID",
                    work_order_ids=[work_id],
                    message=f"Work order {work_id!r} is scheduled more than once.",
                )
            )
        seen_schedule_ids.add(work_id)
        order = orders.get(work_id)
        if order is None:
            findings.append(
                ValidationFinding(
                    code="UNKNOWN_SCHEDULED_ID",
                    work_order_ids=[work_id],
                    message=f"Assignment {work_id!r} was not submitted.",
                )
            )
            continue

        try:
            assignment = (
                row
                if isinstance(row, ScenarioAssignment)
                else ScenarioAssignment.model_validate(row)
            )
        except ValidationError as exc:
            findings.append(
                ValidationFinding(
                    code="INVALID_ASSIGNMENT",
                    work_order_ids=[work_id],
                    message=f"Assignment {work_id!r} is malformed: {exc}",
                )
            )
            continue

        start = _number(assignment.start_time_hr)
        end = _number(assignment.end_time_hr)
        horizon = scenario.solver_configuration.time_horizon_hrs
        if start is None or end is None or not 0 <= start < end <= horizon:
            findings.append(
                ValidationFinding(
                    code="INVALID_ASSIGNMENT_INTERVAL",
                    work_order_ids=[work_id],
                    message=(
                        f"Assignment {work_id!r} must satisfy "
                        "0 <= start < end <= the scenario horizon."
                    ),
                )
            )
        elif not _multiple_of(start, 1_000_000) or not _multiple_of(
            end, 1_000_000
        ):
            findings.append(
                ValidationFinding(
                    code="UNSUPPORTED_ASSIGNMENT_PRECISION",
                    work_order_ids=[work_id],
                    message=(
                        f"Assignment {work_id!r} times must be representable at "
                        "precision 1/1000000."
                    ),
                )
            )
        elif abs((end - start) - order.duration_hrs) > 1e-9:
            findings.append(
                ValidationFinding(
                    code="ASSIGNMENT_DURATION_MISMATCH",
                    work_order_ids=[work_id],
                    message=f"Assignment {work_id!r} does not match its submitted duration.",
                )
            )
        elif not any(
            abs(start - candidate) <= 1e-9
            for candidate in _candidate_starts_for_order(scenario, order)
        ):
            findings.append(
                ValidationFinding(
                    code="INVALID_CANDIDATE_START",
                    work_order_ids=[work_id],
                    message=(
                        f"Assignment {work_id!r} starts outside its generated "
                        "candidate domain after listed-train filtering."
                    ),
                )
            )

        if (
            _enum_value(assignment.department) != _enum_value(order.department)
            or assignment.section_id != order.section_id
            or _enum_value(assignment.track_line) != _enum_value(order.track_line)
            or assignment.heavy_equipment != order.heavy_equipment
        ):
            findings.append(
                ValidationFinding(
                    code="ASSIGNMENT_INPUT_MISMATCH",
                    work_order_ids=[work_id],
                    message=f"Assignment {work_id!r} changes submitted work-order attributes.",
                )
            )
        valid_rows.append((assignment, order))

    if any(not isinstance(work_id, str) for work_id in unscheduled_ids):
        findings.append(
            ValidationFinding(
                code="INVALID_UNSCHEDULED_ID",
                message="Every unscheduled work-order ID must be a string.",
            )
        )
    valid_unscheduled = [item for item in unscheduled_ids if isinstance(item, str)]
    if len(valid_unscheduled) != len(set(valid_unscheduled)):
        findings.append(
            ValidationFinding(
                code="DUPLICATE_UNSCHEDULED_ID",
                message="Unscheduled work-order IDs must not contain duplicates.",
            )
        )
    unknown_unscheduled = sorted(set(valid_unscheduled) - set(orders))
    for work_id in unknown_unscheduled:
        findings.append(
            ValidationFinding(
                code="UNKNOWN_UNSCHEDULED_ID",
                work_order_ids=[work_id],
                message=f"Unscheduled work order {work_id!r} was not submitted.",
            )
        )
    if (
        len(scheduled_ids) != len(seen_schedule_ids)
        or len(unscheduled_ids) != len(valid_unscheduled)
        or set(seen_schedule_ids) & set(valid_unscheduled)
        or set(seen_schedule_ids) | set(valid_unscheduled) != set(orders)
    ):
        findings.append(
            ValidationFinding(
                code="WORK_ORDER_ACCOUNTING_MISMATCH",
                message=(
                    "Scheduled and unscheduled IDs must partition submitted IDs "
                    "exactly once."
                ),
            )
        )

    horizon = scenario.solver_configuration.time_horizon_hrs
    clearance = scenario.solver_configuration.train_clearance_hrs
    for assignment, order in valid_rows:
        start = _number(assignment.start_time_hr)
        end = _number(assignment.end_time_hr)
        if start is None or end is None or not 0 <= start < end <= horizon:
            continue
        for train in scenario.train_windows:
            if train.section_id != order.section_id:
                continue
            same_line = (
                _enum_value(train.track_line) == _enum_value(order.track_line)
            )
            heavy_opposite_line = order.heavy_equipment and not same_line
            if not (same_line or heavy_opposite_line):
                continue
            train_start = max(0.0, train.start_time_hr - clearance)
            train_end = min(horizon, train.end_time_hr + clearance)
            if _overlaps(start, end, train_start, train_end):
                findings.append(
                    ValidationFinding(
                        code=(
                            "TRAIN_OCCUPANCY_CONFLICT"
                            if same_line
                            else "HEAVY_EQUIPMENT_ADJACENT_TRAIN_CONFLICT"
                        ),
                        work_order_ids=[order.work_id],
                        message=(
                            f"Assignment {order.work_id!r} overlaps a listed train "
                            "window under the scenario clearance."
                        ),
                    )
                )

    for index, (left, left_order) in enumerate(valid_rows):
        left_start = _number(left.start_time_hr)
        left_end = _number(left.end_time_hr)
        if left_start is None or left_end is None or left_end <= left_start:
            continue
        for right, right_order in valid_rows[index + 1 :]:
            right_start = _number(right.start_time_hr)
            right_end = _number(right.end_time_hr)
            if right_start is None or right_end is None or right_end <= right_start:
                continue
            if (
                left_order.section_id != right_order.section_id
                or _enum_value(left_order.track_line)
                != _enum_value(right_order.track_line)
                or not _overlaps(left_start, left_end, right_start, right_end)
            ):
                continue

            ids = [left_order.work_id, right_order.work_id]
            if _enum_value(left_order.department) == _enum_value(right_order.department):
                findings.append(
                    ValidationFinding(
                        code="SAME_DEPARTMENT_OVERLAP",
                        work_order_ids=ids,
                        message="Same-department work orders overlap on the same section and line.",
                    )
                )
                continue

            exact_window = left_start == right_start and left_end == right_end
            if not (
                exact_window
                and left_order.co_location_allowed
                and right_order.co_location_allowed
            ):
                findings.append(
                    ValidationFinding(
                        code="INVALID_CROSS_DEPARTMENT_COLOCATION",
                        work_order_ids=ids,
                        message=(
                            "Cross-department overlap requires bilateral co-location "
                            "permission and an identical time interval."
                        ),
                    )
                )

    return ScheduleValidationResult(valid=not findings, findings=findings)


def candidate_start_count(
    scenario: ScenarioComparisonRequest, order_id: str
) -> int:
    """Independently count one order's listed candidate starts after train filtering."""
    order = next((item for item in scenario.work_orders if item.work_id == order_id), None)
    if order is None:
        return 0
    return len(_candidate_starts_for_order(scenario, order))
