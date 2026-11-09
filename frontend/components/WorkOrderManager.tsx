"use client";
import { useState } from "react";
import { X, Plus, Trash2, Pencil, Check } from "lucide-react";
import type { Department, MaintenanceWorkOrder, TrackLine, UrgencyLevel } from "@/lib/types";
import { scenarioWorkOrderDurationError } from "@/lib/scenario-storage";

export interface ManagedOrder {
  order: MaintenanceWorkOrder;
  enabled: boolean;
}

interface Props {
  open: boolean;
  onClose: () => void;
  items: ManagedOrder[];
  onChange: (items: ManagedOrder[]) => void;
  sectionIds: string[];
  customActive: boolean;
  busy: boolean;
  onApply?: () => void;
  onReset?: () => void;
  mode?: "production" | "scenario";
}

const DEPTS: Department[] = ["ENGINEERING", "SIGNALLING", "TRACTION"];
const LINES: TrackLine[] = ["UP_LINE", "DOWN_LINE"];
const PRODUCTION_DURATIONS = [0.5, 1, 1.5, 2, 3, 4];

function blank(sectionIds: string[], existing: ManagedOrder[]): MaintenanceWorkOrder {
  let n = existing.length + 1;
  while (existing.some((m) => m.order.work_id === `WO-CUSTOM-${n}`)) n++;
  return {
    work_id: `WO-CUSTOM-${n}`,
    department: "ENGINEERING",
    section_id: sectionIds[0] ?? "NDLS_CNB_SEC1",
    track_line: "UP_LINE",
    heavy_equipment: false,
    defect_type: "Custom Maintenance",
    duration_hrs: 1,
    urgency: 2,
    co_location_allowed: true,
  };
}

const field = "rounded bg-slate-950 p-1.5 text-xs text-slate-100";

export default function WorkOrderManager({
  open,
  onClose,
  items,
  onChange,
  sectionIds,
  customActive,
  busy,
  onApply,
  onReset,
  mode = "production",
}: Props) {
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState<MaintenanceWorkOrder | null>(null);
  const [isNew, setIsNew] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  if (!open) return null;

  function startEdit(o: MaintenanceWorkOrder) {
    setEditing(o.work_id);
    setDraft({ ...o });
    setIsNew(false);
    setFormError(null);
  }

  function startNew() {
    const o = blank(sectionIds, items);
    setEditing(o.work_id);
    setDraft(o);
    setIsNew(true);
    setFormError(null);
  }

  function save() {
    if (!draft || editing === null) return;
    const id = draft.work_id.trim();
    if (!id) return setFormError("Work order ID is required.");
    if (mode === "scenario") {
      if (draft.work_id !== id) {
        return setFormError("Work order ID must not have leading or trailing whitespace.");
      }
      if (!draft.section_id || draft.section_id !== draft.section_id.trim()) {
        return setFormError("Section ID must be non-empty and trimmed.");
      }
      if (!draft.defect_type || draft.defect_type !== draft.defect_type.trim()) {
        return setFormError("Defect type must be non-empty and trimmed.");
      }
      const durationError = scenarioWorkOrderDurationError(draft.duration_hrs);
      if (durationError) return setFormError(durationError);
    }
    if (items.some((m) => m.order.work_id === id && (isNew || m.order.work_id !== editing)))
      return setFormError(`ID ${id} already exists.`);
    const next = { ...draft, work_id: mode === "scenario" ? draft.work_id : id };
    onChange(isNew ? [...items, { order: next, enabled: true }] : items.map((m) => (m.order.work_id === editing ? { ...m, order: next } : m)));
    setEditing(null);
    setDraft(null);
  }

  const set = <K extends keyof MaintenanceWorkOrder>(k: K, v: MaintenanceWorkOrder[K]) => setDraft((d) => (d ? { ...d, [k]: v } : d));
  const enabledCount = items.filter((m) => m.enabled).length;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={onClose}>
      <aside className="flex h-full w-full max-w-2xl flex-col gap-3 overflow-y-auto border-l border-slate-700 bg-slate-900 p-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Work Order Manager</h2>
          <button onClick={onClose} aria-label="Close"><X className="h-5 w-5" /></button>
        </div>
        <p className="text-xs text-slate-400">
          {mode === "scenario"
            ? "Edit this offline scenario only. Changes do not affect production work orders or invoke a solver."
            : `Create, edit or toggle work orders, then apply them. ${customActive ? "A custom set is active and will be used by the solver." : "Synthetic orders are in use until you apply."}`}
        </p>
        <div className="flex flex-wrap gap-2">
          <button onClick={startNew} className="flex items-center gap-1 rounded bg-cyan-600 px-3 py-1.5 text-sm hover:bg-cyan-500"><Plus className="h-4 w-4" /> New</button>
          {mode === "production" && <>
            <button onClick={onApply} disabled={busy || enabledCount === 0} className="rounded border border-emerald-600 px-3 py-1.5 text-sm text-emerald-300 hover:bg-emerald-950 disabled:opacity-50">
              Apply {enabledCount} enabled
            </button>
            <button onClick={onReset} disabled={busy} className="rounded border border-slate-600 px-3 py-1.5 text-sm hover:bg-slate-800 disabled:opacity-50">Reset to synthetic</button>
          </>}
        </div>

        {draft && (
          <div className="grid grid-cols-2 gap-2 rounded-lg border border-cyan-800 bg-slate-950/60 p-3 text-xs text-slate-400">
            <label className="flex flex-col gap-1">Work order ID<input className={field} value={draft.work_id} onChange={(e) => set("work_id", e.target.value)} /></label>
            <label className="flex flex-col gap-1">Defect<input className={field} value={draft.defect_type} onChange={(e) => set("defect_type", e.target.value)} /></label>
            <label className="flex flex-col gap-1">Department
              <select className={field} value={draft.department} onChange={(e) => set("department", e.target.value as Department)}>{DEPTS.map((d) => <option key={d}>{d}</option>)}</select>
            </label>
            <label className="flex flex-col gap-1">Section
              <select className={field} value={draft.section_id} onChange={(e) => set("section_id", e.target.value)}>{sectionIds.map((s) => <option key={s}>{s}</option>)}</select>
            </label>
            <label className="flex flex-col gap-1">Track line
              <select className={field} value={draft.track_line ?? "UP_LINE"} onChange={(e) => set("track_line", e.target.value as TrackLine)}>{LINES.map((l) => <option key={l}>{l}</option>)}</select>
            </label>
            <label className="flex flex-col gap-1">Duration (hrs)
              {mode === "scenario" ? (
                <input className={field} type="number" min="0.001" max="8" step="0.001" value={draft.duration_hrs} onChange={(e) => set("duration_hrs", Number(e.target.value))} />
              ) : (
                <select className={field} value={draft.duration_hrs} onChange={(e) => set("duration_hrs", Number(e.target.value))}>
                  {PRODUCTION_DURATIONS.map((duration) => <option key={duration} value={duration}>{duration}</option>)}
                </select>
              )}
            </label>
            <label className="flex flex-col gap-1">Urgency
              <select className={field} value={draft.urgency} onChange={(e) => set("urgency", Number(e.target.value) as UrgencyLevel)}>
                {mode === "scenario" ? (
                  <>
                    <option value={1}>1 – Critical</option><option value={2}>2 – Medium</option><option value={3}>3 – Routine</option>
                  </>
                ) : (
                  <>
                    <option value={1}>1 – Low</option><option value={2}>2 – Medium</option><option value={3}>3 – High</option>
                  </>
                )}
              </select>
            </label>
            <div className="flex flex-col justify-end gap-1">
              <label className="flex items-center gap-2"><input type="checkbox" checked={!!draft.heavy_equipment} onChange={(e) => set("heavy_equipment", e.target.checked)} /> Heavy equipment</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={draft.co_location_allowed} onChange={(e) => set("co_location_allowed", e.target.checked)} /> Co-location allowed</label>
            </div>
            {formError && <p className="col-span-2 text-rose-300">{formError}</p>}
            <div className="col-span-2 flex gap-2">
              <button onClick={save} className="flex items-center gap-1 rounded bg-emerald-600 px-3 py-1.5 text-sm text-white hover:bg-emerald-500"><Check className="h-4 w-4" /> Save</button>
              <button onClick={() => { setEditing(null); setDraft(null); }} className="rounded border border-slate-600 px-3 py-1.5 text-sm text-slate-200">Cancel</button>
            </div>
          </div>
        )}

        <ul className="divide-y divide-slate-800 text-sm">
          {items.map((m) => (
            <li key={m.order.work_id} className={`flex items-center gap-3 py-2 ${m.enabled ? "" : "opacity-40"}`}>
              {mode === "production" && <input type="checkbox" checked={m.enabled} aria-label={`Toggle ${m.order.work_id}`}
                onChange={() => onChange(items.map((x) => (x === m ? { ...x, enabled: !x.enabled } : x)))} />}
              <div className="min-w-0 flex-1">
                <div className="font-mono text-xs">{m.order.work_id} · {m.order.department}</div>
                <div className="truncate text-xs text-slate-400">
                  {m.order.section_id} · {m.order.track_line} · {m.order.duration_hrs}h · urgency {m.order.urgency}{m.order.heavy_equipment ? " · heavy" : ""}
                </div>
              </div>
              <button onClick={() => startEdit(m.order)} aria-label="Edit"><Pencil className="h-4 w-4" /></button>
              <button onClick={() => onChange(items.filter((x) => x !== m))} aria-label="Delete"><Trash2 className="h-4 w-4 text-rose-400" /></button>
            </li>
          ))}
          {items.length === 0 && <li className="py-4 text-center text-xs text-slate-500">No work orders. Click New.</li>}
        </ul>
      </aside>
    </div>
  );
}
