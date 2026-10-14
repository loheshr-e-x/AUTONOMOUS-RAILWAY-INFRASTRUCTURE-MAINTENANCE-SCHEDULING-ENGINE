"""Data ingestion and synthetic work-order generation for SymbIO-Block."""

import csv
import random
import re
from pathlib import Path
from typing import NamedTuple

from .schemas.contracts import (
    Department,
    MaintenanceWorkOrder,
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

    return [
        MaintenanceWorkOrder(
            work_id=f"WO-26027-{index:03}",
            department=department,
            section_id=rng.choice(SUB_SECTION_IDS),
            defect_type=rng.choice(defects[department]),
            duration_hrs=round(rng.uniform(1.0, 4.0), 2),
            urgency=urgency,
            co_location_allowed=True,
        )
        for index, (department, urgency) in enumerate(
            zip(departments, urgencies, strict=True), start=1
        )
    ]
