# Prototype UI audit (Playwright)

Contents: `PLAYWRIGHT_TEST_REPORT.md` (narrative + per-test tables), `PLAYWRIGHT_TEST_RESULTS.json` (machine-readable), `screenshots/` (by category), `playwright-report/` (HTML report with traces), `tests/` (suite), `build-results.mjs` (JSON/report builder), `raw-results.json` and `run.log` (raw run output).

## Open the HTML report
```
cd artifacts/prototype-audit
npx playwright show-report playwright-report
```
Traces: `npx playwright show-trace test-results/<test>/trace.zip`.

## View screenshots
Open `screenshots/<A-initial|B-scheduling|C-scenarios|D-comparison|E-gantt|F-export|G-errors-usability|H-responsive>/`. Filenames start with the test ID.

## Re-run
Frontend (http://localhost:3000) and backend (http://localhost:8000) must already be running.
```
cd artifacts/prototype-audit
npm install && npx playwright install chromium   # first time only
rm -rf screenshots playwright-report test-results raw-results.json
npx playwright test
node build-results.mjs     # regenerates results JSON and report
```
(Takes ~7 minutes.) `build-results.mjs` embeds `report-narrative.md`, which is hand-written.

## Interpreting results
- **PASS** – assertions held. **FAIL** – a real prototype defect (tests assert desired behaviour; failures reproduced on retry). **BLOCKED** – needed functionality unavailable (none this run). **SKIPPED** – not run. **FLAKY** – passed only on retry (none this run).
- Tests D07–D09 and G04–G06 use injected faults via `page.route`.
- Results describe UI behaviour of a simulation prototype, not railway operational safety.
