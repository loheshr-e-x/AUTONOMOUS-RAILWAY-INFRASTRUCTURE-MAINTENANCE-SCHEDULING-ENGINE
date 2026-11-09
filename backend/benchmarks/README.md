# Solver benchmark

This harness measures the existing `solve_maintenance_schedule` implementation.
It does not alter solver algorithms, safety verification, or objective weights.
It creates results only under `backend/benchmarks/results/`, outside production
application data.

## Run

From the repository root, using the backend virtual environment:

```sh
PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -m backend.benchmarks.runner
```

Defaults are three runs per supported scenario, a fixed seed of `20261030` for
work-order ordering and simulated annealing, a 24-hour horizon, and the solver's
default search-node limit and other algorithm settings. Output is written to:

- `individual_results.csv`: one row per execution.
- `summary_results.csv`: mean, median, population standard deviation, feasibility
  rate, and mean scheduled/submitted completeness.
- `execution_time.svg`, `feasibility_rate.svg`, and
  `scheduling_completeness.svg`: charts for executed scenario sizes.

Options: `--runs N`, `--seed N`, `--sizes N [N ...]`, and `--output-dir PATH`.
The project generator itself is deterministic; the fixed seed controls the
work-order ordering and simulated annealing seed. Every run at a given size uses
the same work orders, train windows, configuration, and instance SHA-256 digest.

## Scenario availability

The existing project generator creates 30 work orders per route. The three
configured routes provide 90 distinct work orders in total. Therefore the
default 10-, 25-, and 50-order scenarios execute; 100 and 200 are recorded as
`unsupported` in the summary CSV with the reason. The harness deliberately does
not clone work orders or invent a larger dataset. Scenarios up to 90 can be
selected with `--sizes`.

## Measurements and interpretation

`execution_time_sec` is outer wall-clock time for the solver call, including the
small measurement-wrapper overhead. Imports and process startup happen before
timing; cold-start measurements are not collected (`cold_start=false`).
Repeated measurements are in one Python process. The summary uses population
standard deviation (`pstdev`).

Search-node counts come from the solver's backtracking and A* return values.
Domain sizes and AC-3 pruning counts are measured by wrappers around the
solver's existing private functions; wrappers call the original functions
unchanged. If AC-3 is disabled, post-AC-3 size and AC-3 pruning are blank.
`backtracking_limit_reached` reflects the explicit backtracking result.
`astar_limit_reached` is true when an individual A* call returns an expansion
count at its configured limit. The solver does not return A*'s remaining
frontier, so this records reaching the cap and does not distinguish an exactly
exhausted frontier at that same boundary. `search_limit_reached` is true if
either search reports/reaches its configured bound or the solver outcome is
`search_limit_reached`. A complete initial assignment can still have an A*
limit reached; that does not change the solver outcome.

The objective score is calculated after solving by applying the solver's own
objective function to the returned assignment. It is not proof of optimality.
`fol_rule_compliance_pct` is not benchmarked as a solver-performance metric.
The benchmark does not invoke the safety verifier and does not establish
railway safety.

Feasibility rate is the fraction of runs whose solver outcome is `success`.
Scheduling completeness is total scheduled work orders divided by total
submitted work orders across runs. These are descriptive solver outcomes, not
proof that a schedule is safe or globally optimal.

Python, platform, machine, processor, CPU count, and selected installed package
versions are recorded per individual run. SVG graphs are generated with the
Python standard library; the original single-solver benchmark has no added
runtime dependency.

## Experimental CP-SAT comparison

The independent CP-SAT solver is in `backend/app/cpsat_solver.py`. Install its
pinned dependency and run the paired comparison from the repository root:

```sh
backend/.venv/bin/python -m pip install -r backend/requirements-cpsat.txt
PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -m backend.benchmarks.compare \
  --runs 3 --seed 20261030 --sizes 10 25 50 100 200 \
  --cpsat-time-limit-seconds 30
```

Comparison outputs are written separately to
`backend/benchmarks/comparative_results/`; existing baseline benchmark results
are not overwritten. The individual CSV contains paired solver rows sharing
the same input SHA-256, with execution time, complete/partial outcome,
scheduled and unscheduled counts, objective, proof status, termination reason,
CP-SAT branches/conflicts, and Python/platform/package versions. The summary
includes mean, median, population standard deviation, full-schedule feasibility
rate, scheduling completeness, objective mean, and optimality proof rate.
Imports/process startup are excluded and all runs execute in one process;
CP-SAT's Python/native import is performed before timing. Memory is not
measured per solver and is blank in CSV because reliable per-solver memory
measurement is unavailable.

The CP-SAT model uses the baseline's normalized input validation, candidate
start times, train-conflict filtering (including adjacent-track trains for
heavy-equipment work), and same-section/same-track compatibility. It creates
one optional interval per work order and applies `NoOverlap` within each
section/track/department resource. Cross-department overlaps use the baseline's
pairwise compatibility rule, including the exact-window co-location exception.
The benchmark data has no worker, crew, or other capacity inventory, so no
additional resource capacity is modeled. The baseline does not forbid
maintenance assignments on opposite track lines from overlapping, even if one
uses heavy equipment; adding such a rule only to CP-SAT would make the
comparison inequivalent, so it is intentionally omitted. Spatial buffers and
traction-isolation evidence are not solver constraints in the baseline.

Urgency affects CP-SAT's deterministic variable decision order, but, as in the
baseline objective, does not add an urgency score. The objective uses the
baseline disruption cost, department/shift workload imbalance weight, and
co-location reward. CP-SAT maximizes scheduled-order count first; after the
maximum count is proven, it minimizes the baseline objective at that count.
Disruption and co-location coefficients use integer scaling; workload
imbalance uses millihour duration ticks and a weight rounded to 1e-6. Input
durations not representable in millihours or starts/horizon not representable
in microhours are rejected rather than silently rounded. `objective_score` is
reported by recalculating the baseline objective on the returned schedule.

`optimality_proven` means the CP-SAT objective was proven optimal at the
maximum schedule count. A complete feasible schedule may still be returned
after a time limit without an optimality proof. If maximum coverage is not
proven before a limit, the result reports `search_limit_reached`; proven
partial coverage is reported as `partial`, and proven zero coverage as
`unschedulable`. The time limit bounds CP-SAT search phases; model construction
is also included in the reported outer execution time and may add overhead.
The baseline solver does not expose a global objective-optimality proof, so its
proof status remains false.

This experimental solver is not wired into the production API and does not
perform safety verification. A different solver is not evidence of greater
railway safety.

## Task 12: repeated comparative evaluation

Run the bounded, seeded evaluation from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -m backend.benchmarks.task12_runner \
  --repetitions 10 --base-seed 20261030 --sizes 10 25 50 \
  --cpsat-time-limits 5 10 30 60 --baseline-timeout-seconds 120
```

By default this creates results under `backend/benchmarks/task12_results/`,
separate from application data and the earlier benchmark outputs. It records
one baseline run and four CP-SAT time-limit runs per seeded instance. Solver
order alternates by repetition; all runs in a pair share the same work orders,
train windows, base configuration, and input digest. CP-SAT uses one worker and
fixed branching. The baseline's existing search settings are not changed; the
120-second limit is an external process timeout, and timed-out baseline rows
are marked censored rather than treated as infeasible.

The individual CSV retains each execution and its configuration. Summary CSV
rows group by solver, workload size, and CP-SAT limit. Runtime mean/median/
population standard deviation including capped observations are reported
separately from completed-only means. Full-schedule success rate means every
submitted order was scheduled; `feasible_solution_rate` separately means a
nonempty schedule was found, including partial schedules. Objective comparisons
are marked interpretable only if both solvers provide an optimality proof;
the baseline currently exposes no such proof. Each individual row includes
Python/platform/machine/CPU details and the installed FastAPI, Pydantic,
pytest, Matplotlib, and OR-Tools package versions.

`constraint_equivalence_results.csv` reports expected-vs-observed scheduled
counts, statuses, and solver outcomes as separate fields. Matching schedule
counts do not imply matching outcome semantics. `exhaustive_validation_results.csv`
contains three deliberately small cases checked against an independently
implemented enumerator; it is a bounded cross-check, not a proof of general
solver equivalence. The six charts are regenerated from the saved CSVs and
cover runtime versus size, runtime distributions, completeness, full-schedule
feasibility rate, CP-SAT objective-proof rate, and paired objective differences.

The Task 12 CSV schemas are declared in `task12_runner.py`: individual solver
rows, summaries, paired comparisons, constraint cases, and exhaustive checks.
Baseline timeout/success rows and CP-SAT rows have optional metrics; constraint
rows additionally have a validation-only field for the missing-duration case.
CSV serialization writes the declared columns plus any extra row keys, writes
empty cells for absent optional values, and uses an atomic temporary-file
replacement. Empty result sets retain their declared header.

Each run builds outputs in a unique sibling staging directory and atomically
checkpoints `individual_results.csv` after every completed solver execution.
The run-state JSON distinguishes running, completed, and failed checkpoints.
Only after all result files and charts are ready is the directory published.
Failed or interrupted runs leave their checkpoint for inspection and do not
replace the last completed output. When publishing over existing results, the
previous output directory is retained as a hidden sibling backup; a later run
restores that backup if an interrupted directory swap left the output path
absent.

The existing generator supplies 90 orders in total; the default evaluation
uses 10, 25, and 50 order instances. Larger sizes up to 90 can be requested,
but may require substantially more time and memory. No orders are cloned to
create unsupported larger instances. Per-solver memory is not measured
reliably and remains blank. Cold-start timing is not separated; CP-SAT is
loaded before its timed calls, while the baseline worker's solve timing excludes
process startup. Results characterize the prototype's modeled behavior only:
they do not establish safety, operational suitability, global optimality, or
general constraint equivalence.
