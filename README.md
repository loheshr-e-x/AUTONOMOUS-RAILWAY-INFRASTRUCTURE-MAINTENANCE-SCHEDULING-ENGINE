# AUTONOMOUS RAILWAY INFRASTRUCTURE MAINTENANCE SCHEDULING ENGINE

AUTONOMOUS RAILWAY INFRASTRUCTURE MAINTENANCE SCHEDULING ENGINE is a railway maintenance scheduling **prototype**. It combines a
FastAPI backend with a Next.js dashboard to explore maintenance block schedules,
visualize train occupancy, and compare a baseline solver with an experimental
CP-SAT solver.

> **Simulation and research only.** This project is not operationally
> authorized and must not be used to approve railway work or establish railway
> safety. A generated schedule, a completed comparison, or a solver's
> optimality claim is not proof of operational feasibility. Synthetic or
> inferred data is not verified track availability.

## What the prototype does

- Loads example routes, train occupancy and synthetic maintenance work orders.
- Generates a maintenance schedule and displays metrics, an audit trail and a
  time-space Gantt chart.
- Lets users create browser-local scenarios, edit work orders and compare
  baseline and CP-SAT results on the same scenario input.
- Displays scheduled and unscheduled work, comparison validation findings and
  solver proof information where available. Eligible comparisons can be
  exported as JSON or CSV.
- Provides typed railway domain schemas and adapters for future work; the
  domain model is not a substitute for operational validation.

The configured example corridors are New Delhi–Kanpur Central, Howrah–Puri,
and Mumbai Central–Ahmedabad. Each route is divided into three model sections.
Work orders are synthetic; the timetable-derived occupancy and section model
should not be treated as authenticated, live railway data.

## Requirements

- Python 3.12 is a suitable development environment.
- Node.js 22.18 or newer and npm. The frontend test command uses Node's
  TypeScript stripping support.
- OR-Tools is needed for the experimental CP-SAT comparison and its tests.

The repository currently has a pinned requirements file for CP-SAT, but no
complete pinned backend requirements file. The setup below installs the
backend's direct runtime and test dependencies separately.

## Run locally

Run the following from the repository root. Use two terminals to keep the
backend and frontend running.

### 1. Backend

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install "fastapi>=0.100" "pydantic>=2" uvicorn httpx pytest
backend/.venv/bin/python -m pip install -r backend/requirements-cpsat.txt
backend/.venv/bin/python -m uvicorn backend.app.main:app --reload --port 8000
```

On Windows, use `backend\.venv\Scripts\python` in place of
`backend/.venv/bin/python`. The second install is optional for the main
scheduling workflow, but required to run CP-SAT comparisons and the full
backend test suite.

Check [the health endpoint](http://localhost:8000/health) or explore the
[API documentation](http://localhost:8000/docs).

### 2. Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The frontend defaults to
`http://localhost:8000` for the backend. To use a different backend, set
`NEXT_PUBLIC_API_URL` before starting the frontend, for example:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

The backend's development CORS configuration allows any origin. Run this as a
local prototype, not as a publicly exposed service.

## User guide

### Generate a schedule

1. In the scheduling controls, select a corridor and review the section IDs,
   horizon and solver options.
2. Open **Work Orders** to review or edit the current inputs. A timetable can
   also be supplied through the interface.
3. Select **Generate Schedule**. Inspect the chart, counts, status and audit
   log; a dash for safety compliance means a percentage is unavailable, not
   that safety has passed.

The backend can return incomplete, invalid or unverified outcomes. In
particular, `safety_unverified` is not a safety approval. The production view
does not currently list every unscheduled work order or clearly show every
solver outcome; use the API response and audit details when inspecting results.

### Create and compare scenarios

1. Under **Offline simulation scenarios**, enter a name, select one or more
   sections and select **Create**.
2. The scenario starts with the currently available work orders for the
   selected sections, filtered from the backend's route data. If custom work
   orders are active, those are used instead of synthetic defaults. If loading
   fails, the scenario is created empty and the interface reports the error.
   Train windows start empty; no calendar date or verified availability is
   invented.
3. Review the work orders and settings, then select **Save scenarios** to
   persist changes in this browser. Unsaved changes can be lost on reload.
   Scenarios can also be duplicated, edited and deleted.
4. Select **Run comparison**. Both solvers receive the same scenario input;
   examine their outcomes, scheduled/unscheduled work, validation and proof
   indicators. Large scenarios can take several minutes, particularly when
   train windows are empty. The CP-SAT time limit does not bound the baseline
   solver's runtime.
5. When a comparison is eligible, use **Download JSON** or **Download CSV**.
   Comparison results are not saved with browser-local scenarios.

Browser-local storage is not a secure data store. Do not enter credentials,
evidence or operational railway data.

## Tests and development

From the repository root, after installing the dependencies above:

```bash
backend/.venv/bin/python -m pytest backend/tests
cd frontend
npm test
npm run lint
npm run build
```

The backend and frontend commands run independently. For benchmark commands
and interpretation, see [the benchmark guide](backend/benchmarks/README.md).
The prior browser audit and instructions for rerunning it are in
[the Playwright audit](artifacts/prototype-audit/README.md), if that local
artifact is available.

## Project layout

| Path | Purpose |
| --- | --- |
| [`backend/app/main.py`](backend/app/main.py) | FastAPI endpoints and scheduling orchestration |
| [`backend/app/data_engine.py`](backend/app/data_engine.py) | Example routes, timetable ingestion and synthetic work orders |
| [`backend/app/solver_engine.py`](backend/app/solver_engine.py) | Baseline scheduling solver |
| [`backend/app/logic_engine.py`](backend/app/logic_engine.py) | Safety checks and audit findings |
| [`backend/app/cpsat_solver.py`](backend/app/cpsat_solver.py) | Experimental CP-SAT solver |
| [`backend/app/scenario_engine.py`](backend/app/scenario_engine.py) | Scenario comparison orchestration |
| [`backend/app/schemas/`](backend/app/schemas/) | API, scenario and railway domain schemas |
| [`backend/tests/`](backend/tests/) | Backend regression and validation tests |
| [`frontend/`](frontend/) | Next.js dashboard, scenario UI and frontend tests |
| [`backend/benchmarks/`](backend/benchmarks/) | Benchmark harness and research documentation |

For domain entities, provenance and adapter limitations, see the
[domain specification](backend/benchmarks/TASK18_DOMAIN_MODEL_SPECIFICATION.md),
[data dictionary](backend/benchmarks/TASK18_DATA_DICTIONARY.csv) and
[validation rules](backend/benchmarks/TASK18_VALIDATION_RULES.md).

## Development directives

- Preserve the distinction between the baseline scheduling path and the
  experimental CP-SAT comparison; do not describe either as operational
  authorization.
- Keep synthetic, inferred, user-supplied and authenticated data distinct.
  A source label alone is not evidence of authentication.
- Do not silently change existing API contracts, scheduling constraints or
  persisted scenario formats. Update relevant tests and documentation when
  changing behavior.
- Run the relevant tests before proposing changes. For frontend-specific
  agent guidance, see [`frontend/AGENTS.md`](frontend/AGENTS.md).
- `.gitignore` excludes local environments, dependencies and generated caches.
  Already tracked files are not automatically untracked.
