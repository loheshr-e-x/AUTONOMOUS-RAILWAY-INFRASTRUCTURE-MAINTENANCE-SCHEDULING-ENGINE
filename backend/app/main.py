from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .data_engine import (
    SUB_SECTION_IDS,
    get_maintenance_work_orders as load_maintenance_work_orders,
    get_train_schedules as load_train_schedules,
)
from .logic_engine import verify_safety_invariants
from .schemas.contracts import (
    AuditLogEntry,
    BlockScheduleResponse,
    MaintenanceWorkOrder,
    SolverRequest,
    TrainOccupancyWindow,
)
from .solver_engine import solve_maintenance_schedule

app = FastAPI(
    title="SymbIO-Block API Engine",
    description="Symbolic CSP & First-Order Logic Engine for Railway Maintenance Scheduling (SIH26027)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_last_audit_trail: List[AuditLogEntry] = []


@app.get("/health")
def health_check():
    return {"status": "online", "engine": "SymbIO-Block Symbolic Core v1.0"}


@app.get("/api/data/trains", response_model=List[TrainOccupancyWindow])
def get_train_schedules():
    return load_train_schedules()


@app.get("/api/data/work-orders", response_model=List[MaintenanceWorkOrder])
def get_maintenance_work_orders():
    return load_maintenance_work_orders()


@app.post("/api/schedule/generate", response_model=BlockScheduleResponse)
def generate_schedule(payload: SolverRequest):
    global _last_audit_trail
    sections = set(payload.section_ids)
    if "NDLS_CNB" in sections:
        sections.update(SUB_SECTION_IDS)
        payload = payload.model_copy(update={"section_ids": sorted(sections)})
    work_orders = [
        w for w in load_maintenance_work_orders()
        if not sections or w.section_id in sections
    ]
    trains = [
        t for t in load_train_schedules()
        if not sections or t.section_id in sections
    ]

    result = BlockScheduleResponse.model_validate(
        solve_maintenance_schedule(work_orders, trains, payload)
    )

    _, fol_audit = verify_safety_invariants(result.schedule, trains)
    if fol_audit:
        passed = sum(1 for entry in fol_audit if entry.passed)
        result.metrics.fol_rule_compliance_pct = round(
            100.0 * passed / len(fol_audit), 2
        )
    result.audit_trail.extend(fol_audit)
    _last_audit_trail = result.audit_trail
    return result


@app.get("/api/audit/logs")
def get_audit_trail():
    return {"audit_trail": _last_audit_trail}
