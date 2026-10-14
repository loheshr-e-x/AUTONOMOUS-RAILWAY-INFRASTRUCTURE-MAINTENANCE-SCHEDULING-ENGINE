import type { BlockScheduleResponse, SolverRequest, TrainOccupancyWindow } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {}
    throw new Error(`${res.status}: ${typeof detail === "string" ? detail : JSON.stringify(detail)}`);
  }
  return res.json();
}

export const getTrains = () => req<TrainOccupancyWindow[]>("/api/data/trains");
export const getHealth = () => req<{ status: string; engine: string }>("/health");
export const generateSchedule = (body: SolverRequest) =>
  req<BlockScheduleResponse>("/api/schedule/generate", { method: "POST", body: JSON.stringify(body) });
