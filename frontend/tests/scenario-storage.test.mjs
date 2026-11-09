import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import {
  SCENARIO_STORAGE_KEY,
  SCENARIO_STORAGE_VERSION,
  ScenarioStorageError,
  createScenario,
  deleteScenario,
  duplicateScenario,
  loadScenarios,
  parseScenario,
  scenarioWorkOrderDurationError,
  saveScenarios,
  updateScenario,
} from "../lib/scenario-storage.ts";

const workOrderManagerSource = readFileSync(
  new URL("../components/WorkOrderManager.tsx", import.meta.url),
  "utf8",
);

class MemoryStorage {
  values = new Map();

  getItem(key) {
    return this.values.get(key) ?? null;
  }

  setItem(key, value) {
    this.values.set(key, value);
  }
}

function populatedScenario(id, name) {
  const scenario = createScenario(name, ["S1"], id);
  return parseScenario({
    ...scenario,
    work_orders: [{
      work_id: `WO-${id}`,
      department: "ENGINEERING",
      section_id: "S1",
      track_line: "UP_LINE",
      heavy_equipment: false,
      defect_type: "Inspection",
      duration_hrs: 1.5,
      urgency: 2,
      co_location_allowed: true,
    }],
    train_windows: [{
      train_no: "T1",
      section_id: "S1",
      track_line: "DOWN_LINE",
      start_time_hr: 8,
      end_time_hr: 8.5,
    }],
  });
}

test("create, save, and reload preserve a typed scenario", () => {
  const storage = new MemoryStorage();
  const scenario = populatedScenario("scenario-a", "Scenario A");

  saveScenarios([scenario], storage);

  assert.deepEqual(loadScenarios(storage), [scenario]);
  assert.equal(
    JSON.parse(storage.getItem(SCENARIO_STORAGE_KEY) ?? "null").schema_version,
    SCENARIO_STORAGE_VERSION,
  );
});

test("editing one scenario and duplicating it do not mutate sibling scenarios", () => {
  const first = populatedScenario("scenario-a", "Scenario A");
  first.input_digest = "a".repeat(64);
  const sibling = populatedScenario("scenario-b", "Scenario B");
  const duplicate = duplicateScenario(first, "Scenario A copy", "scenario-copy");
  const scenarios = [first, sibling, duplicate];
  const edited = updateScenario(scenarios, first.scenario_id, (scenario) => ({
    ...scenario,
    scenario_name: "Edited A",
    work_orders: scenario.work_orders.map((order) => ({
      ...order,
      duration_hrs: 3,
    })),
    solver_configuration: {
      ...scenario.solver_configuration,
      section_ids: ["S1", "S2"],
    },
  }));

  assert.equal(edited[0].scenario_name, "Edited A");
  assert.equal(edited[0].work_orders[0].duration_hrs, 3);
  assert.deepEqual(edited[0].solver_configuration.section_ids, ["S1", "S2"]);
  assert.equal(edited[1].work_orders[0].duration_hrs, 1.5);
  assert.equal(edited[2].work_orders[0].duration_hrs, 1.5);
  assert.notEqual(duplicate.work_orders, first.work_orders);
  assert.notEqual(duplicate.work_orders[0], first.work_orders[0]);
  assert.equal(duplicate.input_digest, first.input_digest);
  assert.equal(first.scenario_name, "Scenario A");

  const storage = new MemoryStorage();
  saveScenarios(edited, storage);
  assert.deepEqual(loadScenarios(storage), edited);
});

test("deleting a scenario leaves the remaining scenarios unchanged", () => {
  const first = populatedScenario("scenario-a", "Scenario A");
  const second = populatedScenario("scenario-b", "Scenario B");
  const storage = new MemoryStorage();

  const remaining = deleteScenario([first, second], first.scenario_id);
  saveScenarios(remaining, storage);
  assert.deepEqual(remaining, [second]);
  assert.deepEqual(loadScenarios(storage), [second]);
});

test("malformed JSON is reported and the stored bytes are preserved", () => {
  const storage = new MemoryStorage();
  storage.values.set(SCENARIO_STORAGE_KEY, "{not-json");

  assert.throws(
    () => loadScenarios(storage),
    (error) => error instanceof ScenarioStorageError && error.code === "INVALID_JSON",
  );
  assert.equal(storage.getItem(SCENARIO_STORAGE_KEY), "{not-json");
});

test("saving cannot overwrite data that became unreadable after load", () => {
  const storage = new MemoryStorage();
  const raw = "{corrupt after loading";
  storage.values.set(SCENARIO_STORAGE_KEY, raw);

  assert.throws(
    () => saveScenarios([createScenario("New", ["S1"], "new-scenario")], storage),
    (error) => error instanceof ScenarioStorageError && error.code === "INVALID_JSON",
  );
  assert.equal(storage.getItem(SCENARIO_STORAGE_KEY), raw);
});

test("unsupported schema versions are reported without overwriting stored data", () => {
  const storage = new MemoryStorage();
  const raw = JSON.stringify({ schema_version: 999, scenarios: [] });
  storage.values.set(SCENARIO_STORAGE_KEY, raw);

  assert.throws(
    () => loadScenarios(storage),
    (error) => error instanceof ScenarioStorageError && error.code === "UNSUPPORTED_VERSION",
  );
  assert.equal(storage.getItem(SCENARIO_STORAGE_KEY), raw);
});

test("incompatible scenario data is reported without being replaced", () => {
  const storage = new MemoryStorage();
  const raw = JSON.stringify({ schema_version: SCENARIO_STORAGE_VERSION, scenarios: [{ scenario_id: "old" }] });
  storage.values.set(SCENARIO_STORAGE_KEY, raw);

  assert.throws(
    () => loadScenarios(storage),
    (error) => error instanceof ScenarioStorageError && error.code === "INVALID_STORED_DATA",
  );
  assert.equal(storage.getItem(SCENARIO_STORAGE_KEY), raw);
});

test("unavailable browser storage and failed writes are explicit", () => {
  const inaccessibleStorage = {
    getItem: () => { throw new Error("blocked"); },
    setItem: () => { throw new Error("quota"); },
  };

  assert.throws(
    () => loadScenarios(inaccessibleStorage),
    (error) => error instanceof ScenarioStorageError && error.code === "STORAGE_UNAVAILABLE",
  );
  assert.throws(
    () => saveScenarios([createScenario("Scenario", ["S1"], "scenario-a")], inaccessibleStorage),
    (error) => error instanceof ScenarioStorageError && error.code === "SAVE_FAILED",
  );
});

test("browser storage absence is surfaced rather than treated as an empty scenario list", () => {
  assert.throws(
    () => loadScenarios(),
    (error) => error instanceof ScenarioStorageError && error.code === "STORAGE_UNAVAILABLE",
  );
});

test("scenario parsing rejects malformed contract fields", () => {
  const scenario = populatedScenario("scenario-a", "Scenario A");

  assert.throws(() => parseScenario({ ...scenario, extra: true }), /not supported/);
  assert.throws(() => parseScenario({
    ...scenario,
    solver_configuration: { ...scenario.solver_configuration, slot_duration_hrs: 0 },
  }), /slot_duration_hrs/);
  assert.throws(() => parseScenario({
    ...scenario,
    work_orders: scenario.work_orders.map((order) => ({ ...order, duration_hrs: 1.0001 })),
  }), /precision 1\/1000/);
  assert.throws(() => parseScenario({
    ...scenario,
    work_orders: scenario.work_orders.map((order) => ({ ...order, section_id: "OTHER" })),
  }), /selected scenario section/);
});

test("production work-order controls preserve their original options and labels", () => {
  assert.match(workOrderManagerSource, /PRODUCTION_DURATIONS = \[0\.5, 1, 1\.5, 2, 3, 4\]/);
  assert.match(workOrderManagerSource, /1 – Low/);
  assert.match(workOrderManagerSource, /2 – Medium/);
  assert.match(workOrderManagerSource, /3 – High/);
  assert.match(workOrderManagerSource, /mode === "scenario" \? \([\s\S]*?type="number"[\s\S]*?: \([\s\S]*?<select/);
});

test("scenario work-order duration accepts valid precision and rejects invalid values", () => {
  assert.equal(scenarioWorkOrderDurationError(1.25), null);
  assert.match(scenarioWorkOrderDurationError(8.001), /no more than 8 hours/);
  assert.match(scenarioWorkOrderDurationError(1.0001), /precision cannot exceed 0\.001/);
});

test("work-order editor delegates changes to its caller without production API operations", () => {
  assert.match(workOrderManagerSource, /onChange\(isNew \?/);
  assert.match(workOrderManagerSource, /mode === "production" &&/);
  assert.doesNotMatch(
    workOrderManagerSource,
    /setCustomWorkOrders|clearCustomWorkOrders|generateSchedule/,
  );
});
