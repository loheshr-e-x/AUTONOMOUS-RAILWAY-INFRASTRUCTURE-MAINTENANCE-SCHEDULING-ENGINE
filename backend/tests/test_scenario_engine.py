from copy import deepcopy

import pytest

from backend.app import scenario_engine
from backend.app.scenario_engine import ScenarioInputError, run_scenario_comparison
from backend.app.scenario_validation import canonical_scenario_digest
from backend.app.schemas.scenario_contracts import ScenarioComparisonRequest


SECTION = "NDLS_CNB_SEC1"


def _request(work_orders=None):
    return ScenarioComparisonRequest.model_validate(
        {
            "scenario_id": "engine-test",
            "work_orders": work_orders
            if work_orders is not None
            else [
                {
                    "work_id": "WO-1",
                    "department": "ENGINEERING",
                    "section_id": SECTION,
                    "track_line": "UP_LINE",
                    "defect_type": "Inspection",
                    "duration_hrs": 1.0,
                    "urgency": 2,
                }
            ],
            "train_windows": [],
            "solver_configuration": {
                "section_ids": [SECTION],
                "time_horizon_hrs": 8.0,
                "slot_duration_hrs": 0.5,
                "enable_simulated_annealing": False,
            },
        }
    )


def _assignment(work_id="WO-1"):
    return {
        "work_id": work_id,
        "department": "ENGINEERING",
        "section_id": SECTION,
        "track_line": "UP_LINE",
        "start_time_hr": 0.0,
        "end_time_hr": 1.0,
        "co_located_with": [],
        "heavy_equipment": False,
    }


def _result(
    *,
    outcome="success",
    schedule=None,
    unscheduled=None,
    proof=False,
    complete_infeasibility=False,
    objective_proof=False,
):
    assignments = [_assignment()] if schedule is None else schedule
    unscheduled_ids = [] if unscheduled is None else unscheduled
    scheduled_count = len(assignments)
    return {
        "status": outcome,
        "solver_outcome": outcome,
        "schedule": assignments,
        "unscheduled_work_ids": unscheduled_ids,
        "metrics": {
            "total_requests": scheduled_count + len(unscheduled_ids),
            "scheduled_requests": scheduled_count,
            "solver_execution_time_sec": 0.01,
            "scaled_objective_value": 123.0,
            "objective_integer_scale": 9_000_000_000_000,
            "candidate_domain_total_before_train_filtering": 16,
            "candidate_domain_total_after_train_filtering": 12,
        },
        "feasible_solution_found": bool(assignments),
        "complete_schedule_proven_infeasible": complete_infeasibility,
        "optimality_proven": objective_proof,
        "coverage_optimality_proven": proof,
        "termination_reason": "OPTIMAL" if proof else "FEASIBLE",
        "cp_sat_status": "OPTIMAL" if proof else "FEASIBLE",
        "search_stats": {"branches": 3, "conflicts": 1},
    }


def test_invalid_scenario_is_rejected_before_either_solver_runs(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("solver must not run for invalid input")

    monkeypatch.setattr(scenario_engine, "solve_maintenance_schedule", forbidden)
    monkeypatch.setattr(
        scenario_engine.cpsat_solver, "solve_maintenance_schedule_cpsat", forbidden
    )
    request = _request(
        work_orders=[
            {
                "work_id": "WO-1",
                "department": "ENGINEERING",
                "section_id": SECTION,
                "track_line": "UP_LINE",
                "defect_type": "Inspection",
                "duration_hrs": 1.0,
                "urgency": 2,
            },
            {
                "work_id": "WO-1",
                "department": "SIGNALLING",
                "section_id": SECTION,
                "track_line": "DOWN_LINE",
                "defect_type": "Inspection",
                "duration_hrs": 1.0,
                "urgency": 2,
            },
        ]
    )

    with pytest.raises(ScenarioInputError) as error:
        run_scenario_comparison(request, {SECTION})

    assert error.value.findings[0].code == "DUPLICATE_WORK_ORDER_ID"


def test_both_solvers_receive_identical_canonical_input_and_digest(monkeypatch):
    request = _request()
    captured = []

    def baseline(orders, trains, config):
        captured.append(("baseline", deepcopy(orders), deepcopy(trains), deepcopy(config)))
        return _result()

    def cp_sat(orders, trains, config):
        captured.append(("cp_sat", deepcopy(orders), deepcopy(trains), deepcopy(config)))
        return _result()

    monkeypatch.setattr(scenario_engine, "solve_maintenance_schedule", baseline)
    monkeypatch.setattr(
        scenario_engine.cpsat_solver, "solve_maintenance_schedule_cpsat", cp_sat
    )
    response = run_scenario_comparison(request, {SECTION})

    assert [call[0] for call in captured] == ["baseline", "cp_sat"]
    assert captured[0][1:] == captured[1][1:]
    expected_digest = canonical_scenario_digest(request)
    assert captured[0][3]["scenario_input_digest"] == expected_digest
    assert captured[1][3]["scenario_input_digest"] == expected_digest
    assert response.baseline.input_digest == response.cp_sat.input_digest == expected_digest
    assert response.paired_inputs_match
    assert response.comparison_status == "completed"
    assert response.baseline.complete_assignment_witness
    assert response.cp_sat.complete_assignment_witness
    assert response.baseline.solver_feasible_incumbent_found is None
    assert response.cp_sat.solver_feasible_incumbent_found


def test_empty_scenario_is_a_completed_no_work_result_without_proof_claims():
    response = run_scenario_comparison(_request(work_orders=[]), {SECTION})

    assert response.comparison_status == "completed"
    for run in (response.baseline, response.cp_sat):
        assert run.run_status == "completed"
        assert run.solver_outcome == "no_work"
        assert run.validation.valid
        assert not run.complete_assignment_witness
        assert not run.coverage_optimality_proven
        assert not run.objective_optimality_proven


def test_solver_outcomes_and_proof_metadata_are_kept_separate(monkeypatch):
    request = _request(
        work_orders=[
            {
                "work_id": "WO-1",
                "department": "ENGINEERING",
                "section_id": SECTION,
                "track_line": "UP_LINE",
                "defect_type": "Inspection",
                "duration_hrs": 1.0,
                "urgency": 2,
            },
            {
                "work_id": "WO-2",
                "department": "ENGINEERING",
                "section_id": SECTION,
                "track_line": "UP_LINE",
                "defect_type": "Inspection",
                "duration_hrs": 1.0,
                "urgency": 2,
            },
        ]
    )
    monkeypatch.setattr(
        scenario_engine,
        "solve_maintenance_schedule",
        lambda *args: _result(
            outcome="search_limit_reached",
            schedule=[_assignment()],
            unscheduled=["WO-2"],
        ),
    )
    monkeypatch.setattr(
        scenario_engine.cpsat_solver,
        "solve_maintenance_schedule_cpsat",
        lambda *args: _result(
            outcome="partial",
            schedule=[_assignment()],
            unscheduled=["WO-2"],
            proof=True,
            complete_infeasibility=True,
        ),
    )

    response = run_scenario_comparison(request, {SECTION})

    assert response.baseline.solver_outcome == "search_limit_reached"
    assert response.baseline.search_limit_reached
    assert response.baseline.feasibility_not_established
    assert not response.baseline.complete_schedule_proven_infeasible
    assert response.cp_sat.solver_outcome == "partial"
    assert response.cp_sat.coverage_optimality_proven
    assert response.cp_sat.complete_schedule_proven_infeasible
    assert not response.cp_sat.objective_optimality_proven
    assert response.cp_sat.solver_feasible_incumbent_found
    assert not response.cp_sat.complete_assignment_witness
    assert response.cp_sat.unscheduled_reasons[0].code == (
        "GLOBAL_COMPLETE_SCHEDULE_INFEASIBILITY_PROVEN"
    )
    assert "individual" in response.cp_sat.unscheduled_reasons[0].explanation


def test_cp_sat_search_limit_does_not_become_an_infeasibility_claim(monkeypatch):
    request = _request()
    monkeypatch.setattr(
        scenario_engine,
        "solve_maintenance_schedule",
        lambda *args: _result(),
    )
    monkeypatch.setattr(
        scenario_engine.cpsat_solver,
        "solve_maintenance_schedule_cpsat",
        lambda *args: _result(
            outcome="search_limit_reached",
            schedule=[],
            unscheduled=["WO-1"],
            proof=False,
            complete_infeasibility=False,
        ),
    )

    response = run_scenario_comparison(request, {SECTION})

    assert response.cp_sat.search_limit_reached
    assert response.cp_sat.feasibility_not_established
    assert not response.cp_sat.complete_schedule_proven_infeasible
    assert response.cp_sat.unscheduled_reasons[0].code == (
        "NOT_SCHEDULED_BEFORE_SEARCH_LIMIT"
    )


def test_cp_sat_objective_proof_is_preserved_as_model_specific(monkeypatch):
    request = _request()
    monkeypatch.setattr(
        scenario_engine,
        "solve_maintenance_schedule",
        lambda *args: _result(),
    )
    monkeypatch.setattr(
        scenario_engine.cpsat_solver,
        "solve_maintenance_schedule_cpsat",
        lambda *args: _result(proof=True, objective_proof=True),
    )

    response = run_scenario_comparison(request, {SECTION})

    assert response.cp_sat.objective_optimality_proven
    assert response.cp_sat.proof_scope.startswith("Claims apply only to model")
    assert response.baseline.objective_optimality_proven is False


@pytest.mark.parametrize(
    "damage",
    [
        "missing_metrics",
        "missing_schedule",
        "missing_unscheduled",
        "metrics_none",
        "metrics_false",
        "metrics_list",
    ],
)
def test_malformed_solver_output_is_failed_not_normalized_to_a_run(
    monkeypatch, damage
):
    request = _request()
    malformed = _result()
    if damage == "missing_metrics":
        del malformed["metrics"]
    elif damage == "missing_schedule":
        del malformed["schedule"]
    elif damage == "missing_unscheduled":
        del malformed["unscheduled_work_ids"]
    elif damage == "metrics_none":
        malformed["metrics"] = None
    elif damage == "metrics_false":
        malformed["metrics"] = False
    elif damage == "metrics_list":
        malformed["metrics"] = []

    monkeypatch.setattr(
        scenario_engine, "solve_maintenance_schedule", lambda *args: malformed
    )
    monkeypatch.setattr(
        scenario_engine.cpsat_solver,
        "solve_maintenance_schedule_cpsat",
        lambda *args: _result(),
    )

    response = run_scenario_comparison(request, {SECTION})

    assert response.baseline.run_status == "failed"
    assert response.baseline.error_code == "INVALID_SOLVER_RESULT"
    assert response.comparison_status == "incomplete"
    assert response.baseline.validation is None


def test_missing_search_stats_is_allowed_and_exposes_no_search_counts(monkeypatch):
    request = _request()
    result_without_stats = _result()
    del result_without_stats["search_stats"]
    monkeypatch.setattr(
        scenario_engine, "solve_maintenance_schedule", lambda *args: result_without_stats
    )
    monkeypatch.setattr(
        scenario_engine.cpsat_solver,
        "solve_maintenance_schedule_cpsat",
        lambda *args: _result(),
    )

    response = run_scenario_comparison(request, {SECTION})

    assert response.baseline.run_status == "completed"
    assert response.baseline.search_branches is None
    assert response.baseline.search_conflicts is None


@pytest.mark.parametrize("search_stats", [None, False, [], "invalid"])
def test_non_object_search_stats_is_rejected(monkeypatch, search_stats):
    request = _request()
    malformed = _result()
    malformed["search_stats"] = search_stats
    monkeypatch.setattr(
        scenario_engine, "solve_maintenance_schedule", lambda *args: malformed
    )
    monkeypatch.setattr(
        scenario_engine.cpsat_solver,
        "solve_maintenance_schedule_cpsat",
        lambda *args: _result(),
    )

    response = run_scenario_comparison(request, {SECTION})

    assert response.baseline.run_status == "failed"
    assert response.baseline.error_code == "INVALID_SOLVER_RESULT"
    assert response.comparison_status == "incomplete"


def test_cp_sat_contradictory_proof_metadata_fails_the_solver_run(monkeypatch):
    request = _request()
    contradictory = _result(complete_infeasibility=True)
    monkeypatch.setattr(
        scenario_engine,
        "solve_maintenance_schedule",
        lambda *args: _result(),
    )
    monkeypatch.setattr(
        scenario_engine.cpsat_solver,
        "solve_maintenance_schedule_cpsat",
        lambda *args: contradictory,
    )

    response = run_scenario_comparison(request, {SECTION})

    assert response.cp_sat.run_status == "failed"
    assert response.cp_sat.error_code == "INVALID_SOLVER_PROOF_METADATA"
    assert response.cp_sat.validation is None
    assert response.comparison_status == "incomplete"


@pytest.mark.parametrize(
    "field",
    [
        "feasible_solution_found",
        "complete_schedule_proven_infeasible",
        "optimality_proven",
        "coverage_optimality_proven",
    ],
)
def test_cp_sat_non_boolean_proof_metadata_fails_the_solver_run(monkeypatch, field):
    request = _request()
    malformed = _result()
    malformed[field] = "true"
    monkeypatch.setattr(
        scenario_engine, "solve_maintenance_schedule", lambda *args: _result()
    )
    monkeypatch.setattr(
        scenario_engine.cpsat_solver,
        "solve_maintenance_schedule_cpsat",
        lambda *args: malformed,
    )

    response = run_scenario_comparison(request, {SECTION})

    assert response.cp_sat.run_status == "failed"
    assert response.cp_sat.error_code == "INVALID_SOLVER_PROOF_METADATA"
    assert response.comparison_status == "incomplete"


def test_cp_sat_objective_proof_without_coverage_proof_fails(monkeypatch):
    request = _request(
        work_orders=[
            {
                "work_id": "WO-1",
                "department": "ENGINEERING",
                "section_id": SECTION,
                "track_line": "UP_LINE",
                "defect_type": "Inspection",
                "duration_hrs": 1.0,
                "urgency": 2,
            },
            {
                "work_id": "WO-2",
                "department": "ENGINEERING",
                "section_id": SECTION,
                "track_line": "UP_LINE",
                "defect_type": "Inspection",
                "duration_hrs": 1.0,
                "urgency": 2,
            },
        ]
    )
    contradictory = _result(
        outcome="partial",
        schedule=[_assignment()],
        unscheduled=["WO-2"],
        objective_proof=True,
    )
    monkeypatch.setattr(
        scenario_engine, "solve_maintenance_schedule", lambda *args: _result()
    )
    monkeypatch.setattr(
        scenario_engine.cpsat_solver,
        "solve_maintenance_schedule_cpsat",
        lambda *args: contradictory,
    )

    response = run_scenario_comparison(request, {SECTION})

    assert response.cp_sat.run_status == "failed"
    assert response.cp_sat.error_code == "INVALID_SOLVER_PROOF_METADATA"
    assert response.comparison_status == "incomplete"


def test_baseline_unschedulable_outcome_cannot_contradict_a_valid_complete_witness(
    monkeypatch,
):
    request = _request()
    monkeypatch.setattr(
        scenario_engine,
        "solve_maintenance_schedule",
        lambda *args: _result(outcome="unschedulable"),
    )
    monkeypatch.setattr(
        scenario_engine.cpsat_solver,
        "solve_maintenance_schedule_cpsat",
        lambda *args: _result(),
    )

    response = run_scenario_comparison(request, {SECTION})

    assert response.baseline.run_status == "failed"
    assert response.baseline.error_code == "INVALID_SOLVER_PROOF_METADATA"
    assert response.comparison_status == "incomplete"


def test_missing_ortools_is_explicit_and_never_a_successful_pair(monkeypatch):
    request = _request()
    monkeypatch.setattr(
        scenario_engine,
        "solve_maintenance_schedule",
        lambda *args: _result(),
    )

    def missing_ortools(*args):
        raise RuntimeError(
            "The experimental CP-SAT solver requires backend/requirements-cpsat.txt"
        )

    monkeypatch.setattr(
        scenario_engine.cpsat_solver,
        "solve_maintenance_schedule_cpsat",
        missing_ortools,
    )
    response = run_scenario_comparison(request, {SECTION})

    assert response.comparison_status == "incomplete"
    assert response.baseline.run_status == "completed"
    assert response.cp_sat.run_status == "unavailable"
    assert response.cp_sat.error_code == "OPTIONAL_SOLVER_UNAVAILABLE"
    assert response.paired_inputs_match


def test_one_sided_solver_failure_is_not_reported_as_paired_success(monkeypatch):
    request = _request()
    monkeypatch.setattr(
        scenario_engine,
        "solve_maintenance_schedule",
        lambda *args: (_ for _ in ()).throw(RuntimeError("baseline failed")),
    )
    monkeypatch.setattr(
        scenario_engine.cpsat_solver,
        "solve_maintenance_schedule_cpsat",
        lambda *args: _result(),
    )

    response = run_scenario_comparison(request, {SECTION})

    assert response.comparison_status == "incomplete"
    assert response.baseline.run_status == "failed"
    assert response.cp_sat.run_status == "completed"
    assert response.baseline.error_message == "baseline failed"


def test_input_digest_mismatch_prevents_solver_invocation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("solver must not run for mismatched digest")

    monkeypatch.setattr(scenario_engine, "solve_maintenance_schedule", forbidden)
    monkeypatch.setattr(
        scenario_engine.cpsat_solver, "solve_maintenance_schedule_cpsat", forbidden
    )
    request = _request().model_copy(update={"input_digest": "0" * 64})

    with pytest.raises(ScenarioInputError) as error:
        run_scenario_comparison(request, {SECTION})

    assert error.value.findings[0].code == "INPUT_DIGEST_MISMATCH"


def test_actual_small_scenario_runs_through_both_solvers():
    pytest.importorskip("ortools")
    request = _request()

    response = run_scenario_comparison(request, {SECTION})

    assert response.comparison_status == "completed"
    assert response.baseline.validation.valid
    assert response.cp_sat.validation.valid
    assert response.baseline.complete_assignment_witness
    assert response.cp_sat.complete_assignment_witness
    assert response.baseline.coverage_optimality_proven
    assert response.cp_sat.coverage_optimality_proven
