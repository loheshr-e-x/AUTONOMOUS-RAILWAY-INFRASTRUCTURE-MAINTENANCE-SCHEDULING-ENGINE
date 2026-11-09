from typing import List, Literal, Optional

from pydantic import BaseModel, Field, StrictStr, field_validator

from .domain_types import (
    DataProvenance,
    Department,
    ResourceRequirement,
    TrackLine,
    UrgencyLevel,
    WorkCondition,
)


class TrainOccupancyWindow(BaseModel):
    train_no: str
    section_id: str
    track_line: TrackLine = TrackLine.DOWN_LINE
    start_time_hr: float = Field(..., ge=0.0, le=24.0)
    end_time_hr: float = Field(..., ge=0.0, le=24.0)
    train_start_km: Optional[float] = Field(default=None, ge=0.0)
    train_end_km: Optional[float] = Field(default=None, ge=0.0)


class TimetableCoverage(BaseModel):
    """Claim that the supplied timetable is complete for a track and time range.

    `source` is an informational label only. The claim counts only if the
    verifier's EvidenceProvider authenticates the record.
    """

    source: Optional[str] = None
    section_id: str
    track_line: TrackLine
    start_time_hr: float = Field(..., ge=0.0, le=24.0)
    end_time_hr: float = Field(..., ge=0.0, le=24.0)


class MaintenanceWorkOrder(BaseModel):
    work_id: str
    department: Department
    section_id: str
    track_line: TrackLine = TrackLine.DOWN_LINE
    heavy_equipment: bool = False
    defect_type: str
    duration_hrs: float = Field(..., gt=0.0, le=8.0)
    urgency: UrgencyLevel
    co_location_allowed: bool = True
    resource_requirements: Optional[List[ResourceRequirement]] = None
    prerequisites: Optional[List[StrictStr]] = None
    permitted_work_conditions: Optional[List[WorkCondition]] = None
    provenance: DataProvenance = Field(default_factory=DataProvenance)

    @field_validator("prerequisites")
    @classmethod
    def prerequisites_must_be_unique_and_trimmed(
        cls, values: Optional[List[StrictStr]]
    ) -> Optional[List[StrictStr]]:
        if values is None:
            return values
        if any(not value or value != value.strip() for value in values):
            raise ValueError("prerequisite work IDs must be non-empty and trimmed")
        if len(values) != len(set(values)):
            raise ValueError("prerequisites must not contain duplicates")
        return values

    @field_validator("resource_requirements")
    @classmethod
    def resource_types_must_be_unique(
        cls, values: Optional[List[ResourceRequirement]]
    ) -> Optional[List[ResourceRequirement]]:
        if values is not None:
            resource_types = [item.resource_type for item in values]
            if len(resource_types) != len(set(resource_types)):
                raise ValueError("resource requirements must not duplicate resource_type")
        return values

    @field_validator("permitted_work_conditions")
    @classmethod
    def work_conditions_must_be_unique(
        cls, values: Optional[List[WorkCondition]]
    ) -> Optional[List[WorkCondition]]:
        if values is not None:
            condition_ids = [item.condition_id for item in values]
            if len(condition_ids) != len(set(condition_ids)):
                raise ValueError("permitted work conditions must not duplicate condition_id")
        return values


class LegacyMaintenanceWorkOrderResponse(BaseModel):
    """Production response shape retained for clients predating domain metadata."""

    work_id: str
    department: Department
    section_id: str
    track_line: TrackLine = TrackLine.DOWN_LINE
    heavy_equipment: bool = False
    defect_type: str
    duration_hrs: float = Field(..., gt=0.0, le=8.0)
    urgency: UrgencyLevel
    co_location_allowed: bool = True


class SolverRequest(BaseModel):
    section_ids: List[str]
    time_horizon_hrs: int = 24
    enable_ac3_pruning: bool = True
    enable_simulated_annealing: bool = True


class ScheduledBlockAssignment(BaseModel):
    work_id: str
    department: Department
    section_id: str
    track_line: TrackLine = TrackLine.DOWN_LINE
    start_time_hr: float
    end_time_hr: float
    co_located_with: Optional[List[str]] = []
    fol_verified: Optional[bool] = None
    worksite_start_km: Optional[float] = Field(default=None, ge=0.0)
    worksite_end_km: Optional[float] = Field(default=None, ge=0.0)
    power_isolated: Optional[bool] = None
    # Informational label; a positive `power_isolated` needs provider authentication.
    power_isolation_source: Optional[str] = None
    heavy_equipment: bool = False


class AuditLogEntry(BaseModel):
    rule_name: str
    predicate_evaluated: str
    passed: Optional[bool] = Field(
        description="True/false when evaluated; null when required evidence is unavailable."
    )
    explanation: str


class OptimizationMetrics(BaseModel):
    total_requests: int
    scheduled_requests: int
    search_space_pruned_pct: float
    fol_rule_compliance_pct: Optional[float] = Field(
        description=(
            "Passed verifier audit entries divided by all verifier entries; "
            "null if no entries or any check is unevaluated."
        )
    )
    co_location_merges_count: int
    solver_execution_time_sec: float


class BlockScheduleResponse(BaseModel):
    status: Literal[
        "success",
        "partial",
        "unschedulable",
        "no_work",
        "search_limit_reached",
        "safety_invalid",
        "safety_unverified",
    ]
    solver_outcome: Optional[
        Literal[
            "success",
            "partial",
            "unschedulable",
            "no_work",
            "search_limit_reached",
        ]
    ] = None
    schedule: List[ScheduledBlockAssignment]
    unscheduled_work_ids: List[str] = Field(default_factory=list)
    metrics: OptimizationMetrics
    audit_trail: List[AuditLogEntry]
