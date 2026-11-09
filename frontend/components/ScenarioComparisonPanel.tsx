"use client";

import { useState } from "react";
import { AlertTriangle, Play } from "lucide-react";
import ScenarioComparisonGantt from "@/components/ScenarioComparisonGantt";
import {
  downloadExperimentExport,
  type ExperimentExportFormat,
  type ExperimentExportRecord,
} from "@/lib/scenario-export";
import type {
  ScenarioComparisonErrorKind,
} from "@/lib/api";
import type {
  ScenarioComparisonResponse,
  ScenarioObjectiveComponent,
  ScenarioSolverRunResult,
} from "@/lib/types";
import type { ScenarioRecord } from "@/lib/scenario-storage";
import { compareSchedulePlacements } from "@/lib/scenario-diff";
import { isValidatedPairedComparison } from "@/lib/scenario-comparison-state";

interface Props {
  scenario: ScenarioRecord | null;
  expectedInputDigest: string | null;
  running: boolean;
  error: { kind: ScenarioComparisonErrorKind; message: string } | null;
  result: ScenarioComparisonResponse | null;
  exportRecord: ExperimentExportRecord | null;
  exportError: string | null;
  onExportRecordCreated: (record: ExperimentExportRecord) => void;
  onCompare: () => void;
}

const objectiveLabels: Record<keyof ScenarioSolverRunResult["objective_components"], string> = {
  time_of_day_train_gap: "Time-of-day / train-gap disruption component",
  department_workload_imbalance: "Department workload imbalance",
  co_location_merge_count: "Co-location merge count or reward",
  schedule_stability: "Schedule stability",
  utilization: "Resource utilization",
};

function proofLabel(value: boolean | null, provenLabel: string): string {
  if (value === true) return provenLabel;
  if (value === false) return "Not proven";
  return "Unavailable";
}

function validationLabel(run: ScenarioSolverRunResult): string {
  if (!run.validation) return "Unavailable";
  return run.validation.valid ? "Independent model validation passed" : "Validation failed";
}

function assignmentLabel(run: ScenarioSolverRunResult): string {
  if (run.validation?.valid === false) return "Validation failed";
  if (run.validation?.valid !== true) return "Unavailable";
  return proofLabel(run.complete_assignment_witness, "Validated assignment");
}

function displayComponent(component: ScenarioObjectiveComponent): string {
  if (!component.available || component.value === null) return "Unavailable";
  return typeof component.value === "number"
    ? String(Number(component.value.toFixed(6)))
    : String(component.value);
}

function solverTitle(solver: ScenarioSolverRunResult["solver"]): string {
  return solver === "baseline" ? "Baseline solver" : "Experimental CP-SAT solver";
}

function SolverCard({ run }: { run: ScenarioSolverRunResult }) {
  const completed = run.run_status === "completed";
  const reasons = new Map(run.unscheduled_reasons.map((reason) => [reason.work_id, reason]));

  return (
    <article className="space-y-4 rounded-lg border border-slate-700 bg-slate-950/50 p-4">
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold">{solverTitle(run.solver)}</h3>
          <p className="mt-1 text-xs text-slate-400">
            Execution status: <strong className="text-slate-200">{run.run_status}</strong>
            {run.solver_outcome !== null && <> · Outcome: <strong className="text-slate-200">{run.solver_outcome}</strong></>}
          </p>
        </div>
        {run.run_status === "unavailable" && (
          <span className="rounded border border-amber-700 px-2 py-1 text-xs text-amber-200">Unavailable</span>
        )}
      </header>

      {run.error_message && (
        <div role="alert" className="rounded border border-rose-900 bg-rose-950/40 p-2 text-sm text-rose-200">
          {run.error_code && <strong>{run.error_code}: </strong>}{run.error_message}
        </div>
      )}

      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        <div><dt className="text-xs text-slate-500">Scheduled work orders</dt><dd>{completed ? `${run.scheduled_work_ids.length} / ${run.total_work_orders}` : "Unavailable"}</dd></div>
        <div><dt className="text-xs text-slate-500">Unscheduled work orders</dt><dd>{completed ? `${run.unscheduled_work_ids.length} / ${run.total_work_orders}` : "Unavailable"}</dd></div>
        <div><dt className="text-xs text-slate-500">Runtime</dt><dd>{run.runtime_seconds === null ? "Unavailable" : `${run.runtime_seconds.toFixed(3)} s`}</dd></div>
        <div><dt className="text-xs text-slate-500">Termination reason</dt><dd>{run.termination_reason ?? run.termination_status ?? "Unavailable"}</dd></div>
        <div className="sm:col-span-2"><dt className="text-xs text-slate-500">Input digest</dt><dd className="break-all font-mono text-xs">{run.input_digest || "Unavailable"}</dd></div>
        <div><dt className="text-xs text-slate-500">Independent validation</dt><dd className={run.validation?.valid === false ? "text-rose-300" : ""}>{validationLabel(run)}</dd></div>
        <div><dt className="text-xs text-slate-500">Complete assignment</dt><dd>{assignmentLabel(run)}</dd></div>
        <div><dt className="text-xs text-slate-500">Maximum coverage</dt><dd>{proofLabel(run.coverage_optimality_proven, "Maximum coverage proven")}</dd></div>
        <div><dt className="text-xs text-slate-500">Complete schedule infeasibility</dt><dd>{proofLabel(run.complete_schedule_proven_infeasible, "Proven infeasible")}</dd></div>
        <div><dt className="text-xs text-slate-500">Objective optimality</dt><dd>{proofLabel(run.objective_optimality_proven, "Objective optimality proven")}</dd></div>
      </dl>

      {run.validation && run.validation.findings.length > 0 && (
        <div>
          <h4 className="mb-1 text-xs font-semibold text-rose-300">Validation findings</h4>
          <ul className="space-y-1 text-xs text-rose-200">
            {run.validation.findings.map((finding, index) => (
              <li key={`${finding.code}-${index}`}><code>{finding.code}</code>: {finding.message}</li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <h4 className="mb-2 text-xs font-semibold text-slate-300">Unscheduled work orders</h4>
        {!completed ? (
          <p className="text-xs text-slate-500">Unavailable because this solver run did not complete.</p>
        ) : run.unscheduled_work_ids.length === 0 ? (
          <p className="text-xs text-slate-500">None returned.</p>
        ) : (
          <ul className="space-y-2 text-xs">
            {run.unscheduled_work_ids.map((workId) => {
              const reason = reasons.get(workId);
              return (
                <li key={workId} className="rounded border border-slate-800 p-2">
                  <span className="font-mono text-slate-200">{workId}</span>
                  <span className="ml-2 text-amber-200">{reason?.code ?? "Reason unavailable"}</span>
                  <p className="mt-1 text-slate-400">
                    {reason?.explanation ?? "No individual impossibility conclusion is inferred."}
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div>
        <h4 className="mb-2 text-xs font-semibold text-slate-300">Objective components (reported separately)</h4>
        <ul className="space-y-2 text-xs">
          {(Object.keys(objectiveLabels) as Array<keyof ScenarioSolverRunResult["objective_components"]>).map((key) => {
            const component = run.objective_components[key];
            return (
              <li key={key} className="rounded border border-slate-800 p-2">
                <span className="font-medium text-slate-200">{objectiveLabels[key]}: {displayComponent(component)}</span>
                <p className="mt-1 text-slate-400">{component.explanation}</p>
              </li>
            );
          })}
        </ul>
      </div>

      {run.solver === "cp_sat" && run.proof_scope && (
        <p className="break-words border-t border-slate-800 pt-2 text-[11px] text-slate-500">
          CP-SAT proof scope: {run.proof_scope}
        </p>
      )}
      {run.solver === "cp_sat" && (
        <p className="border-t border-slate-800 pt-2 text-[11px] text-slate-500">
          CP-SAT proof claims apply only to the exact encoded model and this run&apos;s recorded input digest.
        </p>
      )}
      {run.solver === "baseline" && (
        <p className="border-t border-slate-800 pt-2 text-[11px] text-slate-500">
          Baseline objective optimality is not asserted by this interface.
        </p>
      )}
    </article>
  );
}

function resultExplanation(
  result: ScenarioComparisonResponse,
  scenario: ScenarioRecord | null,
  inputDigest: string | null,
) {
  const baseline = result.baseline;
  const cpSat = result.cp_sat;
  const workOrderIds = scenario?.work_orders.map((order) => order.work_id) ?? [];
  const pairedComplete = isValidatedPairedComparison(
    result,
    scenario
      ? {
          scenarioId: scenario.scenario_id,
          modelVersion: scenario.model_version,
          inputDigest,
          workOrderIds,
        }
      : null,
  );
  const differences = pairedComplete
    ? compareSchedulePlacements(
        workOrderIds,
        baseline.schedule,
        cpSat.schedule,
      )
    : [];
  const changed = differences.filter(
    (item) => item.kind !== "same_placement" && item.kind !== "unscheduled_both",
  );
  const unscheduledBoth = differences
    .filter((item) => item.kind === "unscheduled_both")
    .map((item) => item.workId);
  const unavailable = [
    ...(["baseline", "cp_sat"] as const).flatMap((solver) => {
      const run = result[solver];
      return (Object.keys(objectiveLabels) as Array<keyof ScenarioSolverRunResult["objective_components"]>)
        .filter((key) => !run.objective_components[key].available)
        .map((key) => `${solver === "baseline" ? "Baseline" : "CP-SAT"}: ${objectiveLabels[key]}`);
    }),
  ];
  const countStatement =
    pairedComplete
      ? baseline.scheduled_work_ids.length === cpSat.scheduled_work_ids.length
        ? `Both returned ${baseline.scheduled_work_ids.length} scheduled work orders.`
        : `${baseline.scheduled_work_ids.length > cpSat.scheduled_work_ids.length ? "Baseline" : "CP-SAT"} returned more scheduled work orders (${baseline.scheduled_work_ids.length} vs ${cpSat.scheduled_work_ids.length}); this count alone is not an operational or safety conclusion.`
      : "Scheduled-count comparison is unavailable because at least one solver did not complete.";

  return (
    <section className="space-y-2 rounded-lg border border-slate-700 bg-slate-950/50 p-4">
      <h3 className="font-semibold">Comparison summary</h3>
      <ul className="space-y-1 text-sm text-slate-300">
        <li>Baseline independent validation: {validationLabel(baseline)}.</li>
        <li>CP-SAT independent validation: {validationLabel(cpSat)}.</li>
        <li>{countStatement}</li>
        <li>Maximum coverage proven — baseline: {proofLabel(baseline.coverage_optimality_proven, "Yes")}; CP-SAT: {proofLabel(cpSat.coverage_optimality_proven, "Yes")}.</li>
        <li>Objective optimality proven — baseline: {proofLabel(baseline.objective_optimality_proven, "Yes")}; CP-SAT: {proofLabel(cpSat.objective_optimality_proven, "Yes")}.</li>
        <li>
          Work-order schedule differences: {pairedComplete
            ? changed.length
              ? changed.map((item) => `${item.workId} (${item.kind.replaceAll("_", " ")})`).join(", ")
              : "none returned"
            : "unavailable until both paired runs complete with matching inputs and valid assignments"}
        </li>
        {pairedComplete && <li>Unscheduled by both: {unscheduledBoth.length ? unscheduledBoth.join(", ") : "none"}.</li>}
        <li>Unavailable objective components: {unavailable.length ? unavailable.join("; ") : "none reported unavailable"}.</li>
      </ul>
      <p className="text-xs text-slate-500">
        Components are shown individually. Baseline and CP-SAT may use different objective scaling and proof capabilities; scalar objective values are not compared here.
      </p>
    </section>
  );
}

export default function ScenarioComparisonPanel({
  scenario,
  expectedInputDigest,
  running,
  error,
  result,
  exportRecord,
  exportError,
  onExportRecordCreated,
  onCompare,
}: Props) {
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const pairedResultsAvailable = isValidatedPairedComparison(
    result,
    scenario
      ? {
          scenarioId: scenario.scenario_id,
          modelVersion: scenario.model_version,
          inputDigest: expectedInputDigest,
          workOrderIds: scenario.work_orders.map((order) => order.work_id),
        }
      : null,
  );

  function download(format: ExperimentExportFormat) {
    if (!exportRecord) return;
    setDownloadError(null);
    try {
      const exportedRecord = downloadExperimentExport(exportRecord, format);
      if (exportedRecord !== exportRecord) {
        onExportRecordCreated(exportedRecord);
      }
    } catch (downloadFailure) {
      setDownloadError((downloadFailure as Error).message);
    }
  }

  return (
    <section className="space-y-4 rounded-xl border border-cyan-900/70 bg-slate-900 p-4" aria-label="Experimental scenario comparison">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold">Scenario solver comparison</h2>
          <p className="mt-1 max-w-3xl text-xs text-slate-400">
            Offline, non-operational simulation. This runs the selected browser-local scenario (including any unsaved edits) against the experimental API; it does not change saved scenario storage or assess railway safety.
          </p>
          {scenario && <p className="mt-2 text-sm text-slate-300">Selected scenario: <strong>{scenario.scenario_name}</strong> · {scenario.work_orders.length} work orders</p>}
        </div>
        <button
          type="button"
          onClick={onCompare}
          disabled={!scenario || running}
          className="flex items-center gap-2 rounded bg-cyan-700 px-4 py-2 text-sm font-medium hover:bg-cyan-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Play className="h-4 w-4" />
          {running ? "Comparing…" : "Run comparison"}
        </button>
      </header>

      {!scenario && <p className="rounded border border-slate-700 p-3 text-sm text-slate-400">Create or select a scenario above to compare it.</p>}

      {running && (
        <p role="status" className="rounded border border-cyan-900 bg-cyan-950/30 p-3 text-sm text-cyan-200">
          Running the baseline and CP-SAT solvers on the same scenario input…
        </p>
      )}

      {error && (
        <div role="alert" className={`flex gap-2 rounded border p-3 text-sm ${
          error.kind === "validation"
            ? "border-amber-800 bg-amber-950/40 text-amber-200"
            : error.kind === "unavailable"
              ? "border-amber-800 bg-amber-950/40 text-amber-200"
              : "border-rose-800 bg-rose-950/40 text-rose-200"
        }`}>
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span><strong>{error.kind === "validation" ? "Scenario validation failed" : error.kind === "unavailable" ? "Solver unavailable" : "Comparison failed"}:</strong> {error.message}</span>
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <section aria-label="Reproducible experiment export" className="space-y-2 rounded-lg border border-slate-700 p-4">
            <div>
              <h3 className="font-semibold">Reproducible experiment export</h3>
              <p className="mt-1 text-xs text-slate-400">
                JSON preserves the submitted request and complete paired response. CSV provides one row per work order with separate solver results and objective components. Export does not rerun solvers or change saved scenarios.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => download("json")}
                disabled={!exportRecord}
                className="rounded border border-cyan-800 px-3 py-2 text-sm text-cyan-200 hover:bg-cyan-950/40 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Download JSON
              </button>
              <button
                type="button"
                onClick={() => download("csv")}
                disabled={!exportRecord}
                className="rounded border border-cyan-800 px-3 py-2 text-sm text-cyan-200 hover:bg-cyan-950/40 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Download CSV
              </button>
            </div>
            {exportRecord ? (
              <p className="break-all text-xs text-emerald-300">
                Export ready · schema v{exportRecord.schema_version} · experiment {exportRecord.experiment.experiment_id} · SHA-256 {exportRecord.experiment.canonical_input_digest}
              </p>
            ) : exportError ? (
              <p role="alert" className="text-xs text-amber-200">Export unavailable: {exportError}</p>
            ) : (
              <p className="text-xs text-slate-500">Exports unlock only after the submitted input digest, paired runs, independent validation, and work-order accounting are verified.</p>
            )}
            {downloadError && <p role="alert" className="text-xs text-rose-300">Download failed: {downloadError}</p>}
            <p className="text-[11px] text-slate-500">
              Simulation-only research output; it is not operational authorization or a railway safety determination.
            </p>
          </section>
          <div className={`rounded border p-3 text-sm ${
            pairedResultsAvailable
              ? "border-emerald-900 bg-emerald-950/30 text-emerald-200"
              : "border-amber-800 bg-amber-950/30 text-amber-200"
          }`}>
            Comparison status: <strong>{pairedResultsAvailable ? "Completed paired comparison; both assignments validated" : "Incomplete or unvalidated comparison — not presented as a successful pair"}</strong>
            {!pairedResultsAvailable && (
              <p className="mt-1">
                The scenario identity, input digests, work-order accounting, or independent validation did not pass the paired-result checks.
              </p>
            )}
            <p className="mt-1 break-all font-mono text-xs">Response input digest: {result.input_digest || "Unavailable"}</p>
          </div>
          {result.cp_sat.run_status === "unavailable" && (
            <p role="status" className="rounded border border-amber-800 bg-amber-950/40 p-3 text-sm text-amber-200">
              CP-SAT is unavailable. The baseline output is shown separately; this is not a successful paired comparison.
            </p>
          )}
          <div className="grid gap-4 xl:grid-cols-2">
            <SolverCard run={result.baseline} />
            <SolverCard run={result.cp_sat} />
          </div>
          {resultExplanation(result, scenario, expectedInputDigest)}
          {pairedResultsAvailable ? (
            <section className="space-y-3 rounded-lg border border-slate-700 p-4">
              <div>
                <h3 className="font-semibold">Schedule placement comparison</h3>
                <p className="mt-1 text-xs text-slate-400">
                  Shared bars indicate the same placement. Changed placement, solver-only scheduling, and both-unscheduled cases are labeled by work order.
                </p>
              </div>
              {scenario && (
                <ScenarioComparisonGantt
                  workOrders={scenario.work_orders}
                  baseline={result.baseline}
                  cpSat={result.cp_sat}
                  horizon={scenario.solver_configuration.time_horizon_hrs}
                />
              )}
            </section>
          ) : (
            <p className="text-xs text-slate-500">
              Schedule-difference visualization is unavailable until both solver results complete with matching input digests.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
