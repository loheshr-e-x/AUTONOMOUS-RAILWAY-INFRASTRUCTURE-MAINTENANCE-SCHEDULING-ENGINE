"""Stateless paired solver orchestration for offline scenario comparisons."""

from __future__ import annotations

import copy
import time
from typing import Any

from pydantic import ValidationError

from . import cpsat_solver
from .scenario_metrics import evaluate_objective_components
from .scenario_validation import (
    candidate_start_count,
    canonical_scenario_digest,
    validate_scenario_input,
    validate_schedule,
)
from .schemas.scenario_contracts import (
    ObjectiveComponent,
    ScenarioAssignment,
    ScenarioComparisonRequest,
    ScenarioComparisonResponse,
    ScenarioObjectiveComponents,
    SolverRunResult,
    UnscheduledWorkReason,
    ValidationFinding,
)
from .solver_engine import solve_maintenance_schedule


class ScenarioInputError(ValueError):
    def __init__(self, findings: list[ValidationFinding]):
        self.findings = findings
        super().__init__("Scenario input failed validation.")


def _unavailable_components(message: str) -> ScenarioObjectiveComponents:
    unavailable = ObjectiveComponent(
        available=False,
        value=None,
        explanation=message,
    )
    return ScenarioObjectiveComponents(
        time_of_day_train_gap=unavailable,
        department_workload_imbalance=unavailable,
        co_location_merge_count=unavailable,
        schedule_stability=ObjectiveComponent(
            available=False,
            value=None,
            explanation="The current model has no schedule-stability objective component.",
        ),
        utilization=ObjectiveComponent(
            available=False,
            value=None,
            explanation="The current model has no utilization objective component.",
        ),
    )


def _solver_inputs(scenario: ScenarioComparisonRequest) -> tuple[list[dict], list[dict]]:
    return (
        [order.model_dump(mode="json") for order in scenario.work_orders],
        [train.model_dump(mode="json") for train in scenario.train_windows],
    )


def _unscheduled_reasons(
    scenario: ScenarioComparisonRequest,
    unscheduled_ids: list[str],
    validation_valid: bool,
    coverage_proven: bool,
    complete_infeasibility_proven: bool,
    search_limit_reached: bool,
) -> list[UnscheduledWorkReason]:
    reasons = []
    for work_id in unscheduled_ids:
        if not validation_valid:
            code = "UNCLASSIFIED_INVALID_SOLVER_RESULT"
            explanation = (
                "The returned schedule failed independent validation; no individual "
                "cause is inferred."
            )
        elif candidate_start_count(scenario, work_id) == 0:
            code = "NO_CANDIDATE_START_UNDER_MODEL"
            explanation = (
                "Independent candidate generation found no start after the encoded "
                "horizon and listed-train filters."
            )
        elif complete_infeasibility_proven:
            code = "GLOBAL_COMPLETE_SCHEDULE_INFEASIBILITY_PROVEN"
            explanation = (
                "The solver proved that the complete encoded instance has no full "
                "assignment. This does not prove that this individual work order is "
                "impossible in isolation."
            )
        elif coverage_proven:
            code = "OMITTED_FROM_PROVEN_MAXIMUM_COVERAGE"
            explanation = (
                "This order is omitted from a solver-proven maximum-coverage result; "
                "the proof does not identify an individual impossibility."
            )
        elif search_limit_reached:
            code = "NOT_SCHEDULED_BEFORE_SEARCH_LIMIT"
            explanation = (
                "The solver reached a search limit without establishing whether more "
                "work could be scheduled."
            )
        else:
            code = "UNCLASSIFIED_UNSCHEDULED"
            explanation = (
                "The solver did not schedule this order; no individual infeasibility "
                "claim is available."
            )
        reasons.append(
            UnscheduledWorkReason(
                work_id=work_id,
                code=code,
                explanation=explanation,
            )
        )
    return reasons


def _run_solver(
    solver_name: str,
    solver_function: Any,
    scenario: ScenarioComparisonRequest,
    input_digest: str,
    work_orders: list[dict],
    train_windows: list[dict],
) -> SolverRunResult:
    submitted_ids = [order.work_id for order in scenario.work_orders]
    solver_config = scenario.solver_configuration.model_dump(mode="json")
    solver_config["scenario_input_digest"] = input_digest
    started_at = time.perf_counter()
    try:
        raw_result = solver_function(
            copy.deepcopy(work_orders),
            copy.deepcopy(train_windows),
            copy.deepcopy(solver_config),
        )
    except RuntimeError as exc:
        elapsed = time.perf_counter() - started_at
        unavailable = (
            solver_name == "cp_sat"
            and "requires backend/requirements-cpsat.txt" in str(exc)
        )
        return SolverRunResult(
            solver=solver_name,
            run_status="unavailable" if unavailable else "failed",
            input_digest=input_digest,
            error_code="OPTIONAL_SOLVER_UNAVAILABLE" if unavailable else "SOLVER_ERROR",
            error_message=str(exc),
            runtime_seconds=elapsed,
            total_work_orders=len(submitted_ids),
            objective_components=_unavailable_components(
                "Solver did not return a schedule."
            ),
        )
    except (ValueError, TypeError, KeyError) as exc:
        return SolverRunResult(
            solver=solver_name,
            run_status="failed",
            input_digest=input_digest,
            error_code="SOLVER_INPUT_OR_RESULT_ERROR",
            error_message=str(exc),
            runtime_seconds=time.perf_counter() - started_at,
            total_work_orders=len(submitted_ids),
            objective_components=_unavailable_components(
                "Solver did not return a schedule."
            ),
        )
    except Exception as exc:
        return SolverRunResult(
            solver=solver_name,
            run_status="failed",
            input_digest=input_digest,
            error_code="SOLVER_ERROR",
            error_message=f"{type(exc).__name__}: {exc}",
            runtime_seconds=time.perf_counter() - started_at,
            total_work_orders=len(submitted_ids),
            objective_components=_unavailable_components(
                "Solver did not return a schedule."
            ),
        )

    elapsed = time.perf_counter() - started_at
    if not isinstance(raw_result, dict):
        return SolverRunResult(
            solver=solver_name,
            run_status="failed",
            input_digest=input_digest,
            error_code="INVALID_SOLVER_RESULT",
            error_message="Solver returned a non-object result.",
            runtime_seconds=elapsed,
            total_work_orders=len(submitted_ids),
            objective_components=_unavailable_components(
                "Solver did not return a schedule."
            ),
        )

    metrics = raw_result.get("metrics")
    stats = raw_result.get("search_stats", {})
    solver_outcome = raw_result.get("solver_outcome")
    if not isinstance(metrics, dict) or not isinstance(stats, dict):
        return SolverRunResult(
            solver=solver_name,
            run_status="failed",
            input_digest=input_digest,
            error_code="INVALID_SOLVER_RESULT",
            error_message="Solver metrics and search statistics must be objects.",
            runtime_seconds=elapsed,
            total_work_orders=len(submitted_ids),
            objective_components=_unavailable_components(
                "Solver did not return valid metrics."
            ),
        )
    if not isinstance(solver_outcome, str) or solver_outcome not in {
        "success",
        "partial",
        "unschedulable",
        "no_work",
        "search_limit_reached",
    }:
        return SolverRunResult(
            solver=solver_name,
            run_status="failed",
            input_digest=input_digest,
            error_code="INVALID_SOLVER_RESULT",
            error_message="Solver returned an unsupported or missing outcome.",
            runtime_seconds=elapsed,
            total_work_orders=len(submitted_ids),
            objective_components=_unavailable_components(
                "Solver did not return a recognized outcome."
            ),
        )
    required_proof_fields = [
        "feasible_solution_found",
        "complete_schedule_proven_infeasible",
        "optimality_proven",
    ]
    if solver_name == "cp_sat" and solver_outcome != "no_work":
        required_proof_fields.append("coverage_optimality_proven")
    if solver_name == "cp_sat" and any(
        not isinstance(raw_result.get(field), bool)
        for field in required_proof_fields
    ):
        return SolverRunResult(
            solver=solver_name,
            run_status="failed",
            input_digest=input_digest,
            error_code="INVALID_SOLVER_PROOF_METADATA",
            error_message="CP-SAT proof metadata must contain Boolean fields.",
            runtime_seconds=elapsed,
            total_work_orders=len(submitted_ids),
            objective_components=_unavailable_components(
                "Solver did not return valid proof metadata."
            ),
        )

    raw_schedule = raw_result.get("schedule")
    raw_unscheduled = raw_result.get("unscheduled_work_ids")
    if not isinstance(raw_schedule, list) or not isinstance(raw_unscheduled, list):
        return SolverRunResult(
            solver=solver_name,
            run_status="failed",
            input_digest=input_digest,
            error_code="INVALID_SOLVER_RESULT",
            error_message="Solver schedule and unscheduled IDs must be lists.",
            runtime_seconds=elapsed,
            total_work_orders=len(submitted_ids),
            objective_components=_unavailable_components(
                "Solver did not return a valid schedule."
            ),
        )

    try:
        parsed_schedule = [
            ScenarioAssignment.model_validate(row) for row in raw_schedule
        ]
        if any(not isinstance(work_id, str) for work_id in raw_unscheduled):
            raise ValueError("unscheduled_work_ids must contain strings")
        unscheduled_ids = list(raw_unscheduled)
    except (ValidationError, ValueError, TypeError) as exc:
        return SolverRunResult(
            solver=solver_name,
            run_status="failed",
            input_digest=input_digest,
            error_code="INVALID_SOLVER_RESULT",
            error_message=str(exc),
            runtime_seconds=elapsed,
            total_work_orders=len(submitted_ids),
            objective_components=_unavailable_components(
                "Solver did not return a valid schedule."
            ),
        )

    validation = validate_schedule(scenario, parsed_schedule, unscheduled_ids)
    objective_components = evaluate_objective_components(
        scenario, parsed_schedule, validation
    )
    scheduled_ids = [row.work_id for row in parsed_schedule]
    complete_witness = (
        bool(submitted_ids)
        and validation.valid
        and len(scheduled_ids) == len(submitted_ids)
        and not unscheduled_ids
    )

    if solver_name == "cp_sat":
        complete_infeasibility = raw_result["complete_schedule_proven_infeasible"]
        coverage_proven = bool(
            raw_result.get("coverage_optimality_proven", False)
        ) or complete_witness
        objective_proven = raw_result["optimality_proven"]
        if objective_proven and not coverage_proven:
            return SolverRunResult(
                solver=solver_name,
                run_status="failed",
                input_digest=input_digest,
                error_code="INVALID_SOLVER_PROOF_METADATA",
                error_message=(
                    "CP-SAT objective optimality cannot be claimed without "
                    "maximum-coverage proof."
                ),
                runtime_seconds=elapsed,
                total_work_orders=len(submitted_ids),
                objective_components=_unavailable_components(
                    "Solver returned contradictory proof metadata."
                ),
            )
        feasible_incumbent_found = raw_result.get("feasible_solution_found", False)
        termination_reason = raw_result.get("termination_reason")
        termination_status = raw_result.get("cp_sat_status")
        search_limit = (
            solver_outcome == "search_limit_reached"
            or termination_status in {"FEASIBLE", "UNKNOWN"}
            or str(termination_reason).startswith("UNKNOWN")
            or str(termination_reason).startswith("TIME_LIMIT")
        )
    else:
        complete_infeasibility = solver_outcome == "unschedulable"
        coverage_proven = complete_witness
        objective_proven = False
        feasible_incumbent_found = None
        termination_reason = (
            "EXHAUSTED_INFEASIBLE"
            if complete_infeasibility
            else "SEARCH_LIMIT_REACHED"
            if solver_outcome == "search_limit_reached"
            else str(solver_outcome or "UNKNOWN")
        )
        termination_status = None
        search_limit = solver_outcome == "search_limit_reached"

    if complete_witness and complete_infeasibility:
        return SolverRunResult(
            solver=solver_name,
            run_status="failed",
            input_digest=input_digest,
            error_code="INVALID_SOLVER_PROOF_METADATA",
            error_message=(
                "A validated complete assignment contradicts the claim that "
                "no complete schedule exists."
            ),
            runtime_seconds=elapsed,
            total_work_orders=len(submitted_ids),
            objective_components=_unavailable_components(
                "Solver returned contradictory proof metadata."
            ),
        )

    feasibility_not_established = (
        bool(submitted_ids)
        and not complete_witness
        and not complete_infeasibility
    )
    reasons = _unscheduled_reasons(
        scenario,
        unscheduled_ids,
        validation.valid,
        coverage_proven,
        complete_infeasibility,
        search_limit,
    )
    proof_scope = (
        f"Claims apply only to model {scenario.model_version} and input digest "
        f"{input_digest}."
    )

    try:
        return SolverRunResult(
            solver=solver_name,
            run_status="completed",
            input_digest=input_digest,
            solver_outcome=solver_outcome,
            termination_reason=termination_reason,
            termination_status=termination_status,
            runtime_seconds=metrics.get("solver_execution_time_sec", elapsed),
            total_work_orders=len(submitted_ids),
            scheduled_work_ids=scheduled_ids,
            unscheduled_work_ids=unscheduled_ids,
            schedule=parsed_schedule,
            validation=validation,
            objective_components=objective_components,
            solver_feasible_incumbent_found=feasible_incumbent_found,
            complete_assignment_witness=complete_witness,
            coverage_optimality_proven=coverage_proven,
            complete_schedule_proven_infeasible=complete_infeasibility,
            objective_optimality_proven=objective_proven,
            feasibility_not_established=feasibility_not_established,
            search_limit_reached=search_limit,
            proof_scope=proof_scope,
            solver_native_objective_value=metrics.get("objective_score"),
            solver_scaled_objective_value=metrics.get("scaled_objective_value"),
            solver_objective_integer_scale=metrics.get("objective_integer_scale"),
            search_branches=stats.get("branches"),
            search_conflicts=stats.get("conflicts"),
            candidate_domain_before_train_filtering=metrics.get(
                "candidate_domain_total_before_train_filtering"
            ),
            candidate_domain_after_train_filtering=metrics.get(
                "candidate_domain_total_after_train_filtering"
            ),
            unscheduled_reasons=reasons,
        )
    except ValidationError as exc:
        return SolverRunResult(
            solver=solver_name,
            run_status="failed",
            input_digest=input_digest,
            error_code="INVALID_SOLVER_RESULT",
            error_message=str(exc),
            runtime_seconds=elapsed,
            total_work_orders=len(submitted_ids),
            objective_components=_unavailable_components(
                "Solver result did not conform to the response contract."
            ),
        )


def run_scenario_comparison(
    scenario: ScenarioComparisonRequest,
    valid_section_ids: set[str] | None = None,
) -> ScenarioComparisonResponse:
    """Validate first, then run each existing solver once on an identical snapshot."""
    input_validation = validate_scenario_input(scenario, valid_section_ids)
    if not input_validation.valid:
        raise ScenarioInputError(input_validation.findings)

    digest = canonical_scenario_digest(scenario)
    if scenario.input_digest is not None and scenario.input_digest != digest:
        raise ScenarioInputError(
            [
                ValidationFinding(
                    code="INPUT_DIGEST_MISMATCH",
                    message="Supplied input_digest does not match the canonical scenario.",
                )
            ]
        )

    work_orders, train_windows = _solver_inputs(scenario)
    baseline = _run_solver(
        "baseline",
        solve_maintenance_schedule,
        scenario,
        digest,
        work_orders,
        train_windows,
    )
    cp_sat = _run_solver(
        "cp_sat",
        cpsat_solver.solve_maintenance_schedule_cpsat,
        scenario,
        digest,
        work_orders,
        train_windows,
    )
    paired_completed = (
        baseline.run_status == "completed" and cp_sat.run_status == "completed"
    )

    return ScenarioComparisonResponse(
        scenario_id=scenario.scenario_id,
        model_version=scenario.model_version,
        input_digest=digest,
        comparison_status="completed" if paired_completed else "incomplete",
        paired_inputs_match=baseline.input_digest == cp_sat.input_digest == digest,
        baseline=baseline,
        cp_sat=cp_sat,
    )
