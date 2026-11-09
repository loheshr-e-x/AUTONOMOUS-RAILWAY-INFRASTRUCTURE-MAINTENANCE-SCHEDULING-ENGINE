"""Pure adapters from existing application contracts to the domain graph."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone, tzinfo
from typing import Sequence

from pydantic import ValidationError

from ..data_engine import Route
from .contracts import MaintenanceWorkOrder, TrainOccupancyWindow
from .domain import (
    BlockWindow,
    RailwayDomainModel,
    RailwayDepartment,
    RailwayRoute,
    RailwaySection,
    RailwayTrainOccupancy,
    RailwayTrainService,
    Resource,
    WorkDependency,
)
from .domain_types import DataOrigin, DataProvenance, VerificationStatus


class DomainAdapterError(ValueError):
    """A legacy record cannot be converted without missing context or data."""


@dataclass(frozen=True)
class OccupancyConversionContext:
    operating_date: date
    timezone: tzinfo

    def __post_init__(self) -> None:
        if isinstance(self.operating_date, datetime):
            raise ValueError("operating_date must be a date, not a datetime")
        if not isinstance(self.operating_date, date):
            raise TypeError("operating_date must be an explicit date")
        if not isinstance(self.timezone, tzinfo):
            raise TypeError("timezone must be an explicit tzinfo instance")
        midnight = _local_datetime(self, 0)
        if midnight.utcoffset() is None:
            raise ValueError("timezone must produce an aware datetime")


@dataclass(frozen=True)
class DomainBuildIssue:
    code: str
    record_type: str
    record_id: str
    message: str


@dataclass(frozen=True)
class DomainBuildResult:
    model: RailwayDomainModel | None
    issues: tuple[DomainBuildIssue, ...] = ()

    @property
    def is_complete(self) -> bool:
        return self.model is not None and not self.issues


def _copy_provenance(value: DataProvenance | None) -> DataProvenance:
    if value is None:
        return DataProvenance()
    return DataProvenance.model_validate(value.model_dump(mode="python"))


def _local_datetime(
    context: OccupancyConversionContext, hour_offset: float
) -> datetime:
    local_clock = datetime.combine(
        context.operating_date,
        datetime.min.time(),
    ) + timedelta(hours=hour_offset)
    candidate = local_clock.replace(tzinfo=context.timezone, fold=0)
    round_trip = candidate.astimezone(timezone.utc).astimezone(context.timezone)
    if round_trip.replace(tzinfo=None) != local_clock:
        raise DomainAdapterError(
            f"local clock time {local_clock.isoformat()} does not exist in the supplied timezone"
        )
    alternate = local_clock.replace(tzinfo=context.timezone, fold=1)
    if alternate.utcoffset() != candidate.utcoffset():
        raise DomainAdapterError(
            f"local clock time {local_clock.isoformat()} is ambiguous in the supplied timezone"
        )
    return candidate


def maintenance_work_order_to_domain(
    order: MaintenanceWorkOrder,
) -> MaintenanceWorkOrder:
    """Copy a legacy work order into the domain graph's compatible order type."""
    return MaintenanceWorkOrder.model_validate(order.model_dump(mode="python"))


def train_occupancy_window_to_domain(
    window: TrainOccupancyWindow,
    *,
    context: OccupancyConversionContext | None,
    occupancy_id: str,
    train_id: str | None = None,
    provenance: DataProvenance | None = None,
) -> RailwayTrainOccupancy:
    """Convert hour-of-day values using only an explicit date and timezone.

    A legacy window stores numeric hours without a date or timezone. This
    adapter therefore has no default conversion context and never assumes UTC.
    """
    if context is None:
        raise DomainAdapterError(
            "an explicit operating date and timezone are required for occupancy conversion"
        )
    if not occupancy_id or occupancy_id != occupancy_id.strip():
        raise ValueError("occupancy_id must be non-empty and trimmed")
    resolved_train_id = window.train_no if train_id is None else train_id
    if not resolved_train_id or resolved_train_id != resolved_train_id.strip():
        raise ValueError("train_id must be non-empty and trimmed")

    start = _local_datetime(context, window.start_time_hr)
    end = _local_datetime(context, window.end_time_hr)
    source_provenance = _copy_provenance(provenance)
    return RailwayTrainOccupancy(
        occupancy_id=occupancy_id,
        train_id=resolved_train_id,
        section_id=window.section_id,
        track_line=window.track_line,
        entry_time=start,
        exit_time=end,
        start_km=window.train_start_km,
        end_km=window.train_end_km,
        source=source_provenance.source_label,
        provenance=source_provenance,
    )


def route_to_domain(route: Route) -> RailwayRoute:
    """Convert a repository route definition; these definitions are synthetic."""
    return RailwayRoute(
        route_id=route.route_id,
        name=route.name,
        origin=route.origin,
        destination=route.destination,
        length_km=route.length_km,
        sections=[section_id for section_id, _, _ in route.sub_sections],
        provenance=DataProvenance(
            origin=DataOrigin.SYNTHETIC,
            source_label="backend.app.data_engine.ROUTES",
            verification_status=VerificationStatus.UNVERIFIED,
        ),
    )


def route_sections_to_domain(route: Route) -> list[RailwaySection]:
    """Convert route section IDs and positions; track-line facts remain unknown."""
    provenance = DataProvenance(
        origin=DataOrigin.SYNTHETIC,
        source_label="backend.app.data_engine.ROUTES",
        verification_status=VerificationStatus.UNVERIFIED,
    )
    return [
        RailwaySection(
            section_id=section_id,
            route_id=route.route_id,
            name=section_id,
            start_km=start_km,
            end_km=end_km,
            track_lines=None,
            provenance=provenance,
        )
        for section_id, start_km, end_km in route.sub_sections
    ]


def build_railway_domain_model(
    *,
    routes: Sequence[Route],
    work_orders: Sequence[MaintenanceWorkOrder] = (),
    train_windows: Sequence[TrainOccupancyWindow] = (),
    occupancy_context: OccupancyConversionContext | None = None,
    train_occupancies: Sequence[RailwayTrainOccupancy] = (),
    train_services: Sequence[RailwayTrainService] = (),
    block_windows: Sequence[BlockWindow] = (),
    resources: Sequence[Resource] = (),
    dependencies: Sequence[WorkDependency] = (),
    departments: Sequence[RailwayDepartment] | None = None,
) -> DomainBuildResult:
    """Adapt known contracts, validate their combined graph, and report gaps.

    Missing occupancy date/timezone context is reported per input window. The
    unconvertible record is not silently discarded and no solver or verifier
    behavior is invoked.
    """
    issues: list[DomainBuildIssue] = []
    domain_routes: list[RailwayRoute] = []
    domain_sections: list[RailwaySection] = []
    for index, route in enumerate(routes):
        try:
            domain_route = route_to_domain(route)
            route_sections = route_sections_to_domain(route)
        except ValidationError as error:
            issues.append(
                DomainBuildIssue(
                    code="ROUTE_CONVERSION_FAILED",
                    record_type="Route",
                    record_id=f"{route.route_id}:{index}",
                    message=str(error),
                )
            )
            continue
        domain_routes.append(domain_route)
        domain_sections.extend(route_sections)
    route_by_section = {
        section.section_id: section.route_id for section in domain_sections
    }

    domain_train_services = list(train_services)
    services_by_id: dict[str, RailwayTrainService] = {}
    for service in domain_train_services:
        services_by_id.setdefault(service.train_id, service)
    domain_occupancies = list(train_occupancies)
    for index, window in enumerate(train_windows):
        route_id = route_by_section.get(window.section_id)
        if route_id is None:
            issues.append(
                DomainBuildIssue(
                    code="UNKNOWN_OCCUPANCY_SECTION",
                    record_type="TrainOccupancyWindow",
                    record_id=f"{window.train_no}:{index}",
                    message=f"section {window.section_id!r} has no supplied route definition",
                )
            )
            continue

        service_id = f"{route_id}:{window.train_no}"
        if service_id not in services_by_id:
            service = RailwayTrainService(
                train_id=service_id,
                train_number=window.train_no,
                route_id=route_id,
                provenance=DataProvenance(),
            )
            services_by_id[service_id] = service
            domain_train_services.append(service)

        if occupancy_context is None:
            issues.append(
                DomainBuildIssue(
                    code="OCCUPANCY_TIME_CONTEXT_REQUIRED",
                    record_type="TrainOccupancyWindow",
                    record_id=f"{window.train_no}:{index}",
                    message=(
                        "legacy numeric hours have no date or timezone; "
                        "supply OccupancyConversionContext to convert this record"
                    ),
                )
            )
            continue

        try:
            occupancy = train_occupancy_window_to_domain(
                window,
                context=occupancy_context,
                occupancy_id=f"{service_id}:{index}",
                train_id=service_id,
            )
        except (DomainAdapterError, ValidationError) as error:
            issues.append(
                DomainBuildIssue(
                    code="OCCUPANCY_CONVERSION_FAILED",
                    record_type="TrainOccupancyWindow",
                    record_id=f"{window.train_no}:{index}",
                    message=str(error),
                )
            )
            continue
        domain_occupancies.append(occupancy)

    domain_work_orders: list[MaintenanceWorkOrder] = []
    for index, order in enumerate(work_orders):
        try:
            domain_work_orders.append(maintenance_work_order_to_domain(order))
        except ValidationError as error:
            issues.append(
                DomainBuildIssue(
                    code="WORK_ORDER_CONVERSION_FAILED",
                    record_type="MaintenanceWorkOrder",
                    record_id=f"{order.work_id}:{index}",
                    message=str(error),
                )
            )

    try:
        model_options: dict[str, object] = {
            "routes": domain_routes,
            "sections": domain_sections,
            "train_services": domain_train_services,
            "train_occupancies": domain_occupancies,
            "work_orders": domain_work_orders,
            "block_windows": list(block_windows),
            "resources": list(resources),
            "dependencies": list(dependencies),
        }
        if departments is not None:
            model_options["departments"] = list(departments)
        model = RailwayDomainModel(
            **model_options,
        )
    except ValidationError as error:
        issues.append(
            DomainBuildIssue(
                code="DOMAIN_GRAPH_VALIDATION_FAILED",
                record_type="RailwayDomainModel",
                record_id="aggregate",
                message=str(error),
            )
        )
        model = None

    return DomainBuildResult(model=model, issues=tuple(issues))


__all__ = [
    "DomainAdapterError",
    "DomainBuildIssue",
    "DomainBuildResult",
    "OccupancyConversionContext",
    "build_railway_domain_model",
    "maintenance_work_order_to_domain",
    "route_sections_to_domain",
    "route_to_domain",
    "train_occupancy_window_to_domain",
]