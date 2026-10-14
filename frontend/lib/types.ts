export type Department = "ENGINEERING" | "SIGNALLING" | "TRACTION";

export interface TrainOccupancyWindow {
  train_no: string;
  section_id: string;
  start_time_hr: number;
  end_time_hr: number;
}
export interface SolverRequest {
  section_ids: string[];
  time_horizon_hrs: number;
  enable_ac3_pruning: boolean;
  enable_simulated_annealing: boolean;
}
export interface ScheduledBlockAssignment {
  work_id: string;
  department: Department;
  section_id: string;
  start_time_hr: number;
  end_time_hr: number;
  co_located_with?: string[] | null;
  fol_verified: boolean;
}
export interface AuditLogEntry {
  rule_name: string;
  predicate_evaluated: string;
  passed: boolean;
  explanation: string;
}
export interface OptimizationMetrics {
  total_requests: number;
  scheduled_requests: number;
  search_space_pruned_pct: number;
  fol_rule_compliance_pct: number;
  co_location_merges_count: number;
  solver_execution_time_sec: number;
}
export interface BlockScheduleResponse {
  status: string;
  schedule: ScheduledBlockAssignment[];
  metrics: OptimizationMetrics;
  audit_trail: AuditLogEntry[];
}
