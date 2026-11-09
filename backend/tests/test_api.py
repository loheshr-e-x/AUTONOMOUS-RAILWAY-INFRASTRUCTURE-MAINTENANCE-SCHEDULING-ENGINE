import pytest
from fastapi.testclient import TestClient

from backend.app import main
from backend.app.schemas.contracts import (
    AuditLogEntry,
    BlockScheduleResponse,
    Department,
    MaintenanceWorkOrder,
    SolverRequest,
    TrainOccupancyWindow,
)
from backend.app.solver_engine import solve_maintenance_schedule

client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset_custom_state():
    main._custom_work_orders = None
    main._custom_trains = None
    yield
    main._custom_work_orders = None
    main._custom_trains = None


def _order(work_id="WO-C1", section="NDLS_CNB_SEC1", line="UP_LINE", dur=1.0):
    return {
        "work_id": work_id, "department": "ENGINEERING", "section_id": section,
        "track_line": line, "heavy_equipment": False, "defect_type": "Custom",
        "duration_hrs": dur, "urgency": 2, "co_location_allowed": True,
    }


def test_routes_listed():
    ids = {r["route_id"] for r in client.get("/api/data/routes").json()}
    assert {"NDLS_CNB", "HWH_PURI", "BCT_AMD"} <= ids


def test_unknown_route_404():
    assert client.get("/api/data/trains?route_id=NOPE").status_code == 404


@pytest.mark.parametrize("horizon", [0, 25])
def test_invalid_schedule_horizon_returns_422(horizon):
    response = client.post(
        "/api/schedule/generate",
        json={"section_ids": ["NDLS_CNB"], "time_horizon_hrs": horizon},
    )

    assert response.status_code == 422


@pytest.mark.parametrize("route", ["NDLS_CNB", "HWH_PURI", "BCT_AMD"])
def test_generate_per_route(route):
    body = client.post("/api/schedule/generate", json={"section_ids": [route]}).json()
    # No traction isolation evidence source exists, so real schedules are unverified, never "success".
    assert body["status"] == "safety_unverified"
    assert len(body["schedule"]) >= 20
    assert not any(a["passed"] is False for a in body["audit_trail"])
    unevaluated = {a["rule_name"] for a in body["audit_trail"] if a["passed"] is None}
    # The timetable source supplies no completeness evidence, so clearance is never verified.
    assert unevaluated >= {
        "Traction Power Isolation Rule",
        "Passenger Train Clearance Invariant",
        "Minimum Distance Safety Buffer",
    }
    assert unevaluated <= {
        "Traction Power Isolation Rule",
        "Passenger Train Clearance Invariant",
        "Minimum Distance Safety Buffer",
        "Adjacent Track Heavy Equipment Buffer",
    }
    assert not any(
        a["rule_name"] == "Adjacent Track Heavy Equipment Buffer" and a["passed"] is True
        for a in body["audit_trail"]
    )
    assert not any(
        a["rule_name"] == "Passenger Train Clearance Invariant" and a["passed"] is True
        for a in body["audit_trail"]
    )


def test_api_preserves_no_work_solver_outcome():
    main._custom_work_orders = []
    main._custom_trains = []

    response = client.post(
        "/api/schedule/generate", json={"section_ids": ["NDLS_CNB"]}
    )
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "no_work"
    assert body["solver_outcome"] == "no_work"
    assert body["schedule"] == []
    assert body["unscheduled_work_ids"] == []
    assert body["metrics"]["total_requests"] == 0
    assert body["metrics"]["scheduled_requests"] == 0
    assert body["metrics"]["fol_rule_compliance_pct"] is None


def test_api_retains_search_limit_outcome_when_safety_is_unverified(monkeypatch):
    limited = _solver_response(status="search_limit_reached", total=2, scheduled=1)
    limited["schedule"] = limited["schedule"][:1]
    limited["unscheduled_work_ids"] = ["W-OMITTED"]
    limited["solver_outcome"] = "search_limit_reached"
    main._custom_work_orders = []
    main._custom_trains = []
    monkeypatch.setattr(main, "solve_maintenance_schedule", lambda *_: limited)

    body = client.post(
        "/api/schedule/generate", json={"section_ids": ["NDLS_CNB_SEC1"]}
    ).json()

    assert body["status"] == "safety_unverified"
    assert body["solver_outcome"] == "search_limit_reached"
    assert body["unscheduled_work_ids"] == ["W-OMITTED"]


def test_api_downgrades_success_with_unscheduled_ids(monkeypatch):
    inconsistent = _solver_response(status="success", total=1, scheduled=1)
    inconsistent["unscheduled_work_ids"] = ["W-OMITTED"]
    main._custom_work_orders = []
    main._custom_trains = []
    monkeypatch.setattr(main, "solve_maintenance_schedule", lambda *_: inconsistent)

    body = client.post(
        "/api/schedule/generate", json={"section_ids": ["NDLS_CNB_SEC1"]}
    ).json()

    assert body["status"] == "safety_unverified"
    assert body["solver_outcome"] == "partial"


def test_custom_work_orders_roundtrip_and_generate():
    r = client.post("/api/data/work-orders/custom", json=[_order(), _order("WO-C2", line="DOWN_LINE")])
    assert r.status_code == 200
    assert len(client.get("/api/data/work-orders").json()) == 2
    body = client.post("/api/schedule/generate", json={"section_ids": ["NDLS_CNB"]}).json()
    assert body["metrics"]["total_requests"] == 2
    client.delete("/api/data/work-orders/custom")
    assert len(client.get("/api/data/work-orders").json()) == 30


def test_custom_work_orders_validation():
    assert client.post("/api/data/work-orders/custom", json=[_order(section="BAD")]).status_code == 422
    assert client.post("/api/data/work-orders/custom", json=[_order(), _order()]).status_code == 422
    assert client.post("/api/data/work-orders/custom", json=[_order(dur=99)]).status_code == 422


def test_custom_trains():
    t = {"train_no": "99999", "section_id": "NDLS_CNB_SEC1", "track_line": "UP_LINE",
         "start_time_hr": 1.0, "end_time_hr": 2.0}
    assert client.post("/api/data/trains/custom", json=[t]).status_code == 200
    assert len(client.get("/api/data/trains").json()) == 1
    t["end_time_hr"] = 0.5
    assert client.post("/api/data/trains/custom", json=[t]).status_code == 422


def _solver_response(status="success", total=1, scheduled=1):
    return {
        "status": status,
        "schedule": [{
            "work_id": "W-API",
            "department": "ENGINEERING",
            "section_id": "NDLS_CNB_SEC1",
            "track_line": "UP_LINE",
            "start_time_hr": 1.0,
            "end_time_hr": 2.0,
            "fol_verified": True,
            "power_isolated": True,
        }],
        "metrics": {
            "total_requests": total,
            "scheduled_requests": scheduled,
            "search_space_pruned_pct": 0.0,
            "fol_rule_compliance_pct": None,
            "co_location_merges_count": 0,
            "solver_execution_time_sec": 0.01,
        },
        "audit_trail": [],
    }


def _generate_with_verification(monkeypatch, solver_result, valid, audit):
    main._custom_work_orders = []
    main._custom_trains = []
    monkeypatch.setattr(main, "solve_maintenance_schedule", lambda *_: solver_result)
    monkeypatch.setattr(
        main,
        "verify_safety_invariants",
        lambda *_: (valid, audit),
    )
    return client.post(
        "/api/schedule/generate",
        json={"section_ids": ["NDLS_CNB_SEC1"]},
    )


def test_failed_safety_verification_cannot_return_success_and_keeps_audit(monkeypatch):
    failed_check = AuditLogEntry(
        rule_name="Controlled failure",
        predicate_evaluated="safe == False",
        passed=False,
        explanation="The test verifier found a controlled safety violation.",
    )

    response = _generate_with_verification(
        monkeypatch, _solver_response(), False, [failed_check]
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "safety_invalid"
    assert body["audit_trail"][-1]["passed"] is False
    assert body["metrics"]["fol_rule_compliance_pct"] == 0.0
    assert body["schedule"][0]["fol_verified"] is None
    assert body["schedule"][0]["power_isolated"] is None


def test_verified_complete_schedule_can_return_success(monkeypatch):
    passed_check = AuditLogEntry(
        rule_name="Controlled pass",
        predicate_evaluated="safe == True",
        passed=True,
        explanation="The test verifier passed the required check.",
    )

    response = _generate_with_verification(
        monkeypatch, _solver_response(), True, [passed_check]
    )

    assert response.json()["status"] == "success"
    assert response.json()["metrics"]["fol_rule_compliance_pct"] == 100.0


def test_verified_but_incomplete_schedule_is_not_success(monkeypatch):
    passed_check = AuditLogEntry(
        rule_name="Controlled pass",
        predicate_evaluated="safe == True",
        passed=True,
        explanation="The scheduled assignment passed verification.",
    )

    response = _generate_with_verification(
        monkeypatch,
        _solver_response(status="success", total=2, scheduled=1),
        True,
        [passed_check],
    )

    assert response.json()["status"] == "partial"


def test_missing_safety_checks_are_unverified_not_one_hundred_percent(monkeypatch):
    response = _generate_with_verification(
        monkeypatch, _solver_response(), True, []
    )

    assert response.json()["status"] == "safety_unverified"
    assert response.json()["metrics"]["fol_rule_compliance_pct"] is None


def test_unevaluated_safety_check_is_unverified_and_has_no_percentage(monkeypatch):
    unknown_check = AuditLogEntry(
        rule_name="Unavailable evidence",
        predicate_evaluated="train_data_available == unknown",
        passed=None,
        explanation="No train windows were provided.",
    )
    response = _generate_with_verification(
        monkeypatch, _solver_response(), False, [unknown_check]
    )

    assert response.json()["status"] == "safety_unverified"
    assert response.json()["audit_trail"][-1]["passed"] is None
    assert response.json()["metrics"]["fol_rule_compliance_pct"] is None


def test_solver_output_does_not_claim_verification_or_power_isolation():
    order = MaintenanceWorkOrder(
        work_id="W-TRACTION",
        department=Department.TRACTION,
        section_id="NDLS_CNB_SEC1",
        track_line="UP_LINE",
        defect_type="Test",
        duration_hrs=1.0,
        urgency=2,
    )
    result = solve_maintenance_schedule(
        [order], [], SolverRequest(section_ids=["NDLS_CNB_SEC1"])
    )
    response = BlockScheduleResponse.model_validate(result)
    assignment = response.schedule[0]

    assert assignment.fol_verified is None
    assert assignment.power_isolated is None
    assert response.metrics.fol_rule_compliance_pct is None
    assert all(entry["rule_name"] != "PhysicalBlockSafety" for entry in result["audit_trail"])


def test_traction_without_isolation_evidence_is_unverified_at_api(monkeypatch):
    solver_result = _solver_response()
    solver_result["schedule"][0].update(
        department="TRACTION",
        fol_verified=None,
        power_isolated=None,
    )
    main._custom_work_orders = []
    main._custom_trains = []
    monkeypatch.setattr(
        main, "solve_maintenance_schedule", lambda *_: solver_result
    )

    response = main.generate_schedule(
        SolverRequest(section_ids=["NDLS_CNB_SEC1"])
    )
    isolation = next(
        entry
        for entry in response.audit_trail
        if entry.rule_name == "Traction Power Isolation Rule"
    )

    assert response.status == "safety_unverified"
    assert isolation.passed is None
    assert "unevaluated" in isolation.explanation
    assert response.schedule[0].power_isolated is None


def test_empty_solver_schedule_is_never_reported_as_success(monkeypatch):
    empty = _solver_response(status="success", total=0, scheduled=0)
    empty["schedule"] = []
    main._custom_work_orders = []
    main._custom_trains = []
    monkeypatch.setattr(main, "solve_maintenance_schedule", lambda *_: empty)

    body = client.post(
        "/api/schedule/generate", json={"section_ids": ["NDLS_CNB_SEC1"]}
    ).json()

    assert body["status"] == "safety_unverified"
    assert body["schedule"] == []
    assert body["metrics"]["fol_rule_compliance_pct"] is None


def test_empty_schedule_with_verifier_true_and_empty_audit_is_not_success(monkeypatch):
    empty = _solver_response(status="success", total=0, scheduled=0)
    empty["schedule"] = []
    body = _generate_with_verification(monkeypatch, empty, True, []).json()

    assert body["status"] == "safety_unverified"
    assert body["metrics"]["fol_rule_compliance_pct"] is None


def _check(passed, name="Controlled check"):
    return AuditLogEntry(
        rule_name=name,
        predicate_evaluated="controlled",
        passed=passed,
        explanation="Controlled audit entry.",
    )


def test_application_default_provider_authenticates_nothing():
    from backend.app import logic_engine
    from backend.app.schemas.contracts import ScheduledBlockAssignment, TimetableCoverage

    provider = logic_engine.DEFAULT_EVIDENCE_PROVIDER
    assert type(provider) is logic_engine.EvidenceProvider
    coverage = TimetableCoverage(
        source="anything", section_id="S", track_line="UP_LINE",
        start_time_hr=0.0, end_time_hr=24.0,
    )
    assignment = ScheduledBlockAssignment(
        work_id="W", department="TRACTION", section_id="S",
        start_time_hr=1.0, end_time_hr=2.0,
        power_isolated=True, power_isolation_source="anything",
    )
    assert provider.authenticates_coverage(coverage) is False
    assert provider.authenticates_isolation(assignment) is False


def test_failure_in_incomplete_schedule_is_not_concealed_by_partial(monkeypatch):
    body = _generate_with_verification(
        monkeypatch,
        _solver_response(status="partial", total=2, scheduled=1),
        False,
        [_check(True), _check(False)],
    ).json()

    assert body["status"] == "safety_invalid"
    assert [e["passed"] for e in body["audit_trail"][-2:]] == [True, False]


def test_unevaluated_check_in_incomplete_schedule_is_not_concealed_by_partial(monkeypatch):
    body = _generate_with_verification(
        monkeypatch,
        _solver_response(status="partial", total=2, scheduled=1),
        False,
        [_check(True), _check(None)],
    ).json()

    assert body["status"] == "safety_unverified"
    assert body["metrics"]["fol_rule_compliance_pct"] is None


def test_failure_and_unknown_together_map_to_safety_invalid(monkeypatch):
    body = _generate_with_verification(
        monkeypatch, _solver_response(), False, [_check(None), _check(False)]
    ).json()

    assert body["status"] == "safety_invalid"
    assert body["metrics"]["fol_rule_compliance_pct"] is None


def test_empty_unschedulable_result_keeps_solver_status_without_verification(monkeypatch):
    empty = _solver_response(status="unschedulable", total=2, scheduled=0)
    empty["schedule"] = []
    for verdict in (False, True):
        body = _generate_with_verification(monkeypatch, empty, verdict, []).json()

        assert body["status"] == "unschedulable"
        assert body["schedule"] == []
        assert body["audit_trail"] == []
        assert body["metrics"]["fol_rule_compliance_pct"] is None


def test_verifier_true_with_unevaluated_entry_is_not_success(monkeypatch):
    body = _generate_with_verification(
        monkeypatch, _solver_response(), True, [_check(True), _check(None)]
    ).json()

    assert body["status"] == "safety_unverified"
    assert body["metrics"]["fol_rule_compliance_pct"] is None


def test_compliance_is_computed_only_for_fully_evaluated_audit(monkeypatch):
    body = _generate_with_verification(
        monkeypatch, _solver_response(), False, [_check(True), _check(False)]
    ).json()

    assert body["metrics"]["fol_rule_compliance_pct"] == 50.0

    body = _generate_with_verification(
        monkeypatch, _solver_response(), True, [_check(True), _check(True)]
    ).json()

    assert body["status"] == "success"
    assert body["metrics"]["fol_rule_compliance_pct"] == 100.0


def test_caller_supplied_positive_isolation_with_source_is_not_trusted_at_api(monkeypatch):
    solver_result = _solver_response()
    solver_result["schedule"][0].update(
        department="TRACTION",
        power_isolated=True,
        power_isolation_source="caller-supplied",
    )
    main._custom_work_orders = []
    main._custom_trains = []
    monkeypatch.setattr(main, "solve_maintenance_schedule", lambda *_: solver_result)

    response = main.generate_schedule(SolverRequest(section_ids=["NDLS_CNB_SEC1"]))
    isolation = next(
        e for e in response.audit_trail if e.rule_name == "Traction Power Isolation Rule"
    )

    assert response.schedule[0].power_isolated is None
    assert response.schedule[0].power_isolation_source is None
    assert isolation.passed is None
    assert response.status == "safety_unverified"


def test_metrics_claiming_completeness_cannot_hide_a_short_schedule(monkeypatch):
    short = _solver_response(status="success", total=2, scheduled=2)
    body = _generate_with_verification(monkeypatch, short, True, [_check(True)]).json()

    assert len(body["schedule"]) == 1
    assert body["status"] == "partial"


def test_solver_fol_verified_and_labels_cannot_establish_verification(monkeypatch):
    solver_result = _solver_response()
    solver_result["schedule"][0].update(
        department="TRACTION",
        fol_verified=True,
        power_isolated=True,
        power_isolation_source="caller-supplied",
    )
    main._custom_work_orders = []
    main._custom_trains = []
    monkeypatch.setattr(main, "solve_maintenance_schedule", lambda *_: solver_result)

    response = main.generate_schedule(SolverRequest(section_ids=["NDLS_CNB_SEC1"]))
    entries = {e.rule_name: e.passed for e in response.audit_trail}

    assert response.schedule[0].fol_verified is None
    assert entries["Traction Power Isolation Rule"] is None
    assert entries["Passenger Train Clearance Invariant"] is None
    assert response.status == "safety_unverified"
    assert response.metrics.fol_rule_compliance_pct is None


def test_generate_endpoint_accepts_no_evidence_fields_from_the_request():
    r = client.post(
        "/api/schedule/generate",
        json={
            "section_ids": ["NDLS_CNB"],
            "timetable_coverage": [
                {"source": "x", "section_id": "NDLS_CNB_SEC1", "track_line": "UP_LINE",
                 "start_time_hr": 0.0, "end_time_hr": 24.0}
            ],
        },
    )

    assert r.status_code == 200
    assert r.json()["status"] == "safety_unverified"
    assert "timetable_coverage" not in SolverRequest.model_fields


def test_failure_takes_precedence_over_empty_unschedulable_status(monkeypatch):
    empty = _solver_response(status="unschedulable", total=2, scheduled=0)
    empty["schedule"] = []
    body = _generate_with_verification(monkeypatch, empty, False, [_check(False)]).json()

    assert body["status"] == "safety_invalid"


def test_compliance_is_none_when_audit_and_verifier_disagree(monkeypatch):
    for verdict, entries in ((True, [_check(True), _check(False)]), (False, [_check(True)])):
        body = _generate_with_verification(
            monkeypatch, _solver_response(), verdict, entries
        ).json()

        assert body["status"] == "safety_invalid"
        assert body["metrics"]["fol_rule_compliance_pct"] is None


def _generate_with_real_verifier(monkeypatch, trains, solver_result=None):
    main._custom_work_orders = []
    main._custom_trains = trains
    monkeypatch.setattr(
        main, "solve_maintenance_schedule", lambda *_: solver_result or _solver_response()
    )
    try:
        return client.post(
            "/api/schedule/generate", json={"section_ids": ["NDLS_CNB_SEC1"]}
        ).json()
    finally:
        main._custom_trains = None


def test_real_verifier_failure_maps_to_safety_invalid_at_api(monkeypatch):
    overlapping = TrainOccupancyWindow(
        train_no="T-OVERLAP",
        section_id="NDLS_CNB_SEC1",
        track_line="UP_LINE",
        start_time_hr=1.0,
        end_time_hr=2.0,
    )

    body = _generate_with_real_verifier(monkeypatch, [overlapping])

    assert body["status"] == "safety_invalid"
    assert any(e["passed"] is False for e in body["audit_trail"])


def test_real_verifier_without_coverage_is_unverified_at_api(monkeypatch):
    elsewhere = TrainOccupancyWindow(
        train_no="T-LATER",
        section_id="NDLS_CNB_SEC1",
        track_line="UP_LINE",
        start_time_hr=5.0,
        end_time_hr=6.0,
    )

    body = _generate_with_real_verifier(monkeypatch, [elsewhere])

    assert body["status"] == "safety_unverified"
    assert not any(e["passed"] is False for e in body["audit_trail"])
    assert body["metrics"]["fol_rule_compliance_pct"] is None
