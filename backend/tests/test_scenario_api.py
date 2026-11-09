from fastapi.testclient import TestClient

from backend.app import main
from backend.app.schemas.contracts import AuditLogEntry, MaintenanceWorkOrder


client = TestClient(main.app)


def _order(work_id="GLOBAL-ONLY"):
    return MaintenanceWorkOrder.model_validate(
        {
            "work_id": work_id,
            "department": "ENGINEERING",
            "section_id": "NDLS_CNB_SEC1",
            "track_line": "UP_LINE",
            "heavy_equipment": False,
            "defect_type": "Inspection",
            "duration_hrs": 1.0,
            "urgency": 2,
            "co_location_allowed": True,
        }
    )


def test_scenario_route_ignores_global_work_orders_and_never_calls_safety(
    monkeypatch,
):
    monkeypatch.setattr(main, "_custom_work_orders", [_order()])
    monkeypatch.setattr(
        main,
        "_last_audit_trail",
        [
            AuditLogEntry(
                rule_name="sentinel",
                predicate_evaluated="unchanged",
                passed=None,
                explanation="",
            )
        ],
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("experimental comparison must not invoke safety verification")

    monkeypatch.setattr(main, "verify_safety_invariants", forbidden)
    response = client.post(
        "/api/experimental/scenarios/compare",
        json={
            "scenario_id": "empty-api-scenario",
            "scenario_name": "Empty scenario",
            "work_orders": [],
            "train_windows": [],
            "solver_configuration": {
                "section_ids": ["NDLS_CNB_SEC1"],
                "time_horizon_hrs": 8.0,
                "slot_duration_hrs": 0.5,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["comparison_status"] == "completed"
    assert body["paired_inputs_match"] is True
    assert body["baseline"]["total_work_orders"] == 0
    assert body["cp_sat"]["total_work_orders"] == 0
    assert body["baseline"]["solver_outcome"] == "no_work"
    assert body["cp_sat"]["solver_outcome"] == "no_work"
    assert main._last_audit_trail[0].rule_name == "sentinel"


def test_scenario_route_returns_useful_validation_error_for_unknown_section():
    response = client.post(
        "/api/experimental/scenarios/compare",
        json={
            "scenario_id": "invalid-section",
            "work_orders": [],
            "train_windows": [],
            "solver_configuration": {
                "section_ids": ["UNKNOWN-SECTION"],
                "time_horizon_hrs": 8.0,
                "slot_duration_hrs": 0.5,
            },
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["code"] == "UNKNOWN_SECTION"
