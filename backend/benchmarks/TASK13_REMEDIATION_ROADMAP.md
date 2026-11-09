# Task 13 — Readiness Remediation Roadmap

This is a gated roadmap for deciding whether the experimental CP-SAT solver
could become the prototype's primary solver. It is not approval for live
railway use, an operational safety case, or a recommendation to change the
production solver now. No application changes are part of this assessment.

## Gate 0 — Define the operational model before implementation

**Decision owner:** railway operations and safety domain owners, supported by
the application/model owners.

Resolve and approve a versioned constraint specification covering:

- The meaning and granularity of a possession/worksite, sections, track
  direction, adjacent track, and physical clearance.
- Which timetable sources and operating-day/date/time-zone semantics are
  authoritative; how completeness, freshness, cancellation, and disruption
  updates are established.
- Crew, skill/certification, equipment type/capacity, access, travel/setup,
  shift/rest, work windows, deadlines, dependencies, and task compatibility.
- Whether heavy equipment or any maintenance can conflict with opposite-line
  maintenance, and how shared access, protection, and possession releases work.
- Whether partial schedules are useful outputs, what coverage objective they
  represent, and how urgency and the existing secondary objective are ranked.
- Required failure, unknown, and non-applicable semantics for every verifier
  rule. Unknown evidence must not be recast as a pass.

**Acceptance criteria**

1. Every operational rule has a named owner, an unambiguous trigger, required
   input fields, a decision table for pass/fail/unknown/not-applicable, and
   at least one testable example.
2. The model explicitly distinguishes solver feasibility from verified
   operational safety; no solver status alone implies a safety finding.
3. Every required field has a defined authoritative source and validation
   policy; fields not available to the system remain explicit blockers rather
   than inferred values.

**Exit:** do not implement new scheduling constraints until this gate is
approved. A domain decision is needed for constraints that have no existing
schema representation.

## Gate 1 — Establish authenticated evidence and input integrity

Implement only real provider boundaries after the source owners and protocols
are identified. The current default must remain fail-closed. A source-name
allowlist is not authentication; caller-supplied coverage or isolation labels
must remain untrusted. Do not populate a trusted-source list merely to produce
passing checks.

**Acceptance criteria**

1. Timetable completeness is tied to authenticated provider identity and a
   specific route, operating date/time interval, version, freshness window,
   and covered lines/sections; absent, stale, partial, mismatched, or
   contradictory records produce unevaluated checks or explicit failures per
   the approved rule.
2. Traction-isolation evidence identifies the relevant worksite, circuit,
   interval, state, authority, and validity period and is authenticated
   independently of the schedule request. Positive Boolean/source-string
   inputs cannot satisfy it.
3. API tests exercise the real trust boundary with missing, forged, stale,
   partial, mismatched, and contradictory evidence. No mock provider returns
   trusted evidence in acceptance tests.
4. Known conflicts remain failures even if other checks lack evidence.
   Empty schedules/audits, partial solver outputs, and solver-provided
   `fol_verified` never establish verified success.
5. Evidence records are validated at the API boundary, retained with
   provenance in audit output, and invalid evidence errors are explicit.

**Exit:** a non-empty schedule cannot be reported verified unless every
applicable required check has authenticated supporting evidence and the
independent verifier agrees. Until then, the API reports unverified.

## Gate 2 — Decide and test the mathematical model

Create a formal mapping from the approved Gate 0 requirements to schema fields,
candidate generation, baseline constraints, and CP-SAT constraints. Reuse
helpers where appropriate, but use an independent validator/reference for
small-instance checks so shared implementation mistakes are detectable.

**Acceptance criteria**

1. Every approved hard constraint is represented in both candidate solvers or
   is explicitly documented as unsupported; no hard constraint is relaxed
   without an approved decision.
2. The baseline/CP-SAT comparison accounts for time precision, durations,
   half-open interval semantics, all resource limits, adjacency/geometry,
   and co-location. Any integer scaling/rounding preserves the approved
   ordering, or its effect is explicitly approved and tested.
3. Fixed and generated small cases compare constraint satisfaction against an
   independent exhaustive reference. Include boundary tests for interval
   endpoints, midnight/time-zone changes, missing occupancy, spatial
   thresholds, resource capacity, and infeasible combinations.
4. Test separately: feasible incumbent, proven maximum coverage, proven
   infeasibility, objective optimality, and limit stop. A feasible incumbent
   is not mislabeled as proven optimal.
5. Decide one consistent API meaning for `partial` and `unschedulable`.
   Preserve the distinction between “no complete assignment exists” and “a
   maximum-coverage partial assignment exists”; never call a global
   infeasibility proof an individual work-order cause.
6. Every request ID appears exactly once as scheduled or unscheduled; test
   duplicates, unknown IDs, fallback, per-line combination, and all solver
   outcomes.

**Exit:** no unexplained baseline/CP-SAT constraint or objective discrepancy
remains for the approved model. “Equivalent” claims are limited to what the
tests and formal mapping actually cover.

## Gate 3 — Independent output validation and API integration

Keep the baseline API unchanged until the experimental CP-SAT output can pass
the same independently implemented validation path. CP-SAT is not currently
called by `backend/app/main.py`; integrating it should be a separately
reviewed, reversible change behind an explicit configuration/experiment
boundary.

**Acceptance criteria**

1. Both solvers' outputs pass the same deterministic schedule validator for
   all hard constraints before any schedule is returned as solver-successful.
2. The evidence-backed safety verifier operates on the validated output and
   authoritative evidence, not on solver assertions. Failure and unknown
   statuses take precedence over solver completion; compliance has a
   documented denominator and is `None` for empty/incomplete/inconsistent
   audits.
3. API contract tests cover `no_work`, `success`, `partial`,
   `unschedulable`, `search_limit_reached`, `safety_invalid`, and
   `safety_unverified`, including full ID accounting and inconsistent counts.
4. API exposes solver outcome and termination/proof detail separately from
   safety verification. No path upgrades partial, capped, empty, or unknown
   evidence to success/verified.
5. Integration is opt-in, can be disabled without data migration, and cannot
   fall back silently to a success-shaped response after a solver or
   validation error.

**Exit:** reviewed tests prove the production route cannot mistake a feasible
incumbent or a solver's own metadata for independent safety verification.

## Gate 4 — Make outcomes understandable to operators

Frontend changes are required before any evaluation intended for an operator.
The current UI does not render `solver_outcome` or the explicit unscheduled
IDs.

**Acceptance criteria**

1. Display distinct solver outcome, solver proof/termination state, safety
   verification state, and compliance state. Safety `unknown` is visibly
   different from a pass.
2. Display scheduled and unscheduled work-order IDs and counts. Do not assign
   per-order failure reasons unless the backend has evidence for those
   reasons.
3. Explain that `search_limit_reached` is inconclusive, and that
   `unschedulable` applies to the modeled instance/constraints, not to an
   individual work order or the real railway in general.
4. UI integration tests cover the status matrix and empty/partial outcomes.

**Exit:** an operator cannot reasonably read solver completion, absent
compliance data, or a partial plan as verified safe or complete.

## Gate 5 — Re-evaluate on representative, governed data

Benchmark only after Gates 0–2 are complete and with approved, de-identified
representative data. Do not treat the current Task 12 results as production
performance evidence.

**Acceptance criteria**

1. Inputs cover the approved size and operational distributions, including
   work orders above 90 only when a governed source exists; no synthetic
   extrapolation is represented as observed operations.
2. Paired comparisons use identical input digests, constraints, objective
   semantics, time limits, and hardware/software. Run order/limit order is
   controlled or randomized and documented.
3. Preserve individual results incrementally and safely; report failures,
   censored runs, incomplete output, mean/median/dispersion and uncertainty,
   feasibility/coverage, objective quality, proof rates, and memory only
   when measured reliably.
4. Compare objective quality only against a reference with a relevant proof
   or a clearly labeled incumbent. Baseline's lack of a global optimality
   certificate must remain visible.
5. Include independent repeat seeds, tail latency, solver restarts, cold
   start if relevant, and constrained/degenerate cases.

**Exit:** results support only the scope and data distribution actually
measured. Speed does not establish safety, model completeness, or global
optimality.

## Final promotion decision

Revisit the decision only after all gates pass, with recorded sign-off from the
model, safety, and operations owners. The current evidence supports **B — Keep
CP-SAT experimental**. This roadmap does not grant authorization for live
railway scheduling or operational control.
