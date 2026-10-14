from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from contracts import (
    TrainOccupancyWindow,
    MaintenanceWorkOrder,
    SolverRequest,
    BlockScheduleResponse
)
from backend.app.data_engine import (
    get_maintenance_work_orders as load_maintenance_work_orders,
    get_train_schedules as load_train_schedules,
)

app = FastAPI(
    title="SymbIO-Block API Engine",
    description="Symbolic CSP & First-Order Logic Engine for Railway Maintenance Scheduling (SIH26027)",
    version="1.0.0"
)

# Enable CORS for Next.js Agent D
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "online", "engine": "SymbIO-Block Symbolic Core v1.0"}

# --- AGENT A ENDPOINTS ---
@app.get("/api/data/trains", response_model=List[TrainOccupancyWindow])
def get_train_schedules():
    """Endpoint for Agent A: Ingests Kaggle train schedule data."""
    return load_train_schedules()

@app.get("/api/data/work-orders", response_model=List[MaintenanceWorkOrder])
def get_maintenance_work_orders():
    """Endpoint for Agent A: Returns synthetic/TMS work orders."""
    return load_maintenance_work_orders()

# --- AGENT B & C ENDPOINTS ---
@app.post("/api/schedule/generate", response_model=BlockScheduleResponse)
def generate_schedule(payload: SolverRequest):
    """
    Main Solver Pipeline Endpoint:
    Calls Agent A (Data) -> Agent B (FOL Filtering) -> Agent C (AC-3 + A* Solver)
    """
    # Placeholder to be hooked up by Coordinator/Agents
    raise HTTPException(status_code=501, detail="Solver Pipeline initializing...")

@app.get("/api/audit/logs")
def get_audit_trail():
    """Endpoint for Agent B: Returns Backward Chaining safety justifications."""
    return {"audit_trail": []}