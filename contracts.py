from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

# --- ENUMS ---
class Department(str, Enum):
    ENGINEERING = "ENGINEERING"
    SIGNALLING = "SIGNALLING"
    TRACTION = "TRACTION"

class UrgencyLevel(int, Enum):
    CRITICAL = 1  # Emergency / High Priority
    MEDIUM = 2    # Overdue Maintenance
    ROUTINE = 3   # Scheduled Preventative

# --- DATA INPUT SCHEMAS ---
class TrainOccupancyWindow(BaseModel):
    train_no: str
    section_id: str
    start_time_hr: float = Field(..., ge=0.0, le=24.0)
    end_time_hr: float = Field(..., ge=0.0, le=24.0)

class MaintenanceWorkOrder(BaseModel):
    work_id: str
    department: Department
    section_id: str
    defect_type: str
    duration_hrs: float = Field(..., gt=0.0, le=8.0)
    urgency: UrgencyLevel
    co_location_allowed: bool = True

# --- SOLVER CONFIGURATION ---
class SolverRequest(BaseModel):
    section_ids: List[str]
    time_horizon_hrs: int = 24
    enable_ac3_pruning: bool = True
    enable_simulated_annealing: bool = True

# --- SOLVER OUTPUT SCHEMAS ---
class ScheduledBlockAssignment(BaseModel):
    work_id: str
    department: Department
    section_id: str
    start_time_hr: float
    end_time_hr: float
    co_located_with: Optional[List[str]] = []
    fol_verified: bool = True

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