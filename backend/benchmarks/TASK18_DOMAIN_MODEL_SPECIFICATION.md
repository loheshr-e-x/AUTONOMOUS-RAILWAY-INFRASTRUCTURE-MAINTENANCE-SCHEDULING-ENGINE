# Task18 — Unified Railway Domain Model

## Scope and compatibility boundary

Task18 introduces a typed, in-memory railway data graph in
`backend/app/schemas/domain.py`, with shared provenance and requirement types in
`backend/app/schemas/domain_types.py`. Pure adapters and aggregate construction
live in `backend/app/schemas/domain_adapters.py`. The graph is versioned with
`schema_version: 1`; it is not a database schema and does not migrate or rewrite
saved scenarios, historical experiments, or benchmark results.

The existing production `MaintenanceWorkOrder` in
`backend/app/schemas/contracts.py` is extended only with optional metadata:
resource requirements, prerequisite IDs, permitted work conditions, and
provenance. Existing scheduling fields, defaults, endpoints, and scenario
contracts remain in place. The work-order request accepts these additive
fields, but the `/api/data/work-orders` and `/api/data/work-orders/custom`
responses use `LegacyMaintenanceWorkOrderResponse` and retain the original
nine-field shape and types. New metadata is not echoed in those legacy API
responses. The retained fields are `work_id: str`, `department: Department`,
`section_id: str`, `track_line: TrackLine`, `heavy_equipment: bool`,
`defect_type: str`, `duration_hrs: float`, `urgency: UrgencyLevel`, and
`co_location_allowed: bool`. The Task16 scenario request and canonical digest
fields are deliberately not extended by this change. Domain-only entities are
not automatically loaded into the production solver.

No external railway rules or actual infrastructure facts are asserted. In
particular, a train-occupancy record is an observation or supplied interval; it
does not establish that a track is available or safe for maintenance. Unknown
positions, lines, operating days, availability, resource capacity, and
verification state remain representable as unknown.

## Legacy adapters and aggregate construction

The pure adapter functions in `backend/app/schemas/domain_adapters.py` are:

- `train_occupancy_window_to_domain(window, *, context, occupancy_id, ...)`
  converts an existing numeric-hour `TrainOccupancyWindow`. A
  `OccupancyConversionContext` is mandatory and must explicitly supply both
  `operating_date` and `timezone`. Numeric hours are interpreted as offsets
  from local midnight on that date; hour `24` maps to midnight on the
  following date. There is no implicit UTC or date default. Calling the
  adapter without context raises `DomainAdapterError`. The legacy type has no
  source/provenance or observation timestamp, so those remain unknown unless
  provenance is explicitly provided. Its optional spatial endpoints are
  preserved. In DST-observing timezones, nonexistent or ambiguous wall-clock
  times are reported as unconvertible instead of silently choosing an offset.
- `maintenance_work_order_to_domain(order)` creates a validated copy of the
  existing `MaintenanceWorkOrder`, which is also the aggregate's compatible
  work-order representation. All fields representable by that schema,
  including additive metadata and provenance, are preserved.
- `route_to_domain(route)` and `route_sections_to_domain(route)` convert the
  current `data_engine.Route`. The route and section positions are available
  from the route definition and are preserved. These hard-coded prototype
  route definitions are labeled `SYNTHETIC` and `UNVERIFIED`; section track
  lines, infrastructure attributes, and other absent facts remain unknown.

`build_railway_domain_model(...)` is the documented aggregate construction
entry point. Supply route definitions and any available legacy work orders and
occupancy windows; already-typed train services, occupancies, block windows,
resources, dependencies, and department declarations can also be supplied.
Pass `OccupancyConversionContext` only when the caller actually knows the
operating date and timezone. The result contains either a validated model or
`None`, plus structured `DomainBuildIssue` entries. A
missing conversion context and an occupancy referencing an unknown section are
reported against their input record; such records are not silently included
or discarded. Aggregate reference-validation failures are returned as
`DOMAIN_GRAPH_VALIDATION_FAILED`. An incomplete result can still contain a
validated graph of the records that were convertible; callers must inspect
`issues` and `is_complete`.

The adapter cannot recover fields absent from a legacy contract. In
particular, `TrainOccupancyWindow` lacks an operating date, timezone,
observation timestamp, occupancy identifier, source, and provenance. The
aggregate builder creates stable per-input occupancy/service IDs from route,
train number, and input position; these are technical identifiers, not
external railway identifiers. Legacy route definitions provide positions but
not track-line inventory or infrastructure metadata. The existing maintenance
work-order contract has no explicit schema-version field; aggregate versioning
applies to `RailwayDomainModel`, not to those legacy records.

This adapter and aggregate validation layer is not connected to the
production solver or safety verifier. Domain validation checks schema,
references, intervals, and declared graph consistency. Operational validation
would require separately specified rules and trusted evidence; successful
domain-model construction is not a schedule-safety or railway-feasibility
claim.

## Entity relationships

```text
RailwayRoute 1 ── * RailwaySection
     │                    │
     └── * TrainService ──┴── * TrainOccupancy
                                  (train + section + time interval)

RailwaySection 1 ── * BlockWindow
RailwaySection 1 ── * MaintenanceWorkOrder
RailwaySection 0..1 ── * Resource

MaintenanceWorkOrder * ── * MaintenanceWorkOrder
    through WorkDependency (prerequisite, successor, shared block,
    or incompatibility); prerequisites are cycle-checked.

MaintenanceWorkOrder ── * ResourceRequirement
MaintenanceWorkOrder ── * WorkCondition
```

`RailwayDomainModel` validates the references that can be resolved within one
provided graph. Route membership and section `route_id` must agree. A train
service references a known route; an occupancy references a known train and
section on the same route. Work, block, resource-location, and dependency
references must resolve. Where a section's track-line list is known, a supplied
occupancy, work-order, or block-window line must belong to it.

## Entity fields

See [TASK18_DATA_DICTIONARY.csv](./TASK18_DATA_DICTIONARY.csv) for the complete
field-level list and compatibility classification. `MaintenanceWorkOrder`
retains its legacy fields:

- `work_id`, `department`, `section_id`, `track_line`,
  `heavy_equipment`, `defect_type`, `duration_hrs`, `urgency`, and
  `co_location_allowed`.

The following optional fields are added:

- `resource_requirements`: `None` means not supplied/unknown; an empty list
  means explicitly no resource types are required. Each entry combines a
  resource type and positive quantity.
- `prerequisites`: `None` means not supplied/unknown; an empty list means no
  prerequisite work IDs are declared.
- `permitted_work_conditions`: optional typed condition identifiers and
  descriptions; these are data, not enforced operating policy.
- `provenance`: defaults to unknown and is not inferred from a source label.

## Provenance and verification

`DataProvenance.origin` distinguishes `PUBLIC_DATA`, `SYNTHETIC`,
`USER_SUPPLIED`, `AUTHENTICATED_EXTERNAL`, `INFERRED`, and `UNKNOWN`.
`verification_status` independently distinguishes `AUTHENTICATED`,
`UNVERIFIED`, and `UNKNOWN`. Missing status defaults to `UNKNOWN` for an
unknown origin and `UNVERIFIED` for a known origin.

An `AUTHENTICATED` status requires `AUTHENTICATED_EXTERNAL` origin plus
`verified_at`, `verified_by`, and `verification_reference`. Supplying only a
source label does not satisfy this schema contract. These fields record an
assertion and its evidence reference; the model itself does not authenticate
the evidence, authorize a source, or replace the production verifier's
trusted-provider boundary.

Timestamped observations and intervals require timezone-aware datetimes.
Confidence, when supplied, is between zero and one. Provenance values default
to unknown; the schema does not relabel existing synthetic route data as
public, verified, or authenticated.

## Validation and incomplete data

The aggregate enforces unique identifiers within each entity collection,
known route/section/train/work/department references, route-section
membership consistency, and acyclic strict prerequisite/successor relations.
Intervals require a start before an end. Spatial section coordinates, when
provided, must be supplied as a pair, have positive length, and fit within a
known route length. Positive resource capacity and resource requirement
quantity are enforced when supplied.

Optional fields intentionally preserve missing information. For example,
unknown section positions are `None`, unknown track-line inventory is `None`,
unknown resource capacity is `None`, and unknown block availability is
`UNKNOWN`. An empty list is distinct from an unknown list when the list is
optional. This distinction prevents a missing timetable, block, or resource
record from being interpreted as proof of availability or nonexistence.

## Data lifecycle and limitations

The aggregate is a validation boundary for typed data; it is not persisted by
Task18 and does not change scenario storage or experiment-export formats.
`schema_version` versions this aggregate payload, not the existing scenario
schema. No destructive migration is required.

The model does not check train/maintenance time conflicts, issue block
authority, infer traction isolation, calculate spatial safety buffers, or
certify railway operational feasibility. Such checks require independently
defined operational rules and trusted evidence, which are outside this task.
