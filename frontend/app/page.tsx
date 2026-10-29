"use client";
import { useCallback, useEffect, useState } from "react";
import { Play, Loader2, ScrollText, AlertTriangle, RefreshCw, ListChecks, Upload } from "lucide-react";
import GanttChart from "@/components/GanttChart";
import MetricsCards from "@/components/MetricsCards";
import AuditDrawer from "@/components/AuditDrawer";
import WorkOrderInspector from "@/components/WorkOrderInspector";
import WorkOrderManager, { type ManagedOrder } from "@/components/WorkOrderManager";
import {
  clearCustomTrains, clearCustomWorkOrders, generateSchedule, getHealth, getRoutes, getTrains, getWorkOrders,
  setCustomTrains, setCustomWorkOrders,
} from "@/lib/api";
import type { BlockScheduleResponse, MaintenanceWorkOrder, RouteInfo, TrainOccupancyWindow } from "@/lib/types";

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
          <h1 className="text-2xl font-bold">SymbIO-Block Dashboard</h1>
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

      <div className="rounded-lg border border-cyan-800/60 bg-cyan-950/30 px-4 py-2 text-sm text-cyan-200">
        Academic Demonstration: Units 1–4 Classical AI (AC-3 CSP + A* Search + FOL Invariants)
      </div>

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
