"""Pure-Python forward-chaining safety verification for scheduled rail work."""

from dataclasses import dataclass
from math import isfinite
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .schemas.contracts import (
    AuditLogEntry,
    Department,
    ScheduledBlockAssignment,
    TimetableCoverage,
    TrackLine,
    TrainOccupancyWindow,
)

MIN_SAFETY_BUFFER_METERS = 1_000.0
ENHANCED_SAFETY_BUFFER_METERS = 2_000.0
ADJACENT_TRACK_BUFFER_METERS = 1_000.0



class EvidenceProvider:
    """Authenticates positive safety evidence for the verifier.

    The verifier never trusts a record because of its contents or a `source`
    label, which are caller-controlled. It trusts a positive claim (timetable
    completeness, power isolation) only if the provider authenticates that exact
    record. This base class authenticates nothing (fail closed). A real provider
    must verify the evidence against an integrated system; none exists yet.
    """

    def authenticates_coverage(self, record: TimetableCoverage) -> bool:
        return False

    def authenticates_isolation(self, assignment: ScheduledBlockAssignment) -> bool:
        return False


DEFAULT_EVIDENCE_PROVIDER = EvidenceProvider()

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
            ("heavy_adjacent_work", "?assignment"),
            ("adjacent_line_train", "?assignment", "?train"),
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


def _isolation_evidence(
    assignment: ScheduledBlockAssignment, provider: EvidenceProvider
) -> Optional[bool]:
    """False: explicit negative. True: positive authenticated by the provider.
    None: unusable (missing, or a positive that could not be authenticated)."""
    if assignment.power_isolated is False:
        return False
    if assignment.power_isolated is True and provider.authenticates_isolation(
        assignment
    ):
        return True
    return None


def _timetable_covers(
    assignment: ScheduledBlockAssignment,
    coverage: Optional[Sequence[TimetableCoverage]],
    provider: EvidenceProvider,
) -> bool:
    if not coverage or not _valid_time_interval(
        assignment.start_time_hr, assignment.end_time_hr
    ):
        return False
    return any(
        provider.authenticates_coverage(item)
        and item.section_id == assignment.section_id
        and item.track_line == assignment.track_line
        and item.start_time_hr <= assignment.start_time_hr
        and assignment.end_time_hr <= item.end_time_hr
        for item in coverage
    )


def _adjacent_line(track_line: TrackLine) -> TrackLine:
    return TrackLine.DOWN_LINE if track_line == TrackLine.UP_LINE else TrackLine.UP_LINE


def _adjacent_line_covered(
    assignment: ScheduledBlockAssignment,
    coverage: Optional[Sequence[TimetableCoverage]],
    provider: EvidenceProvider,
) -> bool:
    """Coverage must be for the line adjacent to the work, not the work's own line."""
    if not coverage or not _valid_time_interval(
        assignment.start_time_hr, assignment.end_time_hr
    ):
        return False
    adjacent = _adjacent_line(assignment.track_line)
    return any(
        provider.authenticates_coverage(item)
        and item.section_id == assignment.section_id
        and item.track_line == adjacent
        and item.start_time_hr <= assignment.start_time_hr
        and assignment.end_time_hr <= item.end_time_hr
        for item in coverage
    )


def verify_safety_invariants(
    schedule: List[ScheduledBlockAssignment],
    trains: List[TrainOccupancyWindow],
    timetable_coverage: Optional[Sequence[TimetableCoverage]] = None,
    evidence_provider: Optional[EvidenceProvider] = None,
) -> Tuple[bool, List[AuditLogEntry]]:
    """Check all block assignments against occupancy, isolation, and distance rules.

    Absence of same-track trains passes only when `timetable_coverage` confirms the
    timetable is complete for the assignment's section, track line, and time
    interval; otherwise clearance is unevaluated.

    Track locations are kilometer intervals on the named section. The physical
    distance rule applies during concurrent work/train windows. Missing or
    malformed evidence fails closed for a concurrent pair.
    """
    provider = evidence_provider or DEFAULT_EVIDENCE_PROVIDER
    facts: Set[Fact] = set()
    for assignment_index, assignment in enumerate(schedule):
        if assignment.department == Department.TRACTION:
            facts.add(("traction_work", assignment_index))
            if _isolation_evidence(assignment, provider) is False:
                facts.add(("isolation_missing", assignment_index))

    pair_keys: Set[Tuple[int, int]] = set()
    adjacent_pairs: Dict[int, List[Tuple[int, TrainOccupancyWindow, bool]]] = {}
    adjacent_invalid_time: Set[int] = set()
    for assignment_index, assignment in enumerate(schedule):
        is_heavy = assignment.heavy_equipment
        adjacent_line = _adjacent_line(assignment.track_line)
        if is_heavy:
            facts.add(("heavy_adjacent_work", assignment_index))
        for train_index, train in enumerate(trains):
            if assignment.section_id != train.section_id:
                continue
            if is_heavy and train.track_line == adjacent_line:
                if not _valid_time_interval(
                    train.start_time_hr, train.end_time_hr
                ) or not _valid_time_interval(
                    assignment.start_time_hr, assignment.end_time_hr
                ):
                    adjacent_invalid_time.add(assignment_index)
                elif (
                    _valid_time_interval(
                        assignment.start_time_hr, assignment.end_time_hr
                    )
                    and _valid_time_interval(
                        train.start_time_hr, train.end_time_hr
                    )
                    and _time_intervals_overlap(assignment, train)
                ):
                    facts.add(("adjacent_line_train", assignment_index, train_index))
                    facts.add(("time_overlap", assignment_index, train_index))
                    coordinates = _spatial_coordinates(assignment, train)
                    # Unverifiable location is treated as inside the buffer (fail closed).
                    if (
                        coordinates is None
                        or not all(
                            _valid_spatial_interval(coordinates[i], coordinates[i + 1])
                            for i in (0, 2)
                        )
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
        coverage_confirmed = _timetable_covers(assignment, timetable_coverage, provider)
        if not applicable_pairs:
            no_matching_track_status = True if coverage_confirmed else None
            no_matching_track_explanation = (
                "The supplied timetable is confirmed complete for section "
                f"{assignment.section_id}, {assignment.track_line.value}, and the "
                "scheduled interval, and contains no same-track train."
                if coverage_confirmed
                else (
                    f"No timetable completeness evidence covers section "
                    f"{assignment.section_id}, {assignment.track_line.value}, and "
                    "the scheduled interval; absence of same-track trains does "
                    "not establish clearance, so it is unevaluated."
                )
            )
            audit.extend(
                (
                    AuditLogEntry(
                        rule_name="Passenger Train Clearance Invariant",
                        predicate_evaluated=(
                            "timetable_complete_and_no_same_track_train("
                            f"{assignment.section_id})"
                        ),
                        passed=no_matching_track_status,
                        explanation=no_matching_track_explanation,
                    ),
                    AuditLogEntry(
                        rule_name="Minimum Distance Safety Buffer",
                        predicate_evaluated=(
                            f"no_concurrent_same_track_train({assignment.section_id})"
                        ),
                        passed=no_matching_track_status,
                        explanation=no_matching_track_explanation,
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
            clearance_passed: Optional[bool] = not clearance_violation and not invalid_time
            # A clean pair never proves that unlisted trains are absent.
            clearance_unconfirmed = clearance_passed and not coverage_confirmed
            if clearance_unconfirmed:
                clearance_passed = None
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
                            else f"No conflict with listed train "
                            f"{train.train_no}, but timetable completeness is "
                            "not confirmed for this section, track line, and "
                            "interval; clearance is unevaluated."
                            if clearance_unconfirmed
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
                    "simultaneous exposure requires a spatial buffer check "
                    "for this known train."
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

        if applicable_pairs and not coverage_confirmed:
            audit.append(
                AuditLogEntry(
                    rule_name="Minimum Distance Safety Buffer",
                    predicate_evaluated=(
                        "timetable_complete_for_exposure("
                        f"{assignment.section_id}, {assignment.track_line.value})"
                    ),
                    passed=None,
                    explanation=(
                        "Exposure to unlisted trains is unknown: no timetable "
                        "completeness evidence covers this section, track line, "
                        "and scheduled interval."
                    ),
                )
            )

        if assignment.heavy_equipment:
            adjacent = adjacent_pairs.get(assignment_index, [])
            adjacent_name = _adjacent_line(assignment.track_line).value
            violations = [
                train.train_no
                for train_index, train, _ in adjacent
                if ("adjacent_track_violation", assignment_index, train_index)
                in inferred_facts
            ]
            covered = _adjacent_line_covered(
                assignment, timetable_coverage, provider
            )
            invalid_time = assignment_index in adjacent_invalid_time
            if violations:
                adjacent_passed: Optional[bool] = False
                adjacent_explanation = (
                    f"Heavy equipment work {assignment.work_id} is within "
                    f"{ADJACENT_TRACK_BUFFER_METERS:g} m of {adjacent_name} trains "
                    f"{', '.join(sorted(set(violations)))} (or their "
                    "position could not be verified)."
                )
            elif invalid_time:
                adjacent_passed = None
                adjacent_explanation = (
                    f"A listed {adjacent_name} train or the work has an invalid "
                    "time interval; the adjacent-track check is unevaluated."
                )
            elif covered:
                adjacent_passed = True
                adjacent_explanation = (
                    f"Heavy equipment work {assignment.work_id} has no "
                    f"concurrent {adjacent_name} train within "
                    f"{ADJACENT_TRACK_BUFFER_METERS:g} m, and the {adjacent_name} "
                    "timetable is confirmed complete for the interval."
                )
            else:
                adjacent_passed = None
                adjacent_explanation = (
                    f"No violating {adjacent_name} train was found for heavy "
                    f"equipment work {assignment.work_id}, but {adjacent_name} "
                    "timetable completeness is not confirmed for this section "
                    "and interval; the check is unevaluated."
                )
            audit.append(
                AuditLogEntry(
                    rule_name="Adjacent Track Heavy Equipment Buffer",
                    predicate_evaluated=(
                        f"heavy_equipment({assignment.work_id}, "
                        f"{assignment.track_line.value}) -> "
                        f"distance_to_{adjacent_name}_trains >= "
                        f"{ADJACENT_TRACK_BUFFER_METERS:g}m"
                    ),
                    passed=adjacent_passed,
                    explanation=adjacent_explanation,
                )
            )

        isolation_violation = (
            "traction_isolation_violation",
            assignment_index,
        ) in inferred_facts
        is_traction_work = assignment.department == Department.TRACTION
        isolation_evidence = _isolation_evidence(assignment, provider)
        isolation_passed = (
            None
            if is_traction_work and isolation_evidence is None
            else not isolation_violation
        )
        audit.append(
            AuditLogEntry(
                rule_name="Traction Power Isolation Rule",
                predicate_evaluated=(
                    f"not_traction_work({assignment.work_id}) or "
                    f"power_isolated({assignment.work_id})"
                ),
                passed=isolation_passed,
                explanation=(
                    (
                        f"Traction work {assignment.work_id} has a positive "
                        "isolation assertion without trusted evidence "
                        "provenance; the check is unevaluated."
                        if assignment.power_isolated is True
                        else f"Traction work {assignment.work_id} lacks "
                        "confirmed isolation evidence; the check is unevaluated."
                    )
                    if is_traction_work and isolation_evidence is None
                    else (
                        f"Available evidence indicates traction work "
                        f"{assignment.work_id} is not power-isolated."
                        if isolation_violation
                        else (
                            f"Available evidence confirms traction work "
                            f"{assignment.work_id} is power-isolated."
                            if is_traction_work
                            else f"Work {assignment.work_id} is not traction "
                            "work; the traction isolation rule does not apply."
                        )
                    )
                ),
            )
        )

    # An empty schedule evaluates no rules, so it cannot demonstrate safety.
    return bool(audit) and all(entry.passed is True for entry in audit), audit
