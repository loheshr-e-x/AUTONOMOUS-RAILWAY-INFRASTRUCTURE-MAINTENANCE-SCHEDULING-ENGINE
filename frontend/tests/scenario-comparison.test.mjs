import assert from "node:assert/strict";
import { test } from "node:test";
import {
  API_BASE,
  compareScenarios,
  createScenarioComparisonRequest,
  ScenarioComparisonError,
} from "../lib/api.ts";
import { createScenario } from "../lib/scenario-storage.ts";
import {
  compareSchedulePlacements,
  formatComparisonClock,
} from "../lib/scenario-diff.ts";
import {
  beginComparisonRequest,
  createComparisonRequestTracker,
  finishComparisonRequest,
  invalidateComparisonRequests,
  isCurrentComparisonRequest,
  isValidatedPairedComparison,
} from "../lib/scenario-comparison-state.ts";

function populatedScenario() {
  const scenario = createScenario("Research scenario", ["S1"], "scenario-a");
  scenario.input_digest = "stale-digest";
  scenario.work_orders = [{
    work_id: "SIM-WO-1",
    department: "ENGINEERING",
    section_id: "S1",
    track_line: "UP_LINE",
    heavy_equipment: false,
    defect_type: "Inspection",
    duration_hrs: 1.5,
    urgency: 2,
    co_location_allowed: true,
  }];
  scenario.train_windows = [{
    train_no: "SIM-TRAIN-1",
    section_id: "S1",
    track_line: "UP_LINE",
    start_time_hr: 3,
    end_time_hr: 4,
  }];
  return scenario;
}

function assignment(workId, start, end = start + 1) {
  return {
    work_id: workId,
    department: "ENGINEERING",
    section_id: "S1",
    track_line: "UP_LINE",
    start_time_hr: start,
    end_time_hr: end,
    co_located_with: [],
    heavy_equipment: false,
  };
}

function solverRun(solver, inputDigest) {
  const scheduledAssignment = assignment("SIM-WO-1", 1, 2);
  return {
    solver,
    run_status: "completed",
    input_digest: inputDigest,
    error_code: null,
    error_message: null,
    total_work_orders: 1,
    scheduled_work_ids: ["SIM-WO-1"],
    unscheduled_work_ids: [],
    schedule: [scheduledAssignment],
    validation: { valid: true, findings: [] },
    unscheduled_reasons: [],
  };
}

function pairedResult() {
  const inputDigest = "a".repeat(64);
  return {
    scenario_id: "scenario-a",
    model_version: "symbio-block-task16-simulation-v1",
    input_digest: inputDigest,
    comparison_status: "completed",
    paired_inputs_match: true,
    baseline: solverRun("baseline", inputDigest),
    cp_sat: solverRun("cp_sat", inputDigest),
  };
}

test("comparison request copies scenario contract data without saved digest", () => {
  const scenario = populatedScenario();
  const request = createScenarioComparisonRequest(scenario);

  assert.equal(request.scenario_id, scenario.scenario_id);
  assert.equal(request.scenario_name, scenario.scenario_name);
  assert.deepEqual(request.work_orders, scenario.work_orders);
  assert.deepEqual(request.train_windows, scenario.train_windows);
  assert.deepEqual(request.solver_configuration, scenario.solver_configuration);
  assert.equal("input_digest" in request, false);

  request.work_orders[0].duration_hrs = 2.25;
  request.train_windows[0].start_time_hr = 5;
  request.solver_configuration.section_ids.push("S2");
  assert.equal(scenario.work_orders[0].duration_hrs, 1.5);
  assert.equal(scenario.train_windows[0].start_time_hr, 3);
  assert.deepEqual(scenario.solver_configuration.section_ids, ["S1"]);
});

test("schedule differences classify shared, changed, solver-only, and both-unscheduled work", () => {
  const differences = compareSchedulePlacements(
    ["same", "changed", "baseline", "cp-sat", "neither"],
    [assignment("same", 1), assignment("changed", 2), assignment("baseline", 3)],
    [assignment("same", 1), assignment("changed", 4), assignment("cp-sat", 5)],
  );

  assert.deepEqual(differences.map(({ workId, kind }) => [workId, kind]), [
    ["same", "same_placement"],
    ["changed", "placement_changed"],
    ["baseline", "baseline_only"],
    ["cp-sat", "cp_sat_only"],
    ["neither", "unscheduled_both"],
  ]);
});

test("comparison timeline formats the horizon boundary without wrapping midnight", () => {
  assert.equal(formatComparisonClock(1.75), "01:45");
  assert.equal(formatComparisonClock(23.5), "23:30");
  assert.equal(formatComparisonClock(24), "24:00");
});

test("experimental comparison submits the request to its dedicated endpoint", async () => {
  const originalFetch = globalThis.fetch;
  let observed;
  const payload = { comparison_status: "incomplete", paired_inputs_match: true };
  globalThis.fetch = async (url, init) => {
    observed = { url, init };
    return new Response(JSON.stringify(payload), { status: 200 });
  };

  try {
    const body = createScenarioComparisonRequest(populatedScenario());
    const response = await compareScenarios(body);
    assert.equal(observed.url, `${API_BASE}/api/experimental/scenarios/compare`);
    assert.equal(observed.init.method, "POST");
    assert.deepEqual(JSON.parse(observed.init.body), body);
    assert.deepEqual(response, payload);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("validation and unavailable API errors retain explicit states", async () => {
  const originalFetch = globalThis.fetch;
  const body = createScenarioComparisonRequest(populatedScenario());
  const cases = [
    { status: 422, kind: "validation", detail: [{ code: "BAD_SCENARIO", message: "Invalid input" }] },
    { status: 503, kind: "unavailable", detail: "CP-SAT unavailable" },
  ];

  try {
    for (const item of cases) {
      globalThis.fetch = async () => new Response(
        JSON.stringify({ detail: item.detail }),
        { status: item.status, statusText: "Request failed" },
      );
      await assert.rejects(compareScenarios(body), (error) => {
        assert.ok(error instanceof ScenarioComparisonError);
        assert.equal(error.kind, item.kind);
        assert.match(error.message, item.status === 422 ? /BAD_SCENARIO/ : /CP-SAT unavailable/);
        return true;
      });
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("paired display gate requires matching scenario, digest, validation, and accounting", () => {
  const result = pairedResult();
  const expected = {
    scenarioId: "scenario-a",
    modelVersion: result.model_version,
    inputDigest: result.input_digest,
    workOrderIds: ["SIM-WO-1"],
  };

  assert.equal(isValidatedPairedComparison(result, expected), true);

  assert.equal(
    isValidatedPairedComparison(
      { ...result, baseline: { ...result.baseline, input_digest: "b".repeat(64) } },
      expected,
    ),
    false,
  );
  assert.equal(
    isValidatedPairedComparison(
      { ...result, cp_sat: { ...result.cp_sat, validation: { valid: true, findings: [{ code: "X" }] } } },
      expected,
    ),
    false,
  );
  assert.equal(
    isValidatedPairedComparison(
      { ...result, scenario_id: "different-scenario" },
      expected,
    ),
    false,
  );
  assert.equal(
    isValidatedPairedComparison(
      { ...result, baseline: { ...result.baseline, unscheduled_work_ids: ["SIM-WO-1"] } },
      expected,
    ),
    false,
  );
});

test("stale comparison generations cannot publish or finish a newer request", () => {
  const tracker = createComparisonRequestTracker();
  const firstRequest = beginComparisonRequest(tracker);

  assert.equal(beginComparisonRequest(tracker), null);
  invalidateComparisonRequests(tracker);
  const secondRequest = beginComparisonRequest(tracker);

  assert.ok(firstRequest !== null);
  assert.ok(secondRequest !== null);
  assert.equal(isCurrentComparisonRequest(tracker, firstRequest), false);
  assert.equal(finishComparisonRequest(tracker, firstRequest), false);
  assert.equal(tracker.inFlight, true);
  assert.equal(isCurrentComparisonRequest(tracker, secondRequest), true);
  assert.equal(finishComparisonRequest(tracker, secondRequest), true);
  assert.equal(tracker.inFlight, false);
});
