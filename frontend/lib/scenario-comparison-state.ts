import type { ScenarioComparisonResponse, ScenarioSolverRunResult } from "./types";

export interface ComparisonRequestTracker {
  generation: number;
  inFlight: boolean;
}

export function createComparisonRequestTracker(): ComparisonRequestTracker {
  return { generation: 0, inFlight: false };
}

export function beginComparisonRequest(
  tracker: ComparisonRequestTracker,
): number | null {
  if (tracker.inFlight) return null;
  tracker.inFlight = true;
  tracker.generation += 1;
  return tracker.generation;
}

export function invalidateComparisonRequests(
  tracker: ComparisonRequestTracker,
): void {
  tracker.generation += 1;
  tracker.inFlight = false;
}

export function isCurrentComparisonRequest(
  tracker: ComparisonRequestTracker,
  requestId: number,
): boolean {
  return tracker.generation === requestId;
}

export function finishComparisonRequest(
  tracker: ComparisonRequestTracker,
  requestId: number,
): boolean {
  if (!isCurrentComparisonRequest(tracker, requestId)) return false;
  tracker.inFlight = false;
  return true;
}

function isValidRunAccounting(
  run: ScenarioSolverRunResult,
  solver: ScenarioSolverRunResult["solver"],
  submittedIds: string[],
  digest: string,
): boolean {
  if (
    run.solver !== solver ||
    run.run_status !== "completed" ||
    run.error_code !== null ||
    run.error_message !== null ||
    run.input_digest !== digest ||
    run.total_work_orders !== submittedIds.length ||
    run.validation?.valid !== true ||
    run.validation.findings.length !== 0
  ) {
    return false;
  }

  const submitted = new Set(submittedIds);
  const scheduled = new Set(run.scheduled_work_ids);
  const unscheduled = new Set(run.unscheduled_work_ids);
  const scheduleIds = run.schedule.map((assignment) => assignment.work_id);
  const reasonIds = run.unscheduled_reasons.map((reason) => reason.work_id);

  return (
    submitted.size === submittedIds.length &&
    scheduled.size === run.scheduled_work_ids.length &&
    unscheduled.size === run.unscheduled_work_ids.length &&
    new Set(scheduleIds).size === scheduleIds.length &&
    scheduleIds.length === run.scheduled_work_ids.length &&
    scheduleIds.every((workId) => scheduled.has(workId)) &&
    run.scheduled_work_ids.every((workId) => submitted.has(workId)) &&
    run.unscheduled_work_ids.every((workId) => submitted.has(workId)) &&
    run.scheduled_work_ids.every((workId) => !unscheduled.has(workId)) &&
    new Set([...scheduled, ...unscheduled]).size === submittedIds.length &&
    submittedIds.every((workId) => scheduled.has(workId) || unscheduled.has(workId)) &&
    new Set(reasonIds).size === reasonIds.length &&
    reasonIds.every((workId) => unscheduled.has(workId))
  );
}

export function isValidatedPairedComparison(
  result: ScenarioComparisonResponse | null,
  expected: {
    scenarioId: string;
    modelVersion: string;
    inputDigest: string | null;
    workOrderIds: string[];
  } | null,
): result is ScenarioComparisonResponse {
  if (
    !result ||
    !expected ||
    !expected.inputDigest ||
    !/^[0-9a-f]{64}$/.test(expected.inputDigest) ||
    result.comparison_status !== "completed" ||
    result.paired_inputs_match !== true ||
    result.scenario_id !== expected.scenarioId ||
    result.model_version !== expected.modelVersion ||
    result.input_digest !== expected.inputDigest
  ) {
    return false;
  }

  return (
    isValidRunAccounting(result.baseline, "baseline", expected.workOrderIds, expected.inputDigest) &&
    isValidRunAccounting(result.cp_sat, "cp_sat", expected.workOrderIds, expected.inputDigest)
  );
}
