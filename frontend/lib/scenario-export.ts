import type {
  ScenarioComparisonRequest,
  ScenarioComparisonResponse,
  ScenarioObjectiveComponent,
  ScenarioSolverRunResult,
} from "./types";
import { compareSchedulePlacements } from "./scenario-diff.ts";

export const EXPERIMENT_EXPORT_FORMAT = "symbio-block-experiment";
export const EXPERIMENT_EXPORT_SCHEMA_VERSION = 1;

export interface ExperimentExportRecord {
  format: typeof EXPERIMENT_EXPORT_FORMAT;
  schema_version: typeof EXPERIMENT_EXPORT_SCHEMA_VERSION;
  experiment: {
    experiment_id: string;
    exported_at_utc: string | null;
    scenario_id: string;
    scenario_name: string | null;
    model_version: string;
    canonical_input_digest: string;
  };
  submitted_request: ScenarioComparisonRequest;
  comparison: ScenarioComparisonResponse;
  schedule_differences: Array<{
    work_order_id: string;
    classification: string;
    baseline_assignment: ScenarioSolverRunResult["schedule"][number] | null;
    cp_sat_assignment: ScenarioSolverRunResult["schedule"][number] | null;
    baseline_unscheduled_reason: string | null;
    cp_sat_unscheduled_reason: string | null;
  }>;
}

export type ExperimentExportFormat = "json" | "csv";

export class ExperimentExportError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ExperimentExportError";
  }
}

const floatInputFields = new Set([
  "work_orders.duration_hrs",
  "train_windows.start_time_hr",
  "train_windows.end_time_hr",
  "solver_configuration.time_horizon_hrs",
  "solver_configuration.slot_duration_hrs",
  "solver_configuration.train_clearance_hrs",
  "solver_configuration.annealing_initial_temperature",
  "solver_configuration.annealing_cooling_rate",
  "solver_configuration.workload_balance_weight",
  "solver_configuration.co_location_reward",
  "solver_configuration.cpsat_time_limit_seconds",
]);

function pythonFloat(value: number): string {
  if (!Number.isFinite(value)) {
    throw new ExperimentExportError("Scenario input contains a non-finite number.");
  }
  if (Object.is(value, -0)) return "-0.0";

  const [mantissa, exponentText] = Math.abs(value).toString().toLowerCase().split("e");
  const exponent = exponentText ? Number(exponentText) : 0;
  const decimalIndex = mantissa.indexOf(".");
  const decimalPosition = (decimalIndex === -1 ? mantissa.length : decimalIndex) + exponent;
  let digits = mantissa.replace(".", "");
  const leadingZeros = digits.match(/^0*/)?.[0].length ?? 0;
  digits = digits.slice(leadingZeros);
  const adjustedDecimalPosition = decimalPosition - leadingZeros;
  digits = digits.replace(/0+$/, "") || "0";
  const scientificExponent = adjustedDecimalPosition - 1;
  const absolute = Math.abs(value);
  const sign = value < 0 ? "-" : "";

  if (absolute !== 0 && (absolute < 1e-4 || absolute >= 1e16)) {
    const significand = digits.length === 1
      ? digits
      : `${digits[0]}.${digits.slice(1)}`;
    const exponentSign = scientificExponent >= 0 ? "+" : "-";
    const paddedExponent = String(Math.abs(scientificExponent)).padStart(2, "0");
    return `${sign}${significand}e${exponentSign}${paddedExponent}`;
  }

  let plain: string;
  if (adjustedDecimalPosition <= 0) {
    plain = `0.${"0".repeat(-adjustedDecimalPosition)}${digits}`;
  } else if (adjustedDecimalPosition >= digits.length) {
    plain = `${digits}${"0".repeat(adjustedDecimalPosition - digits.length)}`;
  } else {
    plain = `${digits.slice(0, adjustedDecimalPosition)}.${digits.slice(adjustedDecimalPosition)}`;
  }
  if (!plain.includes(".")) plain += ".0";
  return `${sign}${plain}`;
}

function escapePythonString(value: string): string {
  return JSON.stringify(value).replace(/[\u007f-\uffff]/g, (character) =>
    `\\u${character.charCodeAt(0).toString(16).padStart(4, "0")}`,
  );
}

function canonicalJson(value: unknown, path = ""): string {
  if (value === null) return "null";
  if (typeof value === "string") return escapePythonString(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    return floatInputFields.has(path) ? pythonFloat(value) : JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((item) => canonicalJson(item, path)).join(",")}]`;
  }
  if (typeof value === "object" && value !== null) {
    const object = value as Record<string, unknown>;
    const entries = Object.keys(object)
      .sort()
      .filter((key) => object[key] !== undefined)
      .map((key) => {
        const nextPath = path ? `${path}.${key}` : key;
        return `${escapePythonString(key)}:${canonicalJson(object[key], nextPath)}`;
      });
    return `{${entries.join(",")}}`;
  }
  throw new ExperimentExportError("Scenario input is not JSON-serializable.");
}

function canonicalInput(request: ScenarioComparisonRequest): Record<string, unknown> {
  return {
    model_version: request.model_version ?? "symbio-block-task16-simulation-v1",
    work_orders: request.work_orders.map((order) => ({
      work_id: order.work_id,
      department: order.department,
      section_id: order.section_id,
      track_line: order.track_line ?? "DOWN_LINE",
      heavy_equipment: order.heavy_equipment ?? false,
      defect_type: order.defect_type,
      duration_hrs: order.duration_hrs,
      urgency: order.urgency,
      co_location_allowed: order.co_location_allowed ?? true,
    })),
    train_windows: (request.train_windows ?? []).map((window) => ({
      train_no: window.train_no,
      section_id: window.section_id,
      track_line: window.track_line ?? "DOWN_LINE",
      start_time_hr: window.start_time_hr,
      end_time_hr: window.end_time_hr,
    })),
    solver_configuration: {
      section_ids: request.solver_configuration.section_ids,
      time_horizon_hrs: request.solver_configuration.time_horizon_hrs ?? 24,
      slot_duration_hrs: request.solver_configuration.slot_duration_hrs ?? 0.5,
      train_clearance_hrs: request.solver_configuration.train_clearance_hrs ?? 0,
      enable_ac3_pruning: request.solver_configuration.enable_ac3_pruning ?? true,
      enable_simulated_annealing: request.solver_configuration.enable_simulated_annealing ?? true,
      max_search_nodes: request.solver_configuration.max_search_nodes ?? 100_000,
      annealing_iterations: request.solver_configuration.annealing_iterations ?? 500,
      annealing_initial_temperature: request.solver_configuration.annealing_initial_temperature ?? 2,
      annealing_cooling_rate: request.solver_configuration.annealing_cooling_rate ?? 0.995,
      workload_balance_weight: request.solver_configuration.workload_balance_weight ?? 0.1,
      co_location_reward: request.solver_configuration.co_location_reward ?? 0.5,
      cpsat_time_limit_seconds: request.solver_configuration.cpsat_time_limit_seconds ?? 30,
      random_seed: request.solver_configuration.random_seed ?? 7,
    },
  };
}

export async function canonicalScenarioInputDigest(
  request: ScenarioComparisonRequest,
): Promise<string> {
  if (!globalThis.crypto?.subtle) {
    throw new ExperimentExportError("This browser does not provide SHA-256 digest support.");
  }
  const bytes = new TextEncoder().encode(canonicalJson(canonicalInput(request)));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function validateRunAccounting(
  run: ScenarioSolverRunResult,
  expectedSolver: ScenarioSolverRunResult["solver"],
  submittedIds: string[],
  digest: string,
): void {
  if (run.solver !== expectedSolver || run.run_status !== "completed") {
    throw new ExperimentExportError(`${expectedSolver} did not return a completed solver run.`);
  }
  if (run.error_code !== null || run.error_message !== null) {
    throw new ExperimentExportError(`${expectedSolver} returned error information.`);
  }
  if (run.input_digest !== digest) {
    throw new ExperimentExportError(`${expectedSolver} input digest does not match the submitted scenario.`);
  }
  if (run.validation?.valid !== true || run.validation.findings.length > 0) {
    throw new ExperimentExportError(`${expectedSolver} assignment did not pass independent validation.`);
  }
  if (run.total_work_orders !== submittedIds.length) {
    throw new ExperimentExportError(`${expectedSolver} work-order total does not match the submitted scenario.`);
  }

  const scheduled = run.scheduled_work_ids;
  const unscheduled = run.unscheduled_work_ids;
  const scheduledIds = run.schedule.map((assignment) => assignment.work_id);
  const uniqueScheduled = new Set(scheduled);
  const uniqueUnscheduled = new Set(unscheduled);
  const uniqueSubmitted = new Set(submittedIds);
  if (
    uniqueSubmitted.size !== submittedIds.length ||
    uniqueScheduled.size !== scheduled.length ||
    uniqueUnscheduled.size !== unscheduled.length ||
    scheduledIds.length !== scheduled.length ||
    new Set(scheduledIds).size !== scheduledIds.length ||
    scheduledIds.some((workId) => !uniqueScheduled.has(workId)) ||
    scheduled.some((workId) => !uniqueSubmitted.has(workId)) ||
    unscheduled.some((workId) => !uniqueSubmitted.has(workId)) ||
    scheduled.some((workId) => uniqueUnscheduled.has(workId)) ||
    new Set([...scheduled, ...unscheduled]).size !== submittedIds.length ||
    submittedIds.some((workId) => !uniqueScheduled.has(workId) && !uniqueUnscheduled.has(workId))
  ) {
    throw new ExperimentExportError(`${expectedSolver} work-order accounting is incomplete or inconsistent.`);
  }

  const unscheduledSet = new Set(unscheduled);
  const reasonIds = run.unscheduled_reasons.map((reason) => reason.work_id);
  if (
    new Set(reasonIds).size !== reasonIds.length ||
    reasonIds.some((workId) => !unscheduledSet.has(workId))
  ) {
    throw new ExperimentExportError(`${expectedSolver} returned inconsistent unscheduled-work reasons.`);
  }
}

export async function createExperimentExportRecord(
  request: ScenarioComparisonRequest,
  response: ScenarioComparisonResponse,
  metadata: { experimentId?: string; exportedAtUtc?: string | null } = {},
): Promise<ExperimentExportRecord> {
  const digest = await canonicalScenarioInputDigest(request);
  if (!/^[0-9a-f]{64}$/.test(digest) || response.input_digest !== digest) {
    throw new ExperimentExportError("Comparison input digest does not match the submitted scenario.");
  }
  if (
    response.scenario_id !== request.scenario_id ||
    response.model_version !== request.model_version ||
    response.comparison_status !== "completed" ||
    response.paired_inputs_match !== true
  ) {
    throw new ExperimentExportError("Only completed comparisons with matching paired inputs can be exported.");
  }
  const submittedIds = request.work_orders.map((order) => order.work_id);
  validateRunAccounting(response.baseline, "baseline", submittedIds, digest);
  validateRunAccounting(response.cp_sat, "cp_sat", submittedIds, digest);

  const baselineReasons = new Map(
    response.baseline.unscheduled_reasons.map((reason) => [reason.work_id, reason.code]),
  );
  const cpSatReasons = new Map(
    response.cp_sat.unscheduled_reasons.map((reason) => [reason.work_id, reason.code]),
  );
  const differences = compareSchedulePlacements(
    submittedIds,
    response.baseline.schedule,
    response.cp_sat.schedule,
  );
  const baselineAssignments = new Map(
    response.baseline.schedule.map((assignment) => [assignment.work_id, assignment]),
  );
  const cpSatAssignments = new Map(
    response.cp_sat.schedule.map((assignment) => [assignment.work_id, assignment]),
  );

  return {
    format: EXPERIMENT_EXPORT_FORMAT,
    schema_version: EXPERIMENT_EXPORT_SCHEMA_VERSION,
    experiment: {
      experiment_id: metadata.experimentId ?? createExperimentId(),
      exported_at_utc: metadata.exportedAtUtc ?? null,
      scenario_id: request.scenario_id,
      scenario_name: request.scenario_name ?? null,
      model_version: request.model_version,
      canonical_input_digest: digest,
    },
    submitted_request: cloneJson(request),
    comparison: cloneJson(response),
    schedule_differences: differences.map((difference) => ({
      work_order_id: difference.workId,
      classification: difference.kind,
      baseline_assignment: baselineAssignments.get(difference.workId) ?? null,
      cp_sat_assignment: cpSatAssignments.get(difference.workId) ?? null,
      baseline_unscheduled_reason: baselineReasons.get(difference.workId) ?? null,
      cp_sat_unscheduled_reason: cpSatReasons.get(difference.workId) ?? null,
    })),
  };
}

function cloneJson<T>(value: T): T {
  try {
    return JSON.parse(JSON.stringify(value)) as T;
  } catch (error) {
    throw new ExperimentExportError(`Experiment data could not be copied safely: ${(error as Error).message}`);
  }
}

function createExperimentId(): string {
  if (!globalThis.crypto?.randomUUID) {
    throw new ExperimentExportError("This browser does not provide secure experiment IDs.");
  }
  return globalThis.crypto.randomUUID();
}

export function stableJsonStringify(record: ExperimentExportRecord): string {
  function serialize(value: unknown, depth: number): string {
    if (value === null || typeof value !== "object") return JSON.stringify(value);
    const indent = "  ".repeat(depth);
    const childIndent = "  ".repeat(depth + 1);
    if (Array.isArray(value)) {
      if (value.length === 0) return "[]";
      return `[\n${value.map((item) => `${childIndent}${serialize(item, depth + 1)}`).join(",\n")}\n${indent}]`;
    }
    const object = value as Record<string, unknown>;
    const keys = Object.keys(object).filter((key) => object[key] !== undefined).sort();
    if (keys.length === 0) return "{}";
    return `{\n${keys.map((key) => `${childIndent}${JSON.stringify(key)}: ${serialize(object[key], depth + 1)}`).join(",\n")}\n${indent}}`;
  }
  return `${serialize(record, 0)}\n`;
}

const objectiveColumns = [
  "time_of_day_train_gap",
  "department_workload_imbalance",
  "co_location_merge_count",
  "schedule_stability",
  "utilization",
] as const;

function componentValue(component: ScenarioObjectiveComponent | undefined, field: "available" | "value" | "explanation"): string | number | boolean | null {
  return component ? component[field] : null;
}

function csvCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  let text = String(value);
  if (typeof value === "string" && /^[=+\-@\t\r]/.test(text)) text = `'${text}`;
  if (/[",\r\n]/.test(text)) return `"${text.replaceAll('"', '""')}"`;
  return text;
}

export function experimentRecordToCsv(record: ExperimentExportRecord): string {
  const headers = [
    "schema_version", "experiment_id", "exported_at_utc", "scenario_id",
    "scenario_name", "model_version", "input_digest", "comparison_status",
    "paired_inputs_match", "work_order_id", "schedule_difference",
    "submitted_department", "submitted_section_id", "submitted_track_line",
    "submitted_duration_hrs", "submitted_heavy_equipment", "submitted_urgency",
    "submitted_defect_type", "submitted_co_location_allowed",
    "baseline_run_status", "baseline_input_digest", "baseline_total_work_orders",
    "baseline_scheduled_count", "baseline_unscheduled_count", "baseline_solver_outcome",
    "baseline_validation_valid", "baseline_complete_assignment_witness",
    "baseline_coverage_optimality_proven", "baseline_complete_schedule_proven_infeasible",
    "baseline_objective_optimality_proven", "baseline_feasibility_not_established",
    "baseline_search_limit_reached", "baseline_termination_reason",
    "baseline_termination_status", "baseline_runtime_seconds",
    "baseline_assignment_start_time_hr", "baseline_assignment_end_time_hr",
    "baseline_assignment_scheduled",
    "baseline_assignment_section_id", "baseline_assignment_track_line",
    "baseline_assignment_department", "baseline_unscheduled_reason_code",
    "cp_sat_run_status", "cp_sat_input_digest", "cp_sat_total_work_orders",
    "cp_sat_scheduled_count", "cp_sat_unscheduled_count", "cp_sat_solver_outcome",
    "cp_sat_validation_valid", "cp_sat_complete_assignment_witness",
    "cp_sat_coverage_optimality_proven", "cp_sat_complete_schedule_proven_infeasible",
    "cp_sat_objective_optimality_proven", "cp_sat_feasibility_not_established",
    "cp_sat_search_limit_reached",
    "cp_sat_termination_reason", "cp_sat_termination_status", "cp_sat_runtime_seconds",
    "cp_sat_assignment_start_time_hr", "cp_sat_assignment_end_time_hr",
    "cp_sat_assignment_scheduled",
    "cp_sat_assignment_section_id", "cp_sat_assignment_track_line",
    "cp_sat_assignment_department", "cp_sat_unscheduled_reason_code", "cp_sat_proof_scope",
    ...objectiveColumns.flatMap((column) => [
      `baseline_${column}_available`, `baseline_${column}_value`,
      `baseline_${column}_explanation`, `cp_sat_${column}_available`,
      `cp_sat_${column}_value`, `cp_sat_${column}_explanation`,
    ]),
  ];
  const orders = new Map(record.submitted_request.work_orders.map((order) => [order.work_id, order]));
  const rows = record.schedule_differences.map((difference) => {
    const order = orders.get(difference.work_order_id);
    const baseline = record.comparison.baseline;
    const cpSat = record.comparison.cp_sat;
    const values: unknown[] = [
      record.schema_version,
      record.experiment.experiment_id,
      record.experiment.exported_at_utc,
      record.experiment.scenario_id,
      record.experiment.scenario_name,
      record.experiment.model_version,
      record.experiment.canonical_input_digest,
      record.comparison.comparison_status,
      record.comparison.paired_inputs_match,
      difference.work_order_id,
      difference.classification,
      order?.department,
      order?.section_id,
      order?.track_line,
      order?.duration_hrs,
      order?.heavy_equipment,
      order?.urgency,
      order?.defect_type,
      order?.co_location_allowed,
      baseline.run_status,
      baseline.input_digest,
      baseline.total_work_orders,
      baseline.scheduled_work_ids.length,
      baseline.unscheduled_work_ids.length,
      baseline.solver_outcome,
      baseline.validation?.valid,
      baseline.complete_assignment_witness,
      baseline.coverage_optimality_proven,
      baseline.complete_schedule_proven_infeasible,
      baseline.objective_optimality_proven,
      baseline.feasibility_not_established,
      baseline.search_limit_reached,
      baseline.termination_reason,
      baseline.termination_status,
      baseline.runtime_seconds,
      difference.baseline_assignment?.start_time_hr,
      difference.baseline_assignment?.end_time_hr,
      difference.baseline_assignment !== null,
      difference.baseline_assignment?.section_id,
      difference.baseline_assignment?.track_line,
      difference.baseline_assignment?.department,
      difference.baseline_unscheduled_reason,
      cpSat.run_status,
      cpSat.input_digest,
      cpSat.total_work_orders,
      cpSat.scheduled_work_ids.length,
      cpSat.unscheduled_work_ids.length,
      cpSat.solver_outcome,
      cpSat.validation?.valid,
      cpSat.complete_assignment_witness,
      cpSat.coverage_optimality_proven,
      cpSat.complete_schedule_proven_infeasible,
      cpSat.objective_optimality_proven,
      cpSat.feasibility_not_established,
      cpSat.search_limit_reached,
      cpSat.termination_reason,
      cpSat.termination_status,
      cpSat.runtime_seconds,
      difference.cp_sat_assignment?.start_time_hr,
      difference.cp_sat_assignment?.end_time_hr,
      difference.cp_sat_assignment !== null,
      difference.cp_sat_assignment?.section_id,
      difference.cp_sat_assignment?.track_line,
      difference.cp_sat_assignment?.department,
      difference.cp_sat_unscheduled_reason,
      cpSat.proof_scope,
      ...objectiveColumns.flatMap((column) => [
        componentValue(baseline.objective_components[column], "available"),
        componentValue(baseline.objective_components[column], "value"),
        componentValue(baseline.objective_components[column], "explanation"),
        componentValue(cpSat.objective_components[column], "available"),
        componentValue(cpSat.objective_components[column], "value"),
        componentValue(cpSat.objective_components[column], "explanation"),
      ]),
    ];
    return values.map(csvCell).join(",");
  });
  return `${headers.join(",")}\r\n${rows.join("\r\n")}${rows.length ? "\r\n" : ""}`;
}

export function downloadExperimentExport(
  sourceRecord: ExperimentExportRecord,
  format: ExperimentExportFormat,
): ExperimentExportRecord {
  const record = sourceRecord.experiment.exported_at_utc === null
    ? {
        ...sourceRecord,
        experiment: {
          ...sourceRecord.experiment,
          exported_at_utc: new Date().toISOString(),
        },
      }
    : sourceRecord;
  const content = format === "json" ? stableJsonStringify(record) : experimentRecordToCsv(record);
  const mimeType = format === "json" ? "application/json;charset=utf-8" : "text/csv;charset=utf-8";
  const extension = format;
  const scenarioSlug = record.experiment.scenario_id.replace(/[^a-zA-Z0-9._-]/g, "_") || "scenario";
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `symbio-experiment-${scenarioSlug}-${record.experiment.experiment_id}.${extension}`;
  link.hidden = true;
  document.body.append(link);
  try {
    link.click();
  } finally {
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  return record;
}
