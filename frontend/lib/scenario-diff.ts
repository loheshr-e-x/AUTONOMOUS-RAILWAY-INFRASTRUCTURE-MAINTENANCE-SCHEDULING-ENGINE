import type { ScenarioAssignment } from "./types";

export function formatComparisonClock(hours: number): string {
  const totalMinutes = Math.round(hours * 60);
  const hour = Math.floor(totalMinutes / 60);
  const minute = totalMinutes % 60;
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

export type ScheduleDifferenceKind =
  | "same_placement"
  | "placement_changed"
  | "baseline_only"
  | "cp_sat_only"
  | "unscheduled_both";

export interface ScheduleDifference {
  workId: string;
  baseline: ScenarioAssignment | null;
  cpSat: ScenarioAssignment | null;
  kind: ScheduleDifferenceKind;
}

function samePlacement(
  baseline: ScenarioAssignment,
  cpSat: ScenarioAssignment,
): boolean {
  return (
    baseline.department === cpSat.department &&
    baseline.section_id === cpSat.section_id &&
    baseline.track_line === cpSat.track_line &&
    Math.abs(baseline.start_time_hr - cpSat.start_time_hr) <= 1e-6 &&
    Math.abs(baseline.end_time_hr - cpSat.end_time_hr) <= 1e-6
  );
}

export function compareSchedulePlacements(
  workOrderIds: string[],
  baselineSchedule: ScenarioAssignment[],
  cpSatSchedule: ScenarioAssignment[],
): ScheduleDifference[] {
  const baselineById = new Map(baselineSchedule.map((assignment) => [assignment.work_id, assignment]));
  const cpSatById = new Map(cpSatSchedule.map((assignment) => [assignment.work_id, assignment]));

  return [...new Set(workOrderIds)].map((workId) => {
    const baseline = baselineById.get(workId) ?? null;
    const cpSat = cpSatById.get(workId) ?? null;
    const kind: ScheduleDifferenceKind =
      baseline && cpSat
        ? samePlacement(baseline, cpSat)
          ? "same_placement"
          : "placement_changed"
        : baseline
          ? "baseline_only"
          : cpSat
            ? "cp_sat_only"
            : "unscheduled_both";
    return { workId, baseline, cpSat, kind };
  });
}
