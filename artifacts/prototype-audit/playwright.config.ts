import { defineConfig, devices } from "@playwright/test";

// Audit-only configuration. Targets an already-running frontend (:3000) and backend (:8000).
export default defineConfig({
  testDir: "./tests",
  outputDir: "./test-results",
  timeout: 120_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 1, // a pass-on-retry is reported as FLAKY, never as a clean PASS
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["json", { outputFile: "raw-results.json" }],
  ],
  use: {
    baseURL: process.env.AUDIT_BASE_URL ?? "http://localhost:3000",
    trace: "on",
    screenshot: "only-on-failure",
    acceptDownloads: true,
    ...devices["Desktop Chrome"],
    viewport: { width: 1366, height: 768 },
  },
  projects: [{ name: "chromium" }],
});
