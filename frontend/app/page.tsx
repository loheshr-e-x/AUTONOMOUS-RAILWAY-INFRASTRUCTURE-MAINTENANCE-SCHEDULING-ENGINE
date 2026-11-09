"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { Play, Loader2, ScrollText, AlertTriangle, RefreshCw, ListChecks, Upload } from "lucide-react";
import GanttChart from "@/components/GanttChart";
import MetricsCards from "@/components/MetricsCards";
import AuditDrawer from "@/components/AuditDrawer";
import WorkOrderInspector from "@/components/WorkOrderInspector";
import WorkOrderManager, { type ManagedOrder } from "@/components/WorkOrderManager";
import ScenarioManager from "@/components/ScenarioManager";
import ScenarioComparisonPanel from "@/components/ScenarioComparisonPanel";
import {
  clearCustomTrains, clearCustomWorkOrders, compareScenarios, generateSchedule, getHealth, getRoutes, getTrains, getWorkOrders,
  createScenarioComparisonRequest, ScenarioComparisonError,
  setCustomTrains, setCustomWorkOrders,
} from "@/lib/api";
import type {
  BlockScheduleResponse,
  MaintenanceWorkOrder,
  RouteInfo,
  ScenarioComparisonResponse,
  TrainOccupancyWindow,
} from "@/lib/types";
import {
  createExperimentExportRecord,
  canonicalScenarioInputDigest,
  type ExperimentExportRecord,
} from "@/lib/scenario-export";
import {
  beginComparisonRequest,
  createComparisonRequestTracker,
  finishComparisonRequest,
  invalidateComparisonRequests,
  isCurrentComparisonRequest,
} from "@/lib/scenario-comparison-state";
import {
  createScenario,
  deleteScenario,
  duplicateScenario,
  loadScenarios,
  saveScenarios,
  updateScenario,
  type ScenarioRecord,
} from "@/lib/scenario-storage";

export default function Home() {
  const [trains, setTrains] = useState<TrainOccupancyWindow[]>([]);
  const [result, setResult] = useState<BlockScheduleResponse | null>(null);
  const [sectionsText, setSectionsText] = useState("");
  const [horizon, setHorizon] = useState(24);
  const [ac3, setAc3] = useState(true);
  const [sa, setSa] = useState(true);
  const [loading, setLoading] = useState(false);
  const [online, setOnline] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [drawer, setDrawer] = useState(false);
  const [orders, setOrders] = useState<MaintenanceWorkOrder[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  const [routes, setRoutes] = useState<RouteInfo[]>([]);
  const [routeId, setRouteId] = useState("NDLS_CNB");
  const [managed, setManaged] = useState<ManagedOrder[]>([]);
  const [customActive, setCustomActive] = useState(false);
  const [uploadName, setUploadName] = useState<string | null>(null);
  const [managerOpen, setManagerOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [scenarios, setScenarios] = useState<ScenarioRecord[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
  const [scenarioStorageStatus, setScenarioStorageStatus] = useState<"loading" | "ready" | "error">("loading");
  const [scenarioStorageError, setScenarioStorageError] = useState<string | null>(null);
  const [scenarioSaveError, setScenarioSaveError] = useState<string | null>(null);
  const [scenarioDirty, setScenarioDirty] = useState(false);
  const [scenarioOrdersOpen, setScenarioOrdersOpen] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<ScenarioComparisonResponse | null>(null);
  const [comparisonRequestDigest, setComparisonRequestDigest] = useState<string | null>(null);
  const [comparisonError, setComparisonError] = useState<{ kind: "validation" | "unavailable" | "failed"; message: string } | null>(null);
  const [comparisonRunning, setComparisonRunning] = useState(false);
  const [experimentExportRecord, setExperimentExportRecord] = useState<ExperimentExportRecord | null>(null);
  const [experimentExportError, setExperimentExportError] = useState<string | null>(null);
  const comparisonRequests = useRef(createComparisonRequestTracker());

  function invalidateComparison() {
    invalidateComparisonRequests(comparisonRequests.current);
    setComparisonRunning(false);
    setComparisonResult(null);
    setComparisonRequestDigest(null);
    setComparisonError(null);
    setExperimentExportRecord(null);
    setExperimentExportError(null);
  }

  function reloadScenarios() {
    if (scenarioDirty && !window.confirm("Discard unsaved scenario changes and reload saved data?")) return;
    invalidateComparison();
    setScenarioStorageStatus("loading");
    setScenarioStorageError(null);
    setScenarioSaveError(null);
    try {
      const saved = loadScenarios();
      setScenarios(saved);
      setSelectedScenarioId((current) =>
        saved.some((scenario) => scenario.scenario_id === current)
          ? current
          : saved[0]?.scenario_id ?? null,
      );
      setScenarioDirty(false);
      setScenarioStorageStatus("ready");
    } catch (e) {
      setScenarioStorageError((e as Error).message);
      setScenarioStorageStatus("error");
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(reloadScenarios, 0);
    return () => window.clearTimeout(timer);
  // Load browser-local scenarios once after hydration; manual reload uses the same path.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedScenario = scenarios.find((scenario) => scenario.scenario_id === selectedScenarioId) ?? null;

  function markScenarioChanged(next: ScenarioRecord[]) {
    invalidateComparison();
    setScenarios(next);
    setScenarioDirty(true);
    setScenarioSaveError(null);
  }

  async function createLocalScenario(name: string, sectionIds: string[]) {
    let defaults: MaintenanceWorkOrder[] = [];
    let defaultsError: string | null = null;
    try {
      const routeIds = routes
        .filter((route) => route.section_ids.some((id) => sectionIds.includes(id)))
        .map((route) => route.route_id);
      const fetched = await Promise.all(routeIds.map((id) => getWorkOrders(id)));
      const seen = new Set<string>();
      defaults = fetched.flat().filter((order) => {
        if (!sectionIds.includes(order.section_id) || seen.has(order.work_id)) return false;
        seen.add(order.work_id);
        return true;
      }).map((order) => ({
        work_id: order.work_id,
        department: order.department,
        section_id: order.section_id,
        track_line: order.track_line,
        heavy_equipment: order.heavy_equipment,
        defect_type: order.defect_type,
        duration_hrs: order.duration_hrs,
        urgency: order.urgency,
        co_location_allowed: order.co_location_allowed,
      }));
    } catch (e) {
      defaultsError = `Default work orders could not be loaded; the scenario was created empty. ${(e as Error).message}`;
    }
    try {
      const created = createScenario(name, sectionIds, undefined, defaults);
      markScenarioChanged([...scenarios, created]);
      setSelectedScenarioId(created.scenario_id);
      if (defaultsError) setScenarioSaveError(defaultsError);
    } catch (e) {
      setScenarioSaveError((e as Error).message);
    }
  }

  function duplicateLocalScenario(scenarioId: string, name: string) {
    try {
      const source = scenarios.find((scenario) => scenario.scenario_id === scenarioId);
      if (!source) throw new Error("The selected scenario no longer exists.");
      const duplicate = duplicateScenario(source, name);
      markScenarioChanged([...scenarios, duplicate]);
      setSelectedScenarioId(duplicate.scenario_id);
    } catch (e) {
      setScenarioSaveError((e as Error).message);
    }
  }

  function updateLocalScenario(
    scenarioId: string,
    update: { scenario_name: string; solver_configuration: ScenarioRecord["solver_configuration"] },
  ) {
    try {
      markScenarioChanged(updateScenario(scenarios, scenarioId, (scenario) => ({
        ...scenario,
        ...update,
        input_digest:
          JSON.stringify(scenario.solver_configuration) ===
          JSON.stringify(update.solver_configuration)
            ? scenario.input_digest
            : null,
      })));
    } catch (e) {
      setScenarioSaveError((e as Error).message);
    }
  }

  function deleteLocalScenario(scenarioId: string) {
    const remaining = deleteScenario(scenarios, scenarioId);
    markScenarioChanged(remaining);
    if (selectedScenarioId === scenarioId) {
      setSelectedScenarioId(remaining[0]?.scenario_id ?? null);
      setScenarioOrdersOpen(false);
    }
  }

  function saveLocalScenarios() {
    try {
      saveScenarios(scenarios);
      setScenarioDirty(false);
      setScenarioSaveError(null);
    } catch (e) {
      setScenarioSaveError((e as Error).message);
    }
  }

  function selectScenario(scenarioId: string | null) {
    if (scenarioId !== selectedScenarioId) invalidateComparison();
    setSelectedScenarioId(scenarioId);
  }

  async function runScenarioComparison() {
    if (!selectedScenario) return;
    const requestId = beginComparisonRequest(comparisonRequests.current);
    if (requestId === null) return;
    setComparisonRunning(true);
    setComparisonResult(null);
    setComparisonRequestDigest(null);
    setComparisonError(null);
    setExperimentExportRecord(null);
    setExperimentExportError(null);
    try {
      const request = createScenarioComparisonRequest(selectedScenario);
      const [inputDigest, response] = await Promise.all([
        canonicalScenarioInputDigest(request),
        compareScenarios(request),
      ]);
      if (isCurrentComparisonRequest(comparisonRequests.current, requestId)) {
        setComparisonRequestDigest(inputDigest);
        setComparisonResult(response);
        try {
          const exportRecord = await createExperimentExportRecord(request, response);
          if (isCurrentComparisonRequest(comparisonRequests.current, requestId)) {
            setExperimentExportRecord(exportRecord);
          }
        } catch (exportError) {
          if (isCurrentComparisonRequest(comparisonRequests.current, requestId)) {
            setExperimentExportError((exportError as Error).message);
          }
        }
      }
    } catch (e) {
      if (isCurrentComparisonRequest(comparisonRequests.current, requestId)) {
        setComparisonError({
          kind: e instanceof ScenarioComparisonError ? e.kind : "failed",
          message: (e as Error).message,
        });
      }
    } finally {
      if (finishComparisonRequest(comparisonRequests.current, requestId)) {
        setComparisonRunning(false);
      }
    }
  }

  function changeScenarioOrders(items: ManagedOrder[]) {
    if (!selectedScenario) return;
    try {
      markScenarioChanged(updateScenario(scenarios, selectedScenario.scenario_id, (scenario) => ({
        ...scenario,
        work_orders: items.map((item) => item.order),
        input_digest: null,
      })));
    } catch (e) {
      setScenarioSaveError((e as Error).message);
    }
  }

  const loadRoute = useCallback(async (id: string) => {
    try {
      const [t, o, rs] = await Promise.all([getTrains(id), getWorkOrders(id), getRoutes()]);
      setTrains(t);
      setOrders(o);
      setManaged(o.map((order) => ({ order, enabled: true })));
      setRoutes(rs);
      const route = rs.find((r) => r.route_id === id);
      setSectionsText(route ? route.section_ids.join(", ") : id);
    } catch (e) {
      setError(`Could not load route data: ${(e as Error).message}`);
    }
  }, []);

  useEffect(() => {
    getHealth().then(() => setOnline(true)).catch(() => setOnline(false));
    void Promise.resolve().then(() => loadRoute("NDLS_CNB"));
  }, [loadRoute]);

  async function changeRoute(id: string) {
    setRouteId(id);
    setResult(null);
    setSelected(null);
    setError(null);
    try {
      await Promise.all([clearCustomWorkOrders(), clearCustomTrains()]);
      setCustomActive(false);
      setUploadName(null);
    } catch (e) {
      setError((e as Error).message);
    }
    await loadRoute(id);
  }

  async function applyCustom() {
    setBusy(true);
    setError(null);
    try {
      const enabled = managed.filter((m) => m.enabled).map((m) => m.order);
      await setCustomWorkOrders(enabled);
      setOrders(enabled);
      setCustomActive(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function resetCustom() {
    setBusy(true);
    try {
      await clearCustomWorkOrders();
      setCustomActive(false);
      await loadRoute(routeId);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function uploadTimetable(file: File) {
    setError(null);
    try {
      const parsed = JSON.parse(await file.text());
      if (!Array.isArray(parsed)) throw new Error("Expected a JSON array of train occupancy windows");
      setTrains(await setCustomTrains(parsed as TrainOccupancyWindow[]));
      setUploadName(file.name);
    } catch (e) {
      setError(`Timetable upload failed: ${(e as Error).message}`);
    }
  }

  async function clearUpload() {
    try {
      await clearCustomTrains();
      setUploadName(null);
      await loadRoute(routeId);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const loadTrains = () => loadRoute(routeId);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const section_ids = sectionsText.split(",").map((s) => s.trim()).filter(Boolean);
      const r = await generateSchedule({
        section_ids,
        time_horizon_hrs: horizon,
        enable_ac3_pruning: ac3,
        enable_simulated_annealing: sa,
      });
      setResult(r);
      setOnline(true);
    } catch (e) {
      setError((e as Error).message);
      if (e instanceof TypeError) setOnline(false);
    } finally {
      setLoading(false);
    }
  }

  const schedule = result?.schedule ?? [];
  const selectedBlock = schedule.find((b) => b.work_id === selected) ?? null;
  const selectedOrder = orders.find((o) => o.work_id === selected) ?? null;
  const sectionList = sectionsText.split(",").map((s) => s.trim()).filter(Boolean);
  const visibleTrains = sectionList.length ? trains.filter((t) => sectionList.includes(t.section_id)) : trains;

  return (
    <main className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">AUTONOMOUS RAILWAY INFRASTRUCTURE MAINTENANCE
SCHEDULING ENGINE</h1>
          <p className="text-sm text-slate-400">Symbolic CSP &amp; FOL railway maintenance block scheduling</p>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${online ? "bg-emerald-400" : online === false ? "bg-rose-500" : "bg-slate-500"}`} />
            API {online ? "online" : online === false ? "offline" : "…"}
          </span>
          <button onClick={() => setDrawer(true)} className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 hover:bg-slate-800">
            <ScrollText className="h-4 w-4" /> Audit Log
            {result && <span className="rounded bg-slate-700 px-1.5 text-xs">{result.audit_trail.length}</span>}
          </button>
        </div>
      </header>

      <ScenarioManager
        scenarios={scenarios}
        routes={routes}
        selectedScenarioId={selectedScenarioId}
        storageStatus={scenarioStorageStatus}
        storageError={scenarioStorageError}
        saveError={scenarioSaveError}
        dirty={scenarioDirty}
        onSelect={selectScenario}
        onCreate={createLocalScenario}
        onDuplicate={duplicateLocalScenario}
        onDelete={deleteLocalScenario}
        onUpdate={updateLocalScenario}
        onSave={saveLocalScenarios}
        onReload={reloadScenarios}
        onManageWorkOrders={() => setScenarioOrdersOpen(true)}
      />

      {selectedScenario && (
        <WorkOrderManager
          key={selectedScenario.scenario_id}
          open={scenarioOrdersOpen && scenarioStorageStatus === "ready"}
          onClose={() => setScenarioOrdersOpen(false)}
          items={selectedScenario.work_orders.map((order) => ({ order, enabled: true }))}
          onChange={changeScenarioOrders}
          sectionIds={selectedScenario.solver_configuration.section_ids}
          customActive={false}
          busy={false}
          mode="scenario"
        />
      )}

      <ScenarioComparisonPanel
        scenario={selectedScenario}
        expectedInputDigest={comparisonRequestDigest}
        running={comparisonRunning}
        error={comparisonError}
        result={comparisonResult}
        exportRecord={experimentExportRecord}
        exportError={experimentExportError}
        onExportRecordCreated={setExperimentExportRecord}
        onCompare={() => void runScenarioComparison()}
      />

      <section className="flex flex-wrap items-end gap-4 rounded-xl border border-slate-800 bg-slate-900 p-4">
        <label className="flex w-56 flex-col gap-1 text-xs text-slate-400">
          Corridor
          <select value={routeId} onChange={(e) => void changeRoute(e.target.value)} className="rounded bg-slate-950 p-2 text-sm text-slate-100">
            {(routes.length ? routes : [{ route_id: "NDLS_CNB", name: "NDLS_CNB" } as RouteInfo]).map((r) => (
              <option key={r.route_id} value={r.route_id}>{r.route_id} · {r.name}</option>
            ))}
          </select>
        </label>
        <label className="flex min-w-64 flex-1 flex-col gap-1 text-xs text-slate-400">
          Section IDs (comma separated)
          <input value={sectionsText} onChange={(e) => setSectionsText(e.target.value)} className="rounded bg-slate-950 p-2 text-sm text-slate-100" />
        </label>
        <label className="flex w-28 flex-col gap-1 text-xs text-slate-400">
          Horizon (hrs)
          <input type="number" min={1} max={48} value={horizon} onChange={(e) => setHorizon(Math.max(1, Number(e.target.value) || 24))} className="rounded bg-slate-950 p-2 text-sm text-slate-100" />
        </label>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={ac3} onChange={(e) => setAc3(e.target.checked)} /> AC-3 pruning</label>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={sa} onChange={(e) => setSa(e.target.checked)} /> Simulated annealing</label>
        <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800" title="Upload a JSON array of train occupancy windows">
          <Upload className="h-4 w-4" /> Timetable
          <input type="file" accept="application/json,.json" className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) void uploadTimetable(f); e.target.value = ""; }} />
        </label>
        {uploadName && <button onClick={clearUpload} className="rounded bg-amber-900/50 px-2 py-1 text-xs text-amber-200">{uploadName} ✕</button>}
        <button onClick={() => setManagerOpen(true)} className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800">
          <ListChecks className="h-4 w-4" /> Work Orders
          <span className="rounded bg-slate-700 px-1.5 text-xs">{customActive ? "custom " : ""}{orders.length}</span>
        </button>
        <button onClick={loadTrains} className="rounded-lg border border-slate-700 p-2.5 hover:bg-slate-800" aria-label="Reload trains"><RefreshCw className="h-4 w-4" /></button>
        <button onClick={run} disabled={loading || !sectionList.length} className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 font-medium hover:bg-cyan-500 disabled:opacity-50">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          {loading ? "Solving…" : "Generate Schedule"}
        </button>
      </section>

      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-rose-800 bg-rose-950/50 p-3 text-sm text-rose-200">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /> {error}
        </div>
      )}

      <MetricsCards metrics={result?.metrics ?? null} schedule={schedule} />

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-4">
        <h2 className="mb-3 font-semibold">Time-Space Schedule {result && <span className="text-xs font-normal text-slate-500">· status: {result.status}</span>}</h2>
        <GanttChart trains={visibleTrains} schedule={schedule} horizon={horizon} selectedId={selected} onSelect={setSelected} />
      </section>

      <WorkOrderInspector block={selectedBlock} order={selectedOrder} onSelect={setSelected} />

      <WorkOrderManager open={managerOpen} onClose={() => setManagerOpen(false)} items={managed} onChange={setManaged}
        sectionIds={routes.find((r) => r.route_id === routeId)?.section_ids ?? []} customActive={customActive} busy={busy}
        onApply={applyCustom} onReset={resetCustom} />

      <AuditDrawer open={drawer} onClose={() => setDrawer(false)} schedule={schedule} audit={result?.audit_trail ?? []} selectedId={selected} onSelect={setSelected} />
    </main>
  );
}
