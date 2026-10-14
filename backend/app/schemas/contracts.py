from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Department(str, Enum):
    ENGINEERING = "ENGINEERING"
    SIGNALLING = "SIGNALLING"
    TRACTION = "TRACTION"


class UrgencyLevel(int, Enum):
    CRITICAL = 1
    MEDIUM = 2
    ROUTINE = 3


class TrainOccupancyWindow(BaseModel):
    train_no: str
    section_id: str
    start_time_hr: float = Field(..., ge=0.0, le=24.0)
    end_time_hr: float = Field(..., ge=0.0, le=24.0)
    train_start_km: Optional[float] = Field(default=None, ge=0.0)
    train_end_km: Optional[float] = Field(default=None, ge=0.0)


class MaintenanceWorkOrder(BaseModel):
    work_id: str
    department: Department
    section_id: str
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
    start_time_hr: float
    end_time_hr: float
    co_located_with: Optional[List[str]] = []
    fol_verified: bool = True
    worksite_start_km: Optional[float] = Field(default=None, ge=0.0)
    worksite_end_km: Optional[float] = Field(default=None, ge=0.0)
    power_isolated: bool = False
    heavy_equipment: bool = False


class AuditLogEntry(BaseModel):
    rule_name: str
    predicate_evaluated: str
    passed: bool
    explanation: str


class OptimizationMetrics(BaseModel):
    total_requests: int
    scheduled_requests: int
    search_space_pruned_pct: float
    fol_rule_compliance_pct: float
    co_location_merges_count: int
    solver_execution_time_sec: float


class BlockScheduleResponse(BaseModel):
    status: str
    schedule: List[ScheduledBlockAssignment]
    metrics: OptimizationMetrics
    audit_trail: List[AuditLogEntry]
