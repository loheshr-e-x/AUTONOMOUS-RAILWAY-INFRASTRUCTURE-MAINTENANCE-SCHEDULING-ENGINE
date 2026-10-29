import type { RouteInfo, BlockScheduleResponse, MaintenanceWorkOrder, SolverRequest, TrainOccupancyWindow } from "./types";

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

export const getRoutes = () => req<RouteInfo[]>("/api/data/routes");
export const getTrains = (routeId = "NDLS_CNB") =>
  req<TrainOccupancyWindow[]>(`/api/data/trains?route_id=${encodeURIComponent(routeId)}`);
export const getWorkOrders = (routeId = "NDLS_CNB") =>
  req<MaintenanceWorkOrder[]>(`/api/data/work-orders?route_id=${encodeURIComponent(routeId)}`);
export const setCustomWorkOrders = (orders: MaintenanceWorkOrder[]) =>
  req<MaintenanceWorkOrder[]>("/api/data/work-orders/custom", { method: "POST", body: JSON.stringify(orders) });
export const clearCustomWorkOrders = () => req<{ custom: boolean }>("/api/data/work-orders/custom", { method: "DELETE" });
export const setCustomTrains = (trains: TrainOccupancyWindow[]) =>
  req<TrainOccupancyWindow[]>("/api/data/trains/custom", { method: "POST", body: JSON.stringify(trains) });
export const clearCustomTrains = () => req<{ custom: boolean }>("/api/data/trains/custom", { method: "DELETE" });
export const getHealth = () => req<{ status: string; engine: string }>("/health");
export const generateSchedule = (body: SolverRequest) =>
  req<BlockScheduleResponse>("/api/schedule/generate", { method: "POST", body: JSON.stringify(body) });
