# Task 15 — Proposed Non-Operational Prototype Scope

**Status:** The project owner approved D-01, D-15, D-25, and D-29 on
2026-11-01 for the bounded offline, non-operational research scope and
reporting policy. This is not approval of a later implementation plan, a
railway rulebook, or authorization to schedule or release real maintenance
work. Every external railway decision remains blocked until its authority
approves it. Do not treat synthetic data, inferred occupancy, solver output,
or verifier output as an operational safety case.

## Executive summary and recommendation

The project owner approved a narrowly bounded **offline solver-comparison
experiment** using the current custom baseline solver and experimental CP-SAT
solver on frozen, reproducible simulation instances. The experiment may use
the public/bundled timetable CSV only as a fixed, non-authoritative input
fixture and deterministic generated work orders only as synthetic demand.
The comparison is limited to the constraints and objective terms actually
encoded in a versioned simulation specification.

The experiment must not claim actual train occupancy, operational feasibility,
railway safety, service disruption, crew/equipment feasibility, or solver
equivalence. Do not integrate CP-SAT into the production API or change the
verifier in this scope. Keep the current evidence boundary fail-closed.

**Remaining project decisions before extending the model:** the proposed
simulation assumptions D-14, D-16–D-24, and D-30 remain unapproved unless
individually recorded otherwise. The approved D-01/D-15/D-25/D-29 decisions do
not approve these extensions or resolve any external railway decision.

## Purpose and answerable research question

**Proposed research question:** Given identical frozen input instances and a
clearly stated prototype simulation model, how do the baseline and CP-SAT
implementations compare in runtime, complete-schedule rate, scheduled-work
coverage, search effort/termination, current objective score, and model-scoped
coverage/objective proof?

This question is answerable within the repository, subject to a fair matched
model and independent validation. It does **not** answer which solver is
operationally safer, which schedule is suitable for railway work, whether a
real-world timetable is complete, or which method is generally superior.

## Scope and exclusions

### In scope after project-owner approval

- Reproduce and benchmark the existing model under fixed seeds and immutable
  instance digests.
- Describe the existing model as a simulation: hour-of-day intervals,
  route/section/line labels, listed train windows, synthetic work orders, and
  fixed durations.
- Compare algorithms only when inputs, hard constraints, and measured
  objective definition are aligned. If a matched model cannot be established,
  report separate model results rather than a head-to-head equivalence claim.
- Independently validate the current modeled hard constraints without
  importing either solver's private compatibility/candidate helper.
- Report separate assignment coverage, termination, proof, and safety-evidence
  dimensions; include all unscheduled IDs and preserve unknown evidence.
- Freeze current compatibility behavior for reproducibility; do not add
  work-order interaction rules or operational constraints by inference.
- Keep solver outcomes and safety-verification status separate in research
  outputs. A UI label may explicitly call results “simulation only” if a
  later project task is approved.

### Out of scope

- Live or operational timetable feeds, dispatch interfaces, operational
  possessions, track closures, isolation commands/confirmation, or protection
  procedures.
- Operational infrastructure topology, adjacency, physical distance
  thresholds, equipment swept envelopes, or verified worksite geometry.
- Real work-order scheduling, crew qualification/availability, equipment
  inventory/capacity, legal duty/rest limits, travel or operational deadlines.
- Changing baseline candidate generation, CSP/AC-3/MRV/A*/annealing behavior,
  CP-SAT constraints/objective, verifier rules, API contracts, or frontend
  behavior as part of this documentation task.
- Promoting CP-SAT or claiming global optimality outside a solver's explicit,
  model-scoped proof.
- Any safety, regulatory, operational-readiness, or deployment claim.

## Evidence classification and current resource inventory

| Input/value | Classification and exact source | Usable in a simulation? | Operational safety conclusion? |
|---|---|---|---|
| `train_no`, `train_name`, `source_station`, `departure_time`, `arrival_time`, `distance`, `destination_station`, `days_of_week`, `classes`, `intermediate_stops` | Direct columns in `backend/app/data/IRCTC_cleaned.csv` (8,366 records per Task 14 audit). The app parses route stops and uses a subset; date/time-zone/authentication/completeness are not established. `days_of_week` is not used to generate occupancy windows. | Yes as source snapshot metadata; record file hash, parser version and selected fields. | No. Public CSV presence is not authority, currentness, service-day coverage, or completeness. |
| `TrainOccupancyWindow.train_no`, `section_id`, `track_line`, `start_time_hr`, `end_time_hr`, `train_start_km`, `train_end_km` | Application schema. Windows are created from route endpoint data; direction is inferred and section occupancy linearly interpolated in `data_engine._window_for_train`. Current section extents are code-derived. | Yes as deterministic, inferred model inputs; label as generated proxy. | No. Not verified real-time or physical occupancy. |
| `Route.route_id`, route names, length, `section_ids`, sub-sections | Code-defined in `backend/app/data_engine.py`; sub-sections use proportional corridor formulas. | Yes as stable-within-version simulation identifiers. | No. Not an authoritative asset register or topology. |
| `MaintenanceWorkOrder.work_id`, `department`, `section_id`, `track_line`, `heavy_equipment`, `defect_type`, `duration_hrs`, `urgency`, `co_location_allowed` | Schema fields. Default orders are generated deterministically: 30 per route, three routes/90 total; tiered fixed durations and labels/locations are synthetic. Custom uploads are caller data. | Yes when each field is tagged synthetic or caller-provided and the instance is frozen. | No. No actual maintenance order, urgency authority, qualified crew, equipment inventory, or worksite geometry. |
| Work-order schedule, solver outcome, search counts, objective, proof flags | Computed by baseline or experimental CP-SAT. Baseline does not produce a global objective certificate. CP-SAT proof applies to its encoded integer/scaled model only. | Yes as algorithm outputs and model-scoped metrics. | No. Solver proof is not evidence or approval. |
| Safety audit and `fol_rule_compliance_pct` | Computed by current verifier/API. Default evidence provider authenticates nothing; the API passes no timetable coverage and removes solver positive claims. | Only to demonstrate fail-closed prototype behavior and known/unknown audit outcomes. | No. Not a complete railway safety case; unknown evidence cannot be treated as pass. |
| Crew/equipment, worksite geometry/topology, possession/isolation/protection evidence, deadlines/dependencies | Absent or unverified in current project/dataset. | Only in explicit synthetic fixtures, after a project-owner decision and with a synthetic label. | No. Real use requires external owner, authoritative data and approvals. |

### Historical benchmark interpretation

Task 12 preserved 150 individual rows, 120 paired CP-SAT rows, 30 baseline
instances, sizes 10/25/50, and four CP-SAT time limits. All saved individual
runs found complete schedules; CP-SAT proved maximum coverage in every run.
This does not show objective equivalence or real performance: baseline has no
global objective certificate, CP-SAT's objective uses integer scaling, inputs
share timetable windows across seeds, and the 90-work-order generator does not
support 100/200-order workloads. The two partial curated cases have
`same_solver_outcome=False` while the preserved CSV says
`classification=equivalent`; Task 13 documents this inconsistency. Preserve
Task 12 files as historical evidence; do not silently relabel or regenerate
them.

## Proposed simulation constraint catalogue

“Supported” below means current code appears to encode the stated prototype
behavior, not that it is operationally approved. **Independent validation**
means a separate checker is needed; solver agreement or shared helpers do not
count. Constraint IDs trace to Task 14.

| Constraint / ID | Proposed simulation rule and needed inputs | Simulation class | Baseline today | CP-SAT today | Independent validation today / limitation |
|---|---|---|---|---|---|
| C-01 Listed train-window exclusion | Do not overlap supplied same-section/same-line window. Inputs: frozen `TrainOccupancyWindow` rows and work section/line/duration. For `heavy_equipment=True`, current model also excludes listed opposite-line train windows. | Hard in this experiment only | Yes, candidate filtering | Yes, shares baseline candidate helper | Partial test coverage exists; add independent exact interval validator. It excludes only supplied windows; no completeness claim. |
| C-02 Same modeled-resource overlap | Same section + same line + same department may not overlap; intervals use half-open overlap. | Hard in this experiment only | Yes | Yes, `NoOverlap` by section/line/department | Tests exist, but independent validator should implement separately. Does not define physical possession. |
| C-02 / C-14 Exact-window co-location | Cross-department jobs may overlap only when interval, section, and line match and both `co_location_allowed` are true. | Hard eligibility; objective reward is soft | Yes | Yes, compatibility plus merge objective | Curated/test cases exist; no shared site/resource/protection evidence. Treat as legacy simulation rule only. |
| C-15 Accounting | Every unique submitted work ID appears exactly once as scheduled or unscheduled; no unknown/duplicate IDs; counts agree. | Hard output invariant | Yes, output accounting | Yes, output accounting | Unit/API tests exist; independent API response validator still required. |
| C-09 Simulated horizon and duration | Fixed contiguous assignment within configured 0–24 hour simulation horizon; default candidate starts use a 0.5-hour grid plus latest fit. | Hard in this experiment only | Yes | Yes, shared candidate domains and intervals | Current input checks and solver tests. Not dated windows, deadlines, or real possession times. |
| C-08 / C-17 Generic resource transitions/capacity | Optional artificial resource IDs/calendars/capacities may be introduced only as synthetic tests, not inferred from `department` or `heavy_equipment`. | Synthetic hard constraint if later approved | No | No | No independent implementation; only after synthetic-fixture approval and independent resource checker. |
| C-06 / C-12 Crew skills and duty rules | No current implementation. Synthetic eligibility/availability may test solver mechanics only; do not use legal limits or real qualification claims without authority. | Synthetic fixtures only; real rule blocked | No | No | No. Operational data/policy requires external approval. |
| C-03 / C-04 / C-05 / C-10 / C-11 / C-13 / C-16 / C-18 | Adjacency/topology, geometry/clearance, actual deadlines/dependencies, possession/isolation, complete/fresh timetable and lifecycle invalidation. Do not invent values or evidence. | Blocked for operational implementation | Absent, partial, or verifier-only legacy constants | Absent or shares candidate behavior | No complete independent validation. External authority/data required. |
| C-07 Equipment fit/capacity and swept envelope | Current Boolean can be held as a synthetic attribute; actual equipment inventory, type compatibility, capacity and envelope are absent. | Out of scope for current prototype; synthetic tests only if separately approved | No actual resource model | No actual resource model | No; no inventory or approved envelope. |

### Constraint classes for follow-up

1. **Existing-data simulation now:** C-01, C-02 legacy co-location behavior,
   C-09, C-15. State exact assumptions in each run, and validate output
   independently.
2. **Synthetic fixtures only:** generic resource capacity, crew eligibility,
   equipment capacity, travel/setup, windows/deadlines, dependencies,
   shift-like calendars, and co-location variants. Require `D-*` simulation
   disposition and never present as railway rules.
3. **Blocked by external approval/evidence:** physical adjacency/topology,
   actual spatial clearances, authoritative train occupancy/completeness,
   possessions, isolation, protection, live change invalidation, real crew
   qualifications/legal duty limits, operational deadlines/priority, and
   safety verification.
4. **Out of scope:** production/API CP-SAT integration, live dispatch,
   operational release, and safety/regulatory acceptance.

The full crosswalk and phase gates are in
[`TASK15_IMPLEMENTATION_BOUNDARY.csv`](./TASK15_IMPLEMENTATION_BOUNDARY.csv).

## Safety and outcome boundary

These are research labels, not additional API behavior:

- **Solver-reported incumbent:** a solver produced an assignment it considers
  valid for its exact encoded input/configuration. Until independently
  checked, this is a solver result, not an independently validated witness.
- **Complete feasible assignment found:** every submitted work order is
  assigned exactly once and an independent validator accepts the result
  against the frozen simulation model. This is a constructive witness that a
  complete assignment exists for that encoded instance. It proves neither
  objective optimality nor any operational condition.
- **Simulation-feasible:** the independent checker accepts the assignment
  under the explicitly frozen simulation constraints and inputs.
- **Complete schedule:** all submitted work-order IDs are scheduled exactly
  once; this says nothing about objective optimality.
- **Partial schedule:** at least one but fewer than all submitted IDs are
  scheduled, with all omitted IDs identified.
- **Maximum coverage proven:** the solver establishes that no solution under
  the encoded model schedules more submitted work orders than the reported
  schedule. This is distinct from finding a feasible incumbent and from
  objective optimality.
- **Objective optimality proven:** the solver establishes the optimum of its
  exact encoded objective, including any numeric scaling. This is not proof
  of baseline-objective equivalence or operational cost optimality.
- **Feasibility not established:** no independently validated complete
  assignment was found and no infeasibility proof was produced. A time/node
  limit or other inconclusive termination belongs here.
- **Infeasibility proven within the model:** exhaustive search or a solver
  proof establishes that a complete assignment is impossible for the exact
  modeled instance. This is not a claim about a real railway or an individual
  job.
- **Search limit reached:** computation stopped before required proof. It is
  not infeasibility and must preserve any feasible incumbent separately.
- **Safety verified:** reserved for an authority-approved, evidence-backed
  independent verification workflow. The current prototype cannot establish
  this for railway operations; this label must not be used for simulation
  results.
- **Safety unverified:** evidence or required checks are missing, unauthenticated,
  incomplete, or unknown. Unknown is never a pass.

Solver outcome and evidence verification remain separate dimensions. The
current default provider authenticates neither timetable coverage nor
isolation. `source` labels, caller booleans, `fol_verified`, empty schedules,
or solver feasibility/coverage/objective proofs cannot establish
verification. Preserve
`safety_invalid` for known failures and `safety_unverified` for unknown checks
in the existing API. Do not change API/verifier in this scope.

## Project-owner decision summary

The following four project-team decisions were **APPROVED** by the project
owner on 2026-11-01, as reflected in the approval register. Their selected
options govern this bounded research scope; they are not operational
authorization and do not approve unrelated assumptions or external decisions.

| ID | Original decision | Recommended option | Alternatives | Consequences of recommendation | Blocks | Approval status |
|---|---|---|---|---|---|---|
| D-01 | What is the intended operational boundary and who is the railway authority for this system? | Approve offline-only, non-operational solver comparison; explicitly exclude operational planning/release. | Planning support with human authority; operational control under a separate railway-authority program. | Permits controlled experiments only. A broader boundary requires external authority, evidence, and assurance work. | Broader workflow still requires external approvals; Task 16 code changes require approval of its implementation plan. | **APPROVED by project owner, 2026-11-01.** |
| D-15 | What lexicographic order should disruption, schedule stability, workload balance, utilization, and co-location follow after hard feasibility and coverage? | Keep hard modeled constraints separate; report coverage first and current objective components individually; do not equate solver-specific scaled values. | Owner-approved lexicographic tiers; Pareto alternatives; approved weighted objective with units and sensitivity analysis. | Current baseline and CP-SAT objectives differ in coverage priority/scaling; baseline has no global objective proof. A common objective requires separate implementation and validation. | Objective-quality claims remain gated on independent objective evaluation; Task 16 plan approval is separate. | **APPROVED by project owner, 2026-11-01.** |
| D-25 | What solver outcome, proof state, partial output, unscheduled reason, and API-status semantics are canonical? | In research, report coverage, termination, proof flags, and evidence verification separately; preserve current backend behavior. | One enum with explicit precedence and metadata; defer operator UI/API semantics. | Avoids equating a limit with infeasibility or solver success with safety; does not authorize production API or verifier changes. | Future solver/API integration and operator-facing outcome semantics remain out of scope. | **APPROVED by project owner, 2026-11-01.** |
| D-29 | Which proof requirements must be met before presenting an objective as optimal or coverage as maximum? | Use proof only for the exact encoded model; distinguish a validated complete assignment, maximum-coverage proof, objective-optimality proof, and no proof. | Report bounds/gaps where available; omit optimality claims without proof. | CP-SAT proof applies to its scaled model; baseline has no global objective certificate. Without the relevant proof, make no maximum-coverage or optimality claim. | Proof claims require solver metadata and independent validation; no claim can exceed exact-model evidence. | **APPROVED by project owner, 2026-11-01.** |

### Existing behavior versus proposed simulation extensions

For reproducibility, an approved experiment may freeze and test existing
simulation behavior (including current section/line/department compatibility,
the exact-window co-location exception, candidate filtering, and ID
accounting) without treating it as an approved railway rule. This freeze does
not approve any extension or change to those semantics.

New crew, equipment, travel/setup, deadlines, dependencies, shift/duty,
topology, adjacency, clearance, possession, isolation, protection, or
co-location policies remain deferred, blocked, or out of scope as recorded in
the boundary and approval register. Synthetic versions require their own
explicit project-owner decision and must stay labeled synthetic; external
railway rules and evidence require the appropriate external authority. No
assumption is approved merely because it appears in a benchmark fixture.

## Project approval register and unresolved external approvals

[`TASK15_PROJECT_APPROVAL_REGISTER.csv`](./TASK15_PROJECT_APPROVAL_REGISTER.csv)
lists the four approved project-team decisions, still-proposed simulation
assumptions, and externally blocked decisions. Every Task 14 decision is dispositioned in
[`TASK15_DECISION_DISPOSITION.csv`](./TASK15_DECISION_DISPOSITION.csv).

Before any operational interpretation, the appropriate railway authorities
must separately resolve D-02 through D-13 and D-17/D-18/D-20/D-24/D-26 through
D-28 as applicable. A project-owner decision to run an offline experiment
cannot approve topology, clearances, movement authority, evidence, work rules,
crew qualifications, or deployment.

## Recommendation

Proceed only with the bounded offline experiment after the Task 16
implementation plan receives separate approval. Implementation can harden
reproducibility and independently validate the *existing simulation model*
without adding operational assumptions. Before claiming a fair solver
comparison, resolve model/objective mismatches and the Task 12 classification
discrepancy. Do not integrate CP-SAT into production or broaden the safety
verifier.
