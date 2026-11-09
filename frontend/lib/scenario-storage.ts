import type {
  Department,
  MaintenanceWorkOrder,
  ScenarioComparisonRequest,
  ScenarioSolverConfiguration,
  TrackLine,
  TrainOccupancyWindow,
  UrgencyLevel,
} from "./types";

export const SCENARIO_STORAGE_KEY = "symbio-block.scenarios";
export const SCENARIO_STORAGE_VERSION = 1;
export const SCENARIO_MODEL_VERSION = "symbio-block-task16-simulation-v1";

export type ScenarioRecord = ScenarioComparisonRequest & { scenario_name: string };

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export type ScenarioStorageErrorCode =
  | "STORAGE_UNAVAILABLE"
  | "INVALID_JSON"
  | "UNSUPPORTED_VERSION"
  | "INVALID_STORED_DATA"
  | "SAVE_FAILED";

export class ScenarioStorageError extends Error {
  public readonly code: ScenarioStorageErrorCode;

  constructor(
    code: ScenarioStorageErrorCode,
    message: string,
    options?: ErrorOptions,
  ) {
    super(message, options);
    this.code = code;
    this.name = "ScenarioStorageError";
  }
}

export function scenarioWorkOrderDurationError(duration: number): string | null {
  if (!Number.isFinite(duration) || duration <= 0 || duration > 8) {
    return "Duration must be greater than 0 and no more than 8 hours.";
  }
  if (!Number.isSafeInteger(duration * 1_000)) {
    return "Duration precision cannot exceed 0.001 hours.";
  }
  return null;
}

const departments: Department[] = ["ENGINEERING", "SIGNALLING", "TRACTION"];
const trackLines: TrackLine[] = ["UP_LINE", "DOWN_LINE"];
const urgencyLevels: UrgencyLevel[] = [1, 2, 3];

function browserStorage(): StorageLike {
  try {
    if (typeof window === "undefined" || !window.localStorage) {
      throw new Error("Browser storage is unavailable.");
    }
    return window.localStorage;
  } catch (error) {
    throw new ScenarioStorageError(
      "STORAGE_UNAVAILABLE",
      "Browser storage is unavailable; saved scenarios cannot be read or changed.",
      { cause: error },
    );
  }
}

function record(value: unknown, label: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${label} must be an object.`);
  }
  return value as Record<string, unknown>;
}

function exactKeys(
  value: Record<string, unknown>,
  required: string[],
  optional: string[],
  label: string,
): void {
  for (const key of required) {
    if (!(key in value)) throw new Error(`${label}.${key} is required.`);
  }
  const allowed = new Set([...required, ...optional]);
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) throw new Error(`${label}.${key} is not supported.`);
  }
}

function text(value: unknown, label: string, allowEmpty = false): string {
  if (
    typeof value !== "string" ||
    value !== value.trim() ||
    (!allowEmpty && value.length === 0)
  ) {
    throw new Error(`${label} must be a non-empty, trimmed string.`);
  }
  return value;
}

function finiteNumber(
  value: unknown,
  label: string,
  minimum: number,
  maximum = Number.POSITIVE_INFINITY,
): number {
  if (
    typeof value !== "number" ||
    !Number.isFinite(value) ||
    value < minimum ||
    value > maximum
  ) {
    throw new Error(`${label} must be a finite number from ${minimum} to ${maximum}.`);
  }
  return value;
}

function positiveFiniteNumber(
  value: unknown,
  label: string,
  maximum = Number.POSITIVE_INFINITY,
): number {
  const parsed = finiteNumber(value, label, 0, maximum);
  if (parsed === 0) throw new Error(`${label} must be greater than 0.`);
  return parsed;
}

function requirePrecision(value: number, label: string, scale: number): void {
  const scaled = value * scale;
  if (!Number.isSafeInteger(scaled)) {
    throw new Error(`${label} is not representable at precision 1/${scale}.`);
  }
}

function integer(
  value: unknown,
  label: string,
  minimum: number,
  maximum = Number.MAX_SAFE_INTEGER,
): number {
  if (
    typeof value !== "number" ||
    !Number.isSafeInteger(value) ||
    value < minimum ||
    value > maximum
  ) {
    throw new Error(`${label} must be an integer from ${minimum} to ${maximum}.`);
  }
  return value;
}

function boolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") throw new Error(`${label} must be a boolean.`);
  return value;
}

function enumValue<T extends string | number>(
  value: unknown,
  values: readonly T[],
  label: string,
): T {
  if (!values.includes(value as T)) throw new Error(`${label} is not supported.`);
  return value as T;
}

function parseWorkOrder(value: unknown, index: number): MaintenanceWorkOrder {
  const label = `work_orders[${index}]`;
  const item = record(value, label);
  exactKeys(
    item,
    [
      "work_id",
      "department",
      "section_id",
      "defect_type",
      "duration_hrs",
      "urgency",
      "co_location_allowed",
    ],
    ["track_line", "heavy_equipment"],
    label,
  );
  const duration = finiteNumber(item.duration_hrs, `${label}.duration_hrs`, 0, 8);
  if (duration === 0) throw new Error(`${label}.duration_hrs must be greater than 0.`);
  requirePrecision(duration, `${label}.duration_hrs`, 1_000);
  return {
    work_id: text(item.work_id, `${label}.work_id`),
    department: enumValue(item.department, departments, `${label}.department`),
    section_id: text(item.section_id, `${label}.section_id`),
    track_line: enumValue(item.track_line ?? "DOWN_LINE", trackLines, `${label}.track_line`),
    heavy_equipment: boolean(item.heavy_equipment ?? false, `${label}.heavy_equipment`),
    defect_type: text(item.defect_type, `${label}.defect_type`),
    duration_hrs: duration,
    urgency: enumValue(item.urgency, urgencyLevels, `${label}.urgency`),
    co_location_allowed: boolean(item.co_location_allowed, `${label}.co_location_allowed`),
  };
}

function parseTrainWindow(value: unknown, index: number): TrainOccupancyWindow {
  const label = `train_windows[${index}]`;
  const item = record(value, label);
  exactKeys(
    item,
    ["train_no", "section_id", "start_time_hr", "end_time_hr"],
    ["track_line"],
    label,
  );
  const start = finiteNumber(item.start_time_hr, `${label}.start_time_hr`, 0, 24);
  const end = finiteNumber(item.end_time_hr, `${label}.end_time_hr`, 0, 24);
  if (end <= start) throw new Error(`${label}.end_time_hr must be later than start_time_hr.`);
  requirePrecision(start, `${label}.start_time_hr`, 1_000_000);
  requirePrecision(end, `${label}.end_time_hr`, 1_000_000);
  return {
    train_no: text(item.train_no, `${label}.train_no`),
    section_id: text(item.section_id, `${label}.section_id`),
    track_line: enumValue(item.track_line ?? "DOWN_LINE", trackLines, `${label}.track_line`),
    start_time_hr: start,
    end_time_hr: end,
  };
}

const configurationKeys = [
  "section_ids",
  "time_horizon_hrs",
  "slot_duration_hrs",
  "train_clearance_hrs",
  "enable_ac3_pruning",
  "enable_simulated_annealing",
  "max_search_nodes",
  "annealing_iterations",
  "annealing_initial_temperature",
  "annealing_cooling_rate",
  "workload_balance_weight",
  "co_location_reward",
  "cpsat_time_limit_seconds",
  "random_seed",
];

function parseConfiguration(value: unknown): ScenarioSolverConfiguration {
  const config = record(value, "solver_configuration");
  exactKeys(config, configurationKeys, [], "solver_configuration");
  if (!Array.isArray(config.section_ids) || config.section_ids.length === 0) {
    throw new Error("solver_configuration.section_ids must contain at least one section.");
  }
  const sectionIds = config.section_ids.map((section, index) =>
    text(section, `solver_configuration.section_ids[${index}]`),
  );
  if (new Set(sectionIds).size !== sectionIds.length) {
    throw new Error("solver_configuration.section_ids must be unique.");
  }
  const timeHorizon = positiveFiniteNumber(config.time_horizon_hrs, "time_horizon_hrs", 24);
  const slotDuration = positiveFiniteNumber(config.slot_duration_hrs, "slot_duration_hrs");
  const trainClearance = finiteNumber(config.train_clearance_hrs, "train_clearance_hrs", 0);
  const workloadWeight = finiteNumber(
    config.workload_balance_weight,
    "workload_balance_weight",
    Number.NEGATIVE_INFINITY,
  );
  const coLocationReward = finiteNumber(
    config.co_location_reward,
    "co_location_reward",
    Number.NEGATIVE_INFINITY,
  );
  requirePrecision(timeHorizon, "time_horizon_hrs", 1_000_000);
  requirePrecision(slotDuration, "slot_duration_hrs", 1_000_000);
  requirePrecision(trainClearance, "train_clearance_hrs", 1_000_000);
  requirePrecision(workloadWeight, "workload_balance_weight", 1_000_000);
  requirePrecision(coLocationReward, "co_location_reward", 9_000_000_000_000);
  return {
    section_ids: sectionIds,
    time_horizon_hrs: timeHorizon,
    slot_duration_hrs: slotDuration,
    train_clearance_hrs: trainClearance,
    enable_ac3_pruning: boolean(config.enable_ac3_pruning, "enable_ac3_pruning"),
    enable_simulated_annealing: boolean(
      config.enable_simulated_annealing,
      "enable_simulated_annealing",
    ),
    max_search_nodes: integer(config.max_search_nodes, "max_search_nodes", 1),
    annealing_iterations: integer(config.annealing_iterations, "annealing_iterations", 0),
    annealing_initial_temperature: positiveFiniteNumber(
      config.annealing_initial_temperature,
      "annealing_initial_temperature",
    ),
    annealing_cooling_rate: positiveFiniteNumber(
      config.annealing_cooling_rate,
      "annealing_cooling_rate",
    ),
    workload_balance_weight: workloadWeight,
    co_location_reward: coLocationReward,
    cpsat_time_limit_seconds: positiveFiniteNumber(
      config.cpsat_time_limit_seconds,
      "cpsat_time_limit_seconds",
    ),
    random_seed: integer(
      config.random_seed,
      "random_seed",
      Number.MIN_SAFE_INTEGER,
      Number.MAX_SAFE_INTEGER,
    ),
  };
}

export function parseScenario(value: unknown): ScenarioRecord {
  const scenario = record(value, "scenario");
  exactKeys(
    scenario,
    [
      "scenario_id",
      "scenario_name",
      "model_version",
      "work_orders",
      "train_windows",
      "solver_configuration",
    ],
    ["input_digest"],
    "scenario",
  );
  if (!Array.isArray(scenario.work_orders)) throw new Error("work_orders must be an array.");
  if (!Array.isArray(scenario.train_windows)) throw new Error("train_windows must be an array.");
  const workOrders = scenario.work_orders.map(parseWorkOrder);
  const ids = workOrders.map((order) => order.work_id);
  if (new Set(ids).size !== ids.length) throw new Error("work order IDs must be unique.");
  let inputDigest: string | null = null;
  if (scenario.input_digest !== undefined && scenario.input_digest !== null) {
    inputDigest = text(scenario.input_digest, "input_digest");
    if (!/^[0-9a-f]{64}$/.test(inputDigest)) {
      throw new Error("input_digest must be a lowercase SHA-256 digest.");
    }
  }
  const scenarioName = text(scenario.scenario_name, "scenario_name");
  const scenarioId = text(scenario.scenario_id, "scenario_id");
  const modelVersion = text(scenario.model_version, "model_version");
  if (modelVersion !== SCENARIO_MODEL_VERSION) {
    throw new Error(`Unsupported scenario model version: ${modelVersion}.`);
  }
  const solverConfiguration = parseConfiguration(scenario.solver_configuration);
  const selectedSections = new Set(solverConfiguration.section_ids);
  if (workOrders.some((order) => !selectedSections.has(order.section_id))) {
    throw new Error("Every work order must belong to a selected scenario section.");
  }
  const trainWindows = scenario.train_windows.map(parseTrainWindow);
  if (trainWindows.some((window) => !selectedSections.has(window.section_id))) {
    throw new Error("Every train window must belong to a selected scenario section.");
  }
  return {
    scenario_id: scenarioId,
    scenario_name: scenarioName,
    model_version: modelVersion,
    work_orders: workOrders,
    train_windows: trainWindows,
    solver_configuration: solverConfiguration,
    input_digest: inputDigest,
  };
}

function cloneScenario(scenario: ScenarioRecord): ScenarioRecord {
  return {
    ...scenario,
    work_orders: scenario.work_orders.map((order) => ({ ...order })),
    train_windows: scenario.train_windows.map((window) => ({ ...window })),
    solver_configuration: {
      ...scenario.solver_configuration,
      section_ids: [...scenario.solver_configuration.section_ids],
    },
  };
}

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return `scenario-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function createScenario(
  scenarioName: string,
  sectionIds: string[],
  scenarioId = newId(),
  workOrders: MaintenanceWorkOrder[] = [],
): ScenarioRecord {
  return parseScenario({
    scenario_id: scenarioId,
    scenario_name: scenarioName,
    model_version: SCENARIO_MODEL_VERSION,
    work_orders: workOrders.map((order) => ({ ...order })),
    train_windows: [],
    solver_configuration: {
      section_ids: sectionIds,
      time_horizon_hrs: 24,
      slot_duration_hrs: 0.5,
      train_clearance_hrs: 0,
      enable_ac3_pruning: true,
      enable_simulated_annealing: true,
      max_search_nodes: 100_000,
      annealing_iterations: 500,
      annealing_initial_temperature: 2,
      annealing_cooling_rate: 0.995,
      workload_balance_weight: 0.1,
      co_location_reward: 0.5,
      cpsat_time_limit_seconds: 30,
      random_seed: 7,
    },
  });
}

export function duplicateScenario(
  scenario: ScenarioRecord,
  scenarioName: string,
  scenarioId = newId(),
): ScenarioRecord {
  const duplicate = cloneScenario(scenario);
  return parseScenario({
    ...duplicate,
    scenario_id: scenarioId,
    scenario_name: scenarioName,
  });
}

export function updateScenario(
  scenarios: ScenarioRecord[],
  scenarioId: string,
  update: (scenario: ScenarioRecord) => ScenarioRecord,
): ScenarioRecord[] {
  return scenarios.map((scenario) =>
    scenario.scenario_id === scenarioId ? parseScenario(update(cloneScenario(scenario))) : scenario,
  );
}

export function deleteScenario(
  scenarios: ScenarioRecord[],
  scenarioId: string,
): ScenarioRecord[] {
  return scenarios.filter((scenario) => scenario.scenario_id !== scenarioId);
}

function getStorage(storage?: StorageLike): StorageLike {
  return storage ?? browserStorage();
}

function parseStoredScenarios(raw: string): ScenarioRecord[] {
  let envelope: unknown;
  try {
    envelope = JSON.parse(raw);
  } catch (error) {
    throw new ScenarioStorageError(
      "INVALID_JSON",
      "Saved scenarios contain malformed JSON and were left unchanged.",
      { cause: error },
    );
  }
  try {
    const data = record(envelope, "stored scenario data");
    exactKeys(data, ["schema_version", "scenarios"], [], "stored scenario data");
    if (data.schema_version !== SCENARIO_STORAGE_VERSION) {
      throw new ScenarioStorageError(
        "UNSUPPORTED_VERSION",
        `Stored scenario schema version ${String(data.schema_version)} is unsupported; saved data was left unchanged.`,
      );
    }
    if (!Array.isArray(data.scenarios)) throw new Error("scenarios must be an array.");
    const scenarios = data.scenarios.map(parseScenario);
    if (new Set(scenarios.map((scenario) => scenario.scenario_id)).size !== scenarios.length) {
      throw new Error("Stored scenario IDs must be unique.");
    }
    return scenarios;
  } catch (error) {
    if (error instanceof ScenarioStorageError) throw error;
    throw new ScenarioStorageError(
      "INVALID_STORED_DATA",
      `Saved scenarios are incompatible and were left unchanged: ${(error as Error).message}`,
      { cause: error },
    );
  }
}

export function loadScenarios(storage?: StorageLike): ScenarioRecord[] {
  let raw: string | null;
  try {
    raw = getStorage(storage).getItem(SCENARIO_STORAGE_KEY);
  } catch (error) {
    if (error instanceof ScenarioStorageError) throw error;
    throw new ScenarioStorageError(
      "STORAGE_UNAVAILABLE",
      "Browser storage could not be read; saved scenarios were left unchanged.",
      { cause: error },
    );
  }
  return raw === null ? [] : parseStoredScenarios(raw);
}

export function saveScenarios(scenarios: ScenarioRecord[], storage?: StorageLike): void {
  let validated: ScenarioRecord[];
  try {
    validated = scenarios.map(parseScenario);
    if (new Set(validated.map((scenario) => scenario.scenario_id)).size !== validated.length) {
      throw new Error("Scenario IDs must be unique.");
    }
  } catch (error) {
    throw new ScenarioStorageError(
      "INVALID_STORED_DATA",
      `Scenarios were not saved: ${(error as Error).message}`,
      { cause: error },
    );
  }
  try {
    const target = getStorage(storage);
    const existing = target.getItem(SCENARIO_STORAGE_KEY);
    if (existing !== null) parseStoredScenarios(existing);
    target.setItem(
      SCENARIO_STORAGE_KEY,
      JSON.stringify({ schema_version: SCENARIO_STORAGE_VERSION, scenarios: validated }),
    );
  } catch (error) {
    if (error instanceof ScenarioStorageError) throw error;
    throw new ScenarioStorageError(
      "SAVE_FAILED",
      "Scenarios could not be saved to browser storage; your in-memory edits are still available.",
      { cause: error },
    );
  }
}
