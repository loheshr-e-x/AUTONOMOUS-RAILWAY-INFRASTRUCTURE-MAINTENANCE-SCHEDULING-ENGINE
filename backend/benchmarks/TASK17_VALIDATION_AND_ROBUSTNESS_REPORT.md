# Task17 Validation and Robustness Report

## Scope

This report covers the experimental scenario validator and paired-comparison
path, solver-result handling, frontend stale-response and paired-result gates,
and their regressions. Production scheduling, the safety verifier, evidence
providers, solver objectives, Task12 historical results, Task16 digest behavior,
and Task16 export schemas were not changed.

## Findings and changes

### Malformed solver output

`_run_solver()` previously used falsy fallbacks for `metrics`, `search_stats`,
`schedule`, and `unscheduled_work_ids`. That allowed missing required result
containers and empty non-object metrics to be normalized into a shape that was
then reported as a completed run. The adapter now requires an object-valued
`metrics` field, rejects non-object search statistics when supplied, and
requires explicit schedule and unscheduled-ID lists. Invalid shapes return a
failed run with `INVALID_SOLVER_RESULT`.

### Contradictory proof claims

The adapter previously accepted incompatible claims from a solver: a
CP-SAT objective-optimality claim without maximum-coverage proof, or a claim
that a complete schedule is infeasible alongside a complete independently
validated assignment. A baseline `unschedulable` outcome could similarly
contradict a complete witness. These combinations now fail closed with
`INVALID_SOLVER_PROOF_METADATA`. Existing proof distinctions are preserved:
coverage is not objective optimality, and the baseline solver does not receive
an objective-optimality claim.

### Paired-result and stale-response gating

The comparison panel previously relied on the top-level
`paired_inputs_match` flag, completed run statuses, and `validation.valid`.
It did not independently verify response/run digests against the selected
scenario, or validate the returned work-order partition before showing the
paired summary and Gantt. The page now computes the canonical digest of the
exact request; the display gate requires matching scenario/model identity,
response and per-solver digests, clean independent validation, and exact
scheduled/unscheduled ID accounting. Invalid reason references also block the
paired display. Export eligibility remains independently enforced by the
existing export checks.

Request generation tracking now has a focused helper used by the page. A
superseded request cannot publish its response or clear the in-flight status of
a newer request.

### Regression coverage

The tests cover empty/no-work comparisons, malformed solver containers,
non-Boolean and contradictory proof metadata, unsupported model/section and
horizon inputs, non-finite assignment intervals, and half-open train/clearance
boundaries. Frontend tests verify that mismatched identity/digests,
validation findings, or accounting cannot unlock paired display, and that
stale requests cannot finish a newer request.

## Browser checks

Using the local application and the saved synthetic scenario
`Task16C Valid Sections Acceptance`:

| Check | Returned observation |
|---|---|
| Real comparison endpoint | HTTP 200; `comparison_status` was `completed`; both solver validations were `true`. |
| Paired UI display | “Completed paired comparison; both assignments validated”; baseline and CP-SAT validation labels each appeared once. |
| Gantt | `Schedule placement comparison` was visible. |
| Scenario persistence | Browser-local scenario storage was byte-for-byte unchanged after comparison. |
| Existing `Acceptance A` invalid section | The page displayed `Scenario validation failed: UNKNOWN_SECTION: Unknown section ID(s): SIM-A`; Gantt count was 0. |
| Mismatched per-solver digest | A real successful response was replayed with the CP-SAT digest changed to 64 zeroes. The UI showed “Incomplete or unvalidated comparison — not presented as a successful pair”; Gantt count was 0; scenario storage was unchanged. |

An initial attempt to inject the digest mismatch using a browser route-fetch
handler timed out before producing an assertion. It is not counted as a pass.
The check was repeated successfully by capturing an actual HTTP 200 comparison
response, altering only its CP-SAT digest, and fulfilling the browser request
with that response.

## Validation results

Commands were run from the repository root unless a `cd frontend` prefix is
shown.

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/pytest -p no:cacheprovider backend/tests` | Exit 0 — 185 passed in 46.04s. |
| `cd frontend && npm run lint` | Exit 0. |
| `cd frontend && npx tsc --noEmit` | Exit 0. |
| `cd frontend && npm run build` | Exit 0 — optimized Next.js production build succeeded. |
| `cd frontend && npm test` | Exit 0 — 30 passed, 0 failed, 0 skipped. |
| `git diff --check` | Exit 0. |

The frontend test runner emits Node.js `MODULE_TYPELESS_PACKAGE_JSON` warnings
for TypeScript modules because `package.json` does not declare `"type":
"module"`. They did not affect test results; package metadata was not changed.

## Changed files for Task17

- `backend/app/scenario_engine.py`
- `backend/tests/test_scenario_engine.py`
- `backend/tests/test_scenario_validation.py`
- `frontend/app/page.tsx`
- `frontend/components/ScenarioComparisonPanel.tsx`
- `frontend/lib/scenario-comparison-state.ts` (new)
- `frontend/tests/scenario-comparison.test.mjs`
- `backend/benchmarks/TASK17_VALIDATION_AND_ROBUSTNESS_REPORT.md` (this report)

The repository already contained unrelated tracked and untracked changes before
Task17. They were preserved; no commit, reset, cleanup, or revert was performed.
