# SymbIO-Block Prototype — Playwright UI Audit Report

**Audit-only.** No application code or styling was modified; no fixes were applied.

## 1. Environment and startup

| Item | Value |
|---|---|
| Audit date | see `meta.audit_started` in `PLAYWRIGHT_TEST_RESULTS.json` |
| Host | macOS, local |
| Frontend | Next.js 16.4.1 (Turbopack dev server), http://localhost:3000 — already running, reused |
| Backend | FastAPI/uvicorn, http://localhost:8000 — already running, reused (`/health` OK) |
| Browser | Chromium headless shell (Playwright 1.x), 1 worker, 1 retry, trace on |
| Default viewport | 1366×768; H-tests use 1920×1080, 1366×768, 768×1024, 390×844 |
| Startup status | Both services reachable; nothing started or stopped by the audit |

Side effects: each test used a fresh browser context (user localStorage untouched). B09 temporarily replaced backend in-memory production work orders and restored them via "Reset to synthetic" (30 verified restored).
Tests D07–D09 and G04–G06 use `page.route` **fault injection** (not real backend failures).

## 2. Summary

63 tests: **49 PASS, 14 FAIL, 0 BLOCKED, 0 SKIPPED, 0 flaky**. All 14 failures reproduced on retry and are genuine prototype findings (test-side defects were fixed earlier). Note that H01–H04 fail for one shared cause (sub-10px text), H04 additionally for horizontal overflow.

## 3. Critical issues and ranked recommendations

**Critical / High (live-demo risk)**
1. **D07 – crash on incomplete comparison response.** If the experimental API omits a solver result, the whole page crashes (`Cannot read properties of undefined (reading 'solver')`, `frontend/lib/scenario-comparison-state.ts:51`). Fix: guard `isValidRunAccounting` and show a "rejected response" message.
2. **B11 – unschedulable/partial outcomes are not communicated in the production UI.** With horizon 1 the API returns `solver_outcome: unschedulable` and 28 unscheduled work orders; the UI shows only "2/30 blocks scheduled" and no unscheduled list/outcome.
3. **G02 – unknown section ID yields a success-looking empty result** (0.0%, "no_work", no error banner).
4. **G03 – horizon silently altered**: 0 → 24, −5 → 1 (partial schedule, no notice); 999 is rejected by the API but stale results stay visible.
5. **G04 – after an HTTP 500 the banner appears but stale metrics and Gantt remain** under it.
6. **G08 – no simulation / not-operationally-safe disclaimer in the production scheduling area** (present only in scenario/comparison panels).

**Medium**
7. **G09 – hardcoded pill** "14 Parallel Maintenance Requests Bundled…" is displayed before any schedule exists while metrics show "—".
8. **D06 – empty scenario** reports "Completed paired comparison; both assignments validated" (misleading).
9. **H04 – horizontal overflow at 390px** (scrollWidth 486 vs 390).
10. **H01–H04 / E07 – text below 10px** (42 text nodes at every viewport; Gantt badge 9px).

**Low**
11. **A01 – tab title is "Create Next App"** (scaffold default).

## 4a. Visual quality and UX (from screenshots)

Dark, polished theme with clear metric cards and strong, explicit disclaimers in the scenario/comparison/export areas. Weaknesses: dense Gantt with many tiny overlapping train labels (9–10px); the main scheduling workflow sits far below the scenario panels; mobile layout overflows; safety card shows "—" (honest, but unexplained); partial results look like successes.

## 4b. Positive findings (passed)
No console/page errors or failed requests on load (A02); metrics match API responses (B04–B07); scenario create/save/reload/duplicate/edit/delete work and do not affect production scheduling (C03–C09); both solvers complete with proof/validation indicators (D01–D05, D08–D11); Gantt bar positions accurate to 0.01px with no overlaps (E02–E04); JSON/CSV exports parse, match the displayed digest, repeat identically, with no extra solver call or storage write (F02–F05); 503/network failures are clearly shown (D08, D09, G05, G06).

## 5. Demo-readiness

**Not ready for an unguided live external demonstration.** A guided demo on the happy path (default horizon, valid sections, scenario comparison with valid data) works well, but items 1–6 can produce a crash or misleading results from ordinary input.

<!--GENERATED-RESULTS-->
