from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from backend.app import main
from backend.app.data_engine import ROUTES
from backend.app.scenario_validation import canonical_scenario_digest
from backend.app.schemas.contracts import (
    Department,
    MaintenanceWorkOrder,
    SolverRequest,
    TrackLine,
    TrainOccupancyWindow,
    UrgencyLevel,
)
from backend.app.schemas.domain import (
    AvailabilityStatus,
    DataOrigin,
    DataProvenance,
    DependencyType,
    DomainTimeInterval,
    RailwayDomainModel,
    RailwayRoute,
    RailwaySection,
    RailwayTrainOccupancy,
    RailwayTrainService,
    Resource,
    ResourceRequirement,
    VerificationStatus,
    WorkCondition,
    WorkDependency,
)
from backend.app.schemas.domain_adapters import (
    DomainAdapterError,
    OccupancyConversionContext,
    build_railway_domain_model,
    maintenance_work_order_to_domain,
    route_sections_to_domain,
    route_to_domain,
    train_occupancy_window_to_domain,
)
from backend.app.schemas.scenario_contracts import ScenarioComparisonRequest
from backend.app.solver_engine import _normalise_inputs


START = datetime(2026, 6, 1, 1, tzinfo=timezone.utc)
END = datetime(2026, 6, 1, 2, tzinfo=timezone.utc)


def _legacy_order(work_id: str = "WO-1", **changes):
    value = {
        "work_id": work_id,
        "department": "ENGINEERING",
        "section_id": "R1-S1",
        "track_line": "UP_LINE",
        "defect_type": "Inspection",
        "duration_hrs": 1.0,
        "urgency": 2,
        "co_location_allowed": True,
    }
    value.update(changes)
    return value


def _domain_payload(**changes):
    payload = {
        "schema_version": 1,
        "routes": [
            {
                "route_id": "R1",
                "name": "Synthetic route",
                "origin": "Origin",
                "destination": "Destination",
                "length_km": 10.0,
                "sections": ["R1-S1"],
            }
        ],
        "sections": [
            {
                "section_id": "R1-S1",
                "route_id": "R1",
                "name": "Section 1",
                "start_km": 0.0,
                "end_km": 10.0,
                "track_lines": ["UP_LINE"],
                "infrastructure_metadata": {"electrification": "unknown"},
                "provenance": {"origin": "UNKNOWN"},
            }
        ],
        "train_services": [
            {
                "train_id": "TRAIN-1",
                "train_number": "00001",
                "route_id": "R1",
            }
        ],
        "train_occupancies": [
            {
                "occupancy_id": "OCC-1",
                "train_id": "TRAIN-1",
                "section_id": "R1-S1",
                "track_line": "UP_LINE",
                "entry_time": START.isoformat(),
                "exit_time": END.isoformat(),
                "source": "synthetic fixture",
                "observation_timestamp": START.isoformat(),
                "provenance": {
                    "origin": "SYNTHETIC",
                    "source_label": "synthetic fixture",
                    "verification_status": "UNVERIFIED",
                    "confidence": 0.5,
                },
            }
        ],
        "work_orders": [
            _legacy_order("WO-1", prerequisites=["WO-0"]),
            _legacy_order("WO-0", defect_type="Prerequisite work"),
        ],
        "block_windows": [
            {
                "block_id": "BLOCK-1",
                "section_id": "R1-S1",
                "track_line": "UP_LINE",
                "start_time": START.isoformat(),
                "end_time": END.isoformat(),
                "availability_status": "UNKNOWN",
                "source": "synthetic timetable",
                "provenance": {"origin": "SYNTHETIC"},
            }
        ],
        "resources": [
            {
                "resource_id": "CREW-1",
                "resource_type": "track_crew",
                "department": "ENGINEERING",
                "capacity": 4,
                "availability_intervals": [
                    {
                        "start_time": START.isoformat(),
                        "end_time": END.isoformat(),
                        "section_id": "R1-S1",
                    }
                ],
                "section_id": "R1-S1",
                "provenance": {"origin": "USER_SUPPLIED"},
            }
        ],
        "dependencies": [
            {
                "dependency_id": "DEP-1",
                "work_id": "WO-0",
                "related_work_id": "WO-1",
                "relationship": "PREREQUISITE",
            }
        ],
    }
    payload.update(changes)
    return payload


def test_valid_domain_model_resolves_references_and_preserves_unknowns():
    model = RailwayDomainModel.model_validate(_domain_payload())

    assert len(model.routes) == len(model.sections) == 1
    assert model.work_orders[0].prerequisites == ["WO-0"]
    assert model.train_occupancies[0].provenance.origin is DataOrigin.SYNTHETIC
    assert (
        model.train_occupancies[0].provenance.verification_status
        is VerificationStatus.UNVERIFIED
    )
    assert model.block_windows[0].availability_status is AvailabilityStatus.UNKNOWN
    assert model.sections[0].provenance.origin is DataOrigin.UNKNOWN
    assert {department.department_id for department in model.departments} == set(
        Department
    )


def test_domain_route_section_and_train_references_are_validated():
    with pytest.raises(ValidationError, match="unknown route_id"):
        RailwayDomainModel.model_validate(
            _domain_payload(
                sections=[
                    {
                        "section_id": "R1-S1",
                        "route_id": "missing-route",
                        "name": "Section 1",
                    }
                ]
            )
        )

    with pytest.raises(ValidationError, match="not listed by its route"):
        RailwayDomainModel.model_validate(
            _domain_payload(
                routes=[
                    {
                        "route_id": "R1",
                        "name": "Synthetic route",
                        "origin": "Origin",
                        "destination": "Destination",
                        "sections": [],
                    }
                ]
            )
        )

    with pytest.raises(ValidationError, match="unknown train_id"):
        RailwayDomainModel.model_validate(
            _domain_payload(
                train_occupancies=[
                    {
                        "occupancy_id": "OCC-1",
                        "train_id": "MISSING",
                        "section_id": "R1-S1",
                        "track_line": "UP_LINE",
                        "entry_time": START.isoformat(),
                        "exit_time": END.isoformat(),
                    }
                ]
            )
        )


def test_occupancy_and_work_order_track_lines_must_exist_on_known_section():
    payload = _domain_payload()
    payload["train_occupancies"][0]["track_line"] = "DOWN_LINE"
    with pytest.raises(ValidationError, match="track line not present"):
        RailwayDomainModel.model_validate(payload)

    payload = _domain_payload()
    payload["work_orders"][0]["track_line"] = "DOWN_LINE"
    with pytest.raises(ValidationError, match="track line not present"):
        RailwayDomainModel.model_validate(payload)


def test_occupancy_spatial_endpoints_must_be_a_valid_interval():
    with pytest.raises(ValidationError, match="must be supplied together"):
        RailwayTrainOccupancy.model_validate(
            {
                "occupancy_id": "OCC-1",
                "train_id": "TRAIN-1",
                "section_id": "R1-S1",
                "entry_time": START.isoformat(),
                "exit_time": END.isoformat(),
                "start_km": 0,
            }
        )
    with pytest.raises(ValidationError, match="end_km must exceed"):
        RailwayTrainOccupancy.model_validate(
            {
                "occupancy_id": "OCC-1",
                "train_id": "TRAIN-1",
                "section_id": "R1-S1",
                "entry_time": START.isoformat(),
                "exit_time": END.isoformat(),
                "start_km": 2,
                "end_km": 2,
            }
        )


def test_duplicate_entity_and_relationship_identifiers_are_rejected():
    payload = _domain_payload()
    payload["sections"].append(payload["sections"][0])
    with pytest.raises(ValidationError, match="duplicate section_id"):
        RailwayDomainModel.model_validate(payload)

    payload = _domain_payload()
    payload["dependencies"].append(payload["dependencies"][0])
    with pytest.raises(ValidationError, match="duplicate dependency_id"):
        RailwayDomainModel.model_validate(payload)


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (
            RailwayRoute,
            {
                "route_id": "R",
                "name": "R",
                "origin": "A",
                "destination": "B",
                "length_km": 0,
            },
        ),
        (
            RailwaySection,
            {
                "section_id": "S",
                "route_id": "R",
                "name": "S",
                "start_km": 4,
                "end_km": 3,
            },
        ),
        (
            DomainTimeInterval,
            {
                "start_time": END.isoformat(),
                "end_time": START.isoformat(),
            },
        ),
        (
            RailwayTrainOccupancy,
            {
                "occupancy_id": "O",
                "train_id": "T",
                "section_id": "S",
                "track_line": "UP_LINE",
                "entry_time": START.isoformat(),
                "exit_time": START.isoformat(),
            },
        ),
        (
            DomainTimeInterval,
            {
                "start_time": "2026-06-01T01:00:00",
                "end_time": END.isoformat(),
            },
        ),
    ],
)
def test_invalid_spatial_and_temporal_intervals_are_rejected(model, payload):
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_work_order_and_dependency_prerequisite_cycles_are_rejected():
    payload = _domain_payload()
    payload["work_orders"] = [
        _legacy_order("WO-1", prerequisites=["WO-0"]),
        _legacy_order("WO-0", prerequisites=["WO-1"]),
    ]
    payload["dependencies"] = []

    with pytest.raises(ValidationError, match="prerequisite cycle"):
        RailwayDomainModel.model_validate(payload)

    payload = _domain_payload()
    payload["work_orders"] = [
        _legacy_order("WO-1"),
        _legacy_order("WO-0", defect_type="Prerequisite work"),
    ]
    payload["dependencies"] = [
        {
            "dependency_id": "DEP-1",
            "work_id": "WO-0",
            "related_work_id": "WO-1",
            "relationship": "PREREQUISITE",
        },
        {
            "dependency_id": "DEP-2",
            "work_id": "WO-1",
            "related_work_id": "WO-0",
            "relationship": "PREREQUISITE",
        },
    ]
    with pytest.raises(ValidationError, match="prerequisite cycle"):
        RailwayDomainModel.model_validate(payload)


@pytest.mark.parametrize("capacity", [0, -1, float("inf")])
def test_invalid_resource_capacity_is_rejected(capacity):
    with pytest.raises(ValidationError):
        Resource.model_validate(
            {
                "resource_id": "R",
                "resource_type": "crew",
                "department": "ENGINEERING",
                "capacity": capacity,
            }
        )


@pytest.mark.parametrize("quantity", [0, -2])
def test_invalid_required_resource_quantity_is_rejected(quantity):
    with pytest.raises(ValidationError):
        ResourceRequirement.model_validate(
            {"resource_type": "crew", "quantity": quantity}
        )


def test_unknown_and_synthetic_provenance_never_imply_authentication():
    unknown = DataProvenance()
    synthetic = DataProvenance.model_validate(
        {"origin": "SYNTHETIC", "source_label": "manual label"}
    )

    assert unknown.origin is DataOrigin.UNKNOWN
    assert unknown.verification_status is VerificationStatus.UNKNOWN
    assert synthetic.verification_status is VerificationStatus.UNVERIFIED
    with pytest.raises(ValidationError, match="authentication requires"):
        DataProvenance.model_validate(
            {
                "origin": "PUBLIC_DATA",
                "source_label": "trusted-looking source",
                "verification_status": "AUTHENTICATED",
                "verified_at": START.isoformat(),
                "verified_by": "reviewer",
                "verification_reference": "record-1",
            }
        )
    with pytest.raises(ValidationError, match="verification evidence"):
        DataProvenance.model_validate(
            {
                "origin": "AUTHENTICATED_EXTERNAL",
                "source_label": "external source",
                "verification_status": "AUTHENTICATED",
            }
        )


def test_resource_and_dependency_references_are_checked_without_inventing_resources():
    payload = _domain_payload()
    payload["work_orders"][0]["resource_requirements"] = [
        {"resource_type": "specialist_crew", "quantity": 2}
    ]
    assert RailwayDomainModel.model_validate(payload).work_orders[0]

    payload["dependencies"][0]["related_work_id"] = "MISSING"
    with pytest.raises(ValidationError, match="unknown work order"):
        RailwayDomainModel.model_validate(payload)


def test_legacy_work_order_and_production_custom_order_api_remain_compatible(monkeypatch):
    payload = _legacy_order(work_id="LEGACY-1", section_id="NDLS_CNB_SEC1")
    legacy = MaintenanceWorkOrder.model_validate(payload)
    assert legacy.department is Department.ENGINEERING
    assert legacy.track_line is TrackLine.UP_LINE
    assert legacy.urgency is UrgencyLevel.MEDIUM
    assert legacy.provenance.origin is DataOrigin.UNKNOWN
    assert legacy.resource_requirements is None
    assert legacy.prerequisites is None

    client = TestClient(main.app)
    monkeypatch.setattr(main, "_custom_work_orders", None)
    response = client.post("/api/data/work-orders/custom", json=[payload])
    assert response.status_code == 200
    returned = response.json()[0]
    assert set(returned) == {
        "work_id",
        "department",
        "section_id",
        "track_line",
        "heavy_equipment",
        "defect_type",
        "duration_hrs",
        "urgency",
        "co_location_allowed",
    }
    assert type(returned["work_id"]) is str
    assert type(returned["duration_hrs"]) is float
    assert type(returned["urgency"]) is int
    assert returned == {
        "work_id": "LEGACY-1",
        "department": "ENGINEERING",
        "section_id": "NDLS_CNB_SEC1",
        "track_line": "UP_LINE",
        "heavy_equipment": False,
        "defect_type": "Inspection",
        "duration_hrs": 1.0,
        "urgency": 2,
        "co_location_allowed": True,
    }

    get_response = client.get("/api/data/work-orders", params={"route_id": "NDLS_CNB"})
    assert get_response.status_code == 200
    assert set(get_response.json()[0]) == set(returned)


def test_production_work_order_api_accepts_metadata_without_changing_response(monkeypatch):
    client = TestClient(main.app)
    monkeypatch.setattr(main, "_custom_work_orders", None)
    payload = _legacy_order(
        work_id="META-1",
        section_id="NDLS_CNB_SEC1",
        resource_requirements=[{"resource_type": "crew", "quantity": 3}],
        prerequisites=[],
        provenance={"origin": "USER_SUPPLIED", "source_label": "manual input"},
    )

    response = client.post("/api/data/work-orders/custom", json=[payload])

    assert response.status_code == 200
    assert set(response.json()[0]) == {
        "work_id",
        "department",
        "section_id",
        "track_line",
        "heavy_equipment",
        "defect_type",
        "duration_hrs",
        "urgency",
        "co_location_allowed",
    }
    stored = main._custom_work_orders[0]
    assert stored.resource_requirements[0].quantity == 3
    assert stored.provenance.origin is DataOrigin.USER_SUPPLIED


def test_work_order_domain_adapter_round_trips_supported_fields():
    legacy = MaintenanceWorkOrder.model_validate(
        _legacy_order(
            resource_requirements=[{"resource_type": "crew", "quantity": 2}],
            prerequisites=[],
            permitted_work_conditions=[
                {"condition_id": "daylight", "description": "Work during daylight"}
            ],
            provenance={
                "origin": "USER_SUPPLIED",
                "source_label": "operator input",
            },
        )
    )

    domain_order = maintenance_work_order_to_domain(legacy)

    assert domain_order is not legacy
    assert domain_order.model_dump(mode="json") == legacy.model_dump(mode="json")


def test_additive_work_order_metadata_does_not_change_solver_normalization():
    base = MaintenanceWorkOrder.model_validate(_legacy_order())
    enriched = MaintenanceWorkOrder.model_validate(
        _legacy_order(
            resource_requirements=[{"resource_type": "crew", "quantity": 8}],
            prerequisites=["OTHER-WORK"],
            permitted_work_conditions=[{"condition_id": "condition"}],
            provenance={"origin": "USER_SUPPLIED", "source_label": "form"},
        )
    )
    config = SolverRequest(section_ids=["R1-S1"])

    base_solver_inputs = _normalise_inputs([base], [], config)
    enriched_solver_inputs = _normalise_inputs([enriched], [], config)

    assert enriched_solver_inputs == base_solver_inputs


def test_train_occupancy_adapter_requires_explicit_date_and_timezone():
    window = TrainOccupancyWindow(
        train_no="00042",
        section_id="NDLS_CNB_SEC1",
        track_line="UP_LINE",
        start_time_hr=1.5,
        end_time_hr=2.25,
    )

    with pytest.raises(DomainAdapterError, match="operating date and timezone"):
        train_occupancy_window_to_domain(
            window,
            context=None,
            occupancy_id="OCC-1",
        )

    converted = train_occupancy_window_to_domain(
        window,
        context=OccupancyConversionContext(
            operating_date=date(2026, 6, 1),
            timezone=ZoneInfo("Asia/Kolkata"),
        ),
        occupancy_id="OCC-1",
    )
    assert converted.entry_time == datetime(
        2026, 6, 1, 1, 30, tzinfo=ZoneInfo("Asia/Kolkata")
    )
    assert converted.exit_time == datetime(
        2026, 6, 1, 2, 15, tzinfo=ZoneInfo("Asia/Kolkata")
    )
    assert converted.entry_time.utcoffset() == timedelta(hours=5, minutes=30)
    assert converted.entry_time.date() == date(2026, 6, 1)
    assert converted.provenance.origin is DataOrigin.UNKNOWN
    assert converted.provenance.verification_status is VerificationStatus.UNKNOWN


def test_occupancy_adapter_preserves_spatial_and_supplied_provenance_fields():
    synthetic_provenance = DataProvenance.model_validate(
        {
            "origin": "SYNTHETIC",
            "source_label": "simulated timetable",
            "confidence": 0.4,
        }
    )
    converted = train_occupancy_window_to_domain(
        TrainOccupancyWindow(
            train_no="42",
            section_id="NDLS_CNB_SEC1",
            track_line="DOWN_LINE",
            start_time_hr=23,
            end_time_hr=24,
            train_start_km=0,
            train_end_km=146.6,
        ),
        context=OccupancyConversionContext(
            operating_date=date(2026, 6, 1),
            timezone=timezone.utc,
        ),
        occupancy_id="OCC-42-0",
        provenance=synthetic_provenance,
    )

    assert converted.entry_time == datetime(2026, 6, 1, 23, tzinfo=timezone.utc)
    assert converted.exit_time == datetime(2026, 6, 2, 0, tzinfo=timezone.utc)
    assert converted.start_km == 0
    assert converted.end_km == 146.6
    assert converted.provenance.origin is DataOrigin.SYNTHETIC
    assert converted.provenance.verification_status is VerificationStatus.UNVERIFIED
    assert converted.source == "simulated timetable"


@pytest.mark.parametrize(
    ("operating_date", "start_hour", "message"),
    [
        (date(2026, 3, 8), 2.5, "does not exist"),
        (date(2026, 11, 1), 1.5, "is ambiguous"),
    ],
)
def test_occupancy_adapter_rejects_nonexistent_or_ambiguous_local_times(
    operating_date, start_hour, message
):
    with pytest.raises(DomainAdapterError, match=message):
        train_occupancy_window_to_domain(
            TrainOccupancyWindow(
                train_no="42",
                section_id="NDLS_CNB_SEC1",
                start_time_hr=start_hour,
                end_time_hr=start_hour + 0.25,
            ),
            context=OccupancyConversionContext(
                operating_date=operating_date,
                timezone=ZoneInfo("America/New_York"),
            ),
            occupancy_id="OCC-42",
        )


def test_route_adapters_preserve_known_positions_and_mark_synthetic_provenance():
    route = ROUTES["NDLS_CNB"]

    converted_route = route_to_domain(route)
    converted_sections = route_sections_to_domain(route)

    assert converted_route.sections == [item.section_id for item in converted_sections]
    assert converted_route.length_km == route.length_km
    assert converted_route.provenance.origin is DataOrigin.SYNTHETIC
    assert all(item.track_lines is None for item in converted_sections)
    assert all(item.start_km is not None and item.end_km is not None for item in converted_sections)
    assert all(
        item.provenance.verification_status is VerificationStatus.UNVERIFIED
        for item in converted_sections
    )


def test_aggregate_builder_reports_unconvertible_occupancies_and_validates_graph():
    route = ROUTES["NDLS_CNB"]
    window = TrainOccupancyWindow(
        train_no="42",
        section_id=route.section_ids[0],
        start_time_hr=1,
        end_time_hr=2,
    )
    order = MaintenanceWorkOrder.model_validate(
        _legacy_order(section_id=route.section_ids[0])
    )

    without_context = build_railway_domain_model(
        routes=[route],
        work_orders=[order],
        train_windows=[window],
    )
    assert without_context.model is not None
    assert not without_context.is_complete
    assert len(without_context.issues) == 1
    assert without_context.issues[0].code == "OCCUPANCY_TIME_CONTEXT_REQUIRED"
    assert without_context.issues[0].record_id == "42:0"
    assert without_context.model.train_occupancies == []

    with_context = build_railway_domain_model(
        routes=[route],
        work_orders=[order],
        train_windows=[window],
        occupancy_context=OccupancyConversionContext(
            operating_date=date(2026, 6, 1),
            timezone=timezone.utc,
        ),
    )
    assert with_context.is_complete
    assert with_context.model is not None
    assert len(with_context.model.train_occupancies) == 1
    assert with_context.model.train_occupancies[0].train_id == "NDLS_CNB:42"

    invalid_reference = build_railway_domain_model(
        routes=[route],
        work_orders=[MaintenanceWorkOrder.model_validate(_legacy_order())],
    )
    assert invalid_reference.model is None
    assert invalid_reference.issues[0].code == "DOMAIN_GRAPH_VALIDATION_FAILED"


def test_aggregate_builder_reports_unknown_occupancy_section_without_silent_drop():
    result = build_railway_domain_model(
        routes=[ROUTES["NDLS_CNB"]],
        train_windows=[
            TrainOccupancyWindow(
                train_no="42",
                section_id="NOT-A-REAL-SECTION",
                start_time_hr=1,
                end_time_hr=2,
            )
        ],
    )

    assert result.model is not None
    assert not result.is_complete
    assert result.issues[0].code == "UNKNOWN_OCCUPANCY_SECTION"


def test_aggregate_builder_validates_supplied_domain_relationships():
    route = ROUTES["NDLS_CNB"]
    order = MaintenanceWorkOrder.model_validate(
        _legacy_order("WO-1", section_id=route.section_ids[0])
    )
    result = build_railway_domain_model(
        routes=[route],
        work_orders=[order],
        dependencies=[
            WorkDependency(
                dependency_id="DEP-1",
                work_id="WO-1",
                related_work_id="MISSING",
                relationship=DependencyType.PREREQUISITE,
            )
        ],
    )

    assert result.model is None
    assert result.issues[0].code == "DOMAIN_GRAPH_VALIDATION_FAILED"
    assert "unknown work order" in result.issues[0].message


def test_experimental_scenario_contract_and_digest_remain_unchanged():
    request_data = {
        "scenario_id": "compatibility",
        "work_orders": [
            {
                "work_id": "WO-1",
                "department": "ENGINEERING",
                "section_id": "NDLS_CNB_SEC1",
                "track_line": "UP_LINE",
                "defect_type": "Inspection",
                "duration_hrs": 1.0,
                "urgency": 2,
            }
        ],
        "train_windows": [],
        "solver_configuration": {
            "section_ids": ["NDLS_CNB_SEC1"],
            "time_horizon_hrs": 8.0,
            "slot_duration_hrs": 0.5,
        },
    }
    request = ScenarioComparisonRequest.model_validate(request_data)

    assert set(request.model_dump(mode="json")) == {
        "scenario_id",
        "scenario_name",
        "model_version",
        "work_orders",
        "train_windows",
        "solver_configuration",
        "input_digest",
    }
    assert set(request.work_orders[0].model_dump(mode="json")) == {
        "work_id",
        "department",
        "section_id",
        "track_line",
        "heavy_equipment",
        "defect_type",
        "duration_hrs",
        "urgency",
        "co_location_allowed",
    }
    assert canonical_scenario_digest(request)
