// Converts Playwright's raw JSON into PLAYWRIGHT_TEST_RESULTS.json and assembles PLAYWRIGHT_TEST_REPORT.md
// (generated tables + hand-written report-narrative.md). Pure post-processing: it never alters test outcomes.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const raw = JSON.parse(fs.readFileSync(path.join(root, "raw-results.json"), "utf8"));
const clean = (s) => String(s ?? "").replace(/\x1b\[[0-9;]*m/g, "");

const CATEGORY = {
  A: "A. Initial application experience",
  B: "B. Maintenance scheduling workflow",
  C: "C. Scenario management",
  D: "D. Scenario comparison",
  E: "E. Gantt chart and visualisation",
  F: "F. Export functionality",
  G: "G. Error handling and usability",
  H: "H. Responsive layout",
};

const results = [];
(function walk(suite) {
  for (const spec of suite.specs ?? []) {
    for (const t of spec.tests) {
      const attempts = t.results;
      const last = attempts[attempts.length - 1];
      const ann = [...(last.annotations ?? []), ...(t.annotations ?? [])];
      const of = (type) => ann.filter((a) => a.type === type).map((a) => a.description);
      const id = spec.title.match(/^([A-H]\d\d)/)?.[1] ?? spec.title;
      const blocked = of("BLOCKED");
      let status;
      let flaky = false;
      if (blocked.length) status = "BLOCKED";
      else if (t.status === "flaky") { status = "PASS"; flaky = true; }
      else if (t.status === "expected") status = "PASS";
      else if (t.status === "skipped") status = "SKIPPED";
      else status = "FAIL";
      const diag = JSON.parse(of("diagnostics")[0] ?? "{}");
      const errors = (last.errors ?? []).map((e) => clean(e.message).split("\n").filter((l) => l.trim()).slice(0, 6).join(" / ").slice(0, 600));
      results.push({
        test_id: id,
        test_name: spec.title.replace(/^[A-H]\d\d\s*/, ""),
        category: CATEGORY[id[0]] ?? "Other",
        status,
        flaky,
        attempts: attempts.length,
        duration_ms: attempts.reduce((a, r) => a + r.duration, 0),
        failure_reason: status === "FAIL" ? errors[0] ?? "unknown" : status === "BLOCKED" ? blocked[0] : null,
        screenshots: [...new Set(of("screenshot"))],
        observations: of("observation"),
        error_details: { assertion_errors: errors, ...diag },
      });
    }
  }
  for (const s of suite.suites ?? []) walk(s);
})(raw.suites[0]);

results.sort((a, b) => a.test_id.localeCompare(b.test_id));
const count = (s) => results.filter((r) => r.status === s).length;
const summary = {
  total: results.length,
  passed: count("PASS"),
  failed: count("FAIL"),
  blocked: count("BLOCKED"),
  skipped: count("SKIPPED"),
  flaky: results.filter((r) => r.flaky).length,
};
const meta = {
  audit_started: raw.stats.startTime,
  total_duration_ms: Math.round(raw.stats.duration),
  playwright_version: raw.config?.version ?? null,
  browser: "Chromium (Playwright headless shell)",
  frontend_url: "http://localhost:3000",
  backend_url: "http://localhost:8000",
  retries_configured: 1,
};
fs.writeFileSync(path.join(root, "PLAYWRIGHT_TEST_RESULTS.json"), JSON.stringify({ meta, summary, results }, null, 2));

const icon = { PASS: "PASS", FAIL: "FAIL", BLOCKED: "BLOCKED", SKIPPED: "SKIPPED" };
const esc = (s) => String(s ?? "").replace(/\|/g, "\\|").replace(/\n/g, " ");
let md = "";
md += "## 4. Test results (generated from `PLAYWRIGHT_TEST_RESULTS.json`)\n\n";
md += `Total **${summary.total}** · PASS **${summary.passed}** · FAIL **${summary.failed}** · BLOCKED **${summary.blocked}** · SKIPPED **${summary.skipped}** · FLAKY (passed only on retry) **${summary.flaky}**\n\n`;
for (const cat of Object.values(CATEGORY)) {
  const rs = results.filter((r) => r.category === cat);
  md += `### ${cat}\n\n| ID | Test | Status | Time | Observation / failure | Screenshots |\n|---|---|---|---|---|---|\n`;
  for (const r of rs) {
    const detail = r.status === "FAIL" ? r.failure_reason : r.status === "BLOCKED" ? r.failure_reason : r.observations.join(" ; ");
    const shots = r.screenshots.map((p) => `[${path.basename(p)}](${p})`).join("<br>");
    md += `| ${r.test_id} | ${esc(r.test_name)} | **${icon[r.status]}**${r.flaky ? " (flaky)" : ""} | ${(r.duration_ms / 1000).toFixed(1)}s | ${esc(detail).slice(0, 420)} | ${shots} |\n`;
  }
  md += "\n";
}
md += "### Browser diagnostics (console errors / failed requests)\n\n";
const withDiag = results.filter((r) => ["consoleErrors", "pageErrors", "failedRequests", "httpErrors"].some((k) => r.error_details[k]?.length));
if (!withDiag.length) md += "No console errors, page errors, failed requests or HTTP >= 400 responses were recorded in any test.\n\n";
else {
  md += "| ID | Console errors | Page errors | Failed requests | HTTP >= 400 |\n|---|---|---|---|---|\n";
  for (const r of withDiag) {
    const d = r.error_details;
    md += `| ${r.test_id} | ${d.consoleErrors?.length ?? 0} | ${d.pageErrors?.length ?? 0} | ${d.failedRequests?.length ?? 0} | ${d.httpErrors?.length ?? 0} |\n`;
  }
  md += "\nMost of these were provoked deliberately by the fault-injection tests (D07-D09, G04-G06); details are in the JSON file.\n\n";
}

const narrative = fs.existsSync(path.join(root, "report-narrative.md")) ? fs.readFileSync(path.join(root, "report-narrative.md"), "utf8") : "";
const [head, tail = ""] = narrative.split("<!--GENERATED-RESULTS-->");
fs.writeFileSync(path.join(root, "PLAYWRIGHT_TEST_REPORT.md"), `${head}${md}${tail}`);
console.log(JSON.stringify(summary), "->", "PLAYWRIGHT_TEST_RESULTS.json, PLAYWRIGHT_TEST_REPORT.md");
