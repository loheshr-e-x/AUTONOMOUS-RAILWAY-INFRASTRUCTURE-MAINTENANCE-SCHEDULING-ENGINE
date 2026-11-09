# Task 12: Comparative Solver Evaluation

## Executive summary

The evaluation contains 30 fixed-input instances (10 seeds at each of 10, 25,
and 50 work orders), one baseline run and four CP-SAT time-limit runs per
instance: 150 solver executions and 120 paired comparisons. Every solver run
returned a complete schedule, and no baseline run hit the external 120-second
timeout.

CP-SAT proved maximum schedule coverage in all 120 runs. It proved objective
optimality in all 10-order runs, in 8/10, 9/10, 9/10, and 10/10 25-order runs
at 5, 10, 30, and 60 seconds respectively, and in 0/10, 0/10, 2/10, and 2/10
50-order runs at those limits. The baseline exposes no global objective proof
and reached a configured search cap in 2/10 10-order runs and all 25- and
50-order runs. Thus the results show full schedules in these tested instances,
but do not establish that either solver is generally feasible or optimal.

## Method

The evaluation used this command:

```sh
PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -m backend.benchmarks.task12_runner \
  --repetitions 10 --base-seed 20261030 --sizes 10 25 50 \
  --cpsat-time-limits 5 10 30 60 --baseline-timeout-seconds 120
```

Seeds were `20261030` through `20261039`. The harness alternated whether the
baseline or CP-SAT group ran first on each repetition. All five runs for an
instance shared its work orders, train windows, base configuration, and
SHA-256 digest. CP-SAT used one search worker and fixed branching. Baseline
search and node limits were unchanged; the 120-second wall-clock bound was an
external process timeout.

The generator contains 90 work orders. The evaluation intentionally used
10/25/50-order subsets and did not clone orders. The larger sizes 100 and 200
are unsupported by this data source. The full train-window data and 24-hour
horizon were retained for each subset.

Environment: Python 3.12.14; macOS 27.0.1, arm64, 12 logical CPUs. Recorded
package versions were FastAPI 0.143.1, Pydantic 2.14.1, pytest 9.2.0,
Matplotlib 3.11.2, and OR-Tools 9.14.6206.

## Results

### Baseline

All 10 runs at each size returned a complete schedule. Runtime is in seconds;
standard deviation is population standard deviation. The objective value is
the baseline floating-point score recalculated on the returned schedule.

| Work orders | Mean | Median | Std. dev. | Full schedules | Search-cap runs | Mean objective |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 5.582 | 2.197 | 7.204 | 10/10 | 2/10 | 12.2753 |
| 25 | 53.930 | 55.096 | 12.590 | 10/10 | 10/10 | 38.8209 |
| 50 | 85.376 | 89.931 | 15.677 | 10/10 | 10/10 | 96.6672 |

Search-cap runs can still return a full feasible assignment; reaching the cap
means the search did not establish its remaining search/objective conclusions.
The benchmark records the cap separately from the solver outcome.

### CP-SAT

All 10 runs in every row returned complete schedules and proved maximum
coverage. “Objective proofs” counts CP-SAT proofs of the integer-scaled
objective at the proven maximum coverage. Objective means below are the
baseline floating-point objective recalculated on each returned schedule.

| Work orders | Limit (s) | Mean (s) | Median (s) | Std. dev. (s) | Full schedules | Coverage proofs | Objective proofs | Mean objective |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 5 | 0.023 | 0.022 | 0.007 | 10/10 | 10/10 | 10/10 | 12.2543 |
| 10 | 10 | 0.022 | 0.021 | 0.007 | 10/10 | 10/10 | 10/10 | 12.2543 |
| 10 | 30 | 0.022 | 0.021 | 0.007 | 10/10 | 10/10 | 10/10 | 12.2543 |
| 10 | 60 | 0.021 | 0.020 | 0.007 | 10/10 | 10/10 | 10/10 | 12.2543 |
| 25 | 5 | 1.807 | 1.083 | 1.718 | 10/10 | 10/10 | 8/10 | 39.2201 |
| 25 | 10 | 2.771 | 1.071 | 3.586 | 10/10 | 10/10 | 9/10 | 38.7752 |
| 25 | 30 | 4.771 | 1.070 | 8.819 | 10/10 | 10/10 | 9/10 | 38.5478 |
| 25 | 60 | 6.266 | 1.075 | 13.168 | 10/10 | 10/10 | 10/10 | 38.2874 |
| 50 | 5 | 5.002 | 5.002 | 0.000 | 10/10 | 10/10 | 0/10 | 107.8458 |
| 50 | 10 | 10.002 | 10.002 | 0.000 | 10/10 | 10/10 | 0/10 | 106.1542 |
| 50 | 30 | 26.403 | 30.002 | 7.243 | 10/10 | 10/10 | 2/10 | 103.7787 |
| 50 | 60 | 50.408 | 60.002 | 19.205 | 10/10 | 10/10 | 2/10 | 103.0849 |

The measured time includes CP-SAT model construction and solving. The solver's
configured limit applies to its search phases, so measured wall time is not
required to equal the configured limit exactly.

The objective means are measurements, not a quality ranking. The baseline
does not provide an objective-optimality certificate, so none of the 120
objective pairs is marked interpretable. In addition, the CP-SAT integer
scaling/rounding is an approximation of the baseline floating-point objective.

## Constraint checks and independent reference

The curated constraint matrix contains eight scheduling cases and one invalid
input case. For all eight scheduling cases, both solvers matched the expected
scheduled count. The invalid missing-duration case was rejected by both with
`ValueError`.

Two partial-schedule cases had the same `status` (`partial`) and the same
scheduled count, but different `solver_outcome` values. In both cases the
baseline returns `status=partial`, `solver_outcome=unschedulable`: its complete
assignment search is exhausted, while its fallback retains a partial
assignment. CP-SAT returns `status=partial`, `solver_outcome=partial` because
it proved the maximum coverage and retained a partial assignment. The CSV
preserves both fields; equal counts/statuses must not be read as equivalent
outcome semantics, and the baseline outcome is not evidence that the retained
partial schedule is itself unschedulable.

The maintenance-heavy opposite-line overlap case is classified
`baseline_limitation`: both implementations permit it because the baseline
does not prohibit maintenance-on-maintenance overlap across opposite track
lines. CP-SAT deliberately preserves that behavior for this comparison.

Three tiny instances were checked against an independently implemented
enumerator: feasible non-overlapping work, a train-blocked infeasible order,
and a two-order partial conflict. CP-SAT matched the reference schedule count
and objective with an optimality proof in all three. This is a bounded check,
not proof of general equivalence.

## Artifacts

All outputs are in [`task12_results/`](./task12_results/), separate from
production application data:

- `individual_results.csv`: 150 executions, configurations, IDs, solver
  outcomes, proof flags, runtime, domains/search statistics, platform, and
  dependency versions.
- `summary_results.csv`: 15 groups by solver, size, and CP-SAT limit.
- `paired_comparisons.csv`: 120 same-instance comparisons.
- `constraint_equivalence_results.csv` and `exhaustive_validation_results.csv`.
- Six charts in [`task12_results/charts/`](./task12_results/charts/): runtime
  by size, runtime distributions, completeness, full-schedule feasibility,
  CP-SAT objective proof rate, and paired objective differences.

No baseline runs were externally censored. Memory is blank because reliable
per-solver peak-memory measurement is unavailable. Cold-start time was not
measured separately: CP-SAT was imported before timed calls, while the
baseline timer starts after the worker process is ready. Candidate-domain and
AC-3 statistics are available per run for the baseline; CP-SAT reports raw
and train-filtered domains but does not run AC-3. Baseline search-node totals
and CP-SAT branch/conflict counts use different algorithms and are not directly
comparable.

## Persistence and reproducibility check

The preserved `individual_results.csv` was parsed and used to reconstruct both
`summary_results.csv` and `paired_comparisons.csv` through the current
aggregation functions. Comparisons were exact at the CSV row and header level:
15/15 summary rows and 120/120 paired rows matched, with zero discrepancies.
The source contains 150 individual rows with 30 baseline and 120 CP-SAT runs;
all 30 paired instances have shared digests, and no executions are missing.

The Task 12 serializer uses declared schemas for individual, summary, paired,
constraint, and exhaustive-result rows, while retaining additional keys found
in any row. Missing optional fields serialize as empty cells; empty datasets
still receive headers. Writes use temporary files and atomic replacement.
Each run incrementally checkpoints completed individual rows to a unique
staging directory. Failed or interrupted runs leave that checkpoint and do
not replace the last completed output; a successful publish preserves the
previous output as a sibling backup.

The two partial-schedule constraint cases are intentionally not normalized to
one outcome label. Both have `status=partial`; the baseline has
`solver_outcome=unschedulable` after exhausting its complete-assignment search
and returning a fallback partial assignment, while CP-SAT has
`solver_outcome=partial` after proving maximum coverage. This is a genuine
outcome-semantics difference, not a difference in returned schedule count.

## Execution and validation notes

The full evaluation command completed all solver calls and saved all 150
individual rows, but its first attempt exited 1 during constraint-CSV
serialization: a validation-only field was present in a later row but absent
from the first row. Task 12A did not rerun the benchmark or create any new
measurements. It added heterogeneous-row and failed-write regression tests,
reconstructed the summaries and pairs directly from the preserved individual
results, and found zero discrepancies. Summary: 15/15 rows matched; paired:
120/120 rows matched; headers also matched exactly.

Validation:

```text
PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/pytest -p no:cacheprovider \
  backend/tests/test_task12_benchmarks.py
14 passed; exit 0

set -o pipefail; PYTHONDONTWRITEBYTECODE=1 \
  backend/.venv/bin/pytest -p no:cacheprovider backend/tests
121 passed; exit 0

git diff --check
exit 0
```

## Conclusion and limitations

CP-SAT was substantially faster in these measurements at the selected sizes,
and both solvers produced complete schedules in every sampled instance.
However, CP-SAT objective proof rates deteriorated at 50 work orders, the
baseline has no global objective proof, and the objective formulations are not
identical in all cases. These results are not grounds to claim general
optimality, improved safety, or production suitability. The CP-SAT solver
remains an experiment and is not connected to the production API or safety
verification.
