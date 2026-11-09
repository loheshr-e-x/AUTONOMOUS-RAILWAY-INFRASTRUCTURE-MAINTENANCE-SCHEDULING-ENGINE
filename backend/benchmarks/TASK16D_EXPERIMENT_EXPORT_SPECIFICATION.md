# Task16D Experiment Export Specification

## Purpose and boundary

Task16D exports a completed, paired baseline/CP-SAT comparison from the
offline, non-operational scenario prototype. It does not rerun a solver,
change browser-local scenarios, call a new service, or establish operational
fitness or railway safety. Use synthetic research inputs only. Do not include
credentials, evidence, or actual railway operational data.

The browser offers JSON and CSV downloads only when all export eligibility
checks below pass. A missing, failed, unavailable, incomplete, unvalidated, or
digest-mismatched run cannot be represented as a successful paired experiment.
Partial scheduling is exportable when both solver runs completed, their
assignments passed independent validation, and each submitted work order is
accounted for exactly once as scheduled or unscheduled.

## JSON format

The JSON document is UTF-8 and has a trailing newline. Object properties are
serialized in sorted-key order and array order is preserved. Its root object is:

| Property | Meaning |
|---|---|
| `format` | Stable identifier: `symbio-block-experiment`. |
| `schema_version` | Export schema version; currently `1`. |
| `experiment` | `experiment_id`, `exported_at_utc`, scenario identity/name, model version, and verified canonical input digest. |
| `submitted_request` | The request snapshot sent to the existing comparison endpoint, including scenario metadata, work orders, train windows, configuration, and any submitted digest field. |
| `comparison` | The complete paired response as returned by the endpoint, retaining each solver's status, schedule, unscheduled reasons, validation findings, objective components, proof fields, runtime, and termination metadata. |
| `schedule_differences` | One entry per submitted work order, classified as `same_placement`, `placement_changed`, `baseline_only`, `cp_sat_only`, or `unscheduled_both`, with assignments and reason codes where returned. |

`experiment_id` is generated once for the validated comparison and is reused
for both file formats. `exported_at_utc` is set when the first download is
initiated; a subsequent download in the same comparison view reuses that
timestamp and identity. The browser does not persist the export record to
localStorage.

## Integrity and eligibility

The browser independently recomputes the backend's SHA-256 digest over only
`model_version`, `work_orders`, `train_windows`, and `solver_configuration`.
The canonical representation uses sorted JSON keys, compact separators,
ASCII-escaped strings, finite numbers only, and the same Pydantic defaults and
float serialization as the backend. `scenario_id`, `scenario_name`, and
`input_digest` are excluded from the hash. Export is enabled only when:

1. The response is `completed`, `paired_inputs_match` is true, and its
   scenario ID and model version match the submitted request.
2. The recomputed digest equals the response digest and both per-solver
   digests.
3. Both solver runs are `completed` and each reports `validation.valid: true`
   with no validation findings.
4. Each run's total equals the submitted work-order count; schedule IDs agree
   with scheduled IDs; scheduled and unscheduled IDs are unique, known, and
   form an exact partition of the submitted IDs.
5. Returned unscheduled reason IDs are unique and refer only to unscheduled
   work orders.

Any failed check blocks both downloads and displays an export-unavailable
reason. No submitted input is silently normalized or replaced for the export;
backend defaults are applied only in the independent canonical digest
calculation, matching request-model serialization.

## Cross-language canonical digest contract

The digest covers exactly the Pydantic-normalized object containing
`model_version`, `work_orders`, `train_windows`, and `solver_configuration`.
Object keys are sorted recursively; array order is significant. JSON is compact
(no insignificant whitespace), strings use ASCII escapes, and non-finite
numbers are rejected. Float-typed request fields retain Python float JSON
semantics, including a decimal marker for whole-valued floats and Python's
scientific-notation thresholds. Pydantic defaults are applied before
serialization. Scenario ID, scenario name, and a supplied `input_digest` are
presentation/verification metadata and are excluded from the hash.

The shared deterministic cases and one-field input mutations live in
[`tests/fixtures/task16-canonical-digest.json`](../tests/fixtures/task16-canonical-digest.json).
The frontend test suite runs against these cases with `npm test`. The backend
suite's `test_scenario_digest_parity.py` runs the JavaScript digest through
Node.js and compares every computed value directly with Python's
`canonical_scenario_digest()`; it does not rely on copied expected hashes.
Run the parity gate with:

```sh
backend/.venv/bin/pytest -p no:cacheprovider backend/tests/test_scenario_digest_parity.py
cd frontend && npm test
```

Changing the canonical object shape, defaults, escaping, or number
serialization requires updating both implementations only with matching
shared-fixture parity. The tests also assert that each listed solver-relevant
mutation changes the digest, while metadata-only changes, key reordering, and
omitted-versus-explicit defaults do not.

## CSV format

CSV is UTF-8 with a header row, CRLF record separators, RFC 4180 quoting, and
one data row per submitted work order. Commas, double quotes, and embedded
line breaks are quoted/escaped. Empty values represent unavailable or
inapplicable data. Text cells beginning with spreadsheet formula markers are
prefixed with an apostrophe to reduce formula-injection risk; the JSON record
retains the original value.

Each row repeats schema version, experiment identity/timestamp, scenario
identity, model version, input digest, comparison status, and paired-input
status. It includes the submitted work-order attributes and classification;
baseline and CP-SAT run status, outcome, validation, coverage/objective proof
states, termination, runtime, placement, and unscheduled reason code; CP-SAT
proof scope; and the availability, value, and explanation for each supplied
objective component. Baseline and CP-SAT components remain separate. The CSV
does not calculate an aggregate score or compare native objective scalars.

The CSV columns are emitted in this order:

```text
schema_version, experiment_id, exported_at_utc, scenario_id, scenario_name,
model_version, input_digest, comparison_status, paired_inputs_match,
work_order_id, schedule_difference, submitted_department,
submitted_section_id, submitted_track_line, submitted_duration_hrs,
submitted_heavy_equipment, submitted_urgency, submitted_defect_type,
submitted_co_location_allowed, baseline_run_status, baseline_input_digest,
baseline_total_work_orders, baseline_scheduled_count,
baseline_unscheduled_count, baseline_solver_outcome,
baseline_validation_valid, baseline_complete_assignment_witness,
baseline_coverage_optimality_proven,
baseline_complete_schedule_proven_infeasible,
baseline_objective_optimality_proven, baseline_feasibility_not_established,
baseline_search_limit_reached, baseline_termination_reason,
baseline_termination_status, baseline_runtime_seconds,
baseline_assignment_start_time_hr, baseline_assignment_end_time_hr,
baseline_assignment_scheduled, baseline_assignment_section_id,
baseline_assignment_track_line, baseline_assignment_department,
baseline_unscheduled_reason_code, cp_sat_run_status, cp_sat_input_digest,
cp_sat_total_work_orders, cp_sat_scheduled_count, cp_sat_unscheduled_count,
cp_sat_solver_outcome, cp_sat_validation_valid,
cp_sat_complete_assignment_witness, cp_sat_coverage_optimality_proven,
cp_sat_complete_schedule_proven_infeasible,
cp_sat_objective_optimality_proven, cp_sat_feasibility_not_established,
cp_sat_search_limit_reached, cp_sat_termination_reason,
cp_sat_termination_status, cp_sat_runtime_seconds,
cp_sat_assignment_start_time_hr, cp_sat_assignment_end_time_hr,
cp_sat_assignment_scheduled, cp_sat_assignment_section_id,
cp_sat_assignment_track_line, cp_sat_assignment_department,
cp_sat_unscheduled_reason_code, cp_sat_proof_scope
```

For each solver, the following triplet is appended for each of
`time_of_day_train_gap`, `department_workload_imbalance`,
`co_location_merge_count`, `schedule_stability`, and `utilization`:

```text
<solver>_<component>_available, <solver>_<component>_value,
<solver>_<component>_explanation
```

The JSON comparison object is authoritative for the full backend response;
CSV is a convenient per-work-order view. Neither file is a safety case,
deployment recommendation, or operational authorization.
