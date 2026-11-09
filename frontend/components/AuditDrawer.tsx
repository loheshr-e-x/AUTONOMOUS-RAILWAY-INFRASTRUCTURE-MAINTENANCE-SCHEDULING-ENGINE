"use client";
import { CheckCircle2, CircleHelp, XCircle, X } from "lucide-react";
import type { AuditLogEntry, ScheduledBlockAssignment } from "@/lib/types";

interface Props {
  open: boolean;
  onClose: () => void;
  schedule: ScheduledBlockAssignment[];
  audit: AuditLogEntry[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}

// Audit entries have no work_id field; associate them by id mention in the text.
function entriesFor(audit: AuditLogEntry[], id: string) {
  const mentioned = audit.filter((a) => `${a.predicate_evaluated} ${a.explanation} ${a.rule_name}`.includes(id));
  return mentioned.length ? mentioned : [];
}

export default function AuditDrawer({ open, onClose, schedule, audit, selectedId, onSelect }: Props) {
  const sel = schedule.find((s) => s.work_id === selectedId) ?? null;
  const list = sel ? entriesFor(audit, sel.work_id) : audit;
  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-black/50" onClick={onClose} />}
      <aside
        className={`fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col border-l border-slate-800 bg-slate-950 transition-transform ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
        aria-hidden={!open}
      >
        <header className="flex items-center justify-between border-b border-slate-800 p-4">
          <h2 className="font-semibold">FOL Audit Log</h2>
          <button onClick={onClose} aria-label="Close audit log"><X className="h-5 w-5" /></button>
        </header>
        <div className="border-b border-slate-800 p-3">
          <select
            value={selectedId ?? ""}
            onChange={(e) => onSelect(e.target.value || null)}
            className="w-full rounded bg-slate-900 p-2 text-sm"
          >
            <option value="">All rules ({audit.length})</option>
            {schedule.map((s) => (
              <option key={s.work_id} value={s.work_id}>
                {s.work_id} — {s.section_id} {(s.track_line ?? "DOWN_LINE").replace("_", " ")} {s.start_time_hr}–{s.end_time_hr}h
              </option>
            ))}
          </select>
          {sel && (
            <p className="mt-2 text-xs text-slate-400">
              {sel.department} · {sel.section_id} {(sel.track_line ?? "DOWN_LINE").replace("_", " ")} · {
                sel.fol_verified === true
                  ? "FOL verified"
                  : sel.fol_verified === false
                    ? "FOL not verified"
                    : "FOL verification unavailable per assignment"
              }
              {sel.co_located_with?.length ? ` · co-located with ${sel.co_located_with.join(", ")}` : ""}
            </p>
          )}
        </div>
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {list.length === 0 && (
            <p className="text-sm text-slate-500">
              {sel ? "No rule explanations reference this block." : "No audit entries yet."}
            </p>
          )}
          {list.map((a, i) => (
            <div key={i} className="rounded-lg border border-slate-800 bg-slate-900 p-3 text-sm">
              <div className="flex items-center gap-2 font-medium">
                {a.passed === true
                  ? <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  : a.passed === false
                    ? <XCircle className="h-4 w-4 text-rose-400" />
                    : <CircleHelp className="h-4 w-4 text-amber-400" />}
                {a.rule_name}
              </div>
              <code className="mt-2 block overflow-x-auto whitespace-pre-wrap rounded bg-black/40 p-2 text-xs text-cyan-300">
                {a.predicate_evaluated}
              </code>
              <p className="mt-2 text-slate-300">{a.explanation}</p>
            </div>
          ))}
        </div>
      </aside>
    </>
  );
}
