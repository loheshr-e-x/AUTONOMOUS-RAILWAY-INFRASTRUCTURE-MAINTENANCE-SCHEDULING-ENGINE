import {
  test,
  expect,
  note,
  blocked,
  shot,
  bodyText,
  openApp,
  createScenario,
  addWorkOrders,
  buildScenarioWithOrders,
  runComparison,
  generateSchedule,
  woBars,
  readDownload,
  creationSections,
  editSections,
  BASIC_ORDERS,
  API,
} from "./helpers";

const scenarioSelect = (page: import("@playwright/test").Page) =>
  page.getByRole("combobox", { name: "Scenario", exact: true });
const saveBtn = (page: import("@playwright/test").Page) => page.getByRole("button", { name: /Save scenarios/ });
const STORAGE_KEY = "symbio-block.scenarios";

// ───────────────────────── A. Initial application experience ─────────────────────────
test.describe("A. Initial application experience", () => {
  test("A01 application loads with a meaningful title and heading", async ({ page }, info) => {
    await openApp(page);
    await shot(page, info, "A-initial", "A01_initial-dashboard_full");
    await expect(page.getByRole("heading", { name: /SymbIO-Block Dashboard/i })).toBeVisible();
    // Browser tab title is part of the first impression of an external reviewer.
    const title = await page.title();
    note(info, `document.title = "${title}"`);
    expect(title, "document.title is still the Next.js scaffold default").not.toMatch(/create next app/i);
  });

  test("A02 no console errors, page errors or failed network requests on load", async ({ page, diag }, info) => {
    await openApp(page);
    await page.waitForLoadState("networkidle");
    await shot(page, info, "A-initial", "A02_after-network-idle", { fullPage: false });
    expect(diag.pageErrors, "uncaught page errors").toEqual([]);
    expect(diag.consoleErrors, "console errors").toEqual([]);
    expect(diag.failedRequests, "failed requests").toEqual([]);
    expect(diag.httpErrors, "HTTP >= 400 responses").toEqual([]);
  });

  test("A03 navigation: Audit Log drawer opens, filters and closes", async ({ page }, info) => {
    await openApp(page);
    await page.getByRole("button", { name: /Audit Log/ }).click();
    const drawer = page.locator("aside").filter({ hasText: "FOL Audit Log" });
    await expect(drawer).toBeVisible();
    await expect(drawer).toHaveAttribute("aria-hidden", "false");
    await shot(page, info, "A-initial", "A03_audit-log-drawer-open", { fullPage: false });
    await page.getByRole("button", { name: "Close audit log" }).click();
    await expect(drawer).toHaveAttribute("aria-hidden", "true");
  });

  test("A04 main controls are visible, enabled and interactive", async ({ page }, info) => {
    await openApp(page);
    const corridor = page.getByLabel("Corridor");
    await expect(corridor).toBeEnabled();
    await expect(page.getByLabel(/Section IDs/)).toBeEditable();
    await expect(page.getByLabel("Horizon (hrs)")).toBeEditable();
    await expect(page.getByLabel("AC-3 pruning")).toBeEnabled();
    await expect(page.getByLabel("Simulated annealing")).toBeEnabled();
    await expect(page.getByRole("button", { name: "Generate Schedule" })).toBeEnabled();
    await expect(page.getByRole("button", { name: /Work Orders/ })).toBeEnabled();
    await expect(page.getByRole("button", { name: "Reload trains" })).toBeEnabled();
    await page.getByLabel("AC-3 pruning").uncheck();
    await expect(page.getByLabel("AC-3 pruning")).not.toBeChecked();
    await page.getByLabel("AC-3 pruning").check();
    await shot(page, info, "A-initial", "A04_main-controls", { fullPage: false });
  });

  test("A05 no unexpected loading state or blank sections after load", async ({ page }, info) => {
    await openApp(page);
    await page.waitForLoadState("networkidle");
    const text = await bodyText(page);
    expect(text).not.toMatch(/loading\.\.\.|loading…/i);
    for (const section of ["Offline simulation scenarios", "Scenario solver comparison", "Time-Space Schedule", "Work Order Inspection"]) {
      expect(text, `section "${section}" present`).toContain(section);
    }
    // Train occupancy rows should be drawn on first paint (real data from /api/data/trains).
    const trainBars = await page.locator("div.bg-slate-600\\/80").count();
    note(info, `train-occupancy bars drawn on first paint: ${trainBars}`);
    expect(trainBars).toBeGreaterThan(0);
  });
});

// ───────────────────────── B. Maintenance scheduling workflow ─────────────────────────
test.describe("B. Maintenance scheduling workflow", () => {
  test("B01 routes load from the backend and match /api/data/routes", async ({ page, request }, info) => {
    const apiRoutes = await (await request.get(`${API}/api/data/routes`)).json();
    await openApp(page);
    const options = await page.getByLabel("Corridor").locator("option").allTextContents();
    note(info, `UI corridors: ${JSON.stringify(options)}`);
    expect(options.length).toBe(apiRoutes.length);
    for (const r of apiRoutes) expect(options.join("|")).toContain(r.route_id);
    await expect(page.getByLabel(/Section IDs/)).toHaveValue(/NDLS_CNB_SEC1/);
  });

  test("B02 changing corridor updates the section list", async ({ page }) => {
    await openApp(page);
    await page.getByLabel("Corridor").selectOption({ index: 1 });
    await expect(page.getByLabel(/Section IDs/)).toHaveValue(/HWH_PURI_SEC1/);
  });

  test("B03 work-order manager lists the synthetic work orders", async ({ page, request }, info) => {
    const apiWos = await (await request.get(`${API}/api/data/work-orders`)).json();
    await openApp(page);
    await page.getByRole("button", { name: /^Work Orders/ }).click();
    const dlg = page.locator("aside").filter({ hasText: "Work Order Manager" });
    await expect(dlg).toBeVisible();
    await expect(dlg.getByRole("checkbox")).toHaveCount(apiWos.length);
    await shot(page, info, "B-scheduling", "B03_production-work-order-manager", { fullPage: false });
    await dlg.getByRole("button", { name: "Close" }).click();
  });

  test("B04 normal scheduling workflow: schedule, metrics and Gantt render", async ({ page }, info) => {
    await openApp(page);
    await shot(page, info, "B-scheduling", "B04_scheduling-interface-before-run", { fullPage: false });
    const { resp, json } = await generateSchedule(page);
    expect(resp.status()).toBe(200);
    await expect(page.getByText(/blocks scheduled/)).toBeVisible();
    await expect(woBars(page)).toHaveCount(json.schedule.length);
    await shot(page, info, "B-scheduling", "B04_completed-scheduling-result_full");
    await shot(page, info, "E-gantt", "E_production-gantt-chart", {
      locator: page.locator("section, div").filter({ has: page.getByText("Time-Space Schedule") }).last(),
    });
  });

  test("B05 displayed metrics correspond to the API response", async ({ page }, info) => {
    await openApp(page);
    const { json } = await generateSchedule(page);
    const m = json.metrics;
    const text = await bodyText(page);
    note(info, `API metrics: ${JSON.stringify(m)}; status=${json.status}; solver_outcome=${json.solver_outcome}`);
    expect(text).toContain(`${m.scheduled_requests}/${m.total_requests} blocks scheduled`);
    expect(text).toContain(`${Number(m.search_space_pruned_pct).toFixed(1)}%`);
    expect(text).toContain(`${m.solver_execution_time_sec.toFixed(2)} s`);
    expect(text).toContain(`${m.co_location_merges_count} co-location merges`);
    expect(m.scheduled_requests + json.unscheduled_work_ids.length).toBe(m.total_requests);
  });

  test("B06 safety-rule compliance is not shown as verified when the API says it is unverified", async ({ page }, info) => {
    await openApp(page);
    const { json } = await generateSchedule(page);
    const card = page.locator("div").filter({ hasText: /^Safety Rule Compliance/ }).last();
    const cardText = (await card.innerText()).replace(/\n/g, " ");
    note(info, `API fol_rule_compliance_pct=${json.metrics.fol_rule_compliance_pct}, status=${json.status}; card="${cardText}"`);
    await shot(page, info, "G-errors-usability", "B06_safety-compliance-card", { fullPage: false });
    if (json.metrics.fol_rule_compliance_pct === null) {
      expect(cardText).not.toMatch(/\d+(\.\d+)?\s*%/);
      await expect(page.getByText(/status: safety_unverified/)).toBeVisible();
    }
  });

  test("B07 scheduled and unscheduled accounting is consistent with Gantt bars", async ({ page }, info) => {
    await openApp(page);
    const { json } = await generateSchedule(page);
    const barIds = (await woBars(page).allInnerTexts()).map((t) => t.replace(/\s+/g, " ").match(/WO-\S+/)?.[0]);
    const apiIds = json.schedule.map((s: { work_id: string }) => s.work_id).sort();
    expect([...new Set(barIds)].sort()).toEqual(apiIds);
    note(info, `bars=${barIds.length}, scheduled=${apiIds.length}, unscheduled=${json.unscheduled_work_ids.length}`);
    if (json.unscheduled_work_ids.length === 0) {
      const text = await bodyText(page);
      note(info, `unscheduled section visible in production UI: ${/unscheduled/i.test(text)}`);
    }
  });

  test("B08 other corridor schedules and renders its own sections", async ({ page }, info) => {
    await openApp(page);
    await page.getByLabel("Corridor").selectOption({ index: 1 });
    const { resp, json } = await generateSchedule(page);
    expect(resp.status()).toBe(200);
    await expect(page.getByText("HWH_PURI_SEC1").first()).toBeVisible();
    note(info, `HWH_PURI scheduled=${json.metrics.scheduled_requests}/${json.metrics.total_requests}`);
    await shot(page, info, "B-scheduling", "B08_second-corridor-schedule", { fullPage: false });
  });

  test("B09 production work-order subset is honoured, then restored (state-restoring test)", async ({ page }, info) => {
    await openApp(page);
    await page.getByRole("button", { name: /^Work Orders/ }).click();
    const dlg = page.locator("aside").filter({ hasText: "Work Order Manager" });
    try {
      const first = dlg.getByRole("checkbox").first();
      await first.uncheck();
      const apply = dlg.getByRole("button", { name: /Apply \d+ enabled/ });
      await expect(apply).toContainText("29");
      await apply.click();
      await dlg.getByRole("button", { name: "Close" }).click();
      const { json } = await generateSchedule(page);
      note(info, `after disabling 1 work order: total_requests=${json.metrics.total_requests}`);
      expect(json.metrics.total_requests).toBe(29);
    } finally {
      // Restore the shared in-memory backend state regardless of outcome.
      const open = await page.locator("aside").filter({ hasText: "Work Order Manager" }).count();
      if (!open) await page.getByRole("button", { name: /^Work Orders/ }).click();
      await page.locator("aside").filter({ hasText: "Work Order Manager" }).getByRole("button", { name: "Reset to synthetic" }).click();
      await page.waitForTimeout(800);
      const wos = await (await page.request.get(`${API}/api/data/work-orders`)).json();
      expect(wos.length, "backend work orders restored to synthetic set").toBe(30);
    }
  });

  test("B10 empty selection cannot be applied (empty work-order set)", async ({ page }, info) => {
    await openApp(page);
    await page.getByRole("button", { name: /^Work Orders/ }).click();
    const dlg = page.locator("aside").filter({ hasText: "Work Order Manager" });
    const boxes = dlg.getByRole("checkbox");
    const n = await boxes.count();
    for (let i = 0; i < n; i++) await boxes.nth(i).uncheck();
    await shot(page, info, "G-errors-usability", "B10_all-work-orders-disabled", { fullPage: false });
    await expect(dlg.getByRole("button", { name: /Apply 0 enabled/ })).toBeDisabled();
  });
});

test.describe("B (cont.). Solver outcome communication", () => {
  test("B11 production UI communicates an unschedulable/partial outcome and lists unscheduled work orders", async ({ page }, info) => {
    await openApp(page);
    await page.getByLabel("Horizon (hrs)").fill("1");
    const { json } = await generateSchedule(page);
    await page.waitForTimeout(600);
    const text = await bodyText(page);
    await shot(page, info, "B-scheduling", "B11_partial-schedule-outcome", { fullPage: true });
    note(info, `API: solver_outcome=${json.solver_outcome}, status=${json.status}, unscheduled=${json.unscheduled_work_ids.length}/${json.metrics.total_requests}`);
    expect(json.unscheduled_work_ids.length, "precondition: horizon=1 should leave work orders unscheduled").toBeGreaterThan(0);
    expect.soft(text, "solver outcome shown").toMatch(new RegExp(json.solver_outcome, "i"));
    expect.soft(text, "unscheduled work-order IDs shown").toContain(json.unscheduled_work_ids[0]);
    expect.soft(text, "unscheduled count / warning shown").toMatch(/unscheduled|not scheduled|could not be scheduled/i);
  });
});

// ───────────────────────── C. Scenario management ─────────────────────────
test.describe("C. Scenario management", () => {
  test("C01 create a scenario", async ({ page }, info) => {
    await openApp(page);
    await shot(page, info, "C-scenarios", "C01_scenario-management-empty", { fullPage: false });
    await createScenario(page, "Audit scenario A", ["NDLS_CNB_SEC1"]);
    await expect(saveBtn(page)).toContainText("*"); // unsaved-changes marker
    await shot(page, info, "C-scenarios", "C01_scenario-created-draft", { fullPage: false });
  });

  test("C02 creation validation: no name / no section", async ({ page }, info) => {
    await openApp(page);
    await page.getByRole("button", { name: "Create", exact: true }).click();
    await shot(page, info, "G-errors-usability", "C02_create-without-input", { fullPage: false });
    await expect(page.getByText(/Select at least one route section|name/i).first()).toBeVisible();
    await page.getByPlaceholder("My maintenance scenario").fill("   ");
    await creationSections(page).getByLabel("NDLS_CNB_SEC1").check();
    await page.getByRole("button", { name: "Create", exact: true }).click();
    const opts = await scenarioSelect(page).count();
    note(info, `whitespace-only name: scenario selector present = ${opts > 0}`);
  });

  test("C03 save a scenario writes versioned data to localStorage", async ({ page }, info) => {
    await openApp(page);
    await createScenario(page, "Audit scenario A", ["NDLS_CNB_SEC1"]);
    await saveBtn(page).click();
    const raw = await page.evaluate((k) => localStorage.getItem(k), STORAGE_KEY);
    expect(raw).not.toBeNull();
    const data = JSON.parse(raw!);
    note(info, `stored keys: ${Object.keys(data)}`);
    expect(data.schema_version).toBe(1);
    expect(JSON.stringify(data)).toContain("Audit scenario A");
    await expect(saveBtn(page)).not.toContainText("*");
    await shot(page, info, "C-scenarios", "C03_scenario-saved", { fullPage: false });
  });

  test("C04 saved scenario persists after reload", async ({ page }, info) => {
    await openApp(page);
    await createScenario(page, "Persist me", ["NDLS_CNB_SEC1"]);
    await addWorkOrders(page, [BASIC_ORDERS[0]]);
    await saveBtn(page).click();
    await page.reload();
    await expect(page.getByText("API online")).toBeVisible();
    const autoLoaded = (await scenarioSelect(page).count()) > 0;
    note(info, `scenario automatically loaded after reload: ${autoLoaded}`);
    if (!autoLoaded) await page.getByRole("button", { name: "Reload saved" }).click();
    await expect(scenarioSelect(page)).toContainText("Persist me");
    await expect(page.getByRole("button", { name: /Manage work orders \(1\)/ })).toBeVisible();
    await shot(page, info, "C-scenarios", "C04_scenario-after-reload", { fullPage: false });
  });

  test("C05 unsaved draft is discarded on reload without warning", async ({ page }, info) => {
    await openApp(page);
    await createScenario(page, "Unsaved draft", ["NDLS_CNB_SEC1"]);
    let beforeUnload = false;
    page.on("dialog", async (d) => {
      if (d.type() === "beforeunload") beforeUnload = true;
      await d.dismiss();
    });
    await page.reload();
    const stillThere = (await scenarioSelect(page).count()) > 0;
    note(info, `draft survived reload=${stillThere}; beforeunload warning shown=${beforeUnload}`);
    await shot(page, info, "G-errors-usability", "C05_draft-lost-after-reload", { fullPage: false });
    // Documented as designed behaviour ("It will remain a draft until saved"); the missing warning is a usability observation.
    expect(stillThere).toBe(false);
  });

  test("C06 duplicate a scenario", async ({ page }, info) => {
    await openApp(page);
    await createScenario(page, "Dup source", ["NDLS_CNB_SEC1"]);
    await page.getByRole("button", { name: "Duplicate" }).click();
    const opts = await scenarioSelect(page).locator("option").allTextContents();
    note(info, `options after duplicate: ${JSON.stringify(opts)}`);
    expect(opts.length).toBe(2);
    expect(new Set(opts).size, "duplicate must be distinguishable by name").toBe(2);
    await shot(page, info, "C-scenarios", "C06_scenario-duplicated", { fullPage: false });
  });

  test("C07 rename / edit a scenario", async ({ page }, info) => {
    await openApp(page);
    await createScenario(page, "Old name", ["NDLS_CNB_SEC1"]);
    await page.getByLabel("Scenario name", { exact: true }).fill("Renamed scenario");
    await page.getByLabel(/Horizon \(hours/).fill("12");
    await editSections(page).getByLabel("NDLS_CNB_SEC2").check();
    await page.getByRole("button", { name: "Update scenario settings" }).click();
    await expect(scenarioSelect(page)).toContainText("Renamed scenario");
    await saveBtn(page).click();
    const data = JSON.parse((await page.evaluate((k) => localStorage.getItem(k), STORAGE_KEY))!);
    const s = JSON.stringify(data);
    expect(s).toContain("Renamed scenario");
    expect(s).toContain("NDLS_CNB_SEC2");
    await shot(page, info, "C-scenarios", "C07_scenario-renamed-edited", { fullPage: false });
  });

  test("C08 delete a scenario (and the deletion persists once saved)", async ({ page }, info) => {
    await openApp(page);
    await createScenario(page, "To delete", ["NDLS_CNB_SEC1"]);
    await saveBtn(page).click();
    let confirmSeen = false;
    page.on("dialog", async (d) => {
      confirmSeen = true;
      await d.accept();
    });
    await page.getByRole("button", { name: "Delete" }).click();
    note(info, `confirmation dialog shown before delete: ${confirmSeen}`);
    await expect(page.getByText("No saved scenarios yet.")).toBeVisible();
    await saveBtn(page).click();
    await page.reload();
    await expect(page.getByText("API online")).toBeVisible();
    await expect(page.getByText("To delete")).toHaveCount(0);
    await shot(page, info, "C-scenarios", "C08_scenario-deleted", { fullPage: false });
    expect(confirmSeen, "destructive Delete should ask for confirmation").toBe(true);
  });

  test("C09 scenario operations do not alter the production scheduling request", async ({ page }, info) => {
    await openApp(page);
    const before = await generateSchedule(page);
    await buildScenarioWithOrders(page, "Isolation check");
    await saveBtn(page).click();
    await runComparison(page);
    await page.getByRole("button", { name: "Duplicate" }).click();
    const after = await generateSchedule(page);
    expect(after.req, "production request body unchanged").toBe(before.req);
    expect(after.json.metrics.total_requests).toBe(before.json.metrics.total_requests);
    expect(after.json.schedule.length).toBe(before.json.schedule.length);
    expect(after.json.status).toBe(before.json.status);
    await shot(page, info, "C-scenarios", "C09_production-after-scenario-ops");
  });
});

// ───────────────────────── D. Scenario comparison ─────────────────────────
test.describe("D. Scenario comparison", () => {
  test("D01 run comparison: both solvers complete and are displayed", async ({ page }, info) => {
    await openApp(page);
    await buildScenarioWithOrders(page);
    await shot(page, info, "D-comparison", "D01_comparison-overview-before-run", { fullPage: false });
    const resp = await runComparison(page);
    expect(resp.status()).toBe(200);
    const text = await bodyText(page);
    expect(text).toContain("Baseline solver");
    expect(text).toContain("Experimental CP-SAT solver");
    expect(text).toMatch(/Completed paired comparison/);
    await shot(page, info, "D-comparison", "D01_comparison-overview_full");
    await shot(page, info, "D-comparison", "D01_solver-results-panels", {
      locator: page.locator("div").filter({ hasText: /^Baseline solver/ }).last(),
    });
  });

  test("D02 scheduled/unscheduled accounting matches API response", async ({ page }) => {
    await openApp(page);
    await buildScenarioWithOrders(page);
    const resp = await runComparison(page);
    const body = await resp.json();
    const text = await bodyText(page);
    const matches = [...text.matchAll(/Scheduled work orders\s*\n?\s*(\d+) \/ (\d+)/g)];
    expect(matches.length).toBe(2);
    for (const m of matches) expect(Number(m[1])).toBeLessThanOrEqual(Number(m[2]));
    expect(JSON.stringify(body)).toContain("AUD-1");
    expect(text).toMatch(/Unscheduled work orders\s*\n?\s*0 \/ 3/);
  });

  test("D03 proof and validation indicators are shown and scoped", async ({ page }, info) => {
    await openApp(page);
    await buildScenarioWithOrders(page);
    await runComparison(page);
    const text = await bodyText(page);
    for (const s of [
      "Independent validation",
      "Complete assignment",
      "Maximum coverage",
      "Complete schedule infeasibility",
      "Objective optimality",
      "CP-SAT proof scope",
      "not operational authorization",
    ]) expect.soft(text, s).toContain(s);
    expect.soft(text).toMatch(/Independent model validation passed/);
    expect.soft(text).toMatch(/Input digest/);
    await shot(page, info, "D-comparison", "D03_proof-and-validation-indicators", {
      locator: page.locator("section, div").filter({ has: page.getByText("Comparison summary", { exact: true }) }).last(),
    });
  });

  test("D04 differences between schedules are visible in the comparison UI", async ({ page }, info) => {
    await openApp(page);
    await buildScenarioWithOrders(page);
    await runComparison(page);
    const text = await bodyText(page);
    expect(text).toMatch(/Work-order schedule differences/);
    expect(text).toMatch(/Same placement/);
    note(info, "Identical placements for a trivial scenario; a differing-placement case could not be forced from the UI alone.");
  });

  test("D05 comparison Gantt renders with solver lanes per work order", async ({ page }, info) => {
    await openApp(page);
    await buildScenarioWithOrders(page);
    await runComparison(page);
    await expect(page.getByText("Schedule placement comparison")).toBeVisible();
    for (const id of ["AUD-1", "AUD-2", "AUD-3"]) await expect(page.getByText(id, { exact: true }).first()).toBeVisible();
    await expect(page.getByText(/Baseline:\d\d:\d\d–\d\d:\d\d/).first()).toBeVisible();
    await expect(page.getByText(/CP-SAT:\d\d:\d\d–\d\d:\d\d/).first()).toBeVisible();
    await shot(page, info, "D-comparison", "D05_comparison-gantt", {
      locator: page.locator("div").filter({ hasText: /^Schedule placement comparison/ }).last(),
    });
  });

  test("D06 empty scenario (no work orders) comparison", async ({ page }, info) => {
    await openApp(page);
    await createScenario(page, "Empty", ["NDLS_CNB_SEC1"]);
    await runComparison(page);
    await expect(page.getByText("This scenario contains no work orders to plot.")).toBeVisible();
    const text = await bodyText(page);
    const banner = text.match(/Comparison status:[^\n]*/)?.[0];
    note(info, `banner for empty scenario: ${banner}`);
    await shot(page, info, "D-comparison", "D06_empty-scenario-comparison", { fullPage: true });
    // A "validated" success banner for zero work orders could mislead; it is recorded, and asserted below.
    expect(banner ?? "", "success wording for an empty comparison").not.toMatch(/both assignments validated/i);
  });

  test("D07 malformed / incomplete solver response is rejected, not shown as success (fault injection)", async ({ page }, info) => {
    await openApp(page);
    await buildScenarioWithOrders(page);
    await page.route("**/api/experimental/scenarios/compare", async (route) => {
      const real = await route.fetch();
      const body = await real.json();
      delete body.cp_sat; // drop one solver result to simulate an incomplete response
      for (const k of Object.keys(body)) if (/cp.?sat/i.test(k)) delete body[k];
      await route.fulfill({ response: real, json: body });
    });
    await runComparison(page);
    await page.waitForTimeout(800);
    const text = await bodyText(page);
    await shot(page, info, "D-comparison", "D07_incomplete-solver-response", { fullPage: false });
    expect(text).not.toMatch(/Completed paired comparison/);
    expect(text).toMatch(/Comparison failed|Solver unavailable|validation failed|invalid|incomplete|malformed/i);
  });

  test("D08 unavailable solver (HTTP 503) is communicated clearly (fault injection)", async ({ page }, info) => {
    await openApp(page);
    await buildScenarioWithOrders(page);
    await page.route("**/api/experimental/scenarios/compare", (r) =>
      r.fulfill({ status: 503, json: { detail: "CP-SAT solver is not installed" } }),
    );
    await runComparison(page);
    await expect(page.getByText(/Solver unavailable|Comparison failed/)).toBeVisible();
    await shot(page, info, "D-comparison", "D08_solver-unavailable-503", { fullPage: false });
    expect(await bodyText(page)).not.toMatch(/Completed paired comparison/);
  });

  test("D09 backend unreachable during comparison (fault injection)", async ({ page }, info) => {
    await openApp(page);
    await buildScenarioWithOrders(page);
    await page.route("**/api/experimental/scenarios/compare", (r) => r.abort("connectionrefused"));
    await page.getByRole("button", { name: "Run comparison" }).click();
    await expect(page.getByText(/Solver unavailable|Comparison failed|Could not|Failed to fetch|network/i).first()).toBeVisible();
    await shot(page, info, "D-comparison", "D09_comparison-network-failure", { fullPage: false });
    expect(await bodyText(page)).not.toMatch(/Completed paired comparison/);
  });

  test("D10 non-co-locatable work orders on the same line are not overlapped by either solver", async ({ page }, info) => {
    await openApp(page);
    await buildScenarioWithOrders(page, "No-coloc", [
      { id: "NC-1", section: "NDLS_CNB_SEC1", line: "UP_LINE", dept: 1, coloc: false },
      { id: "NC-2", section: "NDLS_CNB_SEC1", line: "UP_LINE", dept: 0, coloc: false },
    ]);
    await runComparison(page);
    const text = await bodyText(page);
    for (const solver of ["Baseline", "CP-SAT"]) {
      const iv = [...text.matchAll(new RegExp(`${solver}:(\\d\\d):(\\d\\d)–(\\d\\d):(\\d\\d)`, "g"))].map((m) => [
        +m[1] + +m[2] / 60,
        +m[3] + +m[4] / 60,
      ]);
      note(info, `${solver} intervals: ${JSON.stringify(iv)}`);
      expect(iv.length).toBe(2);
      expect(iv[0][1] <= iv[1][0] || iv[1][1] <= iv[0][0], `${solver} intervals overlap`).toBe(true);
    }
    await shot(page, info, "D-comparison", "D10_no-colocation-gantt", { fullPage: true });
  });

  test("D11 an over-constrained scenario reports unscheduled work orders consistently", async ({ page }, info) => {
    await openApp(page);
    await createScenario(page, "Tight", ["NDLS_CNB_SEC1"]);
    await page.getByLabel(/Horizon \(hours/).fill("2");
    await page.getByRole("button", { name: "Update scenario settings" }).click();
    const orders = ["T-1", "T-2", "T-3", "T-4"].map((id) => ({
      id,
      section: "NDLS_CNB_SEC1",
      line: "UP_LINE" as const,
      dept: 0,
      coloc: false,
    }));
    await addWorkOrders(page, orders);
    await runComparison(page);
    const text = await bodyText(page);
    await shot(page, info, "D-comparison", "D11_over-constrained-scenario", { fullPage: true });
    const unsched = [...text.matchAll(/Unscheduled work orders\s*\n?\s*(\d+) \/ (\d+)/g)].map((m) => [+m[1], +m[2]]);
    note(info, `unscheduled counts per solver: ${JSON.stringify(unsched)}`);
    if (unsched.every(([u]) => u === 0)) {
      blocked(info, "Could not construct an over-constrained scenario through the UI that yields unscheduled orders (all orders were scheduled).");
    }
    expect(unsched.length).toBe(2);
    for (const [u, total] of unsched) {
      expect(u).toBeGreaterThan(0);
      expect(total).toBe(4);
    }
    const scheduled = [...text.matchAll(/Scheduled work orders\s*\n?\s*(\d+) \/ (\d+)/g)].map((m) => +m[1]);
    scheduled.forEach((sc, i) => expect(sc + unsched[i][0]).toBe(4));
    for (const id of ["T-1", "T-2", "T-3", "T-4"]) expect(text).toContain(id);
    note(info, `status banner for a run with unscheduled work orders: ${text.match(/Comparison status:[^\n]*/)?.[0]}`);
  });
});

// ───────────────────────── E. Gantt chart and visualisation ─────────────────────────
test.describe("E. Gantt chart and visualisation", () => {
  test("E01 chart axis, section rows, track-line labels and legend render", async ({ page }) => {
    await openApp(page);
    await generateSchedule(page);
    const text = await bodyText(page);
    for (const t of ["00:00", "12:00", "24:00", "NDLS_CNB_SEC1", "UP LINE", "DOWN LINE", "ENG = ENGINEERING", "SIG = SIGNALLING", "TRC = TRACTION", "Striped = co-located block", "Train occupancy"]) {
      expect.soft(text, t).toContain(t);
    }
  });

  test("E02 maintenance bars are positioned proportionally to start/end times", async ({ page }, info) => {
    await openApp(page);
    const { json } = await generateSchedule(page);
    type Blk = { work_id: string; start_time_hr: number; end_time_hr: number };
    const blocks: Blk[] = json.schedule;
    const geo: Record<string, { x: number; w: number }> = {};
    for (const b of blocks) {
      const box = await page.getByRole("button", { name: new RegExp(`${b.work_id}$`) }).first().boundingBox();
      geo[b.work_id] = { x: box!.x, w: box!.width };
    }
    const minB = blocks.reduce((a, b) => (b.start_time_hr < a.start_time_hr ? b : a));
    const maxB = blocks.reduce((a, b) => (b.start_time_hr > a.start_time_hr ? b : a));
    const k = (geo[maxB.work_id].x - geo[minB.work_id].x) / (maxB.start_time_hr - minB.start_time_hr);
    let worst = 0;
    let worstW = 0;
    for (const b of blocks) {
      const expX = geo[minB.work_id].x + (b.start_time_hr - minB.start_time_hr) * k;
      worst = Math.max(worst, Math.abs(geo[b.work_id].x - expX));
      const expW = (b.end_time_hr - b.start_time_hr) * k;
      worstW = Math.max(worstW, Math.abs(geo[b.work_id].w - expW));
    }
    note(info, `pixels per hour=${k.toFixed(2)}, worst x deviation=${worst.toFixed(2)}px, worst width deviation=${worstW.toFixed(2)}px`);
    expect(worst).toBeLessThan(3);
    expect(worstW).toBeLessThan(4);
  });

  test("E03 departments are visually differentiated and co-located bars are striped", async ({ page }, info) => {
    await openApp(page);
    const { json } = await generateSchedule(page);
    const bg = await woBars(page).evaluateAll((els) =>
      els.map((e) => ({ cls: e.className, img: getComputedStyle(e).backgroundImage })),
    );
    const colours = new Set(bg.map((b) => b.cls.match(/(bg|border)-(blue|sky|cyan|amber|yellow|orange|rose|red|emerald)-\d+/g)?.join(",")));
    note(info, `distinct colour-class sets: ${colours.size}`);
    expect(colours.size).toBeGreaterThanOrEqual(3);
    const striped = bg.filter((b) => b.img.includes("gradient")).length;
    const colocated = json.schedule.filter((s: { co_located_with?: string[] }) => s.co_located_with?.length).length;
    note(info, `striped=${striped}, co-located in API=${colocated}`);
    expect(striped).toBe(colocated);
  });

  test("E04 no pixel overlap between maintenance bars, or with train occupancy, on the same track line", async ({ page }, info) => {
    await openApp(page);
    await generateSchedule(page);
    const result = await page.evaluate(() => {
      const bars = Array.from(document.querySelectorAll("button")).filter((b) => /^(ENG|SIG|TRC)\s*WO-/.test(b.textContent ?? ""));
      const rect = (e: Element) => e.getBoundingClientRect();
      const inter = (a: DOMRect, b: DOMRect) => a.left < b.right - 0.5 && b.left < a.right - 0.5 && a.top < b.bottom - 0.5 && b.top < a.bottom - 0.5;
      const barBar: string[] = [];
      const barTrain: string[] = [];
      for (let i = 0; i < bars.length; i++)
        for (let j = i + 1; j < bars.length; j++) if (inter(rect(bars[i]), rect(bars[j]))) barBar.push(`${bars[i].textContent}|${bars[j].textContent}`);
      for (const b of bars) {
        const lane = b.parentElement!;
        for (const t of Array.from(lane.querySelectorAll("div.absolute")).filter((d) => d.className.includes("bg-slate-600"))) {
          const tr = rect(t);
          const br = rect(b);
          if (tr.left < br.right - 0.5 && br.left < tr.right - 0.5) barTrain.push(`${b.textContent} x-overlaps train ${t.textContent}`);
        }
      }
      return { barBar, barTrain };
    });
    note(info, `bar/bar overlaps=${result.barBar.length}; bar/train horizontal overlaps=${result.barTrain.length}`);
    expect.soft(result.barBar, "overlapping maintenance bars (excluding co-located lanes)").toEqual([]);
    expect.soft(result.barTrain.slice(0, 5), "maintenance bar shares time with train occupancy on same line").toEqual([]);
  });

  test("E05 clicking a bar opens the work-order inspector with matching data", async ({ page }, info) => {
    await openApp(page);
    const { json } = await generateSchedule(page);
    const first = json.schedule[0];
    await page.getByRole("button", { name: new RegExp(`${first.work_id}$`) }).first().click();
    const panel = page.locator("section, div").filter({ has: page.getByText("Work Order Inspection", { exact: true }) }).last();
    await expect(panel).toContainText(first.work_id);
    await expect(panel).toContainText(first.section_id);
    await shot(page, info, "E-gantt", "E05_work-order-inspector", { fullPage: false, locator: panel });
  });

  test("E06 hover tooltip shows work-order details", async ({ page }, info) => {
    await openApp(page);
    const { json } = await generateSchedule(page);
    const id = json.schedule[0].work_id;
    await page.getByRole("button", { name: new RegExp(`${id}$`) }).first().hover();
    await expect(page.getByText(new RegExp(`${id} · `)).first()).toBeVisible();
    await shot(page, info, "E-gantt", "E06_tooltip", { fullPage: false });
  });

  test("E07 chart text is legible (minimum rendered font size)", async ({ page }, info) => {
    await openApp(page);
    await generateSchedule(page);
    const sizes = await woBars(page).first().evaluate((b) =>
      Array.from(b.querySelectorAll("span")).map((s) => parseFloat(getComputedStyle(s).fontSize)),
    );
    note(info, `Gantt bar font sizes (px): ${JSON.stringify(sizes)}`);
    expect(Math.min(...sizes), "smallest Gantt label font size (px)").toBeGreaterThanOrEqual(10);
  });

  test("E08 chart keeps working after viewport resize and scrolls rather than breaking", async ({ page }, info) => {
    await openApp(page);
    await generateSchedule(page);
    for (const [w, h] of [[1366, 768], [768, 1024], [390, 844]]) {
      await page.setViewportSize({ width: w, height: h });
      await page.waitForTimeout(500);
      const m = await page.evaluate(() => ({
        docW: document.documentElement.scrollWidth,
        winW: window.innerWidth,
        bars: Array.from(document.querySelectorAll("button")).filter((b) => /^(ENG|SIG|TRC)\s*WO-/.test(b.textContent ?? "")).length,
      }));
      note(info, `${w}x${h}: docScrollWidth=${m.docW}, bars=${m.bars}`);
      expect.soft(m.bars).toBe(30);
      expect.soft(m.docW, `page horizontal overflow at ${w}px`).toBeLessThanOrEqual(m.winW + 1);
    }
    await shot(page, info, "E-gantt", "E08_gantt-at-mobile-width", { fullPage: false });
  });
});

// ───────────────────────── F. Export functionality ─────────────────────────
test.describe("F. Export functionality", () => {
  async function ready(page: import("@playwright/test").Page) {
    await openApp(page);
    await buildScenarioWithOrders(page);
    const resp = await runComparison(page);
    return resp.json();
  }

  test("F01 export is not offered before a comparison has run", async ({ page }) => {
    await openApp(page);
    await createScenario(page, "No run yet", ["NDLS_CNB_SEC1"]);
    await expect(page.getByRole("button", { name: "Download JSON" })).toHaveCount(0);
  });

  test("F02 JSON export is non-empty, parseable and matches the displayed comparison", async ({ page }, info) => {
    await ready(page);
    const { filename, content } = await readDownload(page, "Download JSON");
    note(info, `filename=${filename}, bytes=${content.length}`);
    expect(content.length).toBeGreaterThan(100);
    const json = JSON.parse(content);
    const text = await bodyText(page);
    note(info, `top-level keys: ${Object.keys(json)}`);
    const digest = text.match(/Response input digest: ([0-9a-f]{64})/)?.[1];
    expect(digest).toBeTruthy();
    expect(content).toContain(digest!);
    const expId = text.match(/experiment ([0-9a-f-]{36})/)?.[1];
    expect(content).toContain(expId!);
    expect(content).toContain("AUD-1");
    await shot(page, info, "F-export", "F02_export-ready-and-json-download", { fullPage: false });
  });

  test("F03 CSV export is non-empty, parseable, one row per work order", async ({ page }, info) => {
    await ready(page);
    const { filename, content } = await readDownload(page, "Download CSV");
    note(info, `filename=${filename}, bytes=${content.length}`);
    const lines = content.trim().split(/\r?\n/);
    expect(lines.length).toBe(1 + 3);
    const cols = lines[0].split(",").length;
    note(info, `header: ${lines[0].slice(0, 300)}`);
    expect(cols).toBeGreaterThan(5);
    for (const id of ["AUD-1", "AUD-2", "AUD-3"]) expect(content).toContain(id);
    await shot(page, info, "F-export", "F03_csv-download-confirmation", { fullPage: false });
  });

  test("F04 repeated export is identical and triggers no extra solver run or storage write", async ({ page }) => {
    await ready(page);
    let compareCalls = 0;
    page.on("request", (r) => {
      if (r.url().includes("/api/experimental/scenarios/compare")) compareCalls++;
    });
    const storageBefore = await page.evaluate(() => JSON.stringify({ ...localStorage }));
    const a = await readDownload(page, "Download JSON");
    const b = await readDownload(page, "Download JSON");
    const storageAfter = await page.evaluate(() => JSON.stringify({ ...localStorage }));
    expect(b.content).toBe(a.content);
    expect(compareCalls).toBe(0);
    expect(storageAfter).toBe(storageBefore);
  });

  test("F05 CSV scheduled/unscheduled columns agree with the on-screen accounting", async ({ page }, info) => {
    await ready(page);
    const { content } = await readDownload(page, "Download CSV");
    const [header, ...rows] = content.trim().split(/\r?\n/);
    note(info, `CSV header: ${header}`);
    const text = await bodyText(page);
    expect(text).toMatch(/Scheduled work orders\s*\n?\s*3 \/ 3/);
    expect(rows.length).toBe(3);
  });
});

// ───────────────────────── G. Error handling and usability ─────────────────────────
test.describe("G. Error handling and usability", () => {
  test("G01 blank section list disables Generate Schedule", async ({ page }, info) => {
    await openApp(page);
    await page.getByLabel(/Section IDs/).fill("");
    await shot(page, info, "G-errors-usability", "G01_blank-sections", { fullPage: false });
    await expect(page.getByRole("button", { name: "Generate Schedule" })).toBeDisabled();
  });

  test("G02 unknown section ID produces a clear error, not a success state", async ({ page }, info) => {
    await openApp(page);
    await page.getByLabel(/Section IDs/).fill("SIM-A");
    await page.getByRole("button", { name: "Generate Schedule" }).click();
    await page.waitForTimeout(3000);
    const text = await bodyText(page);
    await shot(page, info, "G-errors-usability", "G02_unknown-section-error", { fullPage: false });
    note(info, `visible error: ${text.match(/(UNKNOWN_SECTION|Unknown section|error|invalid|failed)[^\n]*/i)?.[0]}`);
    const banner = await page.locator("div.border-rose-800").count();
    note(info, `error banner count=${banner}; metrics show: ${text.match(/\d+\/\d+ blocks scheduled/)?.[0]}; status: ${text.match(/status: \w+/)?.[0]}`);
    expect(banner, "an error banner should explain the unknown section").toBeGreaterThan(0);
  });

  test("G03 invalid horizon values are rejected or clearly reported, never silently altered", async ({ page }, info) => {
    await openApp(page);
    const horizon = page.getByLabel("Horizon (hrs)");
    const outcome: Record<string, { sent: number; status: number; banner: number; scheduled?: string }> = {};
    for (const v of ["0", "-5", "999"]) {
      await horizon.fill(v);
      const { resp, req } = await generateSchedule(page);
      await page.waitForTimeout(600);
      outcome[v] = {
        sent: JSON.parse(req).time_horizon_hrs,
        status: resp.status(),
        banner: await page.locator("div.border-rose-800").count(),
        scheduled: (await bodyText(page)).match(/\d+\/\d+ blocks scheduled/)?.[0],
      };
      await shot(page, info, "G-errors-usability", `G03_horizon-${v.replace("-", "neg")}`, { fullPage: false });
    }
    note(info, `typed -> request/response: ${JSON.stringify(outcome)}`);
    for (const v of ["0", "-5"]) {
      const o = outcome[v];
      expect.soft(o.sent === Number(v) || o.banner > 0, `horizon ${v} was silently changed to ${o.sent} with no error`).toBe(true);
    }
    expect.soft(outcome["999"].banner, "999 is rejected with a visible banner").toBeGreaterThan(0);
  });

  test("G04 schedule API HTTP 500 is surfaced and no stale success remains (fault injection)", async ({ page }, info) => {
    await openApp(page);
    await generateSchedule(page);
    await expect(page.getByText(/blocks scheduled/)).toBeVisible();
    await page.route("**/api/schedule/generate", (r) => r.fulfill({ status: 500, json: { detail: "Internal Server Error" } }));
    await page.getByRole("button", { name: "Generate Schedule" }).click();
    await page.waitForTimeout(1500);
    await shot(page, info, "G-errors-usability", "G04_schedule-http-500", { fullPage: false });
    const text = await bodyText(page);
    await expect(page.locator("div.border-rose-800")).toContainText(/500|Internal Server Error/);
    expect.soft(text, "previous successful result must not remain presented as current").not.toMatch(/\d+\/\d+ blocks scheduled/);
  });

  test("G05 backend unreachable during scheduling (fault injection)", async ({ page }, info) => {
    await openApp(page);
    await page.route("**/api/schedule/generate", (r) => r.abort("connectionrefused"));
    await page.getByRole("button", { name: "Generate Schedule" }).click();
    await page.waitForTimeout(1500);
    await shot(page, info, "G-errors-usability", "G05_schedule-network-failure", { fullPage: false });
    await expect(page.locator("div.border-rose-800")).toBeVisible();
  });

  test("G06 API health indicator reflects an offline backend (fault injection)", async ({ page }, info) => {
    await page.route("**/health", (r) => r.abort("connectionrefused"));
    await page.goto("/");
    await page.waitForTimeout(3000);
    const text = await bodyText(page);
    await shot(page, info, "G-errors-usability", "G06_api-offline-indicator", { fullPage: false });
    note(info, `header status: ${text.match(/API (online|offline|checking)[^\n]*/i)?.[0]}`);
    await expect(page.getByText(/API offline/i)).toBeVisible();
  });

  test("G07 invalid timetable upload is rejected with an error", async ({ page }, info) => {
    await openApp(page);
    await page.locator('input[type="file"]').setInputFiles({ name: "bad.json", mimeType: "application/json", buffer: Buffer.from("{not json") });
    await page.waitForTimeout(1200);
    await shot(page, info, "G-errors-usability", "G07_invalid-timetable-upload", { fullPage: false });
    expect(await bodyText(page)).toMatch(/Timetable upload failed|invalid|error/i);
  });

  test("G08 production dashboard distinguishes simulation from operational safety", async ({ page }, info) => {
    await openApp(page);
    await generateSchedule(page);
    const text = await bodyText(page);
    const production = text.slice(text.indexOf("Corridor\n"));
    await shot(page, info, "G-errors-usability", "G08_production-area-disclaimer-check", { fullPage: true });
    note(info, `production-area text has a non-operational/simulation disclaimer: ${/not operational|simulation|synthetic|not a safety|not.*authori[sz]ed/i.test(production)}`);
    expect(production, "production scheduling area needs a simulation/not-operational disclaimer").toMatch(
      /not operational|simulation|synthetic|not a safety|not.*authori[sz]ed/i,
    );
  });

  test("G09 no misleading success indicator before any schedule has been generated", async ({ page }, info) => {
    await openApp(page);
    const text = await bodyText(page);
    const before = text.slice(text.indexOf("Search Space Pruned"), text.indexOf("Time-Space Schedule"));
    await shot(page, info, "G-errors-usability", "G09_metrics-before-first-run", { fullPage: false });
    note(info, `metrics block before run: ${before.replace(/\n+/g, " | ")}`);
    expect(before, "co-location result pill is shown although nothing has been scheduled").not.toMatch(/\d+ Parallel Maintenance Requests Bundled/);
  });

  test("G10 accessibility basics: unnamed controls and heading structure", async ({ page }, info) => {
    await openApp(page);
    const issues = await page.evaluate(() => {
      const unnamed = Array.from(document.querySelectorAll("button, a, input, select")).filter((e) => {
        const el = e as HTMLInputElement;
        if (el.closest("nextjs-portal")) return false;
        const name = (e.getAttribute("aria-label") ?? "") + (e.textContent ?? "").trim() + (el.labels?.length ? "x" : "") + (e.getAttribute("title") ?? "");
        return !name.trim() && el.type !== "hidden";
      }).map((e) => e.outerHTML.slice(0, 120));
      const h = Array.from(document.querySelectorAll("h1,h2,h3")).map((x) => x.tagName);
      return { unnamed, headings: h, lang: document.documentElement.lang };
    });
    note(info, `unnamed controls=${issues.unnamed.length}; headings=${issues.headings.join(",")}; html lang="${issues.lang}"`);
    expect.soft(issues.unnamed, "controls without accessible names").toEqual([]);
    expect.soft(issues.headings.filter((h) => h === "H1").length, "exactly one H1").toBe(1);
  });
});

// ───────────────────────── H. Responsive layout ─────────────────────────
const VIEWPORTS = [
  { id: "H01", name: "desktop-1920x1080", w: 1920, h: 1080 },
  { id: "H02", name: "laptop-1366x768", w: 1366, h: 768 },
  { id: "H03", name: "tablet-768x1024", w: 768, h: 1024 },
  { id: "H04", name: "mobile-390x844", w: 390, h: 844 },
];
test.describe("H. Responsive layout", () => {
  for (const vp of VIEWPORTS) {
    test(`${vp.id} layout at ${vp.w}x${vp.h}`, async ({ page }, info) => {
      await page.setViewportSize({ width: vp.w, height: vp.h });
      await openApp(page);
      await shot(page, info, "H-responsive", `${vp.id}_${vp.name}_initial`);
      await buildScenarioWithOrders(page);
      await runComparison(page);
      await generateSchedule(page);
      await page.waitForTimeout(500);
      await shot(page, info, "H-responsive", `${vp.id}_${vp.name}_with-results_full`);
      await shot(page, info, "H-responsive", `${vp.id}_${vp.name}_viewport`, { fullPage: false });
      const m = await page.evaluate(() => {
        const winW = window.innerWidth;
        const scrollableAncestor = (e: Element) => {
          for (let p = e.parentElement; p; p = p.parentElement) {
            const cs = getComputedStyle(p);
            if (p.getAttribute("aria-hidden") === "true") return true; // off-canvas drawer is intentionally hidden
            if (/(auto|scroll)/.test(cs.overflowX) && p.scrollWidth > p.clientWidth) return true;
          }
          return false;
        };
        const clipped = Array.from(document.querySelectorAll("button, input, select, a"))
          .filter((e) => {
            const r = e.getBoundingClientRect();
            return r.width > 0 && (r.right > winW + 1 || r.left < -1) && !scrollableAncestor(e);
          })
          .map((e) => (e.textContent || (e as HTMLInputElement).placeholder || e.tagName).trim().slice(0, 40));
        const tiny = Array.from(document.querySelectorAll("body *"))
          .filter((e) => e.children.length === 0 && (e.textContent ?? "").trim() && parseFloat(getComputedStyle(e).fontSize) < 10)
          .length;
        return { docW: document.documentElement.scrollWidth, winW, clipped, tiny };
      });
      note(info, `docScrollWidth=${m.docW}/${m.winW}; clipped controls=${JSON.stringify(m.clipped)}; text nodes <10px=${m.tiny}`);
      expect.soft(m.docW, "horizontal page overflow").toBeLessThanOrEqual(m.winW + 1);
      expect.soft(m.clipped, "controls clipped outside viewport").toEqual([]);
      expect.soft(m.tiny, "text rendered below 10px").toBe(0);
    });
  }
});
