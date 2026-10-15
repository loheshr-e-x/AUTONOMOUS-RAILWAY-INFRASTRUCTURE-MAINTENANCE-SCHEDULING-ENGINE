"""Pure-Python forward-chaining safety verification for scheduled rail work."""

from dataclasses import dataclass
from math import isfinite
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .schemas.contracts import (
    AuditLogEntry,
    Department,
    ScheduledBlockAssignment,
    TrackLine,
    TrainOccupancyWindow,
)

MIN_SAFETY_BUFFER_METERS = 1_000.0
ENHANCED_SAFETY_BUFFER_METERS = 2_000.0
ADJACENT_TRACK_BUFFER_METERS = 1_000.0

Fact = Tuple[object, ...]
Bindings = Dict[str, object]
Coordinates = Tuple[float, float, float, float]


@dataclass(frozen=True)
class _Rule:
    premises: Tuple[Fact, ...]
    conclusion: Fact


def _unify(pattern: Fact, fact: Fact, bindings: Bindings) -> Optional[Bindings]:
    if len(pattern) != len(fact):
        return None

    result = dict(bindings)
    for expected, actual in zip(pattern, fact):
        if isinstance(expected, str) and expected.startswith("?"):
            if expected in result and result[expected] != actual:
                return None
            result[expected] = actual
        elif expected != actual:
            return None
    return result


def _match_premises(
    premises: Sequence[Fact], facts: Sequence[Fact], bindings: Bindings
) -> Iterable[Bindings]:
    if not premises:
        yield bindings
        return

    first, *remaining = premises
    for fact in facts:
        matched = _unify(first, fact, bindings)
        if matched is not None:
            yield from _match_premises(remaining, facts, matched)


class _ForwardChainingEngine:
    def __init__(self, rules: Sequence[_Rule]) -> None:
        self._rules = rules

    def infer(self, initial_facts: Iterable[Fact]) -> Set[Fact]:
        facts = set(initial_facts)
        changed = True
        while changed:
            changed = False
            for rule in self._rules:
                for bindings in _match_premises(rule.premises, tuple(facts), {}):
                    conclusion = tuple(
                        bindings.get(term, term)
                        if isinstance(term, str) and term.startswith("?")
                        else term
                        for term in rule.conclusion
                    )
                    if conclusion not in facts:
                        facts.add(conclusion)
                        changed = True
        return facts


_SAFETY_RULES = (
    _Rule(
        premises=(
            ("same_section", "?assignment", "?train"),
            ("time_overlap", "?assignment", "?train"),
        ),
        conclusion=("clearance_violation", "?assignment", "?train"),
    ),
    _Rule(
        premises=(
            ("traction_work", "?assignment"),
            ("isolation_missing", "?assignment"),
        ),
        conclusion=("traction_isolation_violation", "?assignment"),
    ),
    _Rule(
        premises=(
            ("same_section", "?assignment", "?train"),
            ("time_overlap", "?assignment", "?train"),
            ("buffer_short", "?assignment", "?train"),
        ),
        conclusion=("distance_buffer_violation", "?assignment", "?train"),
    ),
    _Rule(
        premises=(
            ("same_section", "?assignment", "?train"),
            ("time_overlap", "?assignment", "?train"),
            ("spatial_data_unverifiable", "?assignment", "?train"),
        ),
        conclusion=("distance_buffer_unverified", "?assignment", "?train"),
    ),
    _Rule(
        premises=(
            ("heavy_up_line_work", "?assignment"),
            ("adjacent_down_train", "?assignment", "?train"),
            ("time_overlap", "?assignment", "?train"),
            ("adjacent_buffer_short", "?assignment", "?train"),
        ),
        conclusion=("adjacent_track_violation", "?assignment", "?train"),
    ),
)


def _valid_time_interval(start: float, end: float) -> bool:
    return isfinite(start) and isfinite(end) and 0.0 <= start < end <= 24.0


def _time_intervals_overlap(
    assignment: ScheduledBlockAssignment, train: TrainOccupancyWindow
) -> bool:
    return max(assignment.start_time_hr, train.start_time_hr) < min(
        assignment.end_time_hr, train.end_time_hr
    )


def _spatial_coordinates(
    assignment: ScheduledBlockAssignment, train: TrainOccupancyWindow
) -> Optional[Coordinates]:
    values = (
        assignment.worksite_start_km,
        assignment.worksite_end_km,
        train.train_start_km,
        train.train_end_km,
    )
    if any(value is None for value in values):
        return None
    worksite_start, worksite_end, train_start, train_end = values
    assert worksite_start is not None
    assert worksite_end is not None
    assert train_start is not None
    assert train_end is not None
    return worksite_start, worksite_end, train_start, train_end


def _valid_spatial_interval(start: float, end: float) -> bool:
    return isfinite(start) and isfinite(end) and 0.0 <= start < end


def _separation_meters(coordinates: Coordinates) -> float:
    worksite_start_km, worksite_end_km, train_start_km, train_end_km = coordinates
    worksite_start_m = worksite_start_km * 1_000.0
    worksite_end_m = worksite_end_km * 1_000.0
    train_start_m = train_start_km * 1_000.0
    train_end_m = train_end_km * 1_000.0
    return max(
        0.0,
        max(
            worksite_start_m - train_end_m,
            train_start_m - worksite_end_m,
        ),
    )


def _required_buffer_meters(assignment: ScheduledBlockAssignment) -> float:
    if (
        assignment.department == Department.TRACTION
        or assignment.heavy_equipment
    ):
        return ENHANCED_SAFETY_BUFFER_METERS
    return MIN_SAFETY_BUFFER_METERS


def verify_safety_invariants(
    schedule: List[ScheduledBlockAssignment],
    trains: List[TrainOccupancyWindow],
) -> Tuple[bool, List[AuditLogEntry]]:
    """Check all block assignments against occupancy, isolation, and distance rules.

    Track locations are kilometer intervals on the named section. The physical
    distance rule applies during concurrent work/train windows. Missing or
    malformed evidence fails closed for a concurrent pair.
    """
    facts: Set[Fact] = set()
    for assignment_index, assignment in enumerate(schedule):
        if assignment.department == Department.TRACTION:
            facts.add(("traction_work", assignment_index))
            if not assignment.power_isolated:
                facts.add(("isolation_missing", assignment_index))

    pair_keys: Set[Tuple[int, int]] = set()
    adjacent_pairs: Dict[int, List[Tuple[int, TrainOccupancyWindow, bool]]] = {}
    for assignment_index, assignment in enumerate(schedule):
        is_heavy_up = (
            assignment.heavy_equipment
            and assignment.track_line == TrackLine.UP_LINE
        )
        if is_heavy_up:
            facts.add(("heavy_up_line_work", assignment_index))
        for train_index, train in enumerate(trains):
            if assignment.section_id != train.section_id:
                continue
            if is_heavy_up and train.track_line == TrackLine.DOWN_LINE:
                if (
                    _valid_time_interval(
                        assignment.start_time_hr, assignment.end_time_hr
                    )
                    and _valid_time_interval(
                        train.start_time_hr, train.end_time_hr
                    )
                    and _time_intervals_overlap(assignment, train)
                ):
                    facts.add(("adjacent_down_train", assignment_index, train_index))
                    facts.add(("time_overlap", assignment_index, train_index))
                    coordinates = _spatial_coordinates(assignment, train)
                    # Unverifiable location is treated as inside the buffer (fail closed).
                    if (
                        coordinates is None
                        or _separation_meters(coordinates)
                        < ADJACENT_TRACK_BUFFER_METERS
                    ):
                        facts.add(("adjacent_buffer_short", assignment_index, train_index))
                adjacent_pairs.setdefault(assignment_index, []).append(
                    (train_index, train, True)
                )
                continue
            # Clearance is evaluated strictly on the matching track line.
            if assignment.track_line != train.track_line:
                continue

            pair_key = (assignment_index, train_index)
            pair_keys.add(pair_key)
            facts.add(("same_section", assignment_index, train_index))
            if not _valid_time_interval(
                assignment.start_time_hr, assignment.end_time_hr
            ) or not _valid_time_interval(train.start_time_hr, train.end_time_hr):
                facts.add(("invalid_time", assignment_index, train_index))
                continue
            if not _time_intervals_overlap(assignment, train):
                continue

            facts.add(("time_overlap", assignment_index, train_index))
            coordinates = _spatial_coordinates(assignment, train)
            if coordinates is None or not all(
                _valid_spatial_interval(coordinates[i], coordinates[i + 1])
                for i in (0, 2)
            ):
                facts.add(
                    ("spatial_data_unverifiable", assignment_index, train_index)
                )
                continue
            if (
                _separation_meters(coordinates)
                < _required_buffer_meters(assignment)
            ):
                facts.add(("buffer_short", assignment_index, train_index))

    inferred_facts = _ForwardChainingEngine(_SAFETY_RULES).infer(facts)
    audit: List[AuditLogEntry] = []

    for assignment_index, assignment in enumerate(schedule):
        valid_assignment_time = _valid_time_interval(
            assignment.start_time_hr, assignment.end_time_hr
        )
        audit.append(
            AuditLogEntry(
                rule_name="Scheduled Block Time Validity",
                predicate_evaluated=(
                    f"0 <= {assignment.start_time_hr} < "
                    f"{assignment.end_time_hr} <= 24"
                ),
                passed=valid_assignment_time,
                explanation=(
                    f"Work {assignment.work_id} has a valid scheduled time "
                    "interval."
                    if valid_assignment_time
                    else f"Work {assignment.work_id} has an invalid or empty "
                    "scheduled time interval."
                ),
            )
        )

        applicable_pairs = [
            (train_index, train)
            for train_index, train in enumerate(trains)
            if (assignment_index, train_index) in pair_keys
        ]
        if not applicable_pairs:
            audit.extend(
                (
                    AuditLogEntry(
                        rule_name="Passenger Train Clearance Invariant",
                        predicate_evaluated=(
                            f"no_train_occupancy_on_section({assignment.section_id})"
                        ),
                        passed=True,
                        explanation=(
                            f"No train occupancy windows were supplied for "
                            f"section {assignment.section_id}."
                        ),
                    ),
                    AuditLogEntry(
                        rule_name="Minimum Distance Safety Buffer",
                        predicate_evaluated=(
                            f"no_train_occupancy_on_section({assignment.section_id})"
                        ),
                        passed=True,
                        explanation=(
                            f"No train occupancy windows were supplied for "
                            f"section {assignment.section_id}; there is no "
                            "train interval to compare."
                        ),
                    ),
                )
            )

        for train_index, train in applicable_pairs:
            clearance_violation = (
                "clearance_violation",
                assignment_index,
                train_index,
            ) in inferred_facts
            invalid_time = (
                "invalid_time",
                assignment_index,
                train_index,
            ) in facts
            time_overlap = (
                "time_overlap",
                assignment_index,
                train_index,
            ) in facts
            clearance_passed = not clearance_violation and not invalid_time
            audit.append(
                AuditLogEntry(
                    rule_name="Passenger Train Clearance Invariant",
                    predicate_evaluated=(
                        f"same_section({assignment.work_id}, {train.train_no}) "
                        f"and no_time_overlap({assignment.start_time_hr}, "
                        f"{assignment.end_time_hr}, {train.start_time_hr}, "
                        f"{train.end_time_hr})"
                    ),
                    passed=clearance_passed,
                    explanation=(
                        f"Work {assignment.work_id} overlaps train "
                        f"{train.train_no} on section {assignment.section_id}; "
                        "maintenance is prohibited during train occupancy."
                        if clearance_violation
                        else (
                            "Cannot verify clearance because at least one "
                            "time interval is invalid."
                            if invalid_time
                            else f"Work {assignment.work_id} and train "
                            f"{train.train_no} have no overlapping valid "
                            "occupancy windows."
                        )
                    ),
                )
            )

            if invalid_time:
                buffer_passed = False
                buffer_explanation = (
                    "Cannot verify exposure or the distance buffer because at "
                    "least one time interval is invalid."
                )
            elif not time_overlap:
                buffer_passed = True
                buffer_explanation = (
                    "The work and train windows do not overlap, so no "
                    "simultaneous exposure requires a spatial buffer check."
                )
            else:
                unverified = (
                    "distance_buffer_unverified",
                    assignment_index,
                    train_index,
                ) in inferred_facts
                distance_violation = (
                    "distance_buffer_violation",
                    assignment_index,
                    train_index,
                ) in inferred_facts
                coordinates = _spatial_coordinates(assignment, train)
                buffer_passed = not unverified and not distance_violation
                if unverified:
                    buffer_explanation = (
                        "Cannot verify the distance buffer because track "
                        "kilometer endpoints are missing or invalid."
                    )
                else:
                    assert coordinates is not None
                    buffer_explanation = (
                        f"Separation is {_separation_meters(coordinates):g} m; "
                        f"the required buffer is "
                        f"{_required_buffer_meters(assignment):g} m."
                    )

            audit.append(
                AuditLogEntry(
                    rule_name="Minimum Distance Safety Buffer",
                    predicate_evaluated=(
                        f"distance(worksite({assignment.worksite_start_km},"
                        f"{assignment.worksite_end_km}), "
                        f"train({train.train_start_km},{train.train_end_km})) "
                        f">= {_required_buffer_meters(assignment):g}m"
                        if time_overlap
                        else f"no_concurrent_exposure({assignment.work_id},"
                        f"{train.train_no})"
                    ),
                    passed=buffer_passed,
                    explanation=buffer_explanation,
                )
            )

        if assignment.heavy_equipment and assignment.track_line == TrackLine.UP_LINE:
            adjacent = adjacent_pairs.get(assignment_index, [])
            violations = [
                train.train_no
                for train_index, train, _ in adjacent
                if ("adjacent_track_violation", assignment_index, train_index)
                in inferred_facts
            ]
            audit.append(
                AuditLogEntry(
                    rule_name="Adjacent Track Heavy Equipment Buffer",
                    predicate_evaluated=(
                        f"heavy_equipment({assignment.work_id}, UP_LINE) -> "
                        f"distance_to_DOWN_LINE_trains >= "
                        f"{ADJACENT_TRACK_BUFFER_METERS:g}m"
                    ),
                    passed=not violations,
                    explanation=(
                        f"Heavy equipment work {assignment.work_id} is within "
                        f"{ADJACENT_TRACK_BUFFER_METERS:g} m of DOWN_LINE trains "
                        f"{', '.join(sorted(set(violations)))} (or their "
                        "position could not be verified)."
                        if violations
                        else f"Heavy equipment work {assignment.work_id} has no "
                        f"concurrent DOWN_LINE train within "
                        f"{ADJACENT_TRACK_BUFFER_METERS:g} m."
                    ),
                )
            )

        isolation_violation = (
            "traction_isolation_violation",
            assignment_index,
        ) in inferred_facts
        is_traction_work = assignment.department == Department.TRACTION
        audit.append(
            AuditLogEntry(
                rule_name="Traction Power Isolation Rule",
                predicate_evaluated=(
                    f"not_traction_work({assignment.work_id}) or "
                    f"power_isolated({assignment.work_id})"
                ),
                passed=not isolation_violation,
                explanation=(
                    f"Traction work {assignment.work_id} is marked "
                    "power-isolated."
                    if is_traction_work and not isolation_violation
                    else (
                        f"Traction work {assignment.work_id} lacks confirmed "
                        "power isolation."
                        if isolation_violation
                        else f"Work {assignment.work_id} is not traction work; "
                        "the traction isolation rule does not apply."
                    )
                ),
            )
        )

    return all(entry.passed for entry in audit), audit
