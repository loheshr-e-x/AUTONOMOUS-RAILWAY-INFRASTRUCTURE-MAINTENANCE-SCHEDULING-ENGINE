import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createScenarioComparisonRequest } from "../lib/api.ts";
import { createScenario } from "../lib/scenario-storage.ts";
import {
  canonicalScenarioInputDigest,
  createExperimentExportRecord,
  downloadExperimentExport,
  experimentRecordToCsv,
  stableJsonStringify,
} from "../lib/scenario-export.ts";

const digestFixtures = JSON.parse(readFileSync(
  new URL("../../backend/tests/fixtures/task16-canonical-digest.json", import.meta.url),
  "utf8",
));

const objectiveComponents = {
  time_of_day_train_gap: { available: true, value: 1.25, explanation: "Train-gap component." },
  department_workload_imbalance: { available: true, value: 0.5, explanation: "Workload component." },
  co_location_merge_count: { available: true, value: 1, explanation: "Merge component." },
  schedule_stability: { available: false, value: null, explanation: "Not supplied." },
  utilization: { available: false, value: null, explanation: "Not supplied." },
};

function assignment(workId, start, end = start + 1.75) {
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

function workOrder(workId, sectionId = "S1") {
  return {
    work_id: workId,
    department: "ENGINEERING",
    section_id: sectionId,
    track_line: "UP_LINE",
    heavy_equipment: false,
    defect_type: "Synthetic inspection",
    duration_hrs: 1.75,
    urgency: 2,
    co_location_allowed: true,
  };
}

function solverRun(solver, digest, assignments, unscheduledIds, unscheduledReasons) {
  return {
    solver,
    run_status: "completed",
    input_digest: digest,
    error_code: null,
    error_message: null,
    solver_outcome: "FEASIBLE",
    termination_reason: "search_exhausted",
    runtime_seconds: 0.125,
    total_work_orders: 3,
    scheduled_work_ids: assignments.map((item) => item.work_id),
    unscheduled_work_ids: unscheduledIds,
    schedule: assignments,
    validation: { valid: true, findings: [] },
    objective_components: structuredClone(objectiveComponents),
    solver_feasible_incumbent_found: true,
    complete_assignment_witness: false,
    coverage_optimality_proven: solver === "cp_sat",
    complete_schedule_proven_infeasible: null,
    objective_optimality_proven: false,
    feasibility_not_established: false,
    search_limit_reached: false,
    proof_scope: solver === "cp_sat" ? "encoded model" : null,
    solver_native_objective_value: 17.5,
    solver_scaled_objective_value: solver === "cp_sat" ? 175 : null,
    solver_objective_integer_scale: solver === "cp_sat" ? 10 : null,
    termination_status: "OPTIMAL",
    search_branches: 4,
    search_conflicts: 0,
    candidate_domain_before_train_filtering: 24,
    candidate_domain_after_train_filtering: 24,
    unscheduled_reasons: unscheduledReasons,
  };
}

async function fixture() {
  const scenario = createScenario('Research, "paired"\nfixture', ["S1"], "scenario-export");
  scenario.work_orders = ["SIM-WO-1", "SIM-WO-2", "SIM-WO-3"].map((id) => workOrder(id));
  const request = createScenarioComparisonRequest(scenario);
  const digest = await canonicalScenarioInputDigest(request);
  const baselineSchedule = [
    assignment("SIM-WO-1", 0),
    assignment("SIM-WO-2", 2),
  ];
  const cpSatSchedule = [
    assignment("SIM-WO-1", 0),
    assignment("SIM-WO-3", 4),
  ];
  const response = {
    scenario_id: request.scenario_id,
    model_version: request.model_version,
    input_digest: digest,
    comparison_status: "completed",
    paired_inputs_match: true,
    baseline: solverRun(
      "baseline",
      digest,
      baselineSchedule,
      ["SIM-WO-3"],
      [{ work_id: "SIM-WO-3", code: "SEARCH_LIMIT_NO_CONCLUSION", explanation: "Synthetic reason." }],
    ),
    cp_sat: solverRun(
      "cp_sat",
      digest,
      cpSatSchedule,
      ["SIM-WO-2"],
      [{ work_id: "SIM-WO-2", code: "OMITTED_FROM_MAX_COVERAGE_INCUMBENT", explanation: "Synthetic reason." }],
    ),
  };
  return { request, response, digest };
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') {
        value += '"';
        index += 1;
      } else if (character === '"') {
        quoted = false;
      } else {
        value += character;
      }
    } else if (character === '"' && value.length === 0) {
      quoted = true;
    } else if (character === ",") {
      row.push(value);
      value = "";
    } else if (character === "\r" && text[index + 1] === "\n") {
      row.push(value);
      rows.push(row);
      row = [];
      value = "";
      index += 1;
    } else {
      value += character;
    }
  }
  assert.equal(quoted, false, "CSV must close every quoted cell");
  return rows;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function setPath(target, path, value) {
  let current = target;
  for (const part of path.slice(0, -1)) current = current[part];
  current[path.at(-1)] = value === "reverse"
    ? [...current[path.at(-1)]].reverse()
    : value;
}

function reverseObjectKeys(value) {
  if (Array.isArray(value)) return value.map(reverseObjectKeys);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).reverse().map(([key, item]) => [key, reverseObjectKeys(item)]),
    );
  }
  return value;
}

function fixtureDigestRequests() {
  const baseline = digestFixtures.baseline;
  const requests = digestFixtures.cases.map(({ request }) => clone(request));
  requests.push(clone(digestFixtures.default_equivalent_request));
  requests.push(reverseObjectKeys(baseline));
  requests.push({ ...clone(baseline), ...digestFixtures.irrelevant_metadata });
  for (const mutation of digestFixtures.digest_mutations) {
    const request = clone(baseline);
    setPath(request, mutation.path, mutation.value);
    requests.push(request);
  }
  return requests;
}

test("shared Python/JavaScript canonical digest fixtures produce deterministic hashes", async () => {
  const requests = fixtureDigestRequests();
  const digests = await Promise.all(requests.map(canonicalScenarioInputDigest));

  assert.equal(digests.length, digestFixtures.cases.length + digestFixtures.digest_mutations.length + 3);
  assert.ok(digests.every((digest) => /^[0-9a-f]{64}$/.test(digest)));
  assert.equal(
    digests[0],
    await canonicalScenarioInputDigest(digestFixtures.cases[0].request),
  );
});

test("every digest-relevant shared fixture mutation changes the digest", async () => {
  const baselineDigest = await canonicalScenarioInputDigest(digestFixtures.baseline);

  for (const mutation of digestFixtures.digest_mutations) {
    const changed = clone(digestFixtures.baseline);
    setPath(changed, mutation.path, mutation.value);
    assert.notEqual(
      await canonicalScenarioInputDigest(changed),
      baselineDigest,
      `digest did not change for ${mutation.name}`,
    );
  }
});

test("irrelevant metadata, object key order, and explicit defaults do not change the digest", async () => {
  const baselineDigest = await canonicalScenarioInputDigest(digestFixtures.baseline);

  assert.equal(
    await canonicalScenarioInputDigest({
      ...clone(digestFixtures.baseline),
      ...digestFixtures.irrelevant_metadata,
    }),
    baselineDigest,
  );
  assert.equal(
    await canonicalScenarioInputDigest(reverseObjectKeys(digestFixtures.baseline)),
    baselineDigest,
  );
  assert.equal(
    await canonicalScenarioInputDigest(digestFixtures.cases[2].request),
    await canonicalScenarioInputDigest(digestFixtures.default_equivalent_request),
  );
});

test("eligible results create a versioned JSON record with stable experiment identity", async () => {
  const { request, response, digest } = await fixture();
  const metadata = { experimentId: "experiment-fixed", exportedAtUtc: "2026-02-03T04:05:06.000Z" };
  const record = await createExperimentExportRecord(request, response, metadata);
  const json = stableJsonStringify(record);

  assert.equal(record.format, "symbio-block-experiment");
  assert.equal(record.schema_version, 1);
  assert.equal(record.experiment.experiment_id, metadata.experimentId);
  assert.equal(record.experiment.exported_at_utc, metadata.exportedAtUtc);
  assert.equal(record.experiment.canonical_input_digest, digest);
  assert.deepEqual(JSON.parse(json), record);
  assert.equal(stableJsonStringify(record), json);
  assert.deepEqual(record.submitted_request, request);
  assert.deepEqual(record.comparison, response);
  assert.deepEqual(
    record.schedule_differences.map((item) => [item.work_order_id, item.classification]),
    [
      ["SIM-WO-1", "same_placement"],
      ["SIM-WO-2", "baseline_only"],
      ["SIM-WO-3", "cp_sat_only"],
    ],
  );
});

test("CSV has one row per work order and keeps solver proof, reasons, and components separate", async () => {
  const { request, response } = await fixture();
  const record = await createExperimentExportRecord(request, response, {
    experimentId: "experiment-csv",
    exportedAtUtc: "2026-02-03T04:05:06.000Z",
  });
  const rows = parseCsv(experimentRecordToCsv(record));
  const header = rows[0];
  const data = rows.slice(1);
  const field = (row, name) => row[header.indexOf(name)];

  assert.equal(data.length, 3);
  assert.equal(field(data[0], "experiment_id"), "experiment-csv");
  assert.equal(field(data[0], "work_order_id"), "SIM-WO-1");
  assert.equal(field(data[0], "submitted_defect_type"), "Synthetic inspection");
  assert.equal(field(data[0], "baseline_input_digest"), record.experiment.canonical_input_digest);
  assert.equal(field(data[0], "cp_sat_input_digest"), record.experiment.canonical_input_digest);
  assert.equal(field(data[0], "baseline_total_work_orders"), "3");
  assert.equal(field(data[0], "baseline_scheduled_count"), "2");
  assert.equal(field(data[0], "cp_sat_scheduled_count"), "2");
  assert.equal(field(data[1], "schedule_difference"), "baseline_only");
  assert.equal(field(data[1], "baseline_unscheduled_reason_code"), "");
  assert.equal(field(data[1], "cp_sat_unscheduled_reason_code"), "OMITTED_FROM_MAX_COVERAGE_INCUMBENT");
  assert.equal(field(data[2], "baseline_unscheduled_reason_code"), "SEARCH_LIMIT_NO_CONCLUSION");
  assert.equal(field(data[0], "baseline_coverage_optimality_proven"), "false");
  assert.equal(field(data[0], "cp_sat_coverage_optimality_proven"), "true");
  assert.equal(field(data[0], "baseline_time_of_day_train_gap_value"), "1.25");
  assert.equal(field(data[0], "baseline_schedule_stability_available"), "false");
  assert.equal(field(data[0], "baseline_schedule_stability_value"), "");
  assert.equal(header.some((column) => column.includes("native_objective_value")), false);
  assert.equal(field(data[0], "scenario_name"), 'Research, "paired"\nfixture');
});

test("exports reject digest mismatch, incomplete runs, invalid assignments, and inconsistent accounting", async () => {
  const { request, response, digest } = await fixture();

  const changedRequest = structuredClone(request);
  changedRequest.work_orders[0].duration_hrs += 0.25;
  await assert.rejects(
    createExperimentExportRecord(changedRequest, response),
    /input digest does not match the submitted scenario/,
  );
  await assert.rejects(
    createExperimentExportRecord(request, { ...response, input_digest: "0".repeat(64) }),
    /input digest does not match/,
  );
  await assert.rejects(
    createExperimentExportRecord(request, {
      ...response,
      comparison_status: "incomplete",
    }),
    /Only completed comparisons/,
  );
  await assert.rejects(
    createExperimentExportRecord(request, {
      ...response,
      cp_sat: { ...response.cp_sat, run_status: "unavailable" },
    }),
    /cp_sat did not return a completed solver run/,
  );
  await assert.rejects(
    createExperimentExportRecord(request, {
      ...response,
      baseline: { ...response.baseline, run_status: "failed" },
    }),
    /baseline did not return a completed solver run/,
  );
  await assert.rejects(
    createExperimentExportRecord(request, {
      ...response,
      baseline: { ...response.baseline, validation: { valid: false, findings: [] } },
    }),
    /did not pass independent validation/,
  );
  await assert.rejects(
    createExperimentExportRecord(request, {
      ...response,
      cp_sat: { ...response.cp_sat, input_digest: "0".repeat(64) },
    }),
    /input digest does not match the submitted scenario/,
  );
  await assert.rejects(
    createExperimentExportRecord(request, {
      ...response,
      baseline: { ...response.baseline, input_digest: "0".repeat(64) },
    }),
    /input digest does not match the submitted scenario/,
  );
  await assert.rejects(
    createExperimentExportRecord(request, {
      ...response,
      baseline: { ...response.baseline, unscheduled_work_ids: [] },
    }),
    /accounting is incomplete or inconsistent/,
  );
  await assert.rejects(
    createExperimentExportRecord(request, {
      ...response,
      baseline: {
        ...response.baseline,
        scheduled_work_ids: [...response.baseline.scheduled_work_ids, "SIM-WO-1"],
      },
    }),
    /accounting is incomplete or inconsistent/,
  );
  await assert.rejects(
    createExperimentExportRecord(request, {
      ...response,
      cp_sat: {
        ...response.cp_sat,
        unscheduled_work_ids: [...response.cp_sat.unscheduled_work_ids, "SIM-WO-2"],
      },
    }),
    /accounting is incomplete or inconsistent/,
  );
  await assert.rejects(
    createExperimentExportRecord(request, {
      ...response,
      cp_sat: {
        ...response.cp_sat,
        schedule: response.cp_sat.schedule.slice(1),
      },
    }),
    /accounting is incomplete or inconsistent/,
  );
  assert.equal(response.input_digest, digest);
});

test("repeated JSON and CSV downloads reuse identity and timestamp without comparison or storage writes", async () => {
  const { request, response } = await fixture();
  const sourceRecord = await createExperimentExportRecord(request, response, {
    experimentId: "experiment-repeated",
  });
  const originalDocument = globalThis.document;
  const originalWindow = globalThis.window;
  const originalCreateObjectUrl = URL.createObjectURL;
  const originalRevokeObjectUrl = URL.revokeObjectURL;
  const originalFetch = globalThis.fetch;
  const storage = new Map([["scenarios", "saved-snapshot"]]);
  const downloads = [];
  const objectUrls = new Map();
  let urlIndex = 0;
  let solverRequests = 0;

  globalThis.document = {
    body: { append() {} },
    createElement() {
      return {
        href: "",
        download: "",
        hidden: false,
        click() {
          downloads.push({ filename: this.download, blob: objectUrls.get(this.href) });
        },
        remove() {},
      };
    },
  };
  globalThis.window = { setTimeout(callback) { callback(); } };
  URL.createObjectURL = (blob) => {
    const url = `blob:test-${urlIndex++}`;
    objectUrls.set(url, blob);
    return url;
  };
  URL.revokeObjectURL = () => {};
  globalThis.fetch = async () => {
    solverRequests += 1;
    throw new Error("Export must not call fetch.");
  };

  try {
    const jsonRecord = downloadExperimentExport(sourceRecord, "json");
    const csvRecord = downloadExperimentExport(jsonRecord, "csv");

    assert.equal(downloads.length, 2);
    assert.match(downloads[0].filename, /\.json$/);
    assert.match(downloads[1].filename, /\.csv$/);
    assert.equal(downloads[0].blob.type, "application/json;charset=utf-8");
    assert.equal(downloads[1].blob.type, "text/csv;charset=utf-8");
    assert.equal(jsonRecord.experiment.experiment_id, "experiment-repeated");
    assert.equal(csvRecord.experiment.experiment_id, jsonRecord.experiment.experiment_id);
    assert.ok(jsonRecord.experiment.exported_at_utc);
    assert.equal(csvRecord.experiment.exported_at_utc, jsonRecord.experiment.exported_at_utc);
    assert.equal(JSON.parse(await downloads[0].blob.text()).experiment.exported_at_utc, jsonRecord.experiment.exported_at_utc);
    assert.equal(solverRequests, 0);
    assert.deepEqual([...storage], [["scenarios", "saved-snapshot"]]);
  } finally {
    globalThis.document = originalDocument;
    globalThis.window = originalWindow;
    URL.createObjectURL = originalCreateObjectUrl;
    URL.revokeObjectURL = originalRevokeObjectUrl;
    globalThis.fetch = originalFetch;
  }
});
