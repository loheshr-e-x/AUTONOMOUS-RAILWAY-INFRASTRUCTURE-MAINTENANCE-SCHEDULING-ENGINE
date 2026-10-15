"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Department, ScheduledBlockAssignment, TrackLine, TrainOccupancyWindow } from "@/lib/types";

export const DEPT_COLOR: Record<Department, string> = {
  ENGINEERING: "bg-sky-500/80 border-sky-300",
  SIGNALLING: "bg-amber-500/80 border-amber-300",
  TRACTION: "bg-rose-500/80 border-rose-300",
};

export const DEPT_BADGE: Record<Department, string> = {
  ENGINEERING: "ENG",
  SIGNALLING: "SIG",
  TRACTION: "TRC",
};

const LINES: TrackLine[] = ["UP_LINE", "DOWN_LINE"];
const MIN_TRAIN_LABEL_PX = 45;
const BLOCK_LANE_H = 22;
const TRAIN_LANE_H = 20;

export const fmtClock = (h: number) => {
  const total = Math.round(h * 60);
  const hh = Math.floor(total / 60) % 24;
  const mm = total % 60;
  return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
};

interface Props {
  trains: TrainOccupancyWindow[];
  schedule: ScheduledBlockAssignment[];
  horizon: number;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

// Greedy lane packing so overlapping (co-located) blocks never draw on top of each other.
function packLanes(blocks: ScheduledBlockAssignment[]) {
  const ends: number[] = [];
  const out: { b: ScheduledBlockAssignment; lane: number }[] = [];
  for (const b of [...blocks].sort((x, y) => x.start_time_hr - y.start_time_hr || x.work_id.localeCompare(y.work_id))) {
    let lane = ends.findIndex((e) => e <= b.start_time_hr);
    if (lane < 0) lane = ends.length;
    ends[lane] = b.end_time_hr;
    out.push({ b, lane });
  }
  return { items: out, lanes: Math.max(ends.length, 1) };
}

interface Tip {
  x: number;
  y: number;
  lines: string[];
}

export default function GanttChart({ trains, schedule, horizon, selectedId, onSelect }: Props) {
  const [tip, setTip] = useState<Tip | null>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const [trackPx, setTrackPx] = useState(0);

  const sections = useMemo(
    () => Array.from(new Set([...trains.map((t) => t.section_id), ...schedule.map((s) => s.section_id)])).sort(),
    [trains, schedule],
  );
  const hasChart = sections.length > 0;

  useEffect(() => {
    const el = trackRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setTrackPx(el.clientWidth));
    setTrackPx(el.clientWidth);
    ro.observe(el);
    return () => ro.disconnect();
  }, [hasChart]);

  const clamp = (h: number) => Math.min(Math.max(h, 0), horizon);
  const pct = (h: number) => `${(clamp(h) / horizon) * 100}%`;
  const span = (s: number, e: number) => Math.max(clamp(e) - clamp(s), 0);
  const width = (s: number, e: number) => `${(span(s, e) / horizon) * 100}%`;
  const px = (s: number, e: number) => (span(s, e) / horizon) * trackPx;
  const ticks = Array.from({ length: Math.floor(horizon / 2) + 1 }, (_, i) => i * 2);

  const showTip = (e: React.MouseEvent, lines: string[]) => setTip({ x: e.clientX, y: e.clientY, lines });

  if (!hasChart)
    return <p className="py-16 text-center text-slate-500">No data yet — generate a schedule to see the timeline.</p>;

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[760px]">
        <div className="flex">
          <div className="w-36 shrink-0" />
          <div className="relative h-6 flex-1 text-xs text-slate-500">
            {ticks.map((h) => (
              <span key={h} className="absolute -translate-x-1/2" style={{ left: pct(h) }}>
                {String(h).padStart(2, "0")}:00
              </span>
            ))}
          </div>
        </div>
        {sections.map((sec, si) => (
          <div key={sec} className="flex border-t border-slate-700">
            <div className="w-36 shrink-0 py-2 pr-2 text-sm font-medium text-slate-300">{sec}</div>
            <div className="flex-1">
              {LINES.map((line, li) => {
                const tr = trains.filter((t) => t.section_id === sec && (t.track_line ?? "DOWN_LINE") === line);
                const bl = schedule.filter((s) => s.section_id === sec && (s.track_line ?? "DOWN_LINE") === line);
                const { items, lanes } = packLanes(bl);
                const height = TRAIN_LANE_H + lanes * BLOCK_LANE_H + 8;
                return (
                  <div
                    key={line}
                    ref={si === 0 && li === 0 ? trackRef : undefined}
                    className={`relative ${li > 0 ? "border-t border-dashed border-slate-800" : ""}`}
                    style={{ height }}
                  >
                    <span className="pointer-events-none absolute left-1 top-0 z-10 rounded bg-slate-950/70 px-1 text-[9px] uppercase tracking-wide text-slate-500">
                      {line === "UP_LINE" ? "Up line" : "Down line"}
                    </span>
                    {ticks.map((h) => (
                      <div key={h} className="absolute top-0 h-full border-l border-slate-800/70" style={{ left: pct(h) }} />
                    ))}
                    {tr.map((t, i) => {
                      const narrow = px(t.start_time_hr, t.end_time_hr) < MIN_TRAIN_LABEL_PX;
                      const detail = `Train ${t.train_no} | Dep: ${fmtClock(t.start_time_hr)} | Arr: ${fmtClock(t.end_time_hr)}`;
                      return (
                        <div
                          key={`${t.train_no}-${i}`}
                          className="absolute flex items-center justify-center overflow-hidden whitespace-nowrap rounded bg-slate-600/80 text-[10px] text-slate-100 hover:bg-slate-500"
                          style={{
                            top: 12,
                            height: TRAIN_LANE_H - 4,
                            left: pct(t.start_time_hr),
                            width: width(t.start_time_hr, t.end_time_hr),
                          }}
                          onMouseEnter={(e) => showTip(e, [detail])}
                          onMouseMove={(e) => showTip(e, [detail])}
                          onMouseLeave={() => setTip(null)}
                        >
                          {!narrow && t.train_no}
                        </div>
                      );
                    })}
                    {items.map(({ b, lane }) => {
                      const detail = [
                        `${b.work_id} · ${b.department}`,
                        `${fmtClock(b.start_time_hr)}–${fmtClock(b.end_time_hr)} · ${line.replace("_", " ")}`,
                        ...(b.co_located_with?.length ? [`Co-located: ${b.co_located_with.join(", ")}`] : []),
                      ];
                      return (
                        <button
                          key={b.work_id}
                          onClick={() => onSelect(b.work_id)}
                          onMouseEnter={(e) => showTip(e, detail)}
                          onMouseMove={(e) => showTip(e, detail)}
                          onMouseLeave={() => setTip(null)}
                          className={`absolute flex items-center gap-1 overflow-hidden whitespace-nowrap rounded border px-1 text-left text-[10px] font-medium text-white transition ${DEPT_COLOR[b.department]} ${
                            selectedId === b.work_id ? "ring-2 ring-white" : ""
                          } ${b.co_located_with?.length ? "bg-[repeating-linear-gradient(45deg,transparent_0_6px,rgba(255,255,255,.18)_6px_12px)]" : ""}`}
                          style={{
                            top: TRAIN_LANE_H + 4 + lane * BLOCK_LANE_H,
                            height: BLOCK_LANE_H - 3,
                            left: pct(b.start_time_hr),
                            width: width(b.start_time_hr, b.end_time_hr),
                          }}
                        >
                          <span className="rounded bg-black/40 px-1 text-[9px] font-bold tracking-wide">{DEPT_BADGE[b.department]}</span>
                          <span className="truncate">{b.work_id}</span>
                        </button>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
        <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-400">
          <Legend c="bg-slate-600" l="Train occupancy" />
          {(Object.keys(DEPT_COLOR) as Department[]).map((d) => (
            <Legend key={d} c={DEPT_COLOR[d].split(" ")[0]} l={`${DEPT_BADGE[d]} = ${d}`} />
          ))}
          <span>Striped = co-located block</span>
        </div>
      </div>
      {tip && (
        <div
          className="pointer-events-none fixed z-50 max-w-xs rounded-md border border-slate-600 bg-slate-950/95 px-2.5 py-1.5 text-xs text-slate-100 shadow-lg"
          style={{ left: tip.x + 12, top: tip.y + 14 }}
        >
          {tip.lines.map((l, i) => (
            <div key={i} className={i === 0 ? "font-semibold" : "text-slate-300"}>
              {l}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const Legend = ({ c, l }: { c: string; l: string }) => (
  <span className="flex items-center gap-1">
    <span className={`inline-block h-3 w-3 rounded ${c}`} />
    {l}
  </span>
);
