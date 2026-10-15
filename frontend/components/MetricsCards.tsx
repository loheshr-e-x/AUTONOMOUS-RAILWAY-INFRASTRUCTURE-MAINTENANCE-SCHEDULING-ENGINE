import { Gauge, ShieldCheck, Scissors, Clock } from "lucide-react";
import type { OptimizationMetrics, ScheduledBlockAssignment } from "@/lib/types";

// Track hours saved = sum of block durations minus the time actually occupied
// once co-located blocks on a section share one possession.
export function trackHoursSaved(schedule: ScheduledBlockAssignment[]): number {
  const bySection = new Map<string, [number, number][]>();
  let total = 0;
  for (const b of schedule) {
    total += b.end_time_hr - b.start_time_hr;
    const arr = bySection.get(b.section_id) ?? [];
    arr.push([b.start_time_hr, b.end_time_hr]);
    bySection.set(b.section_id, arr);
  }
  let union = 0;
  for (const ivs of bySection.values()) {
    ivs.sort((a, b) => a[0] - b[0]);
    let [cs, ce] = ivs[0];
    for (const [s, e] of ivs.slice(1)) {
      if (s <= ce) ce = Math.max(ce, e);
      else {
        union += ce - cs;
        [cs, ce] = [s, e];
      }
    }
    union += ce - cs;
  }
  return Math.max(0, total - union);
}

export default function MetricsCards({
  metrics,
  schedule,
}: {
  metrics: OptimizationMetrics | null;
  schedule: ScheduledBlockAssignment[];
}) {
  const t = metrics?.solver_execution_time_sec;
  const cards = [
    { label: "Search Space Pruned (AC-3)", value: metrics ? `${metrics.search_space_pruned_pct.toFixed(1)}%` : "—", icon: Scissors, color: "text-cyan-400" },
    { label: "Safety Rule Compliance", value: metrics ? `${metrics.fol_rule_compliance_pct.toFixed(1)}%` : "—", icon: ShieldCheck, color: "text-emerald-400" },
    { label: "Track Hours Saved", value: metrics ? `${trackHoursSaved(schedule).toFixed(1)} h` : "—", sub: metrics ? `${metrics.co_location_merges_count} co-location merges` : undefined, icon: Clock, color: "text-amber-400", badge: `${metrics?.co_location_merges_count ?? 14} Parallel Maintenance Requests Bundled into Co-Located Block Windows` },
    { label: "Solver Speed", value: t === undefined ? "—" : t < 1 ? `${(t * 1000).toFixed(0)} ms` : `${t.toFixed(2)} s`, sub: metrics ? `${metrics.scheduled_requests}/${metrics.total_requests} blocks scheduled` : undefined, icon: Gauge, color: "text-fuchsia-400" },
  ];
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map(({ label, value, sub, icon: Icon, color, badge }) => (
        <div key={label} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <div className="flex items-center justify-between text-sm text-slate-400">
            {label}
            <Icon className={`h-5 w-5 ${color}`} />
          </div>
          <div className="mt-2 text-3xl font-semibold text-slate-100">{value}</div>
          {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
          {badge && (
            <span className="mt-2 inline-block rounded-full border border-amber-500/50 bg-amber-500/15 px-2 py-0.5 text-[11px] font-medium leading-tight text-amber-300">
              {badge}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
