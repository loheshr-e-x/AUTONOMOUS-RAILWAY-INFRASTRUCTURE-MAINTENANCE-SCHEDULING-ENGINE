export type Department = "ENGINEERING" | "SIGNALLING" | "TRACTION";

export type TrackLine = "UP_LINE" | "DOWN_LINE";

export interface TrainOccupancyWindow {
  track_line?: TrackLine;
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
  track_line?: TrackLine;
  heavy_equipment?: boolean;
  power_isolated?: boolean | null;
  co_located_with?: string[] | null;
  fol_verified: boolean | null;
}
export interface AuditLogEntry {
  rule_name: string;
  predicate_evaluated: string;
  passed: boolean | null;
  explanation: string;
}
export interface OptimizationMetrics {
  total_requests: number;
  scheduled_requests: number;
  search_space_pruned_pct: number;
  fol_rule_compliance_pct: number | null;
  co_location_merges_count: number;
  solver_execution_time_sec: number;
}
export interface BlockScheduleResponse {
  status:
    | "success"
    | "partial"
    | "unschedulable"
    | "no_work"
    | "search_limit_reached"
    | "safety_invalid"
    | "safety_unverified";
  solver_outcome:
    | "success"
    | "partial"
    | "unschedulable"
    | "no_work"
    | "search_limit_reached"
    | null;
  schedule: ScheduledBlockAssignment[];
  unscheduled_work_ids: string[];
  metrics: OptimizationMetrics;
  audit_trail: AuditLogEntry[];
}

export type UrgencyLevel = 1 | 2 | 3;

export interface MaintenanceWorkOrder {
  work_id: string;
  department: Department;
  section_id: string;
  track_line?: TrackLine;
  heavy_equipment?: boolean;
  defect_type: string;
  duration_hrs: number;
  urgency: UrgencyLevel;
  co_location_allowed: boolean;
}

export interface RouteInfo {
  route_id: string;
  name: string;
  origin: string;
  destination: string;
  length_km: number;
  section_ids: string[];
  train_windows: number;
}

export interface ScenarioSolverConfiguration {
  section_ids: string[];
  time_horizon_hrs: number;
  slot_duration_hrs: number;
  train_clearance_hrs: number;
  enable_ac3_pruning: boolean;
  enable_simulated_annealing: boolean;
  max_search_nodes: number;
  annealing_iterations: number;
  annealing_initial_temperature: number;
  annealing_cooling_rate: number;
  workload_balance_weight: number;
  co_location_reward: number;
  cpsat_time_limit_seconds: number;
  random_seed: number;
}

export interface ScenarioComparisonRequest {
  scenario_id: string;
  scenario_name?: string | null;
  model_version: string;
  work_orders: MaintenanceWorkOrder[];
  train_windows: TrainOccupancyWindow[];
  solver_configuration: ScenarioSolverConfiguration;
  input_digest?: string | null;
}

export interface ScenarioAssignment {
  work_id: string;
  department: Department;
  section_id: string;
  track_line: TrackLine;
  start_time_hr: number;
  end_time_hr: number;
  co_located_with: string[];
  heavy_equipment: boolean;
}

export interface ScenarioValidationFinding {
  code: string;
  work_order_ids: string[];
  message: string;
}

export interface ScenarioValidationResult {
  valid: boolean;
  findings: ScenarioValidationFinding[];
}

export interface ScenarioObjectiveComponent {
  available: boolean;
  value: number | null;
  explanation: string;
}

export interface ScenarioObjectiveComponents {
  time_of_day_train_gap: ScenarioObjectiveComponent;
  department_workload_imbalance: ScenarioObjectiveComponent;
  co_location_merge_count: ScenarioObjectiveComponent;
  schedule_stability: ScenarioObjectiveComponent;
  utilization: ScenarioObjectiveComponent;
}

export interface UnscheduledWorkReason {
  work_id: string;
  code: string;
  explanation: string;
}

export interface ScenarioSolverRunResult {
  solver: "baseline" | "cp_sat";
  run_status: "completed" | "failed" | "unavailable";
  input_digest: string;
  error_code: string | null;
  error_message: string | null;
  solver_outcome: string | null;
  termination_reason: string | null;
  runtime_seconds: number | null;
  total_work_orders: number;
  scheduled_work_ids: string[];
  unscheduled_work_ids: string[];
  schedule: ScenarioAssignment[];
  validation: ScenarioValidationResult | null;
  objective_components: ScenarioObjectiveComponents;
  solver_feasible_incumbent_found: boolean | null;
  complete_assignment_witness: boolean | null;
  coverage_optimality_proven: boolean | null;
  complete_schedule_proven_infeasible: boolean | null;
  objective_optimality_proven: boolean | null;
  feasibility_not_established: boolean | null;
  search_limit_reached: boolean | null;
  proof_scope: string | null;
  solver_native_objective_value: number | null;
  solver_scaled_objective_value: number | null;
  solver_objective_integer_scale: number | null;
  termination_status: string | null;
  search_branches: number | null;
  search_conflicts: number | null;
  candidate_domain_before_train_filtering: number | null;
  candidate_domain_after_train_filtering: number | null;
  unscheduled_reasons: UnscheduledWorkReason[];
}

export interface ScenarioComparisonResponse {
  scenario_id: string;
  model_version: string;
  input_digest: string;
  comparison_status: "completed" | "incomplete";
  paired_inputs_match: boolean;
  baseline: ScenarioSolverRunResult;
  cp_sat: ScenarioSolverRunResult;
}
