# Task 13 — Operational Constraint Fidelity and CP-SAT Integration Readiness

## Executive decision

**Decision B — Keep CP-SAT experimental.**

CP-SAT shows a clear runtime advantage on the preserved generated instances and
proved maximum coverage in every measured run. That does not justify making it
the primary solver for an operational railway task. Neither solver models
important operational resources and work-order constraints; train occupancy
input is not authenticated as complete; no authenticated traction-isolation
provider is integrated; the production API does not invoke CP-SAT; and the
benchmark is based on generated work orders with a fixed set of timetable
windows. There are also meaningful differences in objective priorities,
partial-schedule construction, and outcome labels.

The current API correctly prevents a solver result from being called safety
verified when required evidence is absent: it clears positive isolation and
`fol_verified` claims, supplies no timetable-coverage evidence to the verifier,
and returns `safety_unverified` for non-empty schedules with unknown checks.
This conservative boundary is useful, but it does not convert the schedules
into operationally validated plans.

## Ranked findings

1. **Critical readiness blocker — required evidence providers are not
   integrated.** `logic_engine.EvidenceProvider` authenticates no records by
   default (`backend/app/logic_engine.py:22-38`); `main.generate_schedule`
   strips solver evidence and calls the verifier without timetable coverage
   (`backend/app/main.py:181-191`). Thus schedule success is not a safety
   verification result. The current API remains conservative; replacing the
   provider with a source-label allowlist would not authenticate evidence.
2. **High — material operating constraints cannot be represented or checked.**
   Work-order schema fields are limited to task labels, location, duration,
   department, priority, flags, and optional coordinates
   (`backend/app/schemas/contracts.py:48-80`). Crew/qualification/equipment
   capacity, travel/setup/rest, deadlines, dependencies, and possession
   windows have no inputs. Neither solver can enforce absent requirements.
3. **High — solver models/objectives/outcomes are not fully equivalent.**
   Baseline seeks a complete solution and may return greedy partial fallback
   after exhaustion (`backend/app/solver_engine.py:318-365, 550-740`); CP-SAT
   maximizes coverage then optimizes its integer secondary objective
   (`backend/app/cpsat_solver.py:60-258, 311-345`). Two saved partial cases have
   equal status/count but different outcome labels. CP-SAT's model and
   proof flags are not production API behavior.
4. **High — the preserved benchmark supports a narrow synthetic result only.**
   It contains 10/25/50 orders and one shared family of train windows; the
   generator has 90 synthetic orders total (`backend/benchmarks/README.md:31-35`,
   `backend/app/data_engine.py:312-355`). No 100/200-order result or
   representative operational timetable study exists. Baseline has no global
   objective proof, so paired objective quality is not established.
5. **Medium — a machine-readable constraint report contradicts its own
   outcome columns.** In
   `backend/benchmarks/task12_results/constraint_equivalence_results.csv`,
   `same_resource_overlap_same_department` and
   `cross_department_partial_overlap` both have `same_status=True`,
   `same_solver_outcome=False`, but `classification=equivalent`. The Task 12
   report prose correctly warns that outcomes differ
   (`backend/benchmarks/TASK12_REPORT.md:101-109, 164-169`); consumers of the
   CSV classification alone could nevertheless misread the rows. This
   assessment records the discrepancy without modifying the preserved result.
6. **Medium — frontend hides outcome fields already present in its response
   type.** The UI shows only `result.status`
   (`frontend/app/page.tsx:218`) and scheduled/total metrics
   (`frontend/components/MetricsCards.tsx:41-43`); it does not show
   `solver_outcome` or `unscheduled_work_ids`, although both are typed
   (`frontend/lib/types.ts:44-62`).

## Scope and method

Inspected the current solver, verifier, schemas, API, tests, Task 12 runner and
preserved CSVs, benchmark documentation, dataset loading/generation code, and
frontend response consumers. The four Task 13 artifacts are an assessment only;
no solver, API, test, frontend, dependency, dataset, or Task 12 result file was
changed. No benchmark was run for this assessment.

The repository includes `backend/app/data/IRCTC_cleaned.csv` (8,366 rows) and
benchmark documentation, but no original implementation plan or standalone
dataset-provenance document was found in the repository. The data engine
selects route-serving trains and estimates section occupancy by linear
interpolation between route endpoints (`backend/app/data_engine.py`,
`_train_data_path`, `_cached_train_schedules`, `_window_for_train`). It does
not use the timetable's `days_of_week` column when building windows. This
schedule is therefore input metadata for the prototype, not proof of the
current operational timetable, dispatch authority, or timetable completeness.

The availability of a CSV or custom uploaded timetable is distinct from
evidence that it is complete and current. `main._trains_for` selects one of
these lists, while the verifier requires an authenticated `TimetableCoverage`
record to establish that no unlisted train occupies a period.

## Operational constraint fidelity

| Area | Classification | Observed implementation | Operational consequence / gap |
|---|---|---|---|
| Train occupancy on the same section and line | **Implemented in solver; completeness not established** | Baseline `_candidate_starts` filters overlapping listed train intervals. CP-SAT uses that candidate filter. | An omitted train can be treated by either optimizer as available time. The API's independent verifier then reports unknown clearance because no authenticated timetable coverage is supplied. |
| Section and track-line distinction | **Implemented in modeled identifiers** | Conflicts are keyed by section and line; same-line work in different sections can overlap. | Section/line identifiers are not physical worksite boundaries or proof of track possession limits. |
| Occupancy intervals | **Partially implemented / simulation assumption** | Data engine builds 24-hour section windows and line direction from route endpoints, splitting crossings of midnight and linearly interpolating train position. Solver uses half-open overlap (`start < other_end && other_start < end`). | No date/operating-day association, signalling-system state, actual train trajectory, uncertainty, or authority to block/release track is represented. Raw data's days-of-week field is not consumed by window generation. |
| Timetable completeness/authentication | **Not implemented** | `EvidenceProvider` defaults to authenticating no coverage. `main.generate_schedule` passes no `TimetableCoverage`. | A source label or uploaded list is not proof that the list is complete or current. Free time may be used for candidate generation, but the result is correctly marked unverified by the API. |
| Heavy equipment versus adjacent-line trains | **Implemented as a coarse solver exclusion; verifier has a separate spatial check** | Both optimizers reject heavy-equipment work that overlaps any listed train on the other line in the same section. Verifier checks the opposite line symmetrically and requires 1 km separation for concurrent work, with complete adjacent-line coverage. | Optimizer uses a blanket adjacent-line temporal exclusion, not actual spatial clearance; missing timetable completeness still leaves verifier status unknown. |
| Heavy equipment versus opposite-line maintenance | **Not implemented** | Baseline `_compatible` permits all different-line maintenance overlap. CP-SAT preserves that behavior. Verifier's adjacent-track rule examines trains, not another maintenance assignment. | Whether the worksite/equipment envelope can foul the other line is an unresolved operational engineering decision. Matching the baseline is not a safety justification. |
| Spatial track buffers | **Verifier-only and partially supported by inputs** | Verifier checks concurrent same-line exposure against 1 km, or 2 km for traction/heavy work; adjacent heavy equipment uses a 1 km rule. It fails closed for concurrent pairs with missing/malformed geometry. | Solver output does not populate worksite km endpoints. The verifier's geometric results depend on supplied coordinates; interpolation and section IDs do not establish accurate worksite geometry. |
| Crews and crew availability | **Not implemented / data unavailable** | No crew entities, calendars, or capacity constraints in work-order/config schemas or either model. | Schedules may assign simultaneous jobs that require the same unavailable crew or skill. |
| Skills/certifications | **Not implemented / data unavailable** | Department is used as a conflict/resource label, not a personnel qualification. | No certification, work authorization, or crew-to-task eligibility check. |
| Equipment capacity/compatibility | **Not implemented / data unavailable** | `heavy_equipment` is a boolean used for adjacent train filtering and an enhanced verifier buffer, not an equipment inventory or equipment capacity. | No machine availability, equipment type, setup, or competing use constraint. |
| Travel, setup, shift/rest limits | **Not implemented / data unavailable** | No location transition or crew-work time model. Three eight-hour bins appear only in the workload-balance objective. | Cannot establish that a crew/equipment team can reach the next site or comply with duty/rest rules. |
| Duration | **Implemented as fixed, non-preemptive duration** | Work orders have one positive `duration_hrs`; candidate/interval choices reserve one contiguous interval. | No uncertainty, work phases, setup/clearance padding, or splitting/preemption. Schema limits duration to 8 hours but not work-time windows. |
| Work windows/deadlines | **Not implemented / data unavailable** | No per-order earliest start, latest finish, deadline, or possession window in `MaintenanceWorkOrder`. | The model can schedule beyond a real deadline or incompatible operating window if not represented as a train conflict. |
| Dependencies/precedence | **Not implemented / data unavailable** | No dependency fields or precedence constraints. | Related jobs may be scheduled in an invalid order. |
| Priority/urgency | **Partially represented** | Urgency affects MRV tie-breaking, A* heuristic, and CP-SAT decision order; it is not an explicit objective weight or deadline. | No guarantee critical work is scheduled first or prioritized in an optimal result. |
| Work-type compatibility | **Not implemented except department/co-location rule** | `defect_type` is descriptive text. Compatibility depends on section, line, department, and the co-location flag. | No permit, method, access, possession, electrical, or task-specific constraint mapping. |
| Co-location | **Implemented as a narrow exception and objective reward** | Different departments may overlap only on the exact same interval, section, and line when both allow it; baseline/CP objective rewards merges. | No shared worksite/access or coordination validation; exact matching interval is a simplifying assumption. |

### Verifier evidence behavior

The verifier has five named audit rule families: scheduled-time validity;
passenger-train clearance; minimum distance buffer; adjacent-track heavy
equipment buffer; and traction-power isolation. The forward-chaining rules
derive clearance, isolation, distance, and adjacent-track violations from the
facts assembled in `logic_engine.verify_safety_invariants`.

- A listed same-line train overlap is a known clearance failure, regardless of
  coverage evidence. A non-overlapping listed train does not prove that no
  other train exists; without authenticated coverage, clearance is unknown.
- A concurrent same-line pair with invalid/missing spatial intervals yields an
  unevaluated distance check. A measured separation below the applicable
  1/2-km threshold fails.
- Heavy-equipment work checks the opposite line in both directions. A known
  concurrent train within 1 km, or with unverifiable location, fails closed;
  no violating train without authenticated adjacent-line coverage is unknown.
- Traction work without positive authenticated isolation is unknown; explicit
  negative isolation is a failure. The default provider authenticates neither
  coverage nor isolation. `source` labels alone have no authority.
- Non-traction isolation is marked passed as not applicable. The API removes
  solver-supplied `fol_verified`, `power_isolated`, and source labels before
  verification. An empty schedule produces no audit and is not considered
  verified.

In the current API path, the verifier receives the solver schedule and selected
train windows but no coverage record or integrated provider. Therefore a
non-empty schedule cannot demonstrate a fully verified result under the
current default provider. The API returns unknown checks as `safety_unverified`,
keeps compliance `None` for empty/incomplete/disagreeing audit results, and
gives known failures precedence as `safety_invalid`
(`backend/app/main.py`, `generate_schedule`). This is conservative, not a
claim that the underlying schedule is safe.

## Baseline versus CP-SAT equivalence matrix

The full machine-readable comparison is in
[`TASK13_SOLVER_EQUIVALENCE.csv`](./TASK13_SOLVER_EQUIVALENCE.csv).

Key source findings:

1. Both solvers normalize the same basic work orders/trains and use the same
   candidate-start generator and `_candidate_starts` train filter. CP-SAT
   reuses the baseline `_compatible` function for cross-department
   incompatibilities; it adds optional intervals/`NoOverlap` by
   section/line/department and pairwise Boolean incompatibility for
   cross-department overlaps.
2. Both reject same-department overlaps on a section/line and allow
   cross-department overlap only at the same exact window when both orders
   permit co-location. Different lines are treated as independent, including
   heavy-equipment maintenance versus maintenance on the other line.
3. CP-SAT **maximizes scheduled-order count first**, proves that maximum if it
   can, then minimizes its secondary objective at that count. Baseline
   backtracking first seeks a complete assignment; on exhausted search it
   uses a greedy partial fallback, not a maximum-coverage proof. Thus partial
   schedule choice and optimization priority differ even where both return
   the same count in the small curated cases.
4. The secondary objective is based on disruption, department/shift workload
   imbalance, and co-location reward. CP-SAT reuses disruption costs and
   encodes the other terms as an integer objective; duration/weight rounding
   and integer scaling mean it is an approximation, not an exact proof of
   equivalence for all input values. CP-SAT rejects values not representable
   at its selected time/duration precision. Baseline A* uses a bounded search
   with its own heuristic; simulated annealing can alter a baseline complete
   solution. Neither baseline result exposes a global objective certificate.
5. In two preserved constraint cases, both statuses are `partial` and both
   schedule one of two orders, but baseline `solver_outcome` is
   `unschedulable` while CP-SAT's is `partial`. Baseline means its search
   failed to find a complete assignment and was exhausted, then returned a
   partial fallback; it does not mean the returned fallback assignment is
   impossible. CP-SAT's outcome describes a proven maximum-coverage partial
   schedule. The distinction is retained in the CSV and must not be collapsed.
6. CP-SAT is an independent module, not an API option. `main.py` imports and
   calls only `solve_maintenance_schedule`; no CP-SAT result is currently
   passed through the production API verifier.

## Task 12 benchmark interpretation

The preserved files were read directly, not inferred from the earlier report:
150 individual rows, 30 baseline runs, 120 CP-SAT runs, 15 summaries, and 120
paired comparisons. There are ten seed values and three sizes (10, 25, 50).
Every run returned a full schedule; there were no externally censored
observations. The baseline outcomes are all `success`, while its instrumentation
records search-cap hits in 2/10 10-order runs and all 25- and 50-order runs.
CP-SAT proved maximum coverage in 120/120 runs.

| Solver / size | Limit | Mean sec | Median sec | Population SD sec | Full schedules | Objective proof |
|---|---:|---:|---:|---:|---:|---:|
| Baseline / 10 | external 120s | 5.582 | 2.197 | 7.204 | 10/10 | 0/10 available |
| Baseline / 25 | external 120s | 53.930 | 55.096 | 12.590 | 10/10 | 0/10 available |
| Baseline / 50 | external 120s | 85.376 | 89.931 | 15.677 | 10/10 | 0/10 available |
| CP-SAT / 10 | 5s | 0.023 | 0.022 | 0.007 | 10/10 | 10/10 |
| CP-SAT / 10 | 10s | 0.022 | 0.021 | 0.007 | 10/10 | 10/10 |
| CP-SAT / 10 | 30s | 0.022 | 0.021 | 0.007 | 10/10 | 10/10 |
| CP-SAT / 10 | 60s | 0.021 | 0.020 | 0.007 | 10/10 | 10/10 |
| CP-SAT / 25 | 5s | 1.807 | 1.083 | 1.718 | 10/10 | 8/10 |
| CP-SAT / 25 | 10s | 2.771 | 1.071 | 3.586 | 10/10 | 9/10 |
| CP-SAT / 25 | 30s | 4.771 | 1.070 | 8.819 | 10/10 | 9/10 |
| CP-SAT / 25 | 60s | 6.266 | 1.075 | 13.168 | 10/10 | 10/10 |
| CP-SAT / 50 | 5s | 5.002 | 5.002 | 0.000 | 10/10 | 0/10 |
| CP-SAT / 50 | 10s | 10.002 | 10.002 | 0.000 | 10/10 | 0/10 |
| CP-SAT / 50 | 30s | 26.403 | 30.002 | 7.243 | 10/10 | 2/10 |
| CP-SAT / 50 | 60s | 50.408 | 60.002 | 19.205 | 10/10 | 2/10 |

Full-schedule completeness and maximum-coverage proof are different: at 50
orders CP-SAT returned complete incumbents in all runs and proved maximum
coverage in all runs, but usually did not prove the secondary objective
optimal. The baseline's all-`success` outcomes likewise do not mean its
searches proved objective optimality; the reported cap counts show the bounded
search stopped in many runs.

The paired CSV has matching instance digests for all 120 comparisons, but zero
pairs are marked objective-interpretable because the baseline lacks an
optimality proof. The data-engine generator provides 30 synthetic work orders
per route, 90 total; 100- and 200-order benchmark scenarios are not supported
without new data. The benchmark reorders/selects generated work orders and
varies the configured random seed, but shares the same timetable windows
across the cases. Ten seeds are not ten independent operational timetable
scenarios. Run order alternates by repetition, while CP-SAT limits are
consistently run in a fixed sequence. The corpus is too small and synthetic
to establish production performance, tail risk, operational feasibility, or
general superiority.

## API and frontend outcome visibility

The backend response contract distinguishes `status` from `solver_outcome`,
includes `unscheduled_work_ids`, and includes audit entries with `passed`
true/false/null. `status` can be a safety status (`safety_invalid` or
`safety_unverified`) while `solver_outcome` retains a solver result such as
`partial` or `search_limit_reached`. This distinction is correct but must be
shown explicitly.

The current dashboard displays only `result.status` next to “Time-Space
Schedule” (`frontend/app/page.tsx`, around line 218); it does not display
`solver_outcome` or `unscheduled_work_ids`. The metrics card gives a
scheduled/total count, but not omitted IDs or a reason
(`frontend/components/MetricsCards.tsx`). Audit entries attach mostly to
scheduled work and do not provide a per-unscheduled-order cause. The UI can
therefore hide whether a status reflects solver completion, safety evidence,
partial coverage, or search termination. The response types already expose
the relevant status and ID fields (`frontend/lib/types.ts`), but display code
does not consume them. The compliance card shows `—` for null without an
explicit “unknown/unverified” explanation; the audit drawer can say
“FOL verification unavailable per assignment,” but it is not a run-level
status.

Minimum UI-only changes before relying on operator interpretation:

- Show separate, prominent solver outcome and safety-verification badges;
  never use solver `success` as a safety badge.
- Show scheduled and unscheduled counts and IDs. For an unscheduled order,
  say “not scheduled; solver-level reason unavailable” unless a solver has
  a separately justified cause. Do not infer the order is individually
  impossible from a global infeasibility result.
- Label `partial`, `unschedulable`, and `search_limit_reached` distinctly and
  explain that a search cutoff is not proof of infeasibility.
- Label null compliance as “not verified / evidence incomplete,” not as a
  missing visual value that can be mistaken for zero or success.
- Preserve the audit details and show known failures even when other checks
  are unknown.

## Risks, limitations, and promotion recommendation

- The solver's feasibility model is not a complete railway operations model:
  no crew/skill/equipment capacity, travel/setup, shift/rest rules, work
  precedence, deadlines, or validated worksite possession semantics exist.
- The timetable mapping is synthetic/derived metadata and has no authenticated
  completeness signal in the API. Positive traction-isolation and
  `fol_verified` assertions are not accepted as proof.
- The verifier is not a complete operational safety case, and the safety
  thresholds/physical assumptions themselves require competent domain review.
- CP-SAT's constraints partly reuse baseline helpers, which is useful for
  consistency but not independent validation. Exhaustive comparison covers
  only three tiny cases plus a curated constraint matrix.
- The benchmark shows speed on these generated cases, not general superiority;
  the baseline has no optimality certificate, and partial-solution semantics
  differ.
- Current CP-SAT results are not routed through the FastAPI production path.

**Decision B — Keep CP-SAT experimental.** Do not promote it to the primary
prototype solver until the P0 safety/data boundary and P1 model, outcome,
validation, and UI gates in [`TASK13_REMEDIATION_ROADMAP.md`](./TASK13_REMEDIATION_ROADMAP.md)
are satisfied. Even then, promotion within the prototype would not establish
real-world safety or operational readiness.
