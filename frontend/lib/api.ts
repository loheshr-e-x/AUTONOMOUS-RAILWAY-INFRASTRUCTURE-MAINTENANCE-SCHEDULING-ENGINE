import type {
  RouteInfo,
  BlockScheduleResponse,
  MaintenanceWorkOrder,
  ScenarioComparisonRequest,
  ScenarioComparisonResponse,
  SolverRequest,
  TrainOccupancyWindow,
} from "./types";
import type { ScenarioRecord } from "./scenario-storage";

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

export type ScenarioComparisonErrorKind = "validation" | "unavailable" | "failed";

export class ScenarioComparisonError extends Error {
  public readonly kind: ScenarioComparisonErrorKind;
  public readonly status: number | null;

  constructor(
    message: string,
    kind: ScenarioComparisonErrorKind,
    status: number | null = null,
  ) {
    super(message);
    this.name = "ScenarioComparisonError";
    this.kind = kind;
    this.status = status;
  }
}

export function createScenarioComparisonRequest(
  scenario: ScenarioRecord,
): ScenarioComparisonRequest {
  return {
    scenario_id: scenario.scenario_id,
    scenario_name: scenario.scenario_name,
    model_version: scenario.model_version,
    work_orders: scenario.work_orders.map((order) => ({ ...order })),
    train_windows: scenario.train_windows.map((window) => ({ ...window })),
    solver_configuration: {
      ...scenario.solver_configuration,
      section_ids: [...scenario.solver_configuration.section_ids],
    },
  };
}

function comparisonErrorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => {
      if (typeof item === "object" && item !== null) {
        const finding = item as { code?: unknown; message?: unknown; loc?: unknown; msg?: unknown };
        const code = typeof finding.code === "string" ? `${finding.code}: ` : "";
        const message =
          typeof finding.message === "string"
            ? finding.message
            : typeof finding.msg === "string"
              ? finding.msg
              : JSON.stringify(item);
        const location = Array.isArray(finding.loc) ? `${finding.loc.join(".")}: ` : "";
        return `${location}${code}${message}`;
      }
      return String(item);
    }).join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return fallback;
}

export async function compareScenarios(
  body: ScenarioComparisonRequest,
): Promise<ScenarioComparisonResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/experimental/scenarios/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (error) {
    throw new ScenarioComparisonError(
      `The experimental comparison request failed: ${(error as Error).message}`,
      "failed",
    );
  }

  if (!response.ok) {
    let detail: unknown = response.statusText;
    try {
      const payload: unknown = await response.json();
      if (typeof payload === "object" && payload !== null && "detail" in payload) {
        detail = (payload as { detail: unknown }).detail;
      }
    } catch {
      detail = response.statusText;
    }
    const kind =
      response.status === 422
        ? "validation"
        : response.status === 503
          ? "unavailable"
          : "failed";
    throw new ScenarioComparisonError(
      comparisonErrorMessage(detail, `Comparison failed with HTTP ${response.status}.`),
      kind,
      response.status,
    );
  }

  try {
    return (await response.json()) as ScenarioComparisonResponse;
  } catch (error) {
    throw new ScenarioComparisonError(
      `The experimental comparison returned an unreadable response: ${(error as Error).message}`,
      "failed",
      response.status,
    );
  }
}
