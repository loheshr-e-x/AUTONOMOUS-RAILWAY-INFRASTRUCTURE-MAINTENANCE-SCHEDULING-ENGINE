import pytest
from fastapi.testclient import TestClient

from backend.app import main

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


@pytest.mark.parametrize("route", ["NDLS_CNB", "HWH_PURI", "BCT_AMD"])
def test_generate_per_route(route):
    body = client.post("/api/schedule/generate", json={"section_ids": [route]}).json()
    assert body["status"] == "success"
    assert len(body["schedule"]) >= 20


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
