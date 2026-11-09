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

## 4. Test results (generated from `PLAYWRIGHT_TEST_RESULTS.json`)

Total **63** · PASS **49** · FAIL **14** · BLOCKED **0** · SKIPPED **0** · FLAKY (passed only on retry) **0**

### A. Initial application experience

| ID | Test | Status | Time | Observation / failure | Screenshots |
|---|---|---|---|---|---|
| A01 | application loads with a meaningful title and heading | **FAIL** | 1.8s | Error: document.title is still the Next.js scaffold default / expect(received).not.toMatch(expected) / Expected pattern: not /create next app/i / Received string:      "Create Next App" /   34 \|     const title = await page.title(); /   35 \|     note(info, `document.title = "${title}"`); | [A01_initial-dashboard_full.png](screenshots/A-initial/A01_initial-dashboard_full.png) |
| A02 | no console errors, page errors or failed network requests on load | **PASS** | 1.2s |  | [A02_after-network-idle.png](screenshots/A-initial/A02_after-network-idle.png) |
| A03 | navigation: Audit Log drawer opens, filters and closes | **PASS** | 0.9s |  | [A03_audit-log-drawer-open.png](screenshots/A-initial/A03_audit-log-drawer-open.png) |
| A04 | main controls are visible, enabled and interactive | **PASS** | 0.9s |  | [A04_main-controls.png](screenshots/A-initial/A04_main-controls.png) |
| A05 | no unexpected loading state or blank sections after load | **PASS** | 0.8s | train-occupancy bars drawn on first paint: 265 ; train-occupancy bars drawn on first paint: 265 |  |

### B. Maintenance scheduling workflow

| ID | Test | Status | Time | Observation / failure | Screenshots |
|---|---|---|---|---|---|
| B01 | routes load from the backend and match /api/data/routes | **PASS** | 0.3s | UI corridors: ["NDLS_CNB · New Delhi - Kanpur Central","HWH_PURI · Howrah - Puri","BCT_AMD · Mumbai Central - Ahmedabad"] ; UI corridors: ["NDLS_CNB · New Delhi - Kanpur Central","HWH_PURI · Howrah - Puri","BCT_AMD · Mumbai Central - Ahmedabad"] |  |
| B02 | changing corridor updates the section list | **PASS** | 0.4s |  |  |
| B03 | work-order manager lists the synthetic work orders | **PASS** | 0.9s |  | [B03_production-work-order-manager.png](screenshots/B-scheduling/B03_production-work-order-manager.png) |
| B04 | normal scheduling workflow: schedule, metrics and Gantt render | **PASS** | 9.8s |  | [B04_scheduling-interface-before-run.png](screenshots/B-scheduling/B04_scheduling-interface-before-run.png)<br>[B04_completed-scheduling-result_full.png](screenshots/B-scheduling/B04_completed-scheduling-result_full.png)<br>[E_production-gantt-chart.png](screenshots/E-gantt/E_production-gantt-chart.png) |
| B05 | displayed metrics correspond to the API response | **PASS** | 7.8s | API metrics: {"total_requests":30,"scheduled_requests":30,"search_space_pruned_pct":84.58,"fol_rule_compliance_pct":null,"co_location_merges_count":14,"solver_execution_time_sec":5.969961}; status=safety_unverified; solver_outcome=success ; API metrics: {"total_requests":30,"scheduled_requests":30,"search_space_pruned_pct":84.58,"fol_rule_compliance_pct":null,"co_location_merges_count":14,"solver_execution_time_sec": |  |
| B06 | safety-rule compliance is not shown as verified when the API says it is unverified | **PASS** | 8.4s | API fol_rule_compliance_pct=null, status=safety_unverified; card="Safety Rule Compliance" ; API fol_rule_compliance_pct=null, status=safety_unverified; card="Safety Rule Compliance" | [B06_safety-compliance-card.png](screenshots/G-errors-usability/B06_safety-compliance-card.png) |
| B07 | scheduled and unscheduled accounting is consistent with Gantt bars | **PASS** | 7.8s | bars=30, scheduled=30, unscheduled=0 ; unscheduled section visible in production UI: false ; bars=30, scheduled=30, unscheduled=0 ; unscheduled section visible in production UI: false |  |
| B08 | other corridor schedules and renders its own sections | **PASS** | 26.2s | HWH_PURI scheduled=30/30 ; HWH_PURI scheduled=30/30 | [B08_second-corridor-schedule.png](screenshots/B-scheduling/B08_second-corridor-schedule.png) |
| B09 | production work-order subset is honoured, then restored (state-restoring test) | **PASS** | 9.0s | after disabling 1 work order: total_requests=29 ; after disabling 1 work order: total_requests=29 |  |
| B10 | empty selection cannot be applied (empty work-order set) | **PASS** | 2.0s |  | [B10_all-work-orders-disabled.png](screenshots/G-errors-usability/B10_all-work-orders-disabled.png) |
| B11 | production UI communicates an unschedulable/partial outcome and lists unscheduled work orders | **FAIL** | 3.3s | Error: solver outcome shown / expect(received).toMatch(expected) / Expected pattern: /unschedulable/i / Received string:  "SymbIO-Block Dashboard· / Symbolic CSP & FOL railway maintenance block scheduling· / API online | [B11_partial-schedule-outcome.png](screenshots/B-scheduling/B11_partial-schedule-outcome.png) |

### C. Scenario management

| ID | Test | Status | Time | Observation / failure | Screenshots |
|---|---|---|---|---|---|
| C01 | create a scenario | **PASS** | 1.4s |  | [C01_scenario-management-empty.png](screenshots/C-scenarios/C01_scenario-management-empty.png)<br>[C01_scenario-created-draft.png](screenshots/C-scenarios/C01_scenario-created-draft.png) |
| C02 | creation validation: no name / no section | **PASS** | 0.9s | whitespace-only name: scenario selector present = false ; whitespace-only name: scenario selector present = false | [C02_create-without-input.png](screenshots/G-errors-usability/C02_create-without-input.png) |
| C03 | save a scenario writes versioned data to localStorage | **PASS** | 1.0s | stored keys: schema_version,scenarios ; stored keys: schema_version,scenarios | [C03_scenario-saved.png](screenshots/C-scenarios/C03_scenario-saved.png) |
| C04 | saved scenario persists after reload | **PASS** | 1.3s | scenario automatically loaded after reload: true ; scenario automatically loaded after reload: true | [C04_scenario-after-reload.png](screenshots/C-scenarios/C04_scenario-after-reload.png) |
| C05 | unsaved draft is discarded on reload without warning | **PASS** | 1.0s | draft survived reload=false; beforeunload warning shown=false ; draft survived reload=false; beforeunload warning shown=false | [C05_draft-lost-after-reload.png](screenshots/G-errors-usability/C05_draft-lost-after-reload.png) |
| C06 | duplicate a scenario | **PASS** | 1.0s | options after duplicate: ["Dup source","Dup source copy"] ; options after duplicate: ["Dup source","Dup source copy"] | [C06_scenario-duplicated.png](screenshots/C-scenarios/C06_scenario-duplicated.png) |
| C07 | rename / edit a scenario | **PASS** | 1.0s |  | [C07_scenario-renamed-edited.png](screenshots/C-scenarios/C07_scenario-renamed-edited.png) |
| C08 | delete a scenario (and the deletion persists once saved) | **PASS** | 1.2s | confirmation dialog shown before delete: true ; confirmation dialog shown before delete: true | [C08_scenario-deleted.png](screenshots/C-scenarios/C08_scenario-deleted.png) |
| C09 | scenario operations do not alter the production scheduling request | **PASS** | 19.5s |  | [C09_production-after-scenario-ops.png](screenshots/C-scenarios/C09_production-after-scenario-ops.png) |

### D. Scenario comparison

| ID | Test | Status | Time | Observation / failure | Screenshots |
|---|---|---|---|---|---|
| D01 | run comparison: both solvers complete and are displayed | **PASS** | 2.5s |  | [D01_comparison-overview-before-run.png](screenshots/D-comparison/D01_comparison-overview-before-run.png)<br>[D01_comparison-overview_full.png](screenshots/D-comparison/D01_comparison-overview_full.png)<br>[D01_solver-results-panels.png](screenshots/D-comparison/D01_solver-results-panels.png) |
| D02 | scheduled/unscheduled accounting matches API response | **PASS** | 0.9s |  |  |
| D03 | proof and validation indicators are shown and scoped | **PASS** | 1.5s |  | [D03_proof-and-validation-indicators.png](screenshots/D-comparison/D03_proof-and-validation-indicators.png) |
| D04 | differences between schedules are visible in the comparison UI | **PASS** | 1.0s | Identical placements for a trivial scenario; a differing-placement case could not be forced from the UI alone. ; Identical placements for a trivial scenario; a differing-placement case could not be forced from the UI alone. |  |
| D05 | comparison Gantt renders with solver lanes per work order | **PASS** | 1.5s |  | [D05_comparison-gantt.png](screenshots/D-comparison/D05_comparison-gantt.png) |
| D06 | empty scenario (no work orders) comparison | **FAIL** | 2.2s | Error: success wording for an empty comparison / expect(received).not.toMatch(expected) / Expected pattern: not /both assignments validated/i / Received string:      "Comparison status: Completed paired comparison; both assignments validated" /   449 \|     await shot(page, info, "D-comparison", "D06_empty-scenario-comparison", { fullPage: true }); /   450 \|     // A "validated" success banner for zero work orders c | [D06_empty-scenario-comparison.png](screenshots/D-comparison/D06_empty-scenario-comparison.png) |
| D07 | malformed / incomplete solver response is rejected, not shown as success (fault injection) | **FAIL** | 4.5s | Error: expect(received).toMatch(expected) / Expected pattern: /Comparison failed\|Solver unavailable\|validation failed\|invalid\|incomplete\|malformed/i / Received string:  "This page couldn’t load· / Reload to try again, or go back.· / Reload / Back" | [D07_incomplete-solver-response.png](screenshots/D-comparison/D07_incomplete-solver-response.png) |
| D08 | unavailable solver (HTTP 503) is communicated clearly (fault injection) | **PASS** | 1.4s |  | [D08_solver-unavailable-503.png](screenshots/D-comparison/D08_solver-unavailable-503.png) |
| D09 | backend unreachable during comparison (fault injection) | **PASS** | 1.4s |  | [D09_comparison-network-failure.png](screenshots/D-comparison/D09_comparison-network-failure.png) |
| D10 | non-co-locatable work orders on the same line are not overlapped by either solver | **PASS** | 1.5s | Baseline intervals: [[1,2],[2,3]] ; CP-SAT intervals: [[1,2],[2,3]] ; Baseline intervals: [[1,2],[2,3]] ; CP-SAT intervals: [[1,2],[2,3]] | [D10_no-colocation-gantt.png](screenshots/D-comparison/D10_no-colocation-gantt.png) |
| D11 | an over-constrained scenario reports unscheduled work orders consistently | **PASS** | 1.8s | unscheduled counts per solver: [[2,4],[2,4]] ; status banner for a run with unscheduled work orders: Comparison status: Completed paired comparison; both assignments validated ; unscheduled counts per solver: [[2,4],[2,4]] ; status banner for a run with unscheduled work orders: Comparison status: Completed paired comparison; both assignments validated | [D11_over-constrained-scenario.png](screenshots/D-comparison/D11_over-constrained-scenario.png) |

### E. Gantt chart and visualisation

| ID | Test | Status | Time | Observation / failure | Screenshots |
|---|---|---|---|---|---|
| E01 | chart axis, section rows, track-line labels and legend render | **PASS** | 7.7s |  |  |
| E02 | maintenance bars are positioned proportionally to start/end times | **PASS** | 8.9s | pixels per hour=43.92, worst x deviation=0.01px, worst width deviation=0.01px ; pixels per hour=43.92, worst x deviation=0.01px, worst width deviation=0.01px |  |
| E03 | departments are visually differentiated and co-located bars are striped | **PASS** | 7.7s | distinct colour-class sets: 3 ; striped=24, co-located in API=24 ; distinct colour-class sets: 3 ; striped=24, co-located in API=24 |  |
| E04 | no pixel overlap between maintenance bars, or with train occupancy, on the same track line | **PASS** | 7.8s | bar/bar overlaps=0; bar/train horizontal overlaps=0 ; bar/bar overlaps=0; bar/train horizontal overlaps=0 |  |
| E05 | clicking a bar opens the work-order inspector with matching data | **PASS** | 8.3s |  | [E05_work-order-inspector.png](screenshots/E-gantt/E05_work-order-inspector.png) |
| E06 | hover tooltip shows work-order details | **PASS** | 8.4s |  | [E06_tooltip.png](screenshots/E-gantt/E06_tooltip.png) |
| E07 | chart text is legible (minimum rendered font size) | **FAIL** | 16.1s | Error: smallest Gantt label font size (px) / expect(received).toBeGreaterThanOrEqual(expected) / Expected: >= 10 / Received:    9 /   650 \|     ); /   651 \|     note(info, `Gantt bar font sizes (px): ${JSON.stringify(sizes)}`); |  |
| E08 | chart keeps working after viewport resize and scrolls rather than breaking | **PASS** | 10.3s | 1366x768: docScrollWidth=1366, bars=30 ; 768x1024: docScrollWidth=768, bars=30 ; 390x844: docScrollWidth=390, bars=30 ; 1366x768: docScrollWidth=1366, bars=30 ; 768x1024: docScrollWidth=768, bars=30 ; 390x844: docScrollWidth=390, bars=30 | [E08_gantt-at-mobile-width.png](screenshots/E-gantt/E08_gantt-at-mobile-width.png) |

### F. Export functionality

| ID | Test | Status | Time | Observation / failure | Screenshots |
|---|---|---|---|---|---|
| F01 | export is not offered before a comparison has run | **PASS** | 0.4s |  |  |
| F02 | JSON export is non-empty, parseable and matches the displayed comparison | **PASS** | 1.5s | filename=symbio-experiment-7f18f681-2fa6-4f77-a9e4-e236c9cb6bcc-b112aca5-52fd-4229-ae8c-fb1fdfdb646c.json, bytes=11712 ; top-level keys: comparison,experiment,format,schedule_differences,schema_version,submitted_request ; filename=symbio-experiment-7f18f681-2fa6-4f77-a9e4-e236c9cb6bcc-b112aca5-52fd-4229-ae8c-fb1fdfdb646c.json, bytes=11712 ; top-level keys: comparison,experiment,format,schedule_differences,schema_vers | [F02_export-ready-and-json-download.png](screenshots/F-export/F02_export-ready-and-json-download.png) |
| F03 | CSV export is non-empty, parseable, one row per work order | **PASS** | 1.4s | filename=symbio-experiment-59f73e1a-0d4d-40b2-a67f-e4586b04d7e8-1face909-a931-482b-ae65-3e1beb85b955.csv, bytes=7662 ; header: schema_version,experiment_id,exported_at_utc,scenario_id,scenario_name,model_version,input_digest,comparison_status,paired_inputs_match,work_order_id,schedule_difference,submitted_department,submitted_section_id,submitted_track_line,submitted_duration_hrs,submitted_heavy_equipment,submitted_u | [F03_csv-download-confirmation.png](screenshots/F-export/F03_csv-download-confirmation.png) |
| F04 | repeated export is identical and triggers no extra solver run or storage write | **PASS** | 1.0s |  |  |
| F05 | CSV scheduled/unscheduled columns agree with the on-screen accounting | **PASS** | 1.0s | CSV header: schema_version,experiment_id,exported_at_utc,scenario_id,scenario_name,model_version,input_digest,comparison_status,paired_inputs_match,work_order_id,schedule_difference,submitted_department,submitted_section_id,submitted_track_line,submitted_duration_hrs,submitted_heavy_equipment,submitted_urgency,submitted_defect_type,submitted_co_location_allowed,baseline_run_status,baseline_input_digest,baseline_total |  |

### G. Error handling and usability

| ID | Test | Status | Time | Observation / failure | Screenshots |
|---|---|---|---|---|---|
| G01 | blank section list disables Generate Schedule | **PASS** | 0.8s |  | [G01_blank-sections.png](screenshots/G-errors-usability/G01_blank-sections.png) |
| G02 | unknown section ID produces a clear error, not a success state | **FAIL** | 7.7s | Error: an error banner should explain the unknown section / expect(received).toBeGreaterThan(expected) / Expected: > 0 / Received:   0 /   762 \|     const banner = await page.locator("div.border-rose-800").count(); /   763 \|     note(info, `error banner count=${banner}; metrics show: ${text.match(/\d+\/\d+ blocks scheduled/)?.[0]}; status: ${text.match(/status: \w+/)?.[0]}`); | [G02_unknown-section-error.png](screenshots/G-errors-usability/G02_unknown-section-error.png) |
| G03 | invalid horizon values are rejected or clearly reported, never silently altered | **FAIL** | 23.8s | Error: horizon 0 was silently changed to 24 with no error / expect(received).toBe(expected) // Object.is equality / Expected: true / Received: false /   784 \|     for (const v of ["0", "-5"]) { /   785 \|       const o = outcome[v]; | [G03_horizon-0.png](screenshots/G-errors-usability/G03_horizon-0.png)<br>[G03_horizon-neg5.png](screenshots/G-errors-usability/G03_horizon-neg5.png)<br>[G03_horizon-999.png](screenshots/G-errors-usability/G03_horizon-999.png) |
| G04 | schedule API HTTP 500 is surfaced and no stale success remains (fault injection) | **FAIL** | 21.0s | Error: previous successful result must not remain presented as current / expect(received).not.toMatch(expected) / Expected pattern: not /\d+\/\d+ blocks scheduled/ / Received string:      "SymbIO-Block Dashboard / Symbolic CSP & FOL railway maintenance block scheduling / API online | [G04_schedule-http-500.png](screenshots/G-errors-usability/G04_schedule-http-500.png) |
| G05 | backend unreachable during scheduling (fault injection) | **PASS** | 2.4s |  | [G05_schedule-network-failure.png](screenshots/G-errors-usability/G05_schedule-network-failure.png) |
| G06 | API health indicator reflects an offline backend (fault injection) | **PASS** | 3.7s | header status: API offline ; header status: API offline | [G06_api-offline-indicator.png](screenshots/G-errors-usability/G06_api-offline-indicator.png) |
| G07 | invalid timetable upload is rejected with an error | **PASS** | 2.0s |  | [G07_invalid-timetable-upload.png](screenshots/G-errors-usability/G07_invalid-timetable-upload.png) |
| G08 | production dashboard distinguishes simulation from operational safety | **FAIL** | 18.0s | Error: production scheduling area needs a simulation/not-operational disclaimer / expect(received).toMatch(expected) / Expected pattern: /not operational\|simulation\|synthetic\|not a safety\|not.*authori[sz]ed/i / Received string:  "Corridor / NDLS_CNB · New Delhi - Kanpur Central / HWH_PURI · Howrah - Puri | [G08_production-area-disclaimer-check.png](screenshots/G-errors-usability/G08_production-area-disclaimer-check.png) |
| G09 | no misleading success indicator before any schedule has been generated | **FAIL** | 1.6s | Error: co-location result pill is shown although nothing has been scheduled / expect(received).not.toMatch(expected) / Expected pattern: not /\d+ Parallel Maintenance Requests Bundled/ / Received string:      "Search Space Pruned (AC-3) / — / Safety Rule Compliance | [G09_metrics-before-first-run.png](screenshots/G-errors-usability/G09_metrics-before-first-run.png) |
| G10 | accessibility basics: unnamed controls and heading structure | **PASS** | 0.3s | unnamed controls=0; headings=H1,H2,H2,H2,H2,H2; html lang="en" ; unnamed controls=0; headings=H1,H2,H2,H2,H2,H2; html lang="en" |  |

### H. Responsive layout

| ID | Test | Status | Time | Observation / failure | Screenshots |
|---|---|---|---|---|---|
| H01 | layout at 1920x1080 | **FAIL** | 22.8s | Error: text rendered below 10px / expect(received).toBe(expected) // Object.is equality / Expected: 0 / Received: 42 /   911 \|       expect.soft(m.docW, "horizontal page overflow").toBeLessThanOrEqual(m.winW + 1); /   912 \|       expect.soft(m.clipped, "controls clipped outside viewport").toEqual([]); | [H01_desktop-1920x1080_initial.png](screenshots/H-responsive/H01_desktop-1920x1080_initial.png)<br>[H01_desktop-1920x1080_with-results_full.png](screenshots/H-responsive/H01_desktop-1920x1080_with-results_full.png)<br>[H01_desktop-1920x1080_viewport.png](screenshots/H-responsive/H01_desktop-1920x1080_viewport.png) |
| H02 | layout at 1366x768 | **FAIL** | 22.7s | Error: text rendered below 10px / expect(received).toBe(expected) // Object.is equality / Expected: 0 / Received: 42 /   911 \|       expect.soft(m.docW, "horizontal page overflow").toBeLessThanOrEqual(m.winW + 1); /   912 \|       expect.soft(m.clipped, "controls clipped outside viewport").toEqual([]); | [H02_laptop-1366x768_initial.png](screenshots/H-responsive/H02_laptop-1366x768_initial.png)<br>[H02_laptop-1366x768_with-results_full.png](screenshots/H-responsive/H02_laptop-1366x768_with-results_full.png)<br>[H02_laptop-1366x768_viewport.png](screenshots/H-responsive/H02_laptop-1366x768_viewport.png) |
| H03 | layout at 768x1024 | **FAIL** | 22.5s | Error: text rendered below 10px / expect(received).toBe(expected) // Object.is equality / Expected: 0 / Received: 42 /   911 \|       expect.soft(m.docW, "horizontal page overflow").toBeLessThanOrEqual(m.winW + 1); /   912 \|       expect.soft(m.clipped, "controls clipped outside viewport").toEqual([]); | [H03_tablet-768x1024_initial.png](screenshots/H-responsive/H03_tablet-768x1024_initial.png)<br>[H03_tablet-768x1024_with-results_full.png](screenshots/H-responsive/H03_tablet-768x1024_with-results_full.png)<br>[H03_tablet-768x1024_viewport.png](screenshots/H-responsive/H03_tablet-768x1024_viewport.png) |
| H04 | layout at 390x844 | **FAIL** | 21.8s | Error: horizontal page overflow / expect(received).toBeLessThanOrEqual(expected) / Expected: <= 391 / Received:    486 /   909 \|       }); /   910 \|       note(info, `docScrollWidth=${m.docW}/${m.winW}; clipped controls=${JSON.stringify(m.clipped)}; text nodes <10px=${m.tiny}`); | [H04_mobile-390x844_initial.png](screenshots/H-responsive/H04_mobile-390x844_initial.png)<br>[H04_mobile-390x844_with-results_full.png](screenshots/H-responsive/H04_mobile-390x844_with-results_full.png)<br>[H04_mobile-390x844_viewport.png](screenshots/H-responsive/H04_mobile-390x844_viewport.png) |

### Browser diagnostics (console errors / failed requests)

| ID | Console errors | Page errors | Failed requests | HTTP >= 400 |
|---|---|---|---|---|
| D07 | 0 | 1 | 0 | 0 |
| D08 | 1 | 0 | 0 | 1 |
| D09 | 1 | 0 | 1 | 0 |
| G03 | 1 | 0 | 0 | 1 |
| G04 | 1 | 0 | 0 | 1 |
| G05 | 1 | 0 | 1 | 0 |
| G06 | 2 | 0 | 2 | 0 |

Most of these were provoked deliberately by the fault-injection tests (D07-D09, G04-G06); details are in the JSON file.


