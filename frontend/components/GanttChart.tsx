"use client";
import { useMemo, useState } from "react";
import type { Department, ScheduledBlockAssignment, TrainOccupancyWindow } from "@/lib/types";

export const DEPT_COLOR: Record<Department, string> = {
  ENGINEERING: "bg-sky-500/80 border-sky-300",
  SIGNALLING: "bg-amber-500/80 border-amber-300",
  TRACTION: "bg-rose-500/80 border-rose-300",
};

interface Props {
  trains: TrainOccupancyWindow[];
  schedule: ScheduledBlockAssignment[];
  horizon: number;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function GanttChart({ trains, schedule, horizon, selectedId, onSelect }: Props) {
  const [hover, setHover] = useState<string | null>(null);
  const sections = useMemo(
    () => Array.from(new Set([...trains.map((t) => t.section_id), ...schedule.map((s) => s.section_id)])).sort(),
    [trains, schedule],
  );
  const pct = (h: number) => `${(Math.min(Math.max(h, 0), horizon) / horizon) * 100}%`;
  const width = (s: number, e: number) => `${(Math.max(Math.min(e, horizon) - Math.max(s, 0), 0) / horizon) * 100}%`;
  const ticks = Array.from({ length: Math.floor(horizon / 2) + 1 }, (_, i) => i * 2);

  if (!sections.length)
    return <p className="py-16 text-center text-slate-500">No data yet — generate a schedule to see the timeline.</p>;

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[760px]">
        <div className="flex">
          <div className="w-28 shrink-0" />
          <div className="relative h-6 flex-1 text-xs text-slate-500">
            {ticks.map((h) => (
              <span key={h} className="absolute -translate-x-1/2" style={{ left: pct(h) }}>
                {String(h).padStart(2, "0")}:00
              </span>
            ))}
          </div>
        </div>
        {sections.map((sec) => {
          const tr = trains.filter((t) => t.section_id === sec);
          const bl = schedule.filter((s) => s.section_id === sec);
          return (
            <div key={sec} className="flex border-t border-slate-800">
              <div className="w-28 shrink-0 py-2 pr-2 text-sm font-medium text-slate-300">{sec}</div>
              <div className="relative flex-1">
                {ticks.map((h) => (
                  <div key={h} className="absolute top-0 h-full border-l border-slate-800/70" style={{ left: pct(h) }} />
                ))}
                <div className="relative h-7 my-1" title="Train occupancy corridors">
                  {tr.map((t, i) => (
                    <div
                      key={i}
                      className="absolute top-0 flex h-full items-center overflow-hidden rounded bg-slate-600/80 px-1 text-[10px] text-slate-100"
                      style={{ left: pct(t.start_time_hr), width: width(t.start_time_hr, t.end_time_hr) }}
                      title={`Train ${t.train_no}: ${t.start_time_hr}–${t.end_time_hr}h`}
                    >
                      {t.train_no}
                    </div>
                  ))}
                </div>
                <div className="relative h-8 mb-1">
                  {bl.map((b) => (
                    <button
                      key={b.work_id}
                      onClick={() => onSelect(b.work_id)}
                      onMouseEnter={() => setHover(b.work_id)}
                      onMouseLeave={() => setHover(null)}
                      className={`absolute top-0 h-full overflow-hidden rounded border px-1 text-left text-[10px] font-medium text-white transition ${DEPT_COLOR[b.department]} ${
                        selectedId === b.work_id ? "ring-2 ring-white" : ""
                      } ${b.co_located_with?.length ? "bg-[repeating-linear-gradient(45deg,transparent_0_6px,rgba(255,255,255,.18)_6px_12px)]" : ""}`}
                      style={{ left: pct(b.start_time_hr), width: width(b.start_time_hr, b.end_time_hr) }}
                    >
                      {b.work_id}
                      {hover === b.work_id && (
                        <span className="pointer-events-none fixed z-50 mt-8 rounded bg-black px-2 py-1 text-xs shadow">
                          {b.work_id} · {b.department} · {b.start_time_hr}–{b.end_time_hr}h
                          {b.co_located_with?.length ? ` · with ${b.co_located_with.join(", ")}` : ""}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
        <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-400">
          <Legend c="bg-slate-600" l="Train occupancy" />
          {(Object.keys(DEPT_COLOR) as Department[]).map((d) => (
            <Legend key={d} c={DEPT_COLOR[d].split(" ")[0]} l={d} />
          ))}
          <span>Striped = co-located block</span>
        </div>
      </div>
    </div>
  );
}

const Legend = ({ c, l }: { c: string; l: string }) => (
  <span className="flex items-center gap-1">
    <span className={`inline-block h-3 w-3 rounded ${c}`} />
    {l}
  </span>
);
