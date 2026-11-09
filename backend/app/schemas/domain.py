"""Versioned railway-domain entities with explicit provenance and validation."""

from __future__ import annotations

from collections import deque
from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictStr,
    field_validator,
    model_validator,
)

from .contracts import MaintenanceWorkOrder
from .domain_types import (
    DataOrigin,
    DataProvenance,
    Department,
    ResourceRequirement,
    TrackLine,
    UrgencyLevel,
    VerificationStatus,
    WorkCondition,
)

class AvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class DependencyType(str, Enum):
    PREREQUISITE = "PREREQUISITE"
    SUCCESSOR = "SUCCESSOR"
    SHARED_BLOCK_REQUIREMENT = "SHARED_BLOCK_REQUIREMENT"
    INCOMPATIBILITY = "INCOMPATIBILITY"


class OperatingDay(str, Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RailwayRoute(DomainModel):
    route_id: Annotated[StrictStr, Field(min_length=1)]
    name: Annotated[StrictStr, Field(min_length=1)]
    origin: Annotated[StrictStr, Field(min_length=1)]
    destination: Annotated[StrictStr, Field(min_length=1)]
    length_km: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    sections: list[Annotated[StrictStr, Field(min_length=1)]] = Field(
        default_factory=list
    )
    provenance: DataProvenance = Field(default_factory=DataProvenance)

    @field_validator("route_id", "name", "origin", "destination")
    @classmethod
    def route_strings_must_be_trimmed(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("route identifiers and names must be trimmed")
        return value

    @field_validator("sections")
    @classmethod
    def route_section_ids_must_be_unique(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("route sections must not contain duplicate section IDs")
        return values


class RailwaySection(DomainModel):
    section_id: Annotated[StrictStr, Field(min_length=1)]
    route_id: Annotated[StrictStr, Field(min_length=1)]
    name: Annotated[StrictStr, Field(min_length=1)]
    start_km: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    end_km: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    track_lines: list[TrackLine] | None = None
    infrastructure_metadata: dict[str, str | int | float | bool | None] | None = None
    provenance: DataProvenance = Field(default_factory=DataProvenance)

    @field_validator("section_id", "route_id", "name")
    @classmethod
    def section_strings_must_be_trimmed(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("section identifiers and names must be trimmed")
        return value

    @field_validator("track_lines")
    @classmethod
    def known_track_lines_must_be_unique(
        cls, values: list[TrackLine] | None
    ) -> list[TrackLine] | None:
        if values is not None and (
            not values or len(values) != len(set(values))
        ):
            raise ValueError("known track_lines must be non-empty and unique")
        return values

    @model_validator(mode="after")
    def spatial_interval_must_be_complete(self) -> RailwaySection:
        if (self.start_km is None) != (self.end_km is None):
            raise ValueError("section start_km and end_km must be supplied together")
        if (
            self.start_km is not None
            and self.end_km is not None
            and self.end_km <= self.start_km
        ):
            raise ValueError("section end_km must exceed start_km")
        return self


class RailwayTrainService(DomainModel):
    train_id: Annotated[StrictStr, Field(min_length=1)]
    train_number: Annotated[StrictStr, Field(min_length=1)]
    train_name: StrictStr | None = None
    operating_days: list[OperatingDay] | None = None
    route_id: Annotated[StrictStr, Field(min_length=1)]
    provenance: DataProvenance = Field(default_factory=DataProvenance)

    @field_validator("train_id", "train_number", "train_name", "route_id")
    @classmethod
    def train_strings_must_be_trimmed(cls, value: str | None) -> str | None:
        if value is not None and (not value or value != value.strip()):
            raise ValueError("train identifiers and names must be non-empty and trimmed")
        return value

    @field_validator("operating_days")
    @classmethod
    def operating_days_must_be_unique(
        cls, values: list[OperatingDay] | None
    ) -> list[OperatingDay] | None:
        if values is not None and len(values) != len(set(values)):
            raise ValueError("operating_days must not contain duplicates")
        return values


class DomainTimeInterval(DomainModel):
    start_time: datetime
    end_time: datetime
    section_id: StrictStr | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def interval_times_require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("interval timestamps must include a timezone")
        return value

    @model_validator(mode="after")
    def interval_must_be_positive(self) -> DomainTimeInterval:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if self.section_id is not None and (
            not self.section_id or self.section_id != self.section_id.strip()
        ):
            raise ValueError("interval section_id must be non-empty and trimmed")
        return self


class RailwayTrainOccupancy(DomainModel):
    occupancy_id: Annotated[StrictStr, Field(min_length=1)]
    train_id: Annotated[StrictStr, Field(min_length=1)]
    section_id: Annotated[StrictStr, Field(min_length=1)]
    track_line: TrackLine | None = None
    entry_time: datetime
    exit_time: datetime
    start_km: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    end_km: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    source: StrictStr | None = None
    observation_timestamp: datetime | None = None
    provenance: DataProvenance = Field(default_factory=DataProvenance)

    @field_validator(
        "entry_time", "exit_time", "observation_timestamp"
    )
    @classmethod
    def occupancy_times_require_timezone(
        cls, value: datetime | None
    ) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("occupancy timestamps must include a timezone")
        return value

    @field_validator("occupancy_id", "train_id", "section_id", "source")
    @classmethod
    def occupancy_strings_must_be_trimmed(
        cls, value: str | None
    ) -> str | None:
        if value is not None and (not value or value != value.strip()):
            raise ValueError("occupancy identifiers and source must be trimmed")
        return value

    @model_validator(mode="after")
    def occupancy_interval_and_source_must_agree(
        self,
    ) -> RailwayTrainOccupancy:
        if self.exit_time <= self.entry_time:
            raise ValueError("occupancy exit_time must be after entry_time")
        if (self.start_km is None) != (self.end_km is None):
            raise ValueError("occupancy start_km and end_km must be supplied together")
        if (
            self.start_km is not None
            and self.end_km is not None
            and self.end_km <= self.start_km
        ):
            raise ValueError("occupancy end_km must exceed start_km")
        if (
            self.source is not None
            and self.provenance.source_label is not None
            and self.source != self.provenance.source_label
        ):
            raise ValueError("occupancy source conflicts with provenance source_label")
        return self


class RailwayDepartment(DomainModel):
    department_id: Department
    name: Annotated[StrictStr, Field(min_length=1)]

    @field_validator("name")
    @classmethod
    def department_name_must_be_trimmed(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("department name must be trimmed")
        return value


def _default_departments() -> list[RailwayDepartment]:
    return [
        RailwayDepartment(department_id=Department.ENGINEERING, name="Engineering"),
        RailwayDepartment(department_id=Department.SIGNALLING, name="Signalling"),
        RailwayDepartment(
            department_id=Department.TRACTION,
            name="Traction Distribution",
        ),
    ]


class BlockWindow(DomainModel):
    block_id: Annotated[StrictStr, Field(min_length=1)]
    section_id: Annotated[StrictStr, Field(min_length=1)]
    track_line: TrackLine | None = None
    start_time: datetime
    end_time: datetime
    availability_status: AvailabilityStatus = AvailabilityStatus.UNKNOWN
    source: StrictStr | None = None
    provenance: DataProvenance = Field(default_factory=DataProvenance)

    @field_validator("start_time", "end_time")
    @classmethod
    def block_times_require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("block window timestamps must include a timezone")
        return value

    @field_validator("block_id", "section_id", "source")
    @classmethod
    def block_strings_must_be_trimmed(cls, value: str | None) -> str | None:
        if value is not None and (not value or value != value.strip()):
            raise ValueError("block identifiers and source must be trimmed")
        return value

    @model_validator(mode="after")
    def block_interval_and_source_must_agree(self) -> BlockWindow:
        if self.end_time <= self.start_time:
            raise ValueError("block window end_time must be after start_time")
        if (
            self.source is not None
            and self.provenance.source_label is not None
            and self.source != self.provenance.source_label
        ):
            raise ValueError("block source conflicts with provenance source_label")
        return self


class Resource(DomainModel):
    resource_id: Annotated[StrictStr, Field(min_length=1)]
    resource_type: Annotated[StrictStr, Field(min_length=1)]
    department: Department
    capacity: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    availability_intervals: list[DomainTimeInterval] | None = None
    section_id: StrictStr | None = None
    provenance: DataProvenance = Field(default_factory=DataProvenance)

    @field_validator("resource_id", "resource_type", "section_id")
    @classmethod
    def resource_strings_must_be_trimmed(
        cls, value: str | None
    ) -> str | None:
        if value is not None and (not value or value != value.strip()):
            raise ValueError("resource identifiers and types must be trimmed")
        return value


class WorkDependency(DomainModel):
    dependency_id: Annotated[StrictStr, Field(min_length=1)]
    work_id: Annotated[StrictStr, Field(min_length=1)]
    related_work_id: Annotated[StrictStr, Field(min_length=1)]
    relationship: DependencyType
    provenance: DataProvenance = Field(default_factory=DataProvenance)

    @field_validator("dependency_id", "work_id", "related_work_id")
    @classmethod
    def dependency_strings_must_be_trimmed(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("dependency identifiers must be trimmed")
        return value

    @model_validator(mode="after")
    def dependency_must_reference_two_orders(self) -> WorkDependency:
        if self.work_id == self.related_work_id:
            raise ValueError("a work dependency cannot reference itself")
        return self


class RailwayDomainModel(DomainModel):
    """Validated, in-memory railway data graph; no persistence or solver behavior."""

    schema_version: Literal[1] = 1
    routes: list[RailwayRoute] = Field(default_factory=list)
    sections: list[RailwaySection] = Field(default_factory=list)
    train_services: list[RailwayTrainService] = Field(default_factory=list)
    train_occupancies: list[RailwayTrainOccupancy] = Field(default_factory=list)
    work_orders: list["MaintenanceWorkOrder"] = Field(default_factory=list)
    block_windows: list[BlockWindow] = Field(default_factory=list)
    departments: list[RailwayDepartment] = Field(default_factory=_default_departments)
    resources: list[Resource] = Field(default_factory=list)
    dependencies: list[WorkDependency] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_domain_references_and_cycles(self) -> RailwayDomainModel:
        self._validate_unique_ids()

        routes = {route.route_id: route for route in self.routes}
        sections = {section.section_id: section for section in self.sections}
        trains = {train.train_id: train for train in self.train_services}
        work_orders = {order.work_id: order for order in self.work_orders}
        departments = {item.department_id for item in self.departments}

        for section in self.sections:
            route = routes.get(section.route_id)
            if route is None:
                raise ValueError(
                    f"section {section.section_id!r} references unknown route_id {section.route_id!r}"
                )
            if section.section_id not in route.sections:
                raise ValueError(
                    f"section {section.section_id!r} is not listed by its route"
                )
            if (
                route.length_km is not None
                and section.end_km is not None
                and section.end_km > route.length_km
            ):
                raise ValueError(
                    f"section {section.section_id!r} exceeds its route length"
                )

        for route in self.routes:
            for section_id in route.sections:
                section = sections.get(section_id)
                if section is None:
                    raise ValueError(
                        f"route {route.route_id!r} references unknown section {section_id!r}"
                    )
                if section.route_id != route.route_id:
                    raise ValueError(
                        f"section {section_id!r} route_id does not match route membership"
                    )

        for train in self.train_services:
            if train.route_id not in routes:
                raise ValueError(
                    f"train {train.train_id!r} references unknown route_id {train.route_id!r}"
                )

        for occupancy in self.train_occupancies:
            train = trains.get(occupancy.train_id)
            if train is None:
                raise ValueError(
                    f"occupancy {occupancy.occupancy_id!r} references unknown train_id {occupancy.train_id!r}"
                )
            section = sections.get(occupancy.section_id)
            if section is None:
                raise ValueError(
                    f"occupancy {occupancy.occupancy_id!r} references unknown section_id {occupancy.section_id!r}"
                )
            if train.route_id != section.route_id:
                raise ValueError(
                    f"occupancy {occupancy.occupancy_id!r} train and section routes disagree"
                )
            if (
                occupancy.start_km is not None
                and section.start_km is not None
                and occupancy.start_km < section.start_km
            ):
                raise ValueError(
                    f"occupancy {occupancy.occupancy_id!r} starts before its section"
                )
            if (
                occupancy.end_km is not None
                and section.end_km is not None
                and occupancy.end_km > section.end_km
            ):
                raise ValueError(
                    f"occupancy {occupancy.occupancy_id!r} ends after its section"
                )
            if (
                occupancy.track_line is not None
                and section.track_lines is not None
                and occupancy.track_line not in section.track_lines
            ):
                raise ValueError(
                    f"occupancy {occupancy.occupancy_id!r} references a track line not present on its section"
                )

        for order in self.work_orders:
            section = sections.get(order.section_id)
            if section is None:
                raise ValueError(
                    f"work order {order.work_id!r} references unknown section_id {order.section_id!r}"
                )
            if order.department not in departments:
                raise ValueError(
                    f"work order {order.work_id!r} references unknown department"
                )
            if (
                section.track_lines is not None
                and order.track_line not in section.track_lines
            ):
                raise ValueError(
                    f"work order {order.work_id!r} references a track line not present on its section"
                )
            for prerequisite in order.prerequisites or []:
                if prerequisite not in work_orders:
                    raise ValueError(
                        f"work order {order.work_id!r} references unknown prerequisite work order {prerequisite!r}"
                    )

        for block in self.block_windows:
            section = sections.get(block.section_id)
            if section is None:
                raise ValueError(
                    f"block {block.block_id!r} references unknown section_id {block.section_id!r}"
                )
            if (
                block.track_line is not None
                and section.track_lines is not None
                and block.track_line not in section.track_lines
            ):
                raise ValueError(
                    f"block {block.block_id!r} references a track line not present on its section"
                )

        for resource in self.resources:
            if resource.department not in departments:
                raise ValueError(
                    f"resource {resource.resource_id!r} references unknown department"
                )
            referenced_sections = [
                section_id
                for section_id in [resource.section_id]
                + [
                    interval.section_id
                    for interval in resource.availability_intervals or []
                ]
                if section_id is not None
            ]
            for section_id in referenced_sections:
                if section_id not in sections:
                    raise ValueError(
                        f"resource {resource.resource_id!r} references unknown section_id {section_id!r}"
                    )

        prerequisite_edges: list[tuple[str, str]] = []
        for order in self.work_orders:
            prerequisite_edges.extend(
                (prerequisite, order.work_id)
                for prerequisite in order.prerequisites or []
            )
        for dependency in self.dependencies:
            if dependency.work_id not in work_orders:
                raise ValueError(
                    f"dependency {dependency.dependency_id!r} references unknown work order {dependency.work_id!r}"
                )
            if dependency.related_work_id not in work_orders:
                raise ValueError(
                    f"dependency {dependency.dependency_id!r} references unknown work order {dependency.related_work_id!r}"
                )
            if dependency.relationship is DependencyType.PREREQUISITE:
                prerequisite_edges.append(
                    (dependency.work_id, dependency.related_work_id)
                )
            elif dependency.relationship is DependencyType.SUCCESSOR:
                prerequisite_edges.append(
                    (dependency.related_work_id, dependency.work_id)
                )

        self._reject_prerequisite_cycles(work_orders, prerequisite_edges)
        return self

    def _validate_unique_ids(self) -> None:
        entities = (
            ("route_id", [item.route_id for item in self.routes]),
            ("section_id", [item.section_id for item in self.sections]),
            ("train_id", [item.train_id for item in self.train_services]),
            ("occupancy_id", [item.occupancy_id for item in self.train_occupancies]),
            ("work_id", [item.work_id for item in self.work_orders]),
            ("block_id", [item.block_id for item in self.block_windows]),
            ("resource_id", [item.resource_id for item in self.resources]),
            (
                "department_id",
                [item.department_id for item in self.departments],
            ),
            (
                "dependency_id",
                [item.dependency_id for item in self.dependencies],
            ),
        )
        for identifier, values in entities:
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate {identifier} in domain model")

    @staticmethod
    def _reject_prerequisite_cycles(
        work_orders: dict[str, object],
        edges: list[tuple[str, str]],
    ) -> None:
        outgoing = {work_id: set() for work_id in work_orders}
        indegree = {work_id: 0 for work_id in work_orders}
        for prerequisite, successor in edges:
            if successor not in outgoing[prerequisite]:
                outgoing[prerequisite].add(successor)
                indegree[successor] += 1

        ready = deque(
            work_id for work_id, degree in indegree.items() if degree == 0
        )
        visited = 0
        while ready:
            work_id = ready.popleft()
            visited += 1
            for successor in outgoing[work_id]:
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    ready.append(successor)
        if visited != len(work_orders):
            raise ValueError("prerequisite cycle detected")


__all__ = [
    "AvailabilityStatus",
    "BlockWindow",
    "DataOrigin",
    "DataProvenance",
    "DependencyType",
    "DomainTimeInterval",
    "OperatingDay",
    "RailwayDepartment",
    "RailwayDomainModel",
    "RailwayRoute",
    "RailwaySection",
    "RailwayTrainOccupancy",
    "RailwayTrainService",
    "Resource",
    "ResourceRequirement",
    "TrackLine",
    "VerificationStatus",
    "WorkCondition",
    "WorkDependency",
]
