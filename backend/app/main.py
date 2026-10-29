from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .data_engine import (
    DEFAULT_ROUTE_ID,
    ROUTES,
    get_maintenance_work_orders as load_maintenance_work_orders,
    get_route,
    get_train_schedules as load_train_schedules,
    route_for_section,
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
# User-supplied inputs replace the synthetic / timetable data until cleared.
_custom_work_orders: Optional[List[MaintenanceWorkOrder]] = None
_custom_trains: Optional[List[TrainOccupancyWindow]] = None


def _valid_section_ids() -> set:
    return {sid for route in ROUTES.values() for sid in route.section_ids}


def _expand_sections(section_ids: List[str]) -> set:
    """Route ids (e.g. NDLS_CNB) stand for all of that route's sub-sections."""
    sections = set()
    for sid in section_ids:
        sections.add(sid)
        if sid in ROUTES:
            sections.update(ROUTES[sid].section_ids)
    return sections


def _require_route(route_id: str) -> str:
    try:
        get_route(route_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return route_id


def _trains_for(sections: set) -> List[TrainOccupancyWindow]:
    if _custom_trains is not None:
        pool = _custom_trains
    else:
        route_ids = {route_for_section(s) for s in sections} - {None}
        pool = [t for r in sorted(route_ids) for t in load_train_schedules(r)]
    return [t for t in pool if not sections or t.section_id in sections]


def _work_orders_for(sections: set) -> List[MaintenanceWorkOrder]:
    if _custom_work_orders is not None:
        pool = _custom_work_orders
    else:
        route_ids = {route_for_section(s) for s in sections} - {None}
        pool = [w for r in sorted(route_ids) for w in load_maintenance_work_orders(r)]
    return [w for w in pool if not sections or w.section_id in sections]


@app.get("/health")
def health_check():
    return {"status": "online", "engine": "SymbIO-Block Symbolic Core v1.0"}


@app.get("/api/data/routes")
def get_routes():
    return [
        {
            "route_id": r.route_id,
            "name": r.name,
            "origin": r.origin,
            "destination": r.destination,
            "length_km": r.length_km,
            "section_ids": list(r.section_ids),
            "train_windows": len(load_train_schedules(r.route_id)),
        }
        for r in ROUTES.values()
    ]


@app.get("/api/data/trains", response_model=List[TrainOccupancyWindow])
def get_train_schedules(route_id: str = Query(DEFAULT_ROUTE_ID)):
    return _trains_for(set(get_route(_require_route(route_id)).section_ids))


@app.post("/api/data/trains/custom", response_model=List[TrainOccupancyWindow])
def set_custom_trains(trains: List[TrainOccupancyWindow]):
    """Upload a dynamic timetable that replaces the IRCTC data until cleared."""
    global _custom_trains
    unknown = sorted({t.section_id for t in trains} - _valid_section_ids())
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown section_id(s): {unknown}")
    bad = [t.train_no for t in trains if t.end_time_hr <= t.start_time_hr]
    if bad:
        raise HTTPException(status_code=422, detail=f"end_time_hr must exceed start_time_hr: {bad}")
    _custom_trains = list(trains)
    return _custom_trains


@app.delete("/api/data/trains/custom")
def clear_custom_trains():
    global _custom_trains
    _custom_trains = None
    return {"custom": False}


@app.get("/api/data/work-orders", response_model=List[MaintenanceWorkOrder])
def get_maintenance_work_orders(route_id: str = Query(DEFAULT_ROUTE_ID)):
    return _work_orders_for(set(get_route(_require_route(route_id)).section_ids))


@app.post("/api/data/work-orders/custom", response_model=List[MaintenanceWorkOrder])
def set_custom_work_orders(orders: List[MaintenanceWorkOrder]):
    """Replace the synthetic work orders with a user-defined list until cleared."""
    global _custom_work_orders
    ids = [o.work_id for o in orders]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise HTTPException(status_code=422, detail=f"Duplicate work_id(s): {duplicates}")
    unknown = sorted({o.section_id for o in orders} - _valid_section_ids())
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown section_id(s): {unknown}")
    _custom_work_orders = list(orders)
    return _custom_work_orders


@app.delete("/api/data/work-orders/custom")
def clear_custom_work_orders():
    global _custom_work_orders
    _custom_work_orders = None
    return {"custom": False}


@app.post("/api/schedule/generate", response_model=BlockScheduleResponse)
def generate_schedule(payload: SolverRequest):
    global _last_audit_trail
    sections = _expand_sections(payload.section_ids)
    payload = payload.model_copy(update={"section_ids": sorted(sections)})
    work_orders = _work_orders_for(sections)
    trains = _trains_for(sections)

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
