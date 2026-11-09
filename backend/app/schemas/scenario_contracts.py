"""Strict request and response contracts for offline scenario comparisons."""

from __future__ import annotations

import math
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    field_validator,
)

from .contracts import Department, TrackLine, UrgencyLevel

MODEL_VERSION = "symbio-block-task16-simulation-v1"

_PositiveFiniteFloat = Annotated[float, Field(gt=0, allow_inf_nan=False)]
_NonnegativeFiniteFloat = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class StrictScenarioModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _numeric_input(value: object) -> object:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("must be a JSON number")
    if not math.isfinite(float(value)):
        raise ValueError("must be finite")
    return value


class ScenarioWorkOrder(StrictScenarioModel):
    work_id: Annotated[StrictStr, Field(min_length=1)]
    department: Department
    section_id: Annotated[StrictStr, Field(min_length=1)]
    track_line: TrackLine = TrackLine.DOWN_LINE
    heavy_equipment: StrictBool = False
    defect_type: Annotated[StrictStr, Field(min_length=1)]
    duration_hrs: _PositiveFiniteFloat = Field(le=8)
    urgency: UrgencyLevel
    co_location_allowed: StrictBool = True

    @field_validator("duration_hrs", mode="before")
    @classmethod
    def duration_must_be_numeric(cls, value: object) -> object:
        return _numeric_input(value)

    @field_validator("work_id", "section_id", "defect_type")
    @classmethod
    def strings_must_be_trimmed(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("must not have leading or trailing whitespace")
        return value


class ScenarioTrainWindow(StrictScenarioModel):
    train_no: Annotated[StrictStr, Field(min_length=1)]
    section_id: Annotated[StrictStr, Field(min_length=1)]
    track_line: TrackLine = TrackLine.DOWN_LINE
    start_time_hr: _NonnegativeFiniteFloat = Field(le=24)
    end_time_hr: _NonnegativeFiniteFloat = Field(le=24)

    @field_validator("start_time_hr", "end_time_hr", mode="before")
    @classmethod
    def times_must_be_numeric(cls, value: object) -> object:
        return _numeric_input(value)

    @field_validator("train_no", "section_id")
    @classmethod
    def strings_must_be_trimmed(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("must not have leading or trailing whitespace")
        return value


class ScenarioSolverConfiguration(StrictScenarioModel):
    section_ids: list[Annotated[StrictStr, Field(min_length=1)]] = Field(min_length=1)
    time_horizon_hrs: _PositiveFiniteFloat = 24.0
    slot_duration_hrs: _PositiveFiniteFloat = 0.5
    train_clearance_hrs: _NonnegativeFiniteFloat = 0.0
    enable_ac3_pruning: StrictBool = True
    enable_simulated_annealing: StrictBool = True
    max_search_nodes: Annotated[StrictInt, Field(ge=1)] = 100_000
    annealing_iterations: Annotated[StrictInt, Field(ge=0)] = 500
    annealing_initial_temperature: _PositiveFiniteFloat = 2.0
    annealing_cooling_rate: _PositiveFiniteFloat = 0.995
    workload_balance_weight: float = Field(default=0.1, allow_inf_nan=False)
    co_location_reward: float = Field(default=0.5, allow_inf_nan=False)
    cpsat_time_limit_seconds: _PositiveFiniteFloat = 30.0
    random_seed: StrictInt = 7

    @field_validator(
        "time_horizon_hrs",
        "slot_duration_hrs",
        "train_clearance_hrs",
        "annealing_initial_temperature",
        "annealing_cooling_rate",
        "workload_balance_weight",
        "co_location_reward",
        "cpsat_time_limit_seconds",
        mode="before",
    )
    @classmethod
    def numeric_configuration_must_be_json_number(cls, value: object) -> object:
        return _numeric_input(value)

    @field_validator("section_ids")
    @classmethod
    def sections_must_be_unique_and_trimmed(cls, values: list[str]) -> list[str]:
        if any(section != section.strip() for section in values):
            raise ValueError("section IDs must not have leading or trailing whitespace")
        if len(values) != len(set(values)):
            raise ValueError("section_ids must be unique")
        return values


class ScenarioComparisonRequest(StrictScenarioModel):
    scenario_id: Annotated[StrictStr, Field(min_length=1)]
    scenario_name: Annotated[StrictStr, Field(min_length=1)] | None = None
    model_version: StrictStr = MODEL_VERSION
    work_orders: list[ScenarioWorkOrder]
    train_windows: list[ScenarioTrainWindow] = Field(default_factory=list)
    solver_configuration: ScenarioSolverConfiguration
    input_digest: StrictStr | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )

    @field_validator("scenario_id", "scenario_name")
    @classmethod
    def identifiers_must_be_trimmed(cls, value: str | None) -> str | None:
        if value is not None and value != value.strip():
            raise ValueError("must not have leading or trailing whitespace")
        return value


class ScenarioAssignment(StrictScenarioModel):
    work_id: StrictStr
    department: Department
    section_id: StrictStr
    track_line: TrackLine
    start_time_hr: float
    end_time_hr: float
    co_located_with: list[StrictStr] = Field(default_factory=list)
    heavy_equipment: StrictBool = False


class ValidationFinding(StrictScenarioModel):
    code: StrictStr
    work_order_ids: list[StrictStr] = Field(default_factory=list)
    message: StrictStr


class ScheduleValidationResult(StrictScenarioModel):
    valid: StrictBool
    findings: list[ValidationFinding] = Field(default_factory=list)


class ObjectiveComponent(StrictScenarioModel):
    available: StrictBool
    value: float | int | None
    explanation: StrictStr


class ScenarioObjectiveComponents(StrictScenarioModel):
    time_of_day_train_gap: ObjectiveComponent
    department_workload_imbalance: ObjectiveComponent
    co_location_merge_count: ObjectiveComponent
    schedule_stability: ObjectiveComponent
    utilization: ObjectiveComponent


class UnscheduledWorkReason(StrictScenarioModel):
    work_id: StrictStr
    code: StrictStr
    explanation: StrictStr


class SolverRunResult(StrictScenarioModel):
    solver: Literal["baseline", "cp_sat"]
    run_status: Literal["completed", "failed", "unavailable"]
    input_digest: StrictStr
    error_code: StrictStr | None = None
    error_message: StrictStr | None = None
    solver_outcome: StrictStr | None = None
    termination_reason: StrictStr | None = None
    runtime_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    total_work_orders: StrictInt
    scheduled_work_ids: list[StrictStr] = Field(default_factory=list)
    unscheduled_work_ids: list[StrictStr] = Field(default_factory=list)
    schedule: list[ScenarioAssignment] = Field(default_factory=list)
    validation: ScheduleValidationResult | None = None
    objective_components: ScenarioObjectiveComponents
    solver_feasible_incumbent_found: StrictBool | None = Field(
        default=None,
        description=(
            "Native solver incumbent indicator; it does not by itself establish "
            "a complete assignment."
        ),
    )
    complete_assignment_witness: StrictBool | None = Field(
        default=None,
        description="A complete assignment independently validated against this scenario.",
    )
    coverage_optimality_proven: StrictBool | None = Field(
        default=None,
        description="Maximum scheduled coverage proven for the exact encoded model.",
    )
    complete_schedule_proven_infeasible: StrictBool | None = Field(
        default=None,
        description="No complete assignment exists for the exact encoded model.",
    )
    objective_optimality_proven: StrictBool | None = Field(
        default=None,
        description="The solver proved its encoded objective optimal, subject to scaling.",
    )
    feasibility_not_established: StrictBool | None = None
    search_limit_reached: StrictBool | None = None
    proof_scope: StrictStr | None = None
    solver_native_objective_value: float | None = Field(
        default=None, allow_inf_nan=False
    )
    solver_scaled_objective_value: float | None = Field(
        default=None, allow_inf_nan=False
    )
    solver_objective_integer_scale: float | None = Field(
        default=None, allow_inf_nan=False
    )
    termination_status: StrictStr | None = None
    search_branches: StrictInt | None = None
    search_conflicts: StrictInt | None = None
    candidate_domain_before_train_filtering: StrictInt | None = None
    candidate_domain_after_train_filtering: StrictInt | None = None
    unscheduled_reasons: list[UnscheduledWorkReason] = Field(default_factory=list)


class ScenarioComparisonResponse(StrictScenarioModel):
    scenario_id: StrictStr
    model_version: StrictStr
    input_digest: StrictStr
    comparison_status: Literal["completed", "incomplete"]
    paired_inputs_match: StrictBool
    baseline: SolverRunResult
    cp_sat: SolverRunResult
