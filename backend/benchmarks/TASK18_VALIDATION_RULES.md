# Task18 — Validation Rules

This document describes the validators implemented by
`backend/app/schemas/domain.py` and `backend/app/schemas/domain_types.py`.
These schemas validate typed records and references; they do not enforce
railway operating rules.

| Area | Rule | Handling of unknown or incomplete values |
|---|---|---|
| Strict input shape | Domain entity models reject unknown fields. | Optional fields may be omitted where specified. |
| Provenance | Origin must be one of the six `DataOrigin` values. Confidence, if present, must be in `[0, 1]`. Timestamps must be timezone-aware. | Origin defaults to `UNKNOWN`; confidence and timestamps may be absent. |
| Authentication | `AUTHENTICATED` requires origin `AUTHENTICATED_EXTERNAL` and all of `verified_at`, `verified_by`, and `verification_reference`. Evidence is rejected for other verification statuses. | A source label alone is informational and never establishes authentication. Schema fields record an assertion; trusted source verification remains external. |
| Identifiers | IDs and names must be non-empty and trimmed. IDs are unique within each entity collection; route section lists, operating days, prerequisites, resource requirement types, and work-condition IDs do not duplicate values. | IDs that define a required relationship cannot be omitted. |
| Route / section | Each section references a route, and route section membership agrees in both directions. Known section end positions cannot exceed known route length. | Route length and section positions can be unknown. A route may have no listed sections. |
| Spatial interval | Section positions must be supplied as a pair and end must exceed start. Positions cannot be negative. | Both positions may be absent. |
| Train service | Every train service references a known route. | Train name and operating days may be unknown (`None`). |
| Train occupancy | Occupancy references a known train and section; both must be on the same route. If section track lines are known, a supplied occupancy line must be included. Entry and exit times must be timezone-aware and strictly increasing. Spatial endpoints must be supplied together, and end must exceed start. | Track line, spatial endpoints, source, observation timestamp, and provenance evidence may be unknown. An occupancy is not proof of availability. |
| Work order | Work order references a known section and declared department. When section track lines are known, its line must be included. | Existing work-order scheduling fields remain required as before. New resource, prerequisite, condition, and provenance metadata are optional. |
| Work requirements | Resource requirement type is non-empty and trimmed; quantity is a positive integer. Work order requirement types and condition IDs are unique within their respective lists. | `None` means not supplied; `[]` means explicitly empty. |
| Block window | Block references a known section. If section track lines are known, a supplied line must be included. Start and end are timezone-aware and strictly increasing. | Availability defaults to `UNKNOWN`; this does not assert availability or unavailability. |
| Resource | Capacity, when present, is finite and positive. Department and any associated section references must resolve. | Capacity, location, and availability intervals may be unknown. |
| Dependency | Both work IDs must resolve; a relationship cannot point to itself. `PREREQUISITE` and `SUCCESSOR` relationships are treated as directed strict-precedence edges for cycle detection. | Shared-block and incompatibility links are validated as references but do not imply scheduling behavior. |
| Prerequisite graph | Cycles in order-level prerequisite lists or strict prerequisite/successor dependency edges are rejected. | Shared-block and incompatibility relationships are not treated as precedence edges. |
| Schema version | Aggregate version must equal `1`. | This is an in-memory versioned contract; no persistence migration is performed. |

## Legacy conversion boundary

`train_occupancy_window_to_domain` requires an explicit operating date and
timezone because `TrainOccupancyWindow` only contains numeric hours. Hours are
local wall-clock offsets from midnight on the supplied date; `24` maps to
midnight the next day. It rejects nonexistent or ambiguous DST wall-clock
times. It never supplies UTC or a calendar date by default.
`build_railway_domain_model` reports each occupancy window it cannot convert,
including absent date/timezone context or unknown section references. Its
`DomainBuildResult.issues` must be checked; partial construction is not a
complete import.

The production work-order APIs accept additive metadata but retain their
original nine response fields and types through
`LegacyMaintenanceWorkOrderResponse`. The scenario API and its digest contract
are unchanged. The production solver's normalized input projection ignores
the new metadata; this model does not add scheduling or safety constraints.

## Not validated by this model

The model does not establish schedule feasibility, detect occupancy overlap
with proposed work, establish block authority, verify traction isolation,
calculate spatial safety buffers, authenticate source systems, or apply
department-specific operational requirements. Those require explicitly
specified operational rules and trusted evidence. No successful schema
validation should be described as proof of railway safety or real-world
availability.
