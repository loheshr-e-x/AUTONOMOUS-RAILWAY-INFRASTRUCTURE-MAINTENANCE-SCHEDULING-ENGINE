"""Data ingestion and synthetic work-order generation for SymbIO-Block."""

import csv
import math
import random
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

from .schemas.contracts import (
    Department,
    MaintenanceWorkOrder,
    TrackLine,
    TrainOccupancyWindow,
    UrgencyLevel,
)


_CORRIDOR_LENGTH_KM = 440.0


@dataclass(frozen=True)
class Route:
    """A corridor: its endpoints, length and the sub-sections it is split into."""

    route_id: str
    name: str
    origin: str
    destination: str
    length_km: float
    origin_names: frozenset[str]
    destination_names: frozenset[str]
    origin_contains: tuple[str, ...] = ()
    destination_contains: tuple[str, ...] = ()
    wo_prefix: str = "WO-26027"

    @property
    def sub_sections(self) -> tuple[tuple[str, float, float], ...]:
        first = round(self.length_km * 150.0 / 440.0, 1)
        second = round(self.length_km * 300.0 / 440.0, 1)
        return (
            (f"{self.route_id}_SEC1", 0.0, first),
            (f"{self.route_id}_SEC2", first, second),
            (f"{self.route_id}_SEC3", second, self.length_km),
        )

    @property
    def section_ids(self) -> tuple[str, ...]:
        return tuple(section[0] for section in self.sub_sections)


ROUTES: dict[str, Route] = {
    route.route_id: route
    for route in (
        Route(
            "NDLS_CNB", "New Delhi - Kanpur Central", "New Delhi", "Kanpur Central",
            _CORRIDOR_LENGTH_KM,
            frozenset({"ndls"}), frozenset({"cnb"}), ("newdelhi",), ("kanpur",),
        ),
        Route(
            "HWH_PURI", "Howrah - Puri", "Howrah", "Puri", 500.0,
            frozenset({"hwh", "howrah", "howrahjn"}), frozenset({"puri"}),
            wo_prefix="WO-HWH",
        ),
        Route(
            "BCT_AMD", "Mumbai Central - Ahmedabad", "Mumbai Central", "Ahmedabad", 490.0,
            frozenset({"bct", "mumbaicentral"}),
            frozenset({"adi", "amd", "ahmedabad", "ahmedabadjn"}),
            wo_prefix="WO-BCT",
        ),
    )
}
DEFAULT_ROUTE_ID = "NDLS_CNB"
SUB_SECTION_IDS = ROUTES[DEFAULT_ROUTE_ID].section_ids


def get_route(route_id: str) -> Route:
    try:
        return ROUTES[route_id]
    except KeyError:
        raise ValueError(f"Unknown route {route_id!r}; expected one of {sorted(ROUTES)}") from None


def route_for_section(section_id: str) -> str | None:
    for route in ROUTES.values():
        if section_id == route.route_id or section_id in route.section_ids:
            return route.route_id
    return None


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


def _normalise_station(station: str) -> str:
    name = re.sub(r"^(pq|rl)\s+", "", station.strip().lower())
    return re.sub(r"[^a-z0-9]", "", name)


def _is_origin(station: str, route: Route) -> bool:
    name = _normalise_station(station)
    return name in route.origin_names or any(t in name for t in route.origin_contains)


def _is_destination(station: str, route: Route) -> bool:
    name = _normalise_station(station)
    return name in route.destination_names or any(
        t in name for t in route.destination_contains
    )


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
    train_no: str, entry: _RouteStop, route_exit: _RouteStop, route: Route
) -> list[TrainOccupancyWindow]:
    # Origin -> destination runs on the DOWN_LINE; the reverse direction on the UP_LINE.
    outbound = _is_origin(entry.station, route)
    track_line = TrackLine.DOWN_LINE if outbound else TrackLine.UP_LINE
    start = _clock_hours(entry.departure, train_no, entry.station)
    end = _clock_hours(route_exit.arrival, train_no, route_exit.station)
    if end <= start:
        end += 24.0
    duration = end - start
    # Position along the corridor is interpolated linearly between the endpoints.
    km_origin, km_dest = (
        (0.0, route.length_km) if outbound else (route.length_km, 0.0)
    )

    windows: list[TrainOccupancyWindow] = []
    for section_id, sec_start_km, sec_end_km in route.sub_sections:
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


def get_train_schedules(route_id: str = DEFAULT_ROUTE_ID) -> list[TrainOccupancyWindow]:
    """Load train windows for schedules passing both endpoints of the route."""
    return list(_cached_train_schedules(route_id))


@lru_cache(maxsize=None)
def _cached_train_schedules(route_id: str) -> tuple[TrainOccupancyWindow, ...]:
    route = get_route(route_id)
    schedules: list[TrainOccupancyWindow] = []
    with _train_data_path().open(encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            train_no = (row.get("train_no") or "").strip()
            stops = _parse_stops(row.get("intermediate_stops") or "")
            origin_index = next(
                (i for i, stop in enumerate(stops) if _is_origin(stop.station, route)),
                None,
            )
            destination_index = next(
                (i for i, stop in enumerate(stops) if _is_destination(stop.station, route)),
                None,
            )
            if origin_index is None or destination_index is None:
                source = (row.get("source_station") or "").strip()
                destination = (row.get("destination_station") or "").strip()
                serves_route = (
                    _is_origin(source, route) and _is_destination(destination, route)
                ) or (_is_destination(source, route) and _is_origin(destination, route))
                if not serves_route:
                    continue
                entry = _RouteStop(source, "", (row.get("departure_time") or "").strip())
                route_exit = _RouteStop(
                    destination, (row.get("arrival_time") or "").strip(), ""
                )
            elif origin_index < destination_index:
                entry, route_exit = stops[origin_index], stops[destination_index]
            else:
                entry, route_exit = stops[destination_index], stops[origin_index]
            if not train_no:
                raise ValueError(f"A train on the {route_id} route has no train number")
            schedules.extend(_window_for_train(train_no, entry, route_exit, route))

    return tuple(schedules)


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


def get_maintenance_work_orders(
    route_id: str = DEFAULT_ROUTE_ID,
) -> list[MaintenanceWorkOrder]:
    """Return 30 deterministic synthetic work orders across the route's sub-sections."""
    route = get_route(route_id)
    section_ids = route.section_ids
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

    windows = get_train_schedules(route_id)
    # Free track per section/line, plus the blocks already opened there. Different
    # departments may share a block (same window), which is how a busy timetable
    # can absorb 30 orders; same-department work never overlaps.
    pools = {
        (section_id, line): _free_gaps(windows, section_id, (line,))
        for section_id in section_ids
        for line in TrackLine
    }
    blocks: dict[tuple[str, TrackLine], list[tuple[float, float, set[Department]]]] = {
        key: [] for key in pools
    }
    # The solver forbids overlap of different sections/departments on one line.
    line_free = {line: [(0.0, 24.0)] for line in TrackLine}
    down_free = {
        sec: _free_gaps(windows, sec, (TrackLine.DOWN_LINE,)) for sec in section_ids
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
            for sec in section_ids:
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
            for sec in section_ids:
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
            section_id = rng.choice(section_ids)
            duration = durations[0]
        orders.append(
            MaintenanceWorkOrder(
                work_id=f"{route.wo_prefix}-{index:03}",
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
