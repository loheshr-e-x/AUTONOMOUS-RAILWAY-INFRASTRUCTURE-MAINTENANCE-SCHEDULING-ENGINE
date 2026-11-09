import { test as base, expect, type Page, type TestInfo } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

export const AUDIT_ROOT = path.resolve(__dirname, "..");
export const SHOT_ROOT = path.join(AUDIT_ROOT, "screenshots");
export const API = process.env.AUDIT_API_URL ?? "http://localhost:8000";

export type Diagnostics = {
  consoleErrors: string[];
  pageErrors: string[];
  failedRequests: string[];
  httpErrors: string[];
};

// Every test gets a fresh browser context (empty localStorage), so no pre-existing user data is touched.
export const test = base.extend<{ diag: Diagnostics }>({
  diag: [
    async ({ page }, use, testInfo) => {
      const d: Diagnostics = { consoleErrors: [], pageErrors: [], failedRequests: [], httpErrors: [] };
      page.on("console", (m) => {
        if (m.type() === "error") d.consoleErrors.push(m.text().slice(0, 400));
      });
      page.on("pageerror", (e) => d.pageErrors.push(String(e).slice(0, 400)));
      page.on("requestfailed", (r) =>
        d.failedRequests.push(`${r.method()} ${r.url()} :: ${r.failure()?.errorText ?? "failed"}`),
      );
      page.on("response", (r) => {
        if (r.status() >= 400) d.httpErrors.push(`${r.status()} ${r.request().method()} ${r.url()}`);
      });
      await use(d);
      testInfo.annotations.push({ type: "diagnostics", description: JSON.stringify(d) });
    },
    { auto: true },
  ],
});
export { expect };

export function note(info: TestInfo, text: string) {
  info.annotations.push({ type: "observation", description: text });
}

export function blocked(info: TestInfo, reason: string): never {
  info.annotations.push({ type: "BLOCKED", description: reason });
  test.skip(true, `BLOCKED: ${reason}`);
  throw new Error("unreachable");
}

export async function shot(
  page: Page,
  info: TestInfo,
  category: string,
  name: string,
  opts: { fullPage?: boolean; locator?: ReturnType<Page["locator"]> } = {},
) {
  const dir = path.join(SHOT_ROOT, category);
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `${name}.png`);
  await page.waitForTimeout(400); // let transitions settle before capture
  if (opts.locator) await opts.locator.screenshot({ path: file });
  else await page.screenshot({ path: file, fullPage: opts.fullPage ?? true });
  info.annotations.push({ type: "screenshot", description: path.relative(AUDIT_ROOT, file) });
}

export async function bodyText(page: Page) {
  return page.locator("body").innerText();
}

export async function openApp(page: Page) {
  await page.goto("/");
  await expect(page.getByText("API online")).toBeVisible({ timeout: 20_000 });
}

export function creationSections(page: Page) {
  return page.getByRole("group", { name: "Scenario sections" }).first();
}
export function editSections(page: Page) {
  return page.getByRole("group", { name: "Scenario sections" }).nth(1);
}

export async function createScenario(page: Page, name: string, sections: string[]) {
  await page.getByPlaceholder("My maintenance scenario").fill(name);
  for (const s of sections) await creationSections(page).getByLabel(s).check();
  await page.getByRole("button", { name: "Create", exact: true }).click();
  await expect(page.getByRole("combobox", { name: "Scenario", exact: true })).toContainText(name);
}

export type WO = { id: string; section: string; line: "UP_LINE" | "DOWN_LINE"; dept: number; coloc?: boolean };

export async function addWorkOrders(page: Page, orders: WO[]) {
  await page.getByRole("button", { name: /Manage work orders/ }).click();
  const dlg = page.locator("aside").filter({ hasText: "Work Order Manager" });
  for (const o of orders) {
    await dlg.getByRole("button", { name: "New" }).click();
    await dlg.getByLabel("Work order ID").fill(o.id);
    await dlg.getByLabel("Defect").fill("audit defect");
    await dlg.getByLabel("Department").selectOption({ index: o.dept });
    await dlg.getByLabel("Section").selectOption(o.section);
    await dlg.getByLabel("Track line").selectOption(o.line);
    const co = dlg.getByLabel("Co-location allowed");
    if (o.coloc === false) await co.uncheck();
    await dlg.getByRole("button", { name: "Save" }).click();
    await expect(dlg).toContainText(o.id);
  }
  await dlg.getByRole("button", { name: "Close" }).click();
}

export const BASIC_ORDERS: WO[] = [
  { id: "AUD-1", section: "NDLS_CNB_SEC1", line: "UP_LINE", dept: 1 },
  { id: "AUD-2", section: "NDLS_CNB_SEC1", line: "UP_LINE", dept: 0 },
  { id: "AUD-3", section: "NDLS_CNB_SEC2", line: "DOWN_LINE", dept: 2 },
];

export async function buildScenarioWithOrders(page: Page, name = "Audit scenario", orders = BASIC_ORDERS) {
  await createScenario(page, name, ["NDLS_CNB_SEC1", "NDLS_CNB_SEC2"]);
  await addWorkOrders(page, orders);
}

export async function runComparison(page: Page) {
  const [resp] = await Promise.all([
    page.waitForResponse((r) => r.url().includes("/api/experimental/scenarios/compare"), { timeout: 60_000 }),
    page.getByRole("button", { name: "Run comparison" }).click(),
  ]);
  return resp;
}

export async function generateSchedule(page: Page) {
  const [resp] = await Promise.all([
    page.waitForResponse((r) => r.url().includes("/api/schedule/generate") && r.request().method() === "POST", {
      timeout: 90_000,
    }),
    page.getByRole("button", { name: "Generate Schedule" }).click(),
  ]);
  const req = resp.request().postData() ?? "";
  const json = await resp.json().catch(() => null);
  return { resp, req, json };
}

export const woBars = (page: Page) => page.getByRole("button", { name: /^(ENG|SIG|TRC)\s*WO-/ });

export async function readDownload(page: Page, buttonName: string) {
  const [dl] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: buttonName }).click()]);
  const p = await dl.path();
  return { filename: dl.suggestedFilename(), content: fs.readFileSync(p!, "utf8") };
}
