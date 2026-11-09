# Task 14 — Formal Operational Constraint Specification

**Status:** implementation-neutral requirements baseline for domain review
**Decision:** not an operational rulebook, safety case, or authorization to
schedule live railway work
**Source of truth for current prototype facts:** the checked SymbIO-Block
source, tests, preserved Task 12 benchmark outputs, and Task 13 reports named
below. Statements marked **proposed** are requirements for review, not facts
about any railway.

## 1. Purpose, boundary, and evidence labels

This specification defines information and decisions that a future
railway-maintenance scheduling model would need before solver or verifier
changes are designed. Railway operations, infrastructure, maintenance, safety,
and data-governance owners must approve any railway-specific rule, threshold,
source, or authority. A solver result means only that the solver found an
assignment under the encoded model. It does not by itself establish possession
authority, isolation, worksite protection, legal compliance, or safe operation.

Use the following labels throughout:

- **Verified project fact:** directly present in the current repository or
  preserved output.
- **Prototype assumption:** a simplifying behavior encoded today; it is not
  asserted to be an operational rule.
- **Proposed requirement:** a candidate system capability that requires
  domain-owner approval and authoritative data.
- **Unresolved decision:** an item in
  [`TASK14_DOMAIN_DECISIONS.csv`](./TASK14_DOMAIN_DECISIONS.csv); no default
  has been silently selected.

### 1.1 Verified current-project facts

1. `MaintenanceWorkOrder` contains a work ID, department, section, track line,
   heavy-equipment Boolean, descriptive defect type, fixed duration, urgency,
   and co-location Boolean. It has no crew, equipment inventory, work window,
   deadline, dependency, possession, isolation circuit, or date fields
   (`backend/app/schemas/contracts.py`, `MaintenanceWorkOrder`).
2. `TrainOccupancyWindow` contains train number, section, line, hour-of-day
   start/end, and optional kilometer endpoints. `TimetableCoverage.source` is
   documented as informational; the default `EvidenceProvider` authenticates
   nothing (`contracts.py`, `logic_engine.EvidenceProvider`).
3. The baseline uses half-open interval overlap, a 0.5-hour default candidate
   grid, one fixed contiguous duration, same-section/line conflicts, and a
   heavy-equipment filter against listed trains on the opposite line
   (`solver_engine._overlaps`, `_candidate_starts`, `_compatible`). These are
   prototype model choices, not approved railway limits.
4. The verifier currently encodes 1,000 m standard, 2,000 m enhanced
   (traction or heavy equipment), and 1,000 m adjacent-track buffers
   (`logic_engine` constants). No source in the reviewed project establishes
   these as operationally approved values. They are **not adopted here**.
5. The bundled CSV has 8,366 rows and fields
   `train_no, train_name, source_station, departure_time, arrival_time,
   distance, destination_station, days_of_week, classes, intermediate_stops`.
   The data engine parses route stops, infers direction, and linearly
   interpolates section occupancy; it does not use `days_of_week` when
   creating windows. The repository does not establish source authentication,
   timetable completeness, current service date, delay/cancellation state, or
   operational authority for this file (`data_engine._train_data_path`,
   `_window_for_train`, `_cached_train_schedules`).
6. Synthetic work orders are deterministic and generated as 30 orders for
   each of three configured routes (90 total), with durations selected from
   tier-specific sets. Their work IDs, departments, urgency, type labels, and
   locations are generated rather than sourced as operational work orders
   (`data_engine.get_maintenance_work_orders`).
7. Production `main.generate_schedule` calls the baseline solver, clears
   solver-supplied FOL/isolation claims, and invokes the verifier without
   timetable coverage. A non-empty schedule with required evidence missing is
   unverified; known failures take precedence. No production CP-SAT path or
   authenticated evidence provider was found (`main.generate_schedule`).
8. Existing tests cover selected interval, adjacency, isolation, evidence,
   outcome, accounting, and API-status cases. They do not constitute
   operational validation. CP-SAT shares baseline normalization/candidate
   helpers; three tiny exhaustive-reference cases and a curated constraint
   matrix do not establish whole-model equivalence.
9. Preserved Task 12 files contain 150 individual benchmark runs at 10, 25,
   and 50 work orders, 120 paired CP-SAT rows, and 9 curated constraint rows.
   All recorded individual runs returned complete assignments; there are no
   baseline global objective certificates. The 30 baseline instances use
   10 seeds and three sizes, but the timetable windows are shared. Results are
   generated evidence, not representative operational data. Two partial
   constraint rows have different solver-outcome labels despite a CSV
   `classification=equivalent`; Task 13 records that discrepancy.

## 2. Formal domain model

### 2.1 Entities and notation

Let:

- \(S\) be physical track segments, each with a stable identity, geometry,
  directionality, and validity period.
- \(L\) be named operational lines/directions; \(A(s)\) be the set of
  segments physically or operationally adjacent to segment \(s\). Logical
  adjacency is an explicit topology relation; it is not inferred solely from
  section names or geographic distance.
- \(J\) be junctions, crossovers, shared assets, and other topology objects
  that can make otherwise distinct segments share an affected resource.
- \(W\) be submitted work orders. Work order \(i\) has location/affected
  footprint \(Z_i\), duration \(d_i\), optional start \(s_i\), end
  \(e_i=s_i+d_i\), required qualifications/equipment, approved work window,
  dependencies, and possession/isolation requirements.
- \(T\) be train movement records. A movement \(t\) has an operating date,
  service identity/version, path, section-entry/exit times, direction, and
  occupancy footprint \(P_t(\tau)\) where such position data is authoritative.
- \(C\) be crews and \(E\) be equipment resources, each with qualifications or
  compatibility, availability calendars, capacity, and location/transition
  data as applicable.
- \(Q\) be possession, closure, isolation, protection, and approval records.
- \(K\) be hard constraints; \(O\) be lower-priority optimization criteria.

Intervals are written \([a,b)\) only as a **proposed computational convention**
for adjacent boundaries not to overlap. Whether this convention fits every
railway event type must be approved. A time must be an unambiguous instant
bound to an operating date and named time zone; local hour-of-day alone is
insufficient to identify a real interval across dates or clock changes.

### 2.2 Infrastructure topology and physical footprint

**Proposed requirement:** represent route, segment, section, line, direction,
junction, crossover, shared trackside asset, and adjacency as distinct,
versioned entities. Each worksite and movement must reference a stable
infrastructure version. Define:

- segment extent and chainage reference, including calibration/version;
- topology connectivity and directed travel paths;
- logical adjacency (an operational relation) separately from geometric
  proximity (measured physical distance);
- shared assets and conflict groups that cross nominal section/line
  boundaries;
- worksite footprint and equipment swept/working envelope, not just a
  section ID or one point;
- mapping from worksite to every segment/line that could be affected;
- how topology, asset ownership, chainage changes, and uncertain location
  affect a schedule already generated.

Two worksites can be geographically near without being operationally
interfering; two assets can be logically coupled or share a junction while
not being nearest neighbors. Coexistence must be based on approved topology,
footprint, activity, and protection data. Do not equate `section_id`, UP/DOWN,
or the two current line enums with a complete physical model.

For activity \(i\) and \(j\), a candidate interference decision is a domain
function
\[
I(i,j,\tau) = f(Z_i,Z_j,\text{topology version},\text{activity types},
                 \text{equipment envelopes},\text{protection state}).
\]
The function and any distance/clearance threshold are unresolved until
infrastructure and safety owners approve them. A computed distance alone does
not establish protection, authority, or safe coexistence.

### 2.3 Train movements and timetable completeness

**Proposed requirement:** timetable input contains identified train movements,
not only anonymous “busy” windows. Each movement needs a stable movement/train
ID, operating date, service identity, source/version, route/path, section
entry and exit instants, line/direction, and applicable occupancy footprint.
Cancellation, delay, diversion, unscheduled movement, and source correction
must be represented as versioned state changes; unknown current state is not
an empty train list.

Timetable completeness for a work interval is not a property of the rows
present in a file. It requires a trusted authority attesting to a defined
scope: infrastructure version, service date and time zone, line/sections,
interval, included movement classes, feed version, issue/effective time,
freshness/expiry, update sequence, and completeness method. Authentication
must bind to the exact evidence and scope. A caller-provided `source` string,
record count, successful CSV parse, or absence of known trains is insufficient.

When a timetable changes after scheduling, compare the new version and scope
against the schedule's evidence basis. If the coverage or any movement
intersects or could intersect the work, mark the schedule stale/invalidated
for review and re-run checks; do not silently retain prior verification.
Operations authority must define which updates require immediate withdrawal
or rescheduling.

### 2.4 Work orders

Every work order must have a unique ID, task/category, responsible department,
required qualifications, exact affected infrastructure/footprint, estimated
duration with source/uncertainty, allowed work window, priority policy,
required equipment, isolation/possession/protection preconditions,
dependencies, permitted interruption/splitting semantics, and co-location
eligibility. A field is essential if its absence makes a hard constraint
uncheckable; it must then be rejected or explicitly unevaluated, never silently
defaulted to a permissive value.

**Required at the interface, proposed:** immutable ID; task classification;
worksite reference/footprint; positive duration or an approved duration
distribution; required activity/authority type; and all preconditions needed
to determine applicable hard rules.

**Conditionally required:** earliest start/latest completion, resources,
dependencies, equipment envelope, possession/isolation type, and co-location
permissions whenever the work type/policy uses them.

**Optional only with explicit semantics:** narrative description, source
notes, secondary preference, and nonbinding preferred time. An optional field
must not control safety unless validated as required evidence.

### 2.5 Resource and operational capacity

Resources are not unlimited because the current project lacks resource data.
For each assignment, define required resource units over time and the
resource's calendar/capacity. For crew \(c\), assignment \(i\) is eligible only
if the crew has all required qualifications valid for the work interval and
is available for work plus transition/setup. For equipment \(e\), enforce
type/compatibility, capacity, calendar, and movement/setup where applicable.

Travel feasibility requires origin/destination locations, network/route,
travel-time model, mobilization and setup/dismantling durations, and restrictions
on transitions. Shift/rest limits require approved shift boundaries, maximum
duty/work definitions, breaks, rest intervals, and jurisdiction/policy
version. Do not infer these from objective shift buckets or the current
department field.

### 2.6 Possession, isolation, protection, and evidence

These are different concepts and must not be collapsed into a Boolean:

1. **Planned maintenance interval:** a solver's proposed time allocation.
2. **Operational possession:** an authorized, bounded operational control
   over specified infrastructure and time; it is not created by a solver.
3. **Track closure:** operational state that prevents specified movements;
   closure scope and authority must be supplied by the responsible system.
4. **Traction power isolation:** a requested or planned electrical state.
5. **Confirmed isolation:** authenticated evidence that the specified
   electrical asset, location, and interval are in the required state under
   an authorized process. The software does not create it.
6. **Worksite protection arrangement:** the authorized controls and limits
   applicable to the worksite and activity. Required procedure is owned by
   railway authority and is out of scope for this prototype specification.
7. **Authenticated safety approval:** a verifiable approval tied to subject,
   scope, actor/authority, timestamp, validity and revocation state.

Required evidence is rule-specific and must bind to the exact worksite,
operating date, interval, infrastructure version, activity, and authority.
Store provenance, integrity/authentication result, issue time, expiry, scope,
and revocation/update status. A positive flag, source label, solver proof, FOL
field, or successful schedule does not provide evidence.

Evidence state is a four-valued type:

| State | Meaning | Verification effect |
|---|---|---|
| `PASS` | Sufficient, current, authenticated evidence supports the applicable predicate and no known violation exists. | May contribute to verified status for that predicate only. |
| `FAIL` | Valid evidence or validated inputs establish a violation. | Overall verification is invalid; another unknown check cannot conceal it. |
| `UNKNOWN` | Missing, incomplete, stale, unauthenticated, malformed, contradictory, or out-of-scope evidence prevents a decision. | Never converts to pass. Overall schedule remains unverified unless a known failure takes precedence. |
| `NOT_APPLICABLE` | The approved rule does not apply to this activity. | Excluded from applicable-check denominator; recorded distinctly, not mislabeled as evaluated pass. |

Current `AuditLogEntry.passed: bool | None` can encode true/false/unknown but
does not have a distinct not-applicable type. Current verifier represents
non-traction isolation as `passed=True` with explanatory text. A future
contract must preserve the four states explicitly; this is a proposed
requirement, not an instruction to change the current API in this task.

### 2.7 Scheduling feasibility and objectives

Feasibility is defined only relative to the versioned input instance and
approved hard constraints. Let \(x_i \in \{0,1\}\) mean work \(i\) is
scheduled. A feasible assignment must satisfy every applicable approved hard
constraint for all \(i\) with \(x_i=1\), plus resource/precedence constraints.
An incomplete input instance cannot support a claim of operational feasibility.

The future objective should be **lexicographic**, not one unreviewed weighted
sum:

0. Satisfy all approved hard operational and safety constraints. No objective
   term can compensate for a violated hard constraint or missing required
   evidence.
1. Apply the approved maintenance-priority policy, with explicit policy for
   how critical work trades against aggregate coverage.
2. Maximize total scheduled work-order coverage subject to priority tier
   decisions.
3. Minimize approved train/service disruption cost using authoritative train
   and movement data.
4. Minimize deviation from an already authorized/published schedule when
   handling updates, while respecting the update invalidation policy.
5. Balance qualified crew/equipment workload and shifts under approved
   resource/duty constraints.
6. Improve equipment/resource utilization only when it does not induce
   unnecessary work or weaken higher criteria.
7. Prefer safe co-location only when independently eligible and operationally
   approved.

This is a candidate hierarchy for domain review. In particular, priority vs
total coverage and whether disruption precedes stability/workload require
decisions (`D-14`, `D-15`). Co-location is a lower-level preference, never a
waiver of hard constraints.

**Calculable from current prototype fields (not necessarily operationally
meaningful):** scheduled count, duration, current hour-based time-of-day
penalty, heuristic train-gap penalty from supplied windows, department/8-hour
bucket workload balance, and exact-window co-location count. The current
solver uses daylight 06:00–22:00, free night 01:00–05:00, shoulder weight
0.25, and an adjacency penalty for train gaps under two hours; these are
prototype objective constants, not approved service-disruption values.

**Requires new authoritative data:** safety/possession feasibility,
priority deadlines, actual train disruption, qualified-resource workload,
travel/setup, resource utilization/capacity, and schedule-change/stability
cost. Do not treat solver runtime, search order, schedule completeness, or
heuristic urgency ordering as these objective values.

## 3. Constraint catalogue

All rows below are **proposed model requirements pending domain-owner
approval**. “Hard candidate” means it should generally be treated as a
feasibility restriction if the responsible authority confirms it; it does not
claim a universal railway rule. Numerical thresholds are parameters to be
approved, not values specified by this document. Baseline/CP-SAT columns
describe only current checked behavior, not future recommendation.

| ID / constraint | Operational rule and formal sketch | Required inputs | Class | Baseline / CP-SAT today | Independent verification; failure / unknown | Owner approval |
|---|---|---|---|---|---|---|
| C-01 Train occupancy conflict | For every selected \(i\) and authoritative movement \(t\), prohibit overlap when \(Z_i\) intersects \(P_t(\tau)\) on an affected resource during \([s_i,e_i)\). Candidate: \([s_i,e_i)\cap[a_t,b_t)=\varnothing\), unless an explicit approved protection/possession rule permits otherwise. | Dated movement path, entry/exit, line/direction, occupancy footprint, worksite affected set, closure/protection state. | Hard candidate | Both filter only listed same-section/line intervals; heavy work also filters adjacent-line listed trains. | Independently check all movements and complete coverage. Known conflict = `FAIL`; missing/stale/uncertain feed = `UNKNOWN`. | Operations, safety, infrastructure |
| C-02 Same-track maintenance overlap | For conflicting work \(i,j\), require disjoint work intervals or an approved compatible shared arrangement: \(I(i,j,\tau)=0\) throughout overlap. | Work footprints, activity types, resource/access/possession scope, time intervals. | Hard candidate | Same section/line overlaps generally disallowed, except exact-window cross-department co-location. Different sections may overlap. | Independent constraint checker; missing topology/footprint = `UNKNOWN`, confirmed forbidden overlap = `FAIL`. | Operations, maintenance, infrastructure |
| C-03 Adjacent-track interference | If work affects adjacent segment \(s'\), prohibit conflicting concurrent train or work exposure unless approved protection and clearance conditions are met. Logical adjacency \(s'\in A(s)\) is separate from proximity. | Versioned adjacency/topology, footprints, affected-work types, movements, protection state. | Hard candidate | Heavy-equipment work filtered against listed opposite-line trains in same section; no adjacent maintenance pair rule. | Check both adjacent lines and activities; unknown topology/coverage = `UNKNOWN`, confirmed interference = `FAIL`. | Infrastructure, operations, safety |
| C-04 Heavy-equipment clearance | Require equipment swept envelope \(E_i(\tau)\) not to intersect protected movement/work envelope, with approved clearance parameter \(B_{\text{equip}}\); do not infer from Boolean `heavy_equipment`. | Equipment identity/type, dimensions/swept envelope, worksite geometry, movement/track geometry, approved clearances, protection. | Hard candidate | Boolean heavy flag causes opposite-line train time filter; verifier uses hardcoded buffers. | Independent geometry/time checker; missing geometry or threshold = `UNKNOWN`, confirmed envelope conflict = `FAIL`. | Safety, infrastructure, maintenance |
| C-05 Worksite spatial separation | For concurrent exposure, require \(d(Z_i,P_t(\tau))\ge B_{\text{activity,type}}\) if this is the approved rule; distance metric and uncertainty policy must be defined. | Georeferenced/chainage worksite and movement footprint, route datum/version, activity/equipment category, approved buffer. | Hard candidate | Verifier only; current 1,000/2,000 m constants are prototype assumptions. Solvers do not model distance. | Independent verifier; invalid/missing geometry = `UNKNOWN` or owner-approved conservative fail, never pass. Below approved threshold = `FAIL`. | Safety, infrastructure |
| C-06 Crew availability and qualifications | Assign eligible crew \(c\) only if all required qualifications are valid and available for full work plus applicable setup/travel; capacity must not be exceeded. | Crew ID, qualifications/expiry, availability, capacity, work type/requirements, shift. | Hard candidate | Not modeled; no data fields. | Independent eligibility and calendar check; missing qualification evidence = `UNKNOWN`/reject per approved policy; unavailable or unqualified = `FAIL`. | Maintenance, HR/credential authority, safety |
| C-07 Equipment capacity and compatibility | Assign compatible equipment type \(e\), with time-varying demand \(\sum_i q_{ie}x_i(t)\le cap_e(t)\). | Equipment inventory, compatibility, quantity/demand, capacity, calendar, maintenance state. | Hard candidate | Not modeled beyond heavy-equipment Boolean. | Independent resource ledger; missing inventory/capacity = `UNKNOWN`; overload/incompatible type = `FAIL`. | Maintenance, infrastructure |
| C-08 Travel and setup times | For consecutive tasks assigned to one resource, require \(s_j\ge e_i+\text{clear}_i+\text{travel}(Z_i,Z_j)+\text{setup}_j\). | Locations, accessible path, travel model/version, speed/restrictions, mobilization/setup/clearance durations. | Hard candidate | Not modeled. | Recompute from approved route/time data; unavailable path/time = `UNKNOWN`; violated minimum = `FAIL`. | Maintenance, operations, infrastructure |
| C-09 Maintenance work windows | Require \([s_i,e_i)\subseteq [a_i,b_i)\) for every authoritative allowed window or an approved union of windows. | Work-order allowed windows, date/time zone, calendar version, possession availability. | Hard candidate | No per-order windows; only global 24-hour hour-of-day horizon and train exclusions. | Independent interval containment check; absent required window = `UNKNOWN`/reject; out-of-window = `FAIL`. | Maintenance, operations |
| C-10 Work-order deadlines | Require completion \(e_i\le D_i\), if deadline is binding and validated. Priorities do not substitute for deadlines. | Deadline instant/time zone, priority/service-level policy, source and update history. | Hard when binding | Not modeled; no deadline field. | Compare validated instants; unknown/ambiguous deadline = `UNKNOWN`; missed hard deadline = `FAIL`. | Maintenance, operations |
| C-11 Work-order precedence/dependencies | For \(i\prec j\), require \(s_j\ge e_i+\ell_{ij}\), where \(\ell_{ij}\) is approved lag; validate acyclic graph or defined cyclic process. | Dependency IDs/type, predecessor completion/state, lag, condition/waiver authority. | Hard candidate | Not modeled. | Independent graph and assignment check; missing dependency state = `UNKNOWN`; reversed order/cycle-invalid = `FAIL` or reject. | Maintenance, engineering |
| C-12 Shift and rest constraints | Crew duty/work/rest totals and consecutive assignments satisfy approved policies over a rolling time horizon. | Crew roster, shift calendars, duty definition, rest rules, previous/following work, jurisdiction/policy version. | Hard candidate | Not modeled. Three solver objective buckets are not shift rules. | Independent rolling-window calculation; incomplete history/policy = `UNKNOWN`; violation = `FAIL`. | Maintenance, workforce policy, safety |
| C-13 Possession, isolation, protection requirements | Work can be operationally released only when required authority grants the correct possession/closure/isolation/protection for the exact resource and interval. | Required controls by task, authority, scope, status, effective interval, authenticated evidence and revocation. | Hard candidate | Not solver constraints; verifier checks traction isolation evidence only and API has no authenticated provider. | Independent evidence verifier; missing/unauthenticated/stale = `UNKNOWN`; explicit denial/violation = `FAIL`. | Operations authority, electrical safety, safety |
| C-14 Co-location rules | Simultaneous work allowed only when each activity is eligible and shared access, resources, possession, and protection are valid; model joint group capacity. | Work types, site/footprints, mutual permissions, shared resource demand, approval, crew/equipment availability. | Hard eligibility plus optional soft preference | Current solvers permit exact-window different-department overlap when both flags allow; objective rewards merged windows. | Verify every member/condition; missing approval = `UNKNOWN` or disallow per policy; conflict = `FAIL`. | Maintenance, operations, safety |
| C-15 Schedule completeness/accounting | Submitted IDs must partition exactly into scheduled and unscheduled sets: \(S\cap U=\varnothing\), \(S\cup U=W\), with no duplicates/unknown IDs. “Complete” iff \(U=\varnothing\). | Immutable request ID list, assignment IDs, unscheduled IDs, output counts. | Hard data invariant | Both solvers calculate unscheduled IDs; API checks some count consistency. | Deterministic independent check; any mismatch = invalid response, not a safety finding. | Application owner, maintenance |
| C-16 Timetable completeness/freshness | A no-conflict result is valid only for a trusted complete feed whose scoped coverage contains every assigned interval on each relevant track. | Authenticated scope, operating date/time zone, infrastructure version, feed version, issue/expiry, movement universe, update sequence. | Evidence prerequisite | Default provider authenticates nothing; API passes no coverage. | Provider validates exact record and scope; missing/partial/stale/unauthenticated = `UNKNOWN`; known train conflict = `FAIL`. | Data governance, operations |
| C-17 General resource conflicts | For each resource \(r\), enforce availability and capacity \( \sum_i demand_{ir}(t)x_i\le capacity_r(t)\); incompatibilities and setup transitions are explicit. | Resource identity, demand, capacity, compatibility, calendar, reservation/maintenance state. | Hard candidate | Only same section/line/department non-overlap is modeled; no actual resource inventory. | Independent schedule/resource validator; missing resource data = `UNKNOWN`; over-capacity = `FAIL`. | Maintenance, infrastructure |
| C-18 Schedule changes/invalidation | A change to timetable, topology, work order, resources, evidence, or approval invalidates affected proofs and requires impact analysis/reverification before reuse. | Input/evidence version digests, validity/revocation, change stream, dependency graph, prior schedule ID. | Hard governance rule | No schedule version, update invalidation, or revalidation lifecycle. | Compare exact versions/scopes and affected intervals; unknown change impact = invalidated/`UNKNOWN`, not silently current. | Operations, data governance, safety |

### 3.1 Missing or contradictory data policy

For every hard rule, define applicability before evaluation. If required
attributes are absent, mismatched, stale, malformed, or conflicting between
authoritative sources, use `UNKNOWN` or reject the request according to a
domain-approved input policy. Do not use a permissive default to create a
candidate assignment. A directly established hard violation remains `FAIL`
even when another independent rule is `UNKNOWN`. Provenance must identify
source, version, scope, and validation; schema validation alone is not source
authentication.

## 4. Solver-independent outcomes and verification

Maintain separate state dimensions:

1. **Assignment coverage:** no assignments, partial feasible assignments, or a
   complete feasible assignment.
2. **Proof/termination:** feasibility found, complete infeasibility proven,
   maximum coverage proven, objective optimality proven, or proof unknown due
   to a limit/error.
3. **Evidence verification:** pass, fail, unknown, or not applicable per rule
   and the aggregate verification result.
4. **Operational authority:** approved/released or not; solver/verifier output
   does not itself grant authority.

Canonical labels (with proof metadata kept separately):

| Label | Required condition | Must not imply |
|---|---|---|
| `no_work` | No work orders submitted; empty assignment and empty unscheduled list. | No safety rules were evaluated; it is not verified success. |
| `success` | Every submitted work order has a valid modeled assignment. | Objective optimality, complete real-world constraints, safety verification, or authority. |
| `partial` | At least one but fewer than all submitted work orders are assigned feasibly; list every omitted ID. | That the omitted items are individually impossible, or that maximum coverage was proven. |
| `unschedulable` | No complete assignment exists under the exact versioned modeled constraints and that fact is proven. Preserve any feasible partial incumbent as assignment state separately; do not label it a complete schedule. | Real-railway infeasibility or an individual work-order cause. |
| `search_limit_reached` | A limit stopped search before the required feasibility/infeasibility/coverage proof was obtained. | `unschedulable`, objective optimality, or absence of a feasible assignment. |

If a partial incumbent exists when a limit is reached, retain both facts:
coverage is `partial`; termination/proof is `search_limit_reached` or
`unknown`. A single enum cannot express both dimensions without ambiguity.
For compatibility with the current API, use solver status plus explicit
proof/termination metadata rather than rewriting status semantics informally.
The baseline currently can return `status=partial` with
`solver_outcome=unschedulable` after exhausting its complete-assignment search
and falling back to a partial assignment; CP-SAT uses `partial` after proving
maximum coverage. This is a known mismatch, not an endorsed canonical mapping.

Safety verification is independent. A complete solver schedule with any
applicable `UNKNOWN` evidence remains unverified. Any `FAIL` makes overall
verification invalid even if another check is unknown. An empty schedule/audit
cannot establish pass. `NOT_APPLICABLE` must be distinct from evaluated pass
and excluded from the applicable-check denominator. Any compliance percentage
must identify the applicable-check denominator and remain unavailable for an
empty, incomplete, inconsistent, or unauthenticated audit.

## 5. Data requirements

The detailed field-by-field catalogue, including current schema/dataset
presence and provenance, is
[`TASK14_DATA_REQUIREMENTS.csv`](./TASK14_DATA_REQUIREMENTS.csv). In
particular, distinguish:

- **Existing app schema:** narrow prototype request and response fields.
- **Existing bundled dataset:** ten raw timetable CSV columns; some are unused
  in occupancy generation, and none are established as authenticated live
  evidence.
- **Derived/inferred:** route-direction mapping, section boundaries,
  interpolated occupancy intervals, deterministic synthetic work orders.
- **Proposed future fields:** all authoritative topology, date/version/
  completeness, resource, window/deadline/dependency, operational control,
  evidence provenance, and update-invalidation fields.

No values for proposed fields are fabricated here. Authoritative sources and
units/validation rules must be named by domain owners before integration.

## 6. Canonical validation scenarios

The future test fixtures are enumerated in
[`TASK14_VALIDATION_SCENARIOS.csv`](./TASK14_VALIDATION_SCENARIOS.csv). They
separate solver feasibility/outcome from evidence state and verification
result. Scenarios that rely on proposed crew, topology, possession, date, or
authenticated-provider fields are blocked from executable implementation
until those contracts and domain policies are approved. Fixtures use symbolic
thresholds (for example `B_approved`) rather than invented distances.

Existing tests already cover selected cases including: empty input;
same-track overlap; listed train conflict; heavy equipment versus opposite
line trains; co-location; search cutoff; unscheduled ID accounting; clearance
and buffer boundaries using current prototype constants; unknown timetable
coverage; untrusted evidence; traction isolation unknown/failure; empty audit;
API status precedence and compliance handling. Their fixture pass-provider is
test-only and is not an integrated evidence source. They do not test the
proposed full topology/resource/date/update model.

## 7. Unresolved domain decisions and implementation gates

The decision register is
[`TASK14_DOMAIN_DECISIONS.csv`](./TASK14_DOMAIN_DECISIONS.csv). P0 decisions
that block operational implementation include:

- the applicable railway authority and operational boundary;
- authoritative infrastructure/topology and definition of worksite/adjacency;
- the timetable source, operating-date/time-zone scope, completeness, update
  and freshness rules;
- possession, isolation, protection, evidence authentication, and change
  invalidation semantics;
- approved spatial/equipment clearance rules and their measurement basis;
- resource data, crew competence, equipment capacity, travel/setup, shift/rest;
- policy for partial coverage, priority trade-offs, objective ordering, and
  solver proof labels.

The project establishes only the current implementation facts in §1.1. The
current 24-hour horizon, 0.5-hour start grid, section interpolation, default
line direction, two-line topology, work-order tiers, and verifier distances
are prototype assumptions. The requirements in §§2–6 are proposals for owner
approval, not railway rules.

## 8. Readiness conclusion

The specification is a sufficiently detailed **requirements baseline for
domain-owner review and decision-making**, not a sufficiently approved
operational model to begin implementing operational constraints. Resolve the
P0 decisions and authenticate authoritative data/evidence first. After those
approvals, update the specification and validate it with domain owners before
coding. Do not modify either solver, the verifier, API, dataset, or frontend
based only on this draft.
