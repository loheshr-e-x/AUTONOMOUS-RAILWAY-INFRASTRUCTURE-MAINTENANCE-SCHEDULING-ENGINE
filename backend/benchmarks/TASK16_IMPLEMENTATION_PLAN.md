# Task 16 — Custom Work-Order and What-If Scenario Engine

**Status:** implementation plan only. No application source, tests, benchmark
results, or datasets were changed for Task 16. Do not start implementation
until this plan is approved.

The project owner explicitly approved D-01, D-15, D-25, and D-29 on
2026-11-01. The Task 15 decision register and scope summary were updated to
record those approvals. The approval is for bounded, offline, non-operational
research and reporting only; it is not operational authorization and does
not approve the Task 16 implementation plan.

## 1. Approved decisions and boundaries

| Decision | Approved policy applied to Task 16 |
|---|---|
| D-01 | Offline-only, non-operational scenario comparison. Scenario inputs and results are simulation/caller data, not railway work orders or safety evidence. |
| D-15 | Keep modeled hard constraints separate; report scheduled coverage and its proof state before objective components; report current components individually. Do not combine solver-specific scaled values into a cross-solver objective-quality claim. |
| D-25 | Report coverage, termination, proof, and evidence verification as distinct fields. Preserve existing production API semantics; Task 16 comparison is an isolated research path. |
| D-29 | Make proof claims only for the exact encoded model and captured proof metadata. Distinguish a validated complete assignment, maximum-coverage proof, objective-optimality proof, and no proof. |

### D-15 custom-work-order test condition

The current Task 14/15 D-15 register describes objective hierarchy and quality
claims but contains no separate custom-work-order test condition. This plan
adds the Task 16 prompt's condition as an acceptance requirement: exercise the
approved reporting order and objective-component breakdown on custom-created,
edited, duplicated, and unusual work orders, not only on the built-in synthetic
instances. Verify that custom urgency is not silently promoted into an
objective priority and that both solver runs receive identical custom inputs.

## 2. Current-state audit

| Surface | Verified current capability | Task 16 work still needed |
|---|---|---|
| Work-order contract | `MaintenanceWorkOrder` already describes IDs, department, section, track line, heavy-equipment Boolean, defect, duration (greater than 0 and at most 8 hours), urgency enum, and co-location Boolean. See [`contracts.py`](../app/schemas/contracts.py). | Scenario-level validation, explicit cross-solver precision checks, useful malformed-input errors, and a stable scenario snapshot. |
| Backend custom-order API | `POST /api/data/work-orders/custom` replaces a module-global list; `DELETE` clears it. Duplicate IDs and unknown sections are checked. See [`main.py`](../app/main.py). | It is not per-scenario CRUD or durable storage. Do not use this mutable global as the comparison request source. |
| Frontend work-order editor | [`WorkOrderManager.tsx`](../../frontend/components/WorkOrderManager.tsx) supports in-memory add, edit, delete, enable/disable, and applying the enabled list. The work-order form checks blank/duplicate IDs, but duration choices stop at 4 hours and urgency labels conflict with the enum/inspector labels. | Keep the existing editor surface, correct its validation and labels, support the schema's duration range up to 8 hours and solver precision, and edit a scenario draft without globally replacing active API data. |
| Production scheduling path | `/api/schedule/generate` calls the baseline solver, then calls the safety verifier and returns the existing production response. See [`main.py`](../app/main.py). | Leave this endpoint and its safety-verification behavior unchanged. Add a separate, explicitly experimental comparison path that does not invoke or alter the verifier. |
| Baseline solver | [`solve_maintenance_schedule`](../app/solver_engine.py) uses the existing candidate generation, AC-3, MRV backtracking, bounded A*, and optional simulated annealing. It returns assignments, unscheduled IDs, outcome, and runtime, but not a public objective breakdown or a maximum-coverage proof field. | Invoke as-is. Do not change its algorithms or claim maximum coverage for a partial fallback. Mark unavailable baseline search/proof metrics as unavailable. |
| Experimental CP-SAT solver | [`solve_maintenance_schedule_cpsat`](../app/cpsat_solver.py) is not wired to the API. It reports termination, coverage proof, complete-schedule infeasibility, objective proof, runtime, native scaled objective, and some search statistics. | Invoke only from the isolated comparison path. Handle the optional OR-Tools dependency explicitly; do not add a production fallback or safety meaning. |
| Current objective | Baseline `_schedule_objective` uses the time-of-day/train-gap heuristic, department workload imbalance, and co-location merges. CP-SAT first maximizes coverage, then minimizes an integer-scaled weighted objective containing related terms. Neither current objective models schedule stability or utilization as named components. See [`solver_engine.py`](../app/solver_engine.py) and [`cpsat_solver.py`](../app/cpsat_solver.py). | Independently report the current measurable components for each returned schedule. Retain solver-native scalar/scaled values only as solver-specific metadata; do not present them as directly comparable scores. |
| Outcome and proof tests | Existing tests cover custom-order upload validation, baseline exhaustion/cutoff, CP-SAT proof fields, and benchmark accounting. See [`test_api.py`](../tests/test_api.py), [`test_solver_engine.py`](../tests/test_solver_engine.py), and [`test_cpsat_solver.py`](../tests/test_cpsat_solver.py). | Add scenario-level tests and independent schedule validation; existing solver tests do not establish scenario persistence, identical paired inputs, safe explanations, or visual diffs. |
| Frontend comparison | [`page.tsx`](../../frontend/app/page.tsx) displays one baseline result; [`GanttChart.tsx`](../../frontend/components/GanttChart.tsx) draws one schedule. The frontend API/types expose no scenario or comparison operations. | Add saved scenario management, side-by-side solver results, unscheduled explanations, and original-versus-modified schedule visualization. |
| Test tooling | Backend uses pytest/unittest tests. `frontend/package.json` has lint/build scripts but no frontend test runner. | Use existing lint/build checks and backend integration tests. Decide separately whether to add browser/component-test tooling; do not install it as part of this plan. |

## 3. Bounded behavior and data flow

### Scenario snapshot

Define a versioned scenario snapshot containing:

- Scenario ID, display name, parent scenario ID (for duplicates/variants),
  schema/model version, revision, and creation/update metadata.
- Exact ordered list of work orders and exact train-window snapshot.
- Selected sections, horizon, baseline settings, CP-SAT time budget, and
  random seed. Keep solver-specific budgets/settings explicit.
- Canonical input digest over the model version, work orders, train windows,
  shared constraints, and common configuration. Exclude presentation-only
  metadata such as scenario name and timestamps.

Both solvers must receive the same canonical ordered work orders, train
windows, and common simulation configuration. Do not build one solver's input
from the other solver's output or from mutable module-global custom data.
Reject a scenario before either solver runs if a shared input cannot be
represented by both models; do not round or silently drop fields.

### Scenario persistence

Recommended bounded default: versioned browser-local storage for scenario
definitions and explicitly saved run snapshots. This supports create, save,
duplicate, reload, and compare within one browser profile without adding a
database, user account, service, or new external-data integration. It is not
shared, backed up, authenticated, or suitable for real railway records.
Surface corrupt/unsupported storage and quota failures to the user; do not
silently reset saved data.

The scenario record should retain immutable revisions/run inputs so editing a
scenario does not rewrite the snapshot used by an earlier result. A duplicate
gets a new scenario ID and parent reference but initially has an identical
input digest. This storage choice remains an implementation assumption for
owner confirmation before coding.

### Work-order editing and validation

Use the existing editor as the starting UI, but bind it to a scenario draft.
Create/edit/delete work orders within that draft; saving a scenario is separate
from running it. Enforce at both frontend and backend boundaries:

- IDs are nonempty, trimmed, unique within a scenario, and stable in results.
  Reject collisions rather than silently rename them.
- Department, track line, urgency, and Boolean fields match existing enums and
  schema. Section IDs must be from the currently code-defined route inventory.
- Duration is finite and `0 < duration_hrs <= 8`. CP-SAT currently requires
  duration precision representable at 1/1000 hour for its balance term; reject
  unsupported precision before either solver runs rather than rounding.
- Reject malformed types, missing required values, unknown fields in the
  experimental scenario DTO, duplicate scenario/run IDs, invalid horizon, and
  sections outside the selected scenario.
- Failed validation must not alter the last valid draft, saved scenario,
  existing global custom work-order list, or prior result.

No new `emergency`, work type, equipment inventory, crew, deadline, dependency,
travel, or operational priority field is introduced. An emergency example may
use existing `urgency=CRITICAL` (enum value 1), but urgency currently affects
search order and is reported descriptively; it is not a guaranteed priority.
The existing `heavy_equipment` Boolean does not establish equipment
availability. Freeze current train filtering and compatibility/co-location
semantics; do not infer new conflicts.

### Experimental paired-run API

Add a separate endpoint, proposed as
`POST /api/experimental/scenarios/compare`, with a typed request carrying one
complete scenario snapshot. It invokes the existing baseline and experimental
CP-SAT functions independently over copies of that exact snapshot, with the
same seed and common model inputs. Return:

- Scenario/input digest and model/config version.
- A separate result object per solver: schedule, scheduled and unscheduled
  IDs, runtime, solver outcome, termination reason, proof fields and
  solver-specific search statistics.
- Independently validated hard-constraint result and objective-component
  measurements.
- Per-order unscheduled explanation with an explicit evidence scope.

Do not call `verify_safety_invariants`, return a safety-compliance percentage,
change `/api/schedule/generate`, or mutate `_custom_work_orders` /
`_custom_trains`. Identify the experimental response/UI as simulation-only.
If OR-Tools is unavailable, return an explicit experimental-solver-unavailable
error for the comparison; never label a baseline-only result as a paired
comparison.

### Coverage, objective, termination, and proof reporting

Apply the approved D-15 reporting order:

1. Independent validation of the encoded hard simulation constraints.
2. Scheduled count, total count, scheduled IDs, unscheduled IDs, and coverage.
3. Separate complete-assignment witness, maximum-coverage proof,
   complete-schedule infeasibility proof, objective-optimality proof, and
   termination reason.
4. Current objective components individually: time-of-day/train-gap
   heuristic, workload imbalance, and co-location merge count/reward.
   Explicitly mark schedule stability and utilization unavailable/not modeled.
5. Runtime and available solver-specific search statistics.

Do not add objective weights or modify either solver objective. Do not compare
baseline scalar and CP-SAT scaled objective values as if they were equivalent.
The independent evaluator reports components, while retaining native scalar
values as opaque solver-specific metadata where available. Do not imply the
baseline proves maximum coverage on a partial result. CP-SAT proof fields apply
only to its exact encoded model and captured precision.

### Unscheduled explanations

An unscheduled ID is not, by itself, proof that the individual order is
impossible. Use bounded reason codes:

- `NO_CANDIDATE_START_UNDER_MODEL`: an independent diagnostic finds no
  candidate interval under the explicit horizon and listed-train filters.
- `OMITTED_FROM_MAX_COVERAGE_INCUMBENT`: CP-SAT proved maximum coverage but
  this ID was not in the selected maximum-coverage assignment. Do not claim
  that the individual order is impossible or uniquely responsible.
- `OMITTED_AFTER_EXHAUSTIVE_NO_COMPLETE_ASSIGNMENT`: the baseline exhausted
  search and returned a greedy partial result; this proves no complete
  assignment under that model, not an individual cause or maximum coverage.
- `SEARCH_LIMIT_NO_CONCLUSION`: the result was limited/cut off without the
  relevant proof. State that feasibility/coverage is unresolved.
- `NO_SCHEDULE_PROVEN_INFEASIBLE`: no assignment was returned and the solver
  proved the exact full model infeasible; do not attribute this to each order.
- `UNCLASSIFIED`: no supported cause can be established. Explain available
  facts without fabricating a conflict.

Any more specific blocker explanation requires an independently checked
conflict witness. A status label or solver's global infeasibility proof is not
an individual work-order cause. Preserve solver proof and validator evidence
alongside the text explanation.

### Schedule-difference visualization

Store the base run and each modified scenario run separately. Compare by
stable work-order ID and show:

- unchanged, moved (time/section/line changed), newly scheduled, newly
  unscheduled, removed from input, and input-edited IDs;
- before/after fields for changed work orders and assignments;
- baseline-versus-CP-SAT differences separately from original-versus-modified
  scenario differences;
- explicit “not scheduled because no conclusion” labeling for search limits.

Extend the existing Gantt view or add a paired comparison component with
distinct legends/lanes for original and modified schedules. A visual overlap
or difference is explanatory UI only, not a validator or safety assertion.

## 4. Implementation sequence

| Phase | Work and dependencies | Proposed files | Measurable acceptance criteria |
|---|---|---|---|
| 0. Contract and gates | Approve this Task 16 plan. Confirm browser-local persistence and whether custom scenario inputs are restricted to synthetic/demo data. Freeze the shared model version, allowed sections, candidate precision, and existing compatibility semantics. | Documentation only until approval. | D-01/D-15/D-25/D-29 recorded as approved; D-14/D-24/D-30 extensions remain unapproved and unchanged; no external data approval is presumed. |
| 1. Scenario contracts and independent validation | Define strict request/result DTOs, canonical digest, schema validation, schedule accounting/constraint validator, objective component evaluator, and bounded reason-code mapper. | New `backend/app/schemas/scenario_contracts.py`, `backend/app/scenario_validation.py`, `backend/app/scenario_metrics.py`; tests `backend/tests/test_scenario_validation.py`. | Reject invalid scenario before solver invocation; digest is stable for the same canonical inputs; validator detects each enumerated violation independently of solver helpers; reason codes never overstate proof. |
| 2. Isolated paired-run orchestration | Add stateless compare service and experimental API route. Call unchanged solver functions with identical common inputs; capture native outcome/proof/termination/runtime; handle missing OR-Tools explicitly. | New `backend/app/scenario_engine.py`; add route/imports in `backend/app/main.py`; add `backend/tests/test_scenario_engine.py` and `backend/tests/test_scenario_api.py`. | Both spy/capture inputs have byte-equivalent canonical digest and same common config; production route and global custom data are unchanged; comparison does not call safety verifier; errors are explicit and a one-sided run cannot be presented as paired. |
| 3. Scenario persistence and work-order management | Add local scenario CRUD/save/duplicate/revision support and bind `WorkOrderManager` drafts to a selected scenario. Correct enum labels and duration validation; keep unsaved edits separate from prior runs. | New `frontend/lib/scenario-storage.ts`; update `frontend/lib/types.ts`, `frontend/lib/api.ts`, `frontend/components/WorkOrderManager.tsx`, and `frontend/app/page.tsx`; new `frontend/components/ScenarioManager.tsx`. | Create/edit/delete/save/duplicate/reload preserves correct IDs and data; duplicate begins with identical input digest and a new scenario ID; validation errors do not mutate saved or active data. |
| 4. Comparison, explanation, and Gantt diff | Add solver comparison panels, proof-aware outcome display, unscheduled list/reasons, objective components, and original/modified visual difference. | New `frontend/components/SolverComparison.tsx` and `frontend/lib/scenario-diff.ts`; update `frontend/app/page.tsx`, `frontend/components/GanttChart.tsx`, and if needed `WorkOrderInspector.tsx`. | UI presents both solvers and scenario diff separately; all submitted IDs appear exactly once as scheduled/unscheduled per solver; unavailable proof/metrics display as unavailable; no safety-verification claim or compliance percentage appears. |
| 5. End-to-end verification | Add integration fixtures and run backend tests, frontend lint/build, plus a manual browser flow if no frontend test runner is approved. Do not run Task 12 benchmarks. | Test files above; no edits to historical result files or benchmark runners. | Ten-order base plus requested five variants execute with identical input digests; all outputs pass independent validation or are explicitly rejected; proof/status and IDs match metadata; old Task 12 result hashes/contents remain unchanged. |

## 5. Proposed test plan

### Backend unit and contract tests

1. Valid custom order round-trip, exact enum values, maximum 8-hour duration,
   and representable CP-SAT precision.
2. Reject blank/whitespace IDs, duplicate IDs, missing fields, invalid
   department/line/urgency, unknown section, duration `<= 0`, duration above
   8, non-finite numeric values, unsupported CP-SAT precision, unknown
   scenario fields, and invalid horizon. Confirm failure leaves stored/draft
   scenario inputs unchanged.
3. Validate scenario digest determinism, ordered inputs, revisions, and
   duplicate semantics.
4. Independently validate valid schedules and detect duplicate/unknown/
   missing assignments, interval/horizon errors, listed-train overlap
   (including current heavy-equipment opposite-line filtering), same-section/
   same-line/same-department overlap, and cross-department invalid
   co-location. Include exact-boundary and valid bilateral exact-window
   co-location cases. Do not add a work-order/adjacent-line heavy-equipment
   constraint absent from the current model.
5. Hand-computed objective-component fixtures for disruption heuristic,
   workload imbalance, and co-location count; test solver-native scalar
   fields remain distinct. Test missing components are reported unavailable.
6. Verify all five unscheduled explanation codes, including baseline
   exhausted partial fallback, CP-SAT proven maximum coverage, full-model
   infeasibility, and a mocked search cutoff. Assert a global proof never
   becomes an individual impossibility claim.

### API and paired-solver tests

1. Two solver spies receive identical ordered work orders, train windows,
   model version, seed, and common configuration/digest.
2. Real small deterministic baseline/CP-SAT fixtures cover complete feasible,
   cross-department co-location, same-resource conflict, train conflict,
   partial maximum-coverage proof, proven no-complete-schedule, and
   time-limit/no-proof. Mock only solver termination when a deterministic
   cutoff cannot be forced without timing sensitivity.
3. Return per-solver runtime, outcome, termination, objective breakdown,
   scheduled/unscheduled IDs, and proof fields without status inference.
4. Demonstrate a complete independently validated assignment is a feasibility
   witness; a CP-SAT coverage proof is not objective optimality; a search
   limit is not infeasibility; baseline partial fallback does not claim
   maximum coverage.
5. Confirm comparison endpoint does not change `_custom_work_orders`,
   `_custom_trains`, `/api/schedule/generate`, audit state, or safety verifier
   calls. Confirm missing OR-Tools returns an explicit unavailable error.
6. Confirm one solver exception is surfaced for that side and does not produce
   success-shaped fabricated data for it.

### Frontend and integrated tests

1. Add/edit/delete work orders; reject invalid input; duration can reach 8
   hours; emergency demonstration uses existing CRITICAL urgency without
   promising prioritization; heavy equipment is presented as a model flag.
2. Save, duplicate, rename/revise, reload, and delete scenarios; a duplicate
   has a new ID and the same content digest before edits.
3. Run base and modified scenarios and ensure each displayed result maps to
   its run digest; unchanged input reproduces the same canonical request.
4. Display completeness, scheduled IDs, unscheduled IDs/reasons, solver
   termination, proof flags, runtime, objective components, and unavailable
   values separately.
5. Gantt diff tests/manual checks cover unchanged, moved, newly scheduled,
   newly unscheduled, removed, and edited work orders. Distinguish solver
   comparison from scenario revision comparison.
6. UI labels state simulation-only; no safety verification, operational
   validity, or railway-compliance claim is inferred from solver output.

No frontend automated test runner is currently configured. Prefer existing
`npm run lint` and `npm run build`; any new component/browser test dependency
requires explicit approval before installation.

## 6. Demo acceptance criteria

Use a reproducible 10-order starting scenario selected from current
code-generated synthetic orders; freeze its exact input snapshot and digest.
Create saved variants introducing, in order:

1. A custom order with existing `urgency=CRITICAL` (not a new emergency policy).
2. A longer custom duration within the existing 8-hour schema/model range.
3. A custom order with `heavy_equipment=true` (only current modeled filtering
   is claimed).
4. A deliberate same-resource conflict fixture and a separately valid
   cross-department exact-window co-location fixture.
5. A work order in another department/section to demonstrate the currently
   modeled separation behavior, without inferring physical adjacency.

For each run, the UI must answer which orders were scheduled/unscheduled,
whether a complete assignment was independently validated, whether coverage
was proven maximum, how the solvers terminated, which proof is available,
what objective components were measured, and how the schedule differs.
An unresolved search limit must be shown as unresolved, not as a proven
infeasible order. A complete assignment or solver proof is never described as
railway safety approval.

Acceptance is correctness and reproducibility on these fixed examples, not a
runtime improvement target or general solver-performance claim.

## 7. Affected-file proposal

No files in this list are being changed now except the Task 15 approval
documentation described in the completion report.

### Backend

- Update: [`backend/app/main.py`](../app/main.py) — add isolated experimental
  route only; do not alter production generation/verification behavior.
- Add: `backend/app/scenario_engine.py` — stateless paired-run orchestration.
- Add: `backend/app/scenario_validation.py` — independent schedule validator
  and conservative explanation classification.
- Add: `backend/app/scenario_metrics.py` — independent component reporting
  with no combined cross-solver claim.
- Add: `backend/app/schemas/scenario_contracts.py` — strict scenario and
  comparison DTOs; preserve production contracts.
- Add: `backend/tests/test_scenario_validation.py`,
  `backend/tests/test_scenario_engine.py`, and
  `backend/tests/test_scenario_api.py`.
- Preserve unchanged: `backend/app/solver_engine.py`,
  `backend/app/cpsat_solver.py`, `backend/app/logic_engine.py`, existing
  safety contracts/behavior, and all `backend/benchmarks/task12_results/*`.

### Frontend

- Update: `frontend/app/page.tsx`, `frontend/lib/api.ts`,
  `frontend/lib/types.ts`, `frontend/components/WorkOrderManager.tsx`,
  `frontend/components/GanttChart.tsx`, and as needed
  `frontend/components/WorkOrderInspector.tsx`.
- Add: `frontend/lib/scenario-storage.ts`,
  `frontend/lib/scenario-diff.ts`,
  `frontend/components/ScenarioManager.tsx`, and
  `frontend/components/SolverComparison.tsx`.
- Do not add test dependencies unless separately approved.

## 8. Risks, assumptions, and unresolved gates

1. **Task 16 plan approval:** explicit D-01/D-15/D-25/D-29 decisions do not
   approve this implementation plan. Source changes wait for plan approval.
2. **Scenario storage:** browser-local persistence is the bounded proposal;
   confirm this versus server persistence before coding. No database or
   account isolation exists in the current app.
3. **Objective semantics:** approved D-15 requires coverage-first reporting
   and component-wise display, not a new scalar objective. Existing solver
   algorithms/objectives differ; do not claim matched optimization quality.
   Workload balance and co-location are current soft terms; stability and
   utilization are unavailable/not modeled.
4. **Custom urgency:** D-14 remains a proposed simulation assumption. Use
   existing urgency values descriptively/search-order-wise only; emergency
   scheduling priority is not implemented.
5. **Co-location and equipment:** D-24 remains unapproved for changes. Freeze
   the legacy exact-window bilateral Boolean rule; no real crew, access,
   possession, shared resource, or equipment compatibility is implied.
6. **Data use:** use only code-generated synthetic orders and frozen
   non-authoritative timetable-window fixtures. Do not accept or persist
   real operational railway data. D-27 and applicable external approvals
   remain blocked.
7. **Proof and diagnostics:** baseline has no explicit maximum-coverage proof
   output, and its partial fallback is not a maximum-coverage algorithm.
   CP-SAT flags are model-specific. Specific per-order causes need separate
   independent evidence; otherwise use global/unknown reason codes.
8. **Optional dependency:** CP-SAT requires OR-Tools. The experimental
   comparison must report unavailable dependency explicitly and never
   substitute a baseline-only result.
9. **Frontend test tooling:** no test runner is present. Lint/build plus
   backend API tests and a documented browser acceptance flow are proposed;
   automated browser tests require a separate tooling decision.
10. **Historical result integrity:** no Task 12 benchmark is rerun, migrated,
    or rewritten. Verify the result directory is unchanged in the later
    implementation task.

## 9. Stop/go criteria

Task 16 implementation may start only after explicit approval of this plan and
confirmation of the scenario-storage assumption. Any proposal to change solver
algorithms/objectives, production API behavior, safety verification, trusted
evidence, external data use, D-14 urgency semantics, D-24 co-location policy,
or other unapproved assumptions returns for a separate decision and approval.
