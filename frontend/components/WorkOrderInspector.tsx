"use client";
import type { MaintenanceWorkOrder, ScheduledBlockAssignment } from "@/lib/types";
import { DEPT_BADGE, DEPT_COLOR, fmtClock } from "@/components/GanttChart";

interface Props {
  block: ScheduledBlockAssignment | null;
  order: MaintenanceWorkOrder | null;
  onSelect: (id: string) => void;
}

const URGENCY: Record<number, { label: string; cls: string }> = {
  1: { label: "Critical", cls: "bg-rose-500/20 text-rose-300 border-rose-500/50" },
  2: { label: "Medium", cls: "bg-amber-500/20 text-amber-300 border-amber-500/50" },
  3: { label: "Routine", cls: "bg-emerald-500/20 text-emerald-300 border-emerald-500/50" },
};

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm text-slate-100">{children}</dd>
    </div>
  );
}

const Flag = ({ on, label }: { on: boolean | undefined; label: string }) => (
  <span
    className={`rounded border px-2 py-0.5 text-xs ${
      on ? "border-cyan-500/50 bg-cyan-500/15 text-cyan-300" : "border-slate-700 text-slate-500"
    }`}
  >
    {label}: {on ? "Yes" : "No"}
  </span>
);

export default function WorkOrderInspector({ block, order, onSelect }: Props) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-4" aria-live="polite">
      <h2 className="mb-3 font-semibold">Work Order Inspection</h2>
      {!block ? (
        <p className="py-6 text-center text-sm text-slate-500">Click a maintenance block on the Gantt chart to inspect its work order.</p>
      ) : (
        <dl className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
          <Field label="Work Order ID">
            <span className="font-mono">{block.work_id}</span>
          </Field>
          <Field label="Department">
            <span className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-xs font-medium text-white ${DEPT_COLOR[block.department]}`}>
              {DEPT_BADGE[block.department]} · {block.department}
            </span>
          </Field>
          <Field label="Section & Track Line">
            {block.section_id} · {(block.track_line ?? "DOWN_LINE").replace("_", " ")}
          </Field>
          <Field label="Duration">
            {(block.end_time_hr - block.start_time_hr).toFixed(1)} h
            <span className="block text-xs text-slate-400">
              {fmtClock(block.start_time_hr)}–{fmtClock(block.end_time_hr)}
            </span>
          </Field>
          <Field label="Urgency Level">
            {order ? (
              <span className={`rounded border px-2 py-0.5 text-xs ${URGENCY[order.urgency]?.cls ?? ""}`}>
                {URGENCY[order.urgency]?.label ?? order.urgency}
              </span>
            ) : (
              <span className="text-slate-500">n/a</span>
            )}
          </Field>
          <Field label="Equipment Type">
            <div className="flex flex-wrap gap-1">
              <Flag on={block.heavy_equipment} label="Heavy equipment" />
              <Flag on={block.power_isolated} label="Power isolated" />
            </div>
          </Field>
          <div className="col-span-2 md:col-span-3 xl:col-span-6">
            <dt className="text-xs uppercase tracking-wide text-slate-500">Co-located Work Orders</dt>
            <dd className="mt-1 flex flex-wrap gap-2 text-sm">
              {block.co_located_with?.length ? (
                block.co_located_with.map((id) => (
                  <button key={id} onClick={() => onSelect(id)} className="rounded border border-slate-700 px-2 py-0.5 font-mono text-xs hover:bg-slate-800">
                    {id}
                  </button>
                ))
              ) : (
                <span className="text-slate-500">None — standalone block</span>
              )}
            </dd>
            {order && <p className="mt-2 text-xs text-slate-400">Defect: {order.defect_type}</p>}
          </div>
        </dl>
      )}
    </section>
  );
}
