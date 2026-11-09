"use client";

import {
  compareSchedulePlacements,
  formatComparisonClock,
  type ScheduleDifference,
} from "@/lib/scenario-diff";
import type {
  MaintenanceWorkOrder,
  ScenarioSolverRunResult,
} from "@/lib/types";

interface Props {
  workOrders: MaintenanceWorkOrder[];
  baseline: ScenarioSolverRunResult;
  cpSat: ScenarioSolverRunResult;
  horizon: number;
}

function assignmentDetails(assignment: ScheduleDifference["baseline"]): string {
  if (!assignment) return "Not scheduled";
  const duration = assignment.end_time_hr - assignment.start_time_hr;
  return `${formatComparisonClock(assignment.start_time_hr)}–${formatComparisonClock(assignment.end_time_hr)} · ${duration.toFixed(3).replace(/\.?0+$/, "")}h · ${assignment.section_id} · ${assignment.track_line.replace("_", " ")}`;
}

const differenceLabels = {
  same_placement: "Same placement",
  placement_changed: "Different placement",
  baseline_only: "Baseline only",
  cp_sat_only: "CP-SAT only",
  unscheduled_both: "Unscheduled by both",
} as const;

export default function ScenarioComparisonGantt({
  workOrders,
  baseline,
  cpSat,
  horizon,
}: Props) {
  const differences = compareSchedulePlacements(
    workOrders.map((order) => order.work_id),
    baseline.schedule,
    cpSat.schedule,
  );
  const tickStep = horizon <= 12 ? 1 : 2;
  const ticks = Array.from(
    new Set([
      ...Array.from({ length: Math.floor(horizon / tickStep) + 1 }, (_, index) => index * tickStep),
      horizon,
    ]),
  );
  const position = (hours: number) => `${(Math.min(Math.max(hours, 0), horizon) / horizon) * 100}%`;
  const width = (start: number, end: number) =>
    `${Math.max(0, Math.min(end, horizon) - Math.max(start, 0)) / horizon * 100}%`;
  const orderById = new Map(workOrders.map((order) => [order.work_id, order]));

  function lane(
    label: string,
    assignment: ScheduleDifference["baseline"],
    solver: "baseline" | "cp_sat",
  ) {
    return (
      <div className="grid grid-cols-[minmax(14rem,1fr)_minmax(16rem,2fr)] items-center gap-3 py-1.5">
        <div className="truncate text-[11px] text-slate-400" title={`${label}: ${assignmentDetails(assignment)}`}>
          <span className="mr-1 text-slate-500">{label}:</span>
          {assignmentDetails(assignment)}
        </div>
        <div className="relative h-6 border-l border-slate-700 bg-slate-950/60">
          {ticks.map((tick) => (
            <span
              key={tick}
              className="pointer-events-none absolute inset-y-0 border-l border-slate-800"
              style={{ left: position(tick) }}
            />
          ))}
          {assignment && (
            <div
              role="img"
              aria-label={`${label} ${assignment.work_id}, ${assignment.department}, ${assignment.section_id}, ${assignment.track_line.replace("_", " ")}, ${formatComparisonClock(assignment.start_time_hr)} to ${formatComparisonClock(assignment.end_time_hr)}, duration ${(assignment.end_time_hr - assignment.start_time_hr).toFixed(3)} hours`}
              title={`${label} · ${assignment.work_id} · ${assignment.department} · ${assignment.section_id} · ${assignment.track_line.replace("_", " ")} · ${formatComparisonClock(assignment.start_time_hr)}–${formatComparisonClock(assignment.end_time_hr)} · ${(assignment.end_time_hr - assignment.start_time_hr).toFixed(3)}h`}
              className={`absolute inset-y-0.5 z-10 overflow-hidden whitespace-nowrap rounded border px-1 text-[9px] font-medium text-white ${
                solver === "baseline"
                  ? "border-cyan-300 bg-cyan-800"
                  : "border-fuchsia-300 bg-fuchsia-800"
              }`}
              style={{
                left: position(assignment.start_time_hr),
                width: width(assignment.start_time_hr, assignment.end_time_hr),
                minWidth: "3px",
              }}
            >
              {assignment.work_id}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (workOrders.length === 0) {
    return <p className="text-sm text-slate-400">This scenario contains no work orders to plot.</p>;
  }

  return (
    <section aria-label="Schedule difference timeline" className="space-y-3">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
        <span className="flex items-center gap-1"><i className="h-3 w-3 rounded bg-cyan-700" /> Baseline</span>
        <span className="flex items-center gap-1"><i className="h-3 w-3 rounded bg-fuchsia-700" /> CP-SAT</span>
        <span>Each work order has separate solver lanes; only returned assignments are plotted.</span>
      </div>
      <div className="overflow-x-auto rounded-lg border border-slate-800">
        <div className="min-w-[760px] bg-slate-950/30 p-3">
          <div className="grid grid-cols-[minmax(14rem,1fr)_minmax(16rem,2fr)] gap-3 border-b border-slate-800 pb-2">
            <span className="text-xs font-medium text-slate-400">Work order and returned placement</span>
            <div className="relative h-5 text-[10px] text-slate-500">
              {ticks.map((tick) => (
                <span key={tick} className="absolute -translate-x-1/2" style={{ left: position(tick) }}>
                  {formatComparisonClock(tick)}
                </span>
              ))}
            </div>
          </div>
          <ul className="divide-y divide-slate-800">
            {differences.map((difference) => {
              const order = orderById.get(difference.workId);
              const section = difference.baseline?.section_id ?? difference.cpSat?.section_id ?? order?.section_id ?? "Unavailable";
              const line = difference.baseline?.track_line ?? difference.cpSat?.track_line ?? order?.track_line ?? "Unavailable";
              const department = difference.baseline?.department ?? difference.cpSat?.department ?? order?.department ?? "Unavailable";
              return (
                <li key={difference.workId} className="py-2">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-slate-200">{difference.workId}</span>
                    <span className="text-[10px] text-slate-400">{department} · {section} · {line.replace("_", " ")}</span>
                    <span className="rounded border border-slate-700 px-1.5 py-0.5 text-[10px] text-slate-300">{differenceLabels[difference.kind]}</span>
                  </div>
                  {lane("Baseline", difference.baseline, "baseline")}
                  {lane("CP-SAT", difference.cpSat, "cp_sat")}
                </li>
              );
            })}
          </ul>
        </div>
      </div>
      <p className="text-xs text-slate-500">
        Timeline represents solver output only; it is not operational authorization or a safety assessment.
      </p>
    </section>
  );
}
