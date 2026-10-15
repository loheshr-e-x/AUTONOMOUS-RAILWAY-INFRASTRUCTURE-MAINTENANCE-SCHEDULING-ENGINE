"""Data ingestion and synthetic work-order generation for SymbIO-Block."""

import csv
import math
import random
import re
from pathlib import Path
from typing import NamedTuple

from .schemas.contracts import (
    Department,
    MaintenanceWorkOrder,
    TrackLine,
    TrainOccupancyWindow,
    UrgencyLevel,
)


_ROUTE_SECTION_ID = "NDLS_CNB"
_CORRIDOR_LENGTH_KM = 440.0
_SUB_SECTIONS = (
    ("NDLS_CNB_SEC1", 0.0, 150.0),
    ("NDLS_CNB_SEC2", 150.0, 300.0),
    ("NDLS_CNB_SEC3", 300.0, _CORRIDOR_LENGTH_KM),
)
SUB_SECTION_IDS = tuple(section[0] for section in _SUB_SECTIONS)
_STOP_RE = re.compile(
    r"^(?P<station>.*?)\s*\(arr=(?P<arrival>[^,]+),dep=(?P<departure>[^)]+)"
)
_TIME_RE = re.compile(r"^(?P<hour>\d{1,2}):(?P<minute>\d{2})$")
_RANDOM_SEED = 26027


class _RouteStop(NamedTuple):
    station: str
    arrival: str
    departure: str


def _train_data_path() -> Path:
    """Prefer the specified Kaggle file, falling back to the bundled dataset."""
    app_dir = Path(__file__).resolve().parent
    repository_dir = app_dir.parents[1]
    candidates = (
        app_dir / "data" / "raw_trains.csv",
        repository_dir / "data" / "raw_trains.csv",
        app_dir / "data" / "IRCTC_cleaned.csv",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Train schedule CSV not found; searched: {searched}")


def _parse_stops(raw_stops: str) -> list[_RouteStop]:
    stops: list[_RouteStop] = []
    for value in raw_stops.split("|"):
        match = _STOP_RE.match(value.strip())
        if match is not None:
            stops.append(
                _RouteStop(
                    station=match.group("station").strip(),
                    arrival=match.group("arrival").strip(),
                    departure=match.group("departure").strip(),
                )
            )
    return stops


def _is_new_delhi(station: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", station.lower())
    return normalized == "ndls" or "newdelhi" in normalized


def _is_kanpur(station: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", station.lower())
    return normalized == "cnb" or "kanpur" in normalized


def _clock_hours(value: str, train_no: str, station: str) -> float:
    match = _TIME_RE.fullmatch(value)
    if match is None:
        raise ValueError(
            f"Invalid schedule time {value!r} for train {train_no} at {station}"
        )

    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    if hour > 24 or minute > 59 or (hour == 24 and minute != 0):
        raise ValueError(
            f"Invalid schedule time {value!r} for train {train_no} at {station}"
        )
    return hour + minute / 60


def _window_for_train(
    train_no: str, entry: _RouteStop, route_exit: _RouteStop
) -> list[TrainOccupancyWindow]:
    # Delhi -> Kanpur (eastbound) runs on the DOWN_LINE; Kanpur -> Delhi (westbound) on the UP_LINE.
    track_line = TrackLine.DOWN_LINE if _is_new_delhi(entry.station) else TrackLine.UP_LINE
    start = _clock_hours(entry.departure, train_no, entry.station)
    end = _clock_hours(route_exit.arrival, train_no, route_exit.station)
    if end <= start:
        end += 24.0
    duration = end - start
    # Position along the corridor is interpolated linearly between the endpoints.
    km_origin, km_dest = (
        (0.0, _CORRIDOR_LENGTH_KM)
        if _is_new_delhi(entry.station)
        else (_CORRIDOR_LENGTH_KM, 0.0)
    )

    windows: list[TrainOccupancyWindow] = []
    for section_id, sec_start_km, sec_end_km in _SUB_SECTIONS:
        fractions = sorted(
            (km - km_origin) / (km_dest - km_origin)
            for km in (sec_start_km, sec_end_km)
        )
        enter, leave = start + fractions[0] * duration, start + fractions[1] * duration
        # Split anything that crosses midnight into two same-day windows.
        for lo, hi in ((enter, leave), (enter - 24.0, leave - 24.0)):
            lo, hi = max(lo, 0.0), min(hi, 24.0)
            if hi - lo > 1e-6:
                windows.append(
                    TrainOccupancyWindow(
                        train_no=train_no,
                        section_id=section_id,
                        track_line=track_line,
                        start_time_hr=lo,
                        end_time_hr=hi,
                        train_start_km=sec_start_km,
                        train_end_km=sec_end_km,
                    )
                )
    return windows


def get_train_schedules() -> list[TrainOccupancyWindow]:
    """Load train windows for schedules passing both New Delhi and Kanpur."""
    schedules: list[TrainOccupancyWindow] = []
    with _train_data_path().open(encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            train_no = (row.get("train_no") or "").strip()
            stops = _parse_stops(row.get("intermediate_stops") or "")
            new_delhi_index = next(
                (
                    index
                    for index, stop in enumerate(stops)
                    if _is_new_delhi(stop.station)
                ),
                None,
            )
            kanpur_index = next(
                (
                    index
                    for index, stop in enumerate(stops)
                    if _is_kanpur(stop.station)
                ),
                None,
            )
            if new_delhi_index is None or kanpur_index is None:
                source = (row.get("source_station") or "").strip()
                destination = (row.get("destination_station") or "").strip()
                serves_route = (
                    _is_new_delhi(source) and _is_kanpur(destination)
                ) or (_is_kanpur(source) and _is_new_delhi(destination))
                if serves_route:
                    entry = _RouteStop(
                        source, "", (row.get("departure_time") or "").strip()
                    )
                    route_exit = _RouteStop(
                        destination, (row.get("arrival_time") or "").strip(), ""
                    )
                else:
                    continue
                if not train_no:
                    raise ValueError("A train on the NDLS_CNB route has no train number")
                schedules.extend(_window_for_train(train_no, entry, route_exit))
                continue
            if not train_no:
                raise ValueError("A train on the NDLS_CNB route has no train number")

            if new_delhi_index < kanpur_index:
                entry, route_exit = stops[new_delhi_index], stops[kanpur_index]
            else:
                entry, route_exit = stops[kanpur_index], stops[new_delhi_index]
            schedules.extend(_window_for_train(train_no, entry, route_exit))

    return schedules


def _free_gaps(
    windows: list[TrainOccupancyWindow], section_id: str, lines: tuple[TrackLine, ...]
) -> list[tuple[float, float]]:
    """Hours of the day in which no train occupies the section on any of `lines`."""
    busy = sorted(
        (w.start_time_hr, w.end_time_hr)
        for w in windows
        if w.section_id == section_id and w.track_line in lines
    )
    gaps: list[tuple[float, float]] = []
    cursor = 0.0
    for start, end in busy:
        if start > cursor:
            gaps.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < 24.0:
        gaps.append((cursor, 24.0))
    return gaps


def _aligned_fit(
    gaps: list[tuple[float, float]], duration_hrs: float
) -> tuple[float, float] | None:
    """First gap that fits `duration_hrs` on the solver's half-hour grid."""
    for gap_start, gap_end in gaps:
        start = math.ceil(gap_start * 2 - 1e-9) / 2
        if start + duration_hrs <= gap_end + 1e-9:
            return gap_start, start + duration_hrs
    return None


def _intersect(
    left: list[tuple[float, float]], right: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    return [
        (max(a, c), min(b, d))
        for a, b in left
        for c, d in right
        if min(b, d) - max(a, c) > 1e-9
    ]


def _consume(
    gaps: list[tuple[float, float]], used: tuple[float, float]
) -> list[tuple[float, float]]:
    remaining: list[tuple[float, float]] = []
    for start, end in gaps:
        if used[1] <= start or used[0] >= end:
            remaining.append((start, end))
            continue
        if used[0] > start:
            remaining.append((start, used[0]))
        if used[1] < end:
            remaining.append((used[1], end))
    return remaining


def get_maintenance_work_orders() -> list[MaintenanceWorkOrder]:
    """Return 30 deterministic synthetic work orders across the NDLS_CNB sub-sections."""
    rng = random.Random(_RANDOM_SEED)
    departments = [
        Department.ENGINEERING,
        Department.SIGNALLING,
        Department.TRACTION,
    ] * 10
    urgencies = [
        UrgencyLevel.CRITICAL,
        UrgencyLevel.MEDIUM,
        UrgencyLevel.ROUTINE,
    ] * 10
    rng.shuffle(departments)
    rng.shuffle(urgencies)

    # (label, allowed durations in hours). Tier 3 is deliberately small:
    # 3-4 h possessions only fit the few long gaps of a busy timetable.
    tier_bounds = (12, 26, 30)
    tiers = (
        ("tier1", [0.5, 1.0]),  # minor inspection / lubrication
        ("tier2", [1.0, 1.5, 2.0]),  # standard preventive maintenance
        ("tier3", [3.0, 3.5, 4.0]),  # critical structural repair
    )

    defects = {
        Department.ENGINEERING: (
            "rail fracture inspection",
            "sleeper replacement",
            "track geometry correction",
            "ballast packing",
        ),
        Department.SIGNALLING: (
            "interlocking inspection",
            "track circuit repair",
            "signal lamp replacement",
            "signalling cable test",
        ),
        Department.TRACTION: (
            "overhead insulator replacement",
            "pantograph inspection",
            "feeder cable repair",
            "contact wire adjustment",
        ),
    }

    windows = get_train_schedules()
    # Free track per section/line, plus the blocks already opened there. Different
    # departments may share a block (same window), which is how a busy timetable
    # can absorb 30 orders; same-department work never overlaps.
    pools = {
        (section_id, line): _free_gaps(windows, section_id, (line,))
        for section_id in SUB_SECTION_IDS
        for line in TrackLine
    }
    blocks: dict[tuple[str, TrackLine], list[tuple[float, float, set[Department]]]] = {
        key: [] for key in pools
    }
    # The solver forbids overlap of different sections/departments on one line.
    line_free = {line: [(0.0, 24.0)] for line in TrackLine}
    down_free = {
        sec: _free_gaps(windows, sec, (TrackLine.DOWN_LINE,)) for sec in SUB_SECTION_IDS
    }

    def heavy_clear(sec: str, start: float, end: float) -> bool:
        return any(g0 <= start + 1e-9 and end <= g1 + 1e-9 for g0, g1 in down_free[sec])

    orders: list[MaintenanceWorkOrder] = []
    # Allocate the longest possessions first so short work cannot fragment the long gaps.
    numbered = list(enumerate(zip(departments, urgencies, strict=True), start=1))
    for index, (department, urgency) in reversed(numbered):
        tier, durations = next(
            spec for spec, bound in zip(tiers, tier_bounds) if index <= bound
        )
        critical_repair = tier == "tier3"
        track_line = TrackLine.UP_LINE if index % 2 else TrackLine.DOWN_LINE
        want_heavy = critical_repair and department == Department.ENGINEERING

        def plan(heavy_work: bool) -> list[tuple[str, float, float, bool]]:
            found: list[tuple[str, float, float, bool]] = []
            for sec in SUB_SECTION_IDS:
                for start, end, depts in blocks[(sec, track_line)]:
                    if (
                        department not in depts
                        and round(end - start, 6) in durations
                        and (
                            not (heavy_work and track_line == TrackLine.UP_LINE)
                            or heavy_clear(sec, start, end)
                        )
                    ):
                        found.append((sec, start, end, True))
            if found:
                return found
            for sec in SUB_SECTION_IDS:
                gaps = _intersect(pools[(sec, track_line)], line_free[track_line])
                if heavy_work and track_line == TrackLine.UP_LINE:
                    gaps = _intersect(gaps, down_free[sec])
                for duration in durations:
                    fit = _aligned_fit(gaps, duration)
                    if fit:
                        start = math.ceil(fit[0] * 2 - 1e-9) / 2
                        found.append((sec, start, start + duration, False))
            return found

        heavy = want_heavy
        options = plan(True) if want_heavy else plan(False)
        if not options:
            heavy = False
            options = plan(False)
        if options:
            section_id, start, end, joined = rng.choice(options)
            duration = end - start
            key = (section_id, track_line)
            if joined:
                blocks[key] = [
                    (s0, e0, d | {department}) if (s0, e0) == (start, end) else (s0, e0, d)
                    for s0, e0, d in blocks[key]
                ]
            else:
                pools[key] = _consume(pools[key], (start, end))
                line_free[track_line] = _consume(line_free[track_line], (start, end))
                blocks[key].append((start, end, {department}))
        else:
            section_id = rng.choice(SUB_SECTION_IDS)
            duration = durations[0]
        orders.append(
            MaintenanceWorkOrder(
                work_id=f"WO-26027-{index:03}",
                department=department,
                section_id=section_id,
                # Alternate lines so each tier splits evenly: 15 UP, 15 DOWN.
                track_line=track_line,
                heavy_equipment=heavy,
                defect_type=(
                    "critical structural repair - "
                    if critical_repair
                    else ""
                )
                + rng.choice(defects[department]),
                duration_hrs=duration,
                urgency=urgency,
                co_location_allowed=True,
            )
        )
    return sorted(orders, key=lambda order: order.work_id)
