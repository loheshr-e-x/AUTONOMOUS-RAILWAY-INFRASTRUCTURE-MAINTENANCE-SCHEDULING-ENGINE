# Task 15 — Research Evaluation Plan

**Status:** proposed protocol for project-owner approval; no benchmark was run
for this document. This plan evaluates software on an explicit simulation
model only. It does not evaluate railway safety, operational feasibility, or
authority to perform work.

## Research question and hypotheses

**Research question:** On identical, frozen synthetic instances under a
versioned model of the constraints both implementations are intended to
share, how do the baseline solver and CP-SAT compare in finding complete
assignments, maximizing scheduled-order coverage, runtime, search effort,
termination/proof, and the reported objective?

### Testable hypotheses (not established results)

- **H1:** CP-SAT may reduce runtime or improve coverage on some instance
  classes. Measure rather than assume; report distributions and failure/cap
  cases.
- **H2:** The solvers may return different schedules, even with equal counts,
  because search, objective hierarchy, partial fallback, and objective
  scaling differ.
- **H3:** Any equivalence claim is limited to the exact shared constraint
  model and independently validated fixture set. Current helper reuse means
  agreement alone is not independent validation.
- **H4:** Solver completion does not imply safety evidence or operational
  approval. No benchmark outcome tests or establishes those claims.

## Model and experiment boundary

The first evaluation tier should reproduce the existing simulation model:

- Work orders: current fields and deterministic synthetic orders; freeze
  selected order IDs, values and ordering.
- Timetable: one frozen digest of the bundled CSV-derived
  `TrainOccupancyWindow` set; label route direction and section occupancy as
  inferred simulation values, not verified movements.
- Time: current hour-of-day horizon and candidate grid, with all solver
  configuration captured. This is not a dated timetable.
- Hard simulated rules: listed-train candidate exclusion, same modeled
  section/line/department overlap, exact-window bilateral co-location
  exception, and complete request-ID accounting. These are legacy simulation
  rules, not approved operational rules.
- Out of the first tier: crew, skills, actual equipment inventory, travel,
  legal shift/rest, deadlines, dependencies, physical topology, actual
  clearances, possession, isolation, protection and external evidence.

Before any comparison described as “same model,” write a versioned crosswalk
for all constraints, precision/rounding, fixed/optional assignments, and
objective terms. The solvers currently share candidate-generation and
compatibility code; baseline searches for a complete assignment and may use a
greedy partial fallback, while CP-SAT first maximizes coverage then optimizes
an integer-scaled objective. If a truly matched objective/constraint model
cannot be established without changing solver behavior, report separate
solver/model results and limit claims to measured outputs; do not normalize
labels after the fact to make them look equivalent.

## Metrics and definitions

Record each raw run, not only aggregates. Every metric must include its source
and interpretation:

| Metric | Definition | Interpretation limits |
|---|---|---|
| Input identity | Canonical serialized work orders, train windows, configuration and model version hashed to an instance digest. | Same digest is required for pairing; it does not prove source truth. |
| Complete-schedule rate | Count of runs with every submitted work order assigned exactly once and accepted by the independent validator, divided by completed runs. | A complete validated assignment is a constructive witness that the encoded instance is feasible; it does not establish objective optimality. |
| Scheduled coverage | `scheduled_work_orders / total_work_orders`; also report scheduled IDs and count. | A coverage count does not prove maximum coverage unless proven. |
| Unscheduled work | Exact unique unscheduled IDs and count; validate that scheduled/unscheduled form a disjoint partition of submissions. | Do not infer individual cause from global infeasibility. |
| Runtime | Wall time from common run boundary, with model-build and solve times separately if reliably instrumented. | Compare on the same host/environment; disclose time limits and censored/stopped runs. |
| Search effort | Baseline explored nodes and any available CP-SAT branches/conflicts/propagations; report unavailable metrics as unavailable. | Node/branch counts are solver-specific and not directly comparable units. |
| Termination | Explicit terminal reason, configured node/time limit, and whether a feasible incumbent exists. | A limit is inconclusive, not proof of infeasibility. |
| Complete feasible assignment witness | Yes only when every submitted work order is assigned exactly once and the independent validator accepts the assignment against the frozen model. | This validated constructive witness establishes feasibility of that encoded instance. A solver-reported incumbent that has not passed independent validation is not yet a validated witness. |
| Feasibility not established | No independently validated complete assignment was found, and infeasibility was not proven. Record this when a search limit or other inconclusive termination prevents a conclusion. | This is not proof of infeasibility. A partial assignment does not establish complete feasibility. |
| Infeasibility proven | The solver or an independent exhaustive method establishes that no complete assignment exists for the exact encoded instance. Record the proof basis and termination state. | Do not infer this from no incumbent, a partial result, a timeout, or an outcome label alone. |
| Maximum-coverage proof | Whether evidence establishes that no model-feasible schedule includes more work orders than the reported schedule. For a complete schedule, the total submitted count is the trivial upper bound; otherwise this requires a solver proof. | Distinct from establishing feasibility of an incumbent and from objective optimality; applies only to the encoded instance. |
| Objective value | Independently recomputed objective components from the exact output and model version; preserve solver-native scaled value separately. | CP-SAT integer/scaled value is not numerically interchangeable with baseline score without a validated mapping. |
| Objective optimality proof | Solver’s explicit proof status for the exact encoded objective. | Baseline has no global objective certificate. CP-SAT certificate applies to its scaled mathematical model, not to an operational objective. |
| Constraint validation | Pass/fail from an independent checker for each modeled hard constraint. | Validator must not call solver private constraint helpers; this is not a railway safety verifier. |
| Reproducibility | Repeated same input/config/seed results, including schedule digest and proof/termination metadata. | A deterministic seed does not guarantee portability across solver/library/hardware versions. |
| Validated assignment rate | Fraction of completed runs with a nonempty returned assignment accepted by the independent checker; report complete and partial assignments separately. | A partial valid assignment does not establish complete feasibility or maximum coverage. Do not conflate with safety verification or operational feasibility. |

For elapsed-time summaries report individual observations plus mean, median,
standard deviation, quantiles, minimum/maximum, sample count, censored count,
and confidence interval or bootstrap method where the number of instances
supports it. State whether deviation is sample or population standard
deviation. Include every failed run and preserve partial outputs.

## Fairness and reproducibility controls

1. **Freeze instances first.** Generate each synthetic instance once; record
   canonical input JSON, SHA-256, seed, selected work IDs, train-window
   digest, generator/parser version and model version. Both solvers receive
   byte-equivalent canonical data.
2. **Freeze common semantics.** Record horizon, slot size, train clearance,
   work-order ordering, every hard constraint, objective definition/units,
   CP-SAT scaling/precision, and any solver-specific configuration. Do not
   compare differing constraints or objectives as if they were identical.
3. **Pair and alternate.** Pair by input digest. Randomize or counterbalance
   solver run order and time-limit order; document warm/cold state. Use the
   same machine, process limits, environment, dependency versions and
   concurrency policy. Capture Python, OR-Tools, OS, CPU and worker count.
4. **Separate time limits and outcomes.** Use predeclared budgets, repeated
   runs and deterministic seeds where supported. Record node/time limits,
   model-build time, solve time, termination reason and censored/time-limited
   runs. A complete incumbent accepted by the independent validator is a
   constructive feasibility witness, but does not prove maximum coverage or
   objective optimality. No complete witness plus a limit is inconclusive,
   not proof of infeasibility.
5. **Preserve results incrementally.** Append or atomically persist each
   completed result without replacing prior completed rows on failure.
   Store raw individual records as the source of truth; derive summaries and
   paired output from them and verify reproducibility of aggregation.
6. **Independent validation.** Implement a checker from the documented
   simulation rules, not from either solver's private helpers. Run it on
   every returned assignment; use exhaustive enumeration for small fixtures
   with an independent implementation. Include boundary-touch, empty,
   duplicate-ID, train overlap, same-resource conflict, co-location,
   partial/fallback and limit cases. Report any validator disagreement as a
   failed run.
7. **Proof-aware comparison.** Report complete feasibility witnesses,
   maximum-coverage proofs, objective-optimality proofs, and infeasibility
   proofs as separate results. Compare objective values only after a common
   independent objective evaluator and model mapping are established. Mark
   comparisons uninterpretable if one side has no relevant proof or if score
   scaling differs. A feasible schedule proves feasibility only; do not
   report maximum coverage or “optimal” without the corresponding proof.
8. **Workload limits.** Current generator offers 30 orders per route and 90
   total; historical Task 12 sizes are 10, 25 and 50. Do not claim observed
   100/200-order performance from this data. Larger synthetic cases require
   an explicitly approved generator/assumptions and separate result labels.
9. **Historical data integrity.** Task 12 is historical. Preserve its
   individual, summary, paired, constraint and exhaustive outputs. The
   120 paired rows share input digests, but there are only 30 baseline
   instances, and train windows are shared across seeds. Task 12 records all
   runs as complete; CP-SAT proved coverage for all, while objective proof
   varied by size/budget. Baseline has no objective proof. Two partial
   constraint rows have mismatched solver outcomes despite
   `classification=equivalent`; retain and disclose this discrepancy.
   Do not rerun or overwrite historical output as part of this proposal.

## Required interpretation separation

Report these independently:

1. **Complete feasible assignment found:** every submitted order is assigned
   exactly once and an independent validator accepts the schedule against the
   frozen model. This validated assignment is a constructive witness that a
   complete solution exists for that encoded instance. A solver-reported
   incumbent alone is not an independently validated witness.
2. **Maximum coverage proven:** evidence establishes that no schedule under
   the encoded model includes more submitted work orders than the reported
   schedule. For a complete schedule, the total submitted count is the
   trivial upper bound. Otherwise, a solver proof is required. This is
   distinct from merely finding a feasible incumbent and does not establish
   objective optimality.
3. **Objective optimality proven:** the solver proves the optimum of the exact
   encoded objective, including CP-SAT's integer scaling. It does not imply
   equivalence to the baseline objective or any operational cost.
4. **Feasibility not established:** no independently validated complete
   assignment was found and no infeasibility proof was produced. A limit,
   cutoff, or inconclusive termination belongs here, not under infeasibility.
5. **Infeasibility proven:** exhaustive search or a solver proof establishes
   that the exact encoded instance has no complete feasible assignment.
   Record the proof basis; do not infer this from an outcome label.
6. **Model equivalence:** both solvers implement the same documented hard
   constraints and objective semantics within declared precision, as checked
   against independent reference cases. Shared helper use is not independent
   evidence.
7. **Safety verification:** separate authenticated, authority-approved process.
   Current benchmark inputs and verifier cannot establish this.

Use outcome language that preserves coverage and termination separately.
`partial` does not mean infeasible for each omitted order. `unschedulable`
may be described as infeasibility only when an explicit proof establishes no
complete solution for the stated model; otherwise report that feasibility was
not established and preserve the actual termination reason.
`search_limit_reached` is not infeasibility. `no_work` is neither success nor
safety verification. Safety unknown remains unverified; known failure remains
invalid even if another check is unknown.

## Criteria for defensible research claims

A claim that “solver X was faster” must identify benchmark corpus, hardware,
matched instances, constraints, budgets, aggregation method and dispersion.
A claim that “solver X scheduled more work” must compare paired IDs on matched
models and distinguish incumbent from coverage proof. A claim about objective
quality needs a common independent evaluator and relevant proof/bounds; the
baseline's lack of a global optimality certificate must be explicit. A claim
of model equivalence needs constraint-by-constraint traceability, independent
small-instance checks and boundary tests; a few shared-helper comparisons are
insufficient.

No set of these solver benchmarks licenses a safety, compliance, operational
performance, or deployment claim. Task 13's current recommendation remains
**B — Keep CP-SAT experimental** until its model, evidence, validation, API/UI,
and governed-data gates are resolved.
