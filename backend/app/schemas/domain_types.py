"""Shared railway schema types used by legacy and versioned contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)


class Department(str, Enum):
    ENGINEERING = "ENGINEERING"
    SIGNALLING = "SIGNALLING"
    TRACTION = "TRACTION"


class UrgencyLevel(int, Enum):
    CRITICAL = 1
    MEDIUM = 2
    ROUTINE = 3


class TrackLine(str, Enum):
    UP_LINE = "UP_LINE"
    DOWN_LINE = "DOWN_LINE"


class DataOrigin(str, Enum):
    PUBLIC_DATA = "PUBLIC_DATA"
    SYNTHETIC = "SYNTHETIC"
    USER_SUPPLIED = "USER_SUPPLIED"
    AUTHENTICATED_EXTERNAL = "AUTHENTICATED_EXTERNAL"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class VerificationStatus(str, Enum):
    AUTHENTICATED = "AUTHENTICATED"
    UNVERIFIED = "UNVERIFIED"
    UNKNOWN = "UNKNOWN"


class DataProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: DataOrigin = DataOrigin.UNKNOWN
    source_label: StrictStr | None = None
    source_uri: StrictStr | None = None
    observed_at: datetime | None = None
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    verification_status: VerificationStatus | None = None
    verified_at: datetime | None = None
    verified_by: StrictStr | None = None
    verification_reference: StrictStr | None = None

    @field_validator("observed_at", "verified_at")
    @classmethod
    def provenance_times_require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("provenance timestamps must include a timezone")
        return value

    @field_validator("source_label", "source_uri", "verified_by", "verification_reference")
    @classmethod
    def provenance_strings_must_be_trimmed(
        cls, value: str | None
    ) -> str | None:
        if value is not None and (not value or value != value.strip()):
            raise ValueError("provenance strings must be non-empty and trimmed")
        return value

    @model_validator(mode="after")
    def authentication_requires_evidence(self) -> DataProvenance:
        evidence = (
            self.verified_at,
            self.verified_by,
            self.verification_reference,
        )
        if self.verification_status is None:
            self.verification_status = (
                VerificationStatus.UNKNOWN
                if self.origin is DataOrigin.UNKNOWN
                else VerificationStatus.UNVERIFIED
            )
        if self.verification_status is VerificationStatus.AUTHENTICATED:
            if self.origin is not DataOrigin.AUTHENTICATED_EXTERNAL:
                raise ValueError(
                    "authentication requires AUTHENTICATED_EXTERNAL provenance"
                )
            if any(value is None for value in evidence):
                raise ValueError(
                    "authenticated provenance requires verification evidence"
                )
        elif any(value is not None for value in evidence):
            raise ValueError(
                "verification evidence may only accompany AUTHENTICATED provenance"
            )
        return self


class WorkCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    condition_id: Annotated[StrictStr, Field(min_length=1)]
    description: StrictStr | None = None
    provenance: DataProvenance = Field(default_factory=DataProvenance)

    @field_validator("condition_id", "description")
    @classmethod
    def condition_strings_must_be_trimmed(
        cls, value: str | None
    ) -> str | None:
        if value is not None and (not value or value != value.strip()):
            raise ValueError("condition strings must be non-empty and trimmed")
        return value


class ResourceRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_type: Annotated[StrictStr, Field(min_length=1)]
    quantity: Annotated[StrictInt, Field(gt=0)]

    @field_validator("resource_type")
    @classmethod
    def resource_type_must_be_trimmed(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("resource_type must be trimmed")
        return value
