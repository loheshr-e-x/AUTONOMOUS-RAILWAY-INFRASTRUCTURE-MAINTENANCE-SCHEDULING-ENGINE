import pytest

from backend.app import solver_engine
from backend.app.scenario_metrics import evaluate_objective_components
from backend.app.scenario_validation import (
    canonical_scenario_digest,
    validate_scenario_input,
    validate_schedule,
)
from backend.app.schemas.scenario_contracts import (
    ScenarioAssignment,
    ScenarioComparisonRequest,
)


SECTION = "NDLS_CNB_SEC1"


def _order(work_id="WO-1", **changes):
    value = {
        "work_id": work_id,
        "department": "ENGINEERING",
        "section_id": SECTION,
        "track_line": "UP_LINE",
        "heavy_equipment": False,
        "defect_type": "Inspection",
        "duration_hrs": 1.0,
        "urgency": 2,
        "co_location_allowed": True,
    }
    value.update(changes)
    return value


def _scenario(orders=None, trains=None, **config_changes):
    config = {
        "section_ids": [SECTION],
        "time_horizon_hrs": 8.0,
        "slot_duration_hrs": 0.5,
    }
    config.update(config_changes)
    return ScenarioComparisonRequest.model_validate(
        {
            "scenario_id": "scenario-test",
            "work_orders": orders if orders is not None else [_order()],
            "train_windows": trains if trains is not None else [],
            "solver_configuration": config,
        }
    )


def _assignment(work_id="WO-1", **changes):
    value = {
        "work_id": work_id,
        "department": "ENGINEERING",
        "section_id": SECTION,
        "track_line": "UP_LINE",
        "start_time_hr": 0.0,
        "end_time_hr": 1.0,
        "heavy_equipment": False,
    }
    value.update(changes)
    return value


def _codes(result):
    return {finding.code for finding in result.findings}


def test_canonical_digest_is_stable_across_dictionary_key_order():
    first = _scenario()
    reordered = ScenarioComparisonRequest.model_validate(
        {
            "solver_configuration": {
                "slot_duration_hrs": 0.5,
                "time_horizon_hrs": 8.0,
                "section_ids": [SECTION],
            },
            "train_windows": [],
            "work_orders": [
                {
                    "urgency": 2,
                    "duration_hrs": 1.0,
                    "defect_type": "Inspection",
                    "heavy_equipment": False,
                    "track_line": "UP_LINE",
                    "section_id": SECTION,
                    "department": "ENGINEERING",
                    "work_id": "WO-1",
                    "co_location_allowed": True,
                }
            ],
            "scenario_id": "a-different-presentation-id",
        }
    )

    assert canonical_scenario_digest(first) == canonical_scenario_digest(reordered)


@pytest.mark.parametrize(
    "change",
    [
        {"duration_hrs": 2.0},
        {"track_line": "DOWN_LINE"},
        {"co_location_allowed": False},
    ],
)
def test_canonical_digest_changes_when_work_order_input_changes(change):
    first = _scenario()
    changed = _scenario(orders=[_order(**change)])

    assert canonical_scenario_digest(first) != canonical_scenario_digest(changed)


def test_canonical_digest_changes_when_solver_configuration_changes():
    assert canonical_scenario_digest(_scenario()) != canonical_scenario_digest(
        _scenario(slot_duration_hrs=0.25)
    )


def test_rejects_duplicate_and_unknown_scenario_sections_and_precision():
    duplicate_orders = _scenario(orders=[_order(), _order()])
    assert "DUPLICATE_WORK_ORDER_ID" in _codes(
        validate_scenario_input(duplicate_orders, {SECTION})
    )

    unknown_section = _scenario(
        orders=[_order(section_id="UNKNOWN")],
        section_ids=["UNKNOWN"],
    )
    assert "UNKNOWN_SECTION" in _codes(
        validate_scenario_input(unknown_section, {SECTION})
    )

    unsupported_precision = _scenario(orders=[_order(duration_hrs=1.0001)])
    assert "UNSUPPORTED_NUMERIC_PRECISION" in _codes(
        validate_scenario_input(unsupported_precision, {SECTION})
    )


def test_rejects_unsupported_model_sections_and_horizon():
    unsupported_model = _scenario().model_copy(update={"model_version": "unknown"})
    assert "UNSUPPORTED_MODEL_VERSION" in _codes(
        validate_scenario_input(unsupported_model, {SECTION})
    )

    section_mismatch = _scenario(
        orders=[_order(section_id="NDLS_CNB_SEC2")],
        trains=[
            {
                "train_no": "T1",
                "section_id": "NDLS_CNB_SEC3",
                "track_line": "UP_LINE",
                "start_time_hr": 1.0,
                "end_time_hr": 2.0,
            }
        ],
    )
    assert "SECTION_OUTSIDE_SCENARIO" in _codes(
        validate_scenario_input(section_mismatch)
    )

    excessive_horizon = _scenario(time_horizon_hrs=24.5)
    assert "HORIZON_OUT_OF_RANGE" in _codes(
        validate_scenario_input(excessive_horizon)
    )


def test_rejects_bad_train_interval_before_solver_use():
    invalid = _scenario(
        trains=[
            {
                "train_no": "T1",
                "section_id": SECTION,
                "track_line": "UP_LINE",
                "start_time_hr": 4.0,
                "end_time_hr": 3.0,
            }
        ]
    )

    assert "INVALID_TRAIN_INTERVAL" in _codes(validate_scenario_input(invalid))


def test_duplicate_and_unknown_scheduled_ids_are_reported():
    scenario = _scenario(orders=[_order(), _order("WO-2")])
    duplicate = validate_schedule(
        scenario,
        [_assignment(), _assignment()],
        ["WO-2"],
    )
    unknown = validate_schedule(
        scenario,
        [_assignment(), _assignment("WO-UNKNOWN")],
        [],
    )

    assert "DUPLICATE_SCHEDULED_ID" in _codes(duplicate)
    assert "UNKNOWN_SCHEDULED_ID" in _codes(unknown)
    assert "WORK_ORDER_ACCOUNTING_MISMATCH" in _codes(unknown)


def test_scheduled_and_unscheduled_ids_must_partition_submitted_ids():
    scenario = _scenario(orders=[_order(), _order("WO-2")])
    valid_partial = validate_schedule(scenario, [_assignment()], ["WO-2"])
    missing = validate_schedule(scenario, [_assignment()], [])
    duplicated_unscheduled = validate_schedule(
        scenario, [_assignment()], ["WO-2", "WO-2"]
    )

    assert valid_partial.valid
    assert "WORK_ORDER_ACCOUNTING_MISMATCH" in _codes(missing)
    assert "DUPLICATE_UNSCHEDULED_ID" in _codes(duplicated_unscheduled)


@pytest.mark.parametrize(
    "assignment",
    [
        _assignment(start_time_hr=1.0, end_time_hr=1.0),
        _assignment(start_time_hr=-0.5, end_time_hr=0.5),
        _assignment(start_time_hr=7.5, end_time_hr=8.5),
        _assignment(end_time_hr=2.0),
    ],
)
def test_rejects_invalid_time_intervals_or_horizon_violations(assignment):
    result = validate_schedule(_scenario(), [assignment], [])

    assert not result.valid
    assert _codes(result) & {
        "INVALID_ASSIGNMENT_INTERVAL",
        "ASSIGNMENT_DURATION_MISMATCH",
    }


def test_rejects_assignment_time_precision_not_supported_by_solver_outputs():
    result = validate_schedule(
        _scenario(),
        [
            _assignment(
                start_time_hr=0.0000001,
                end_time_hr=1.0000001,
            )
        ],
        [],
    )

    assert "UNSUPPORTED_ASSIGNMENT_PRECISION" in _codes(result)


@pytest.mark.parametrize("start_time_hr", [float("nan"), float("inf"), float("-inf")])
def test_rejects_non_finite_assignment_times(start_time_hr):
    result = validate_schedule(
        _scenario(),
        [
            _assignment(
                start_time_hr=start_time_hr,
                end_time_hr=start_time_hr,
            )
        ],
        [],
    )

    assert not result.valid
    assert "INVALID_ASSIGNMENT_INTERVAL" in _codes(result)


def test_accepts_grid_aligned_candidate_start():
    result = validate_schedule(
        _scenario(),
        [_assignment(start_time_hr=0.5, end_time_hr=1.5)],
        [],
    )

    assert result.valid


def test_accepts_final_horizon_candidate_off_the_slot_grid():
    scenario = _scenario(time_horizon_hrs=7.3, slot_duration_hrs=0.5)
    result = validate_schedule(
        scenario,
        [_assignment(start_time_hr=6.3, end_time_hr=7.3)],
        [],
    )

    assert result.valid


def test_rejects_off_grid_start_outside_candidate_domain():
    result = validate_schedule(
        _scenario(),
        [_assignment(start_time_hr=0.25, end_time_hr=1.25)],
        [],
    )

    assert "INVALID_CANDIDATE_START" in _codes(result)


def test_rejects_start_removed_by_same_line_train_filtering():
    scenario = _scenario(
        trains=[
            {
                "train_no": "T1",
                "section_id": SECTION,
                "track_line": "UP_LINE",
                "start_time_hr": 1.0,
                "end_time_hr": 2.0,
            }
        ]
    )
    result = validate_schedule(
        scenario,
        [_assignment(start_time_hr=1.0, end_time_hr=2.0)],
        [],
    )

    assert "INVALID_CANDIDATE_START" in _codes(result)
    assert "TRAIN_OCCUPANCY_CONFLICT" in _codes(result)


def test_rejects_start_removed_by_heavy_equipment_adjacent_line_filtering():
    scenario = _scenario(
        orders=[_order(heavy_equipment=True)],
        trains=[
            {
                "train_no": "T1",
                "section_id": SECTION,
                "track_line": "DOWN_LINE",
                "start_time_hr": 1.0,
                "end_time_hr": 2.0,
            }
        ],
    )
    result = validate_schedule(
        scenario,
        [
            _assignment(
                start_time_hr=1.0,
                end_time_hr=2.0,
                heavy_equipment=True,
            )
        ],
        [],
    )

    assert "INVALID_CANDIDATE_START" in _codes(result)
    assert "HEAVY_EQUIPMENT_ADJACENT_TRAIN_CONFLICT" in _codes(result)


def test_opposite_line_train_does_not_filter_non_heavy_candidate():
    scenario = _scenario(
        trains=[
            {
                "train_no": "T1",
                "section_id": SECTION,
                "track_line": "DOWN_LINE",
                "start_time_hr": 1.0,
                "end_time_hr": 2.0,
            }
        ]
    )
    result = validate_schedule(
        scenario,
        [_assignment(start_time_hr=1.0, end_time_hr=2.0)],
        [],
    )

    assert result.valid


def test_rejects_same_department_overlap_on_same_section_and_line():
    scenario = _scenario(orders=[_order(), _order("WO-2")])
    result = validate_schedule(
        scenario,
        [_assignment(), _assignment("WO-2", start_time_hr=0.5, end_time_hr=1.5)],
        [],
    )

    assert "SAME_DEPARTMENT_OVERLAP" in _codes(result)


def test_allows_bilateral_exact_window_cross_department_colocation():
    scenario = _scenario(
        orders=[
            _order(),
            _order("WO-2", department="SIGNALLING"),
        ]
    )
    result = validate_schedule(
        scenario,
        [_assignment(), _assignment("WO-2", department="SIGNALLING")],
        [],
    )
    components = evaluate_objective_components(
        scenario,
        [
            ScenarioAssignment.model_validate(_assignment()),
            ScenarioAssignment.model_validate(
                _assignment("WO-2", department="SIGNALLING")
            ),
        ],
        result,
    )

    assert result.valid
    assert components.co_location_merge_count.value == 1


@pytest.mark.parametrize(
    "second_order,second_assignment,first_order",
    [
        (
            _order("WO-2", department="SIGNALLING", co_location_allowed=False),
            _assignment("WO-2", department="SIGNALLING"),
            _order(),
        ),
        (
            _order("WO-2", department="SIGNALLING"),
            _assignment("WO-2", department="SIGNALLING"),
            _order(co_location_allowed=False),
        ),
        (
            _order("WO-2", department="SIGNALLING"),
            _assignment(
                "WO-2",
                department="SIGNALLING",
                start_time_hr=0.5,
                end_time_hr=1.5,
            ),
            _order(),
        ),
    ],
)
def test_rejects_cross_department_overlap_without_required_colocation(
    second_order, second_assignment, first_order
):
    scenario = _scenario(orders=[first_order, second_order])
    result = validate_schedule(scenario, [_assignment(), second_assignment], [])

    assert "INVALID_CROSS_DEPARTMENT_COLOCATION" in _codes(result)


@pytest.mark.parametrize(
    "second_order,second_assignment",
    [
        (
            _order("WO-2", section_id="NDLS_CNB_SEC2"),
            _assignment(
                "WO-2",
                section_id="NDLS_CNB_SEC2",
                start_time_hr=0.5,
                end_time_hr=1.5,
            ),
        ),
        (
            _order("WO-2", track_line="DOWN_LINE"),
            _assignment(
                "WO-2",
                track_line="DOWN_LINE",
                start_time_hr=0.5,
                end_time_hr=1.5,
            ),
        ),
    ],
)
def test_different_sections_or_track_lines_remain_compatible(
    second_order, second_assignment
):
    scenario = _scenario(
        orders=[_order(), second_order],
        section_ids=[SECTION, "NDLS_CNB_SEC2"],
    )

    assert validate_schedule(
        scenario, [_assignment(), second_assignment], []
    ).valid


def test_detects_listed_train_occupancy_conflict_and_clearance():
    scenario = _scenario(
        trains=[
            {
                "train_no": "T1",
                "section_id": SECTION,
                "track_line": "UP_LINE",
                "start_time_hr": 1.0,
                "end_time_hr": 2.0,
            }
        ],
        train_clearance_hrs=0.25,
    )
    result = validate_schedule(scenario, [_assignment()], [])

    assert "TRAIN_OCCUPANCY_CONFLICT" in _codes(result)


def test_half_open_train_and_clearance_boundaries_do_not_conflict():
    train_boundary = _scenario(
        trains=[
            {
                "train_no": "T1",
                "section_id": SECTION,
                "track_line": "UP_LINE",
                "start_time_hr": 1.0,
                "end_time_hr": 2.0,
            }
        ]
    )
    clearance_boundary = _scenario(
        trains=[
            {
                "train_no": "T1",
                "section_id": SECTION,
                "track_line": "UP_LINE",
                "start_time_hr": 1.0,
                "end_time_hr": 2.5,
            }
        ],
        train_clearance_hrs=0.5,
    )

    assert validate_schedule(
        train_boundary,
        [_assignment(start_time_hr=2.0, end_time_hr=3.0)],
        [],
    ).valid
    assert validate_schedule(
        clearance_boundary,
        [_assignment(start_time_hr=3.0, end_time_hr=4.0)],
        [],
    ).valid


def test_heavy_equipment_is_filtered_against_opposite_line_train():
    train = {
        "train_no": "T1",
        "section_id": SECTION,
        "track_line": "DOWN_LINE",
        "start_time_hr": 1.0,
        "end_time_hr": 2.0,
    }
    ordinary = _scenario(trains=[train])
    heavy = _scenario(
        orders=[_order(heavy_equipment=True)],
        trains=[train],
    )
    assert validate_schedule(ordinary, [_assignment()], []).valid
    assert "HEAVY_EQUIPMENT_ADJACENT_TRAIN_CONFLICT" in _codes(
        validate_schedule(
            heavy,
            [
                _assignment(
                    heavy_equipment=True,
                    start_time_hr=0.5,
                    end_time_hr=1.5,
                )
            ],
            [],
        )
    )


def test_validator_does_not_depend_on_solver_compatibility_helpers(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("solver compatibility helper must not be used")

    monkeypatch.setattr(solver_engine, "_compatible", forbidden)
    scenario = _scenario(orders=[_order(), _order("WO-2", department="SIGNALLING")])
    result = validate_schedule(
        scenario,
        [_assignment(), _assignment("WO-2", department="SIGNALLING")],
        [],
    )

    assert result.valid


def test_objective_components_remain_separate_and_unweighted():
    scenario = _scenario()
    result = validate_schedule(scenario, [_assignment()], [])
    components = evaluate_objective_components(
        scenario,
        [ScenarioAssignment.model_validate(_assignment())],
        result,
    )

    assert components.time_of_day_train_gap.available
    assert components.time_of_day_train_gap.value == pytest.approx(0.25)
    assert components.department_workload_imbalance.available
    assert components.department_workload_imbalance.value == pytest.approx(2 / 9)
    assert components.co_location_merge_count.value == 0
    assert not components.schedule_stability.available
    assert not components.utilization.available


def test_time_component_includes_same_line_train_gap_cost():
    scenario = _scenario(
        trains=[
            {
                "train_no": "T1",
                "section_id": SECTION,
                "track_line": "UP_LINE",
                "start_time_hr": 2.0,
                "end_time_hr": 3.0,
            }
        ]
    )
    schedule = [ScenarioAssignment.model_validate(_assignment())]
    validation = validate_schedule(scenario, schedule, [])
    components = evaluate_objective_components(scenario, schedule, validation)

    assert components.time_of_day_train_gap.value == pytest.approx(0.75)
