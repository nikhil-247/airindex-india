"""Pydantic contracts shared by collectors, pipelines and API boundaries."""

from datetime import date, datetime, time
from decimal import Decimal
from enum import StrEnum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

AirportCode = Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")]
CurrencyCode = Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")]
NonNegativeMoney = Annotated[Decimal, Field(ge=Decimal("0"), max_digits=12, decimal_places=2)]


class SourceType(StrEnum):
    AIRLINE = "airline"
    OTA = "ota"
    REFERENCE = "reference"


class AvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    SOLD_OUT = "sold_out"
    UNKNOWN = "unknown"


class QualityStatus(StrEnum):
    PENDING = "pending"
    VALID = "valid"
    SUSPECT = "suspect"
    OUTLIER = "outlier"
    REJECTED = "rejected"


class FareSearchRequest(BaseModel):
    """Normalized search request used by every collector adapter."""

    model_config = ConfigDict(frozen=True)

    origin: AirportCode
    destination: AirportCode
    travel_date: date
    requested_at: datetime
    currency: CurrencyCode = "INR"
    non_stop_only: bool = True

    @model_validator(mode="after")
    def validate_route(self) -> "FareSearchRequest":
        if self.origin == self.destination:
            raise ValueError("origin and destination must differ")
        if self.travel_date < self.requested_at.date():
            raise ValueError("travel_date cannot be before requested_at date")
        return self

    @computed_field
    @property
    def advance_days(self) -> int:
        return (self.travel_date - self.requested_at.date()).days


class FareObservation(BaseModel):
    """Canonical immutable-style observation emitted by a source adapter.

    Collectors may have richer source-specific fields internally, but only this
    contract crosses into the normalized pipeline.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    observation_id: UUID = Field(default_factory=uuid4)
    source_name: str = Field(min_length=1, max_length=120)
    source_type: SourceType
    source_url: str | None = None
    collected_at: datetime

    origin: AirportCode
    destination: AirportCode
    travel_date: date
    carrier_code: str = Field(min_length=2, max_length=3)
    flight_number: str | None = Field(default=None, max_length=20)
    fare_class: str | None = Field(default=None, max_length=40)
    fare_family: str | None = Field(default=None, max_length=80)

    departure_time: time | None = None
    arrival_time: time | None = None
    stops: int = Field(default=0, ge=0, le=9)

    base_fare: NonNegativeMoney
    taxes: NonNegativeMoney = Decimal("0")
    user_development_fee: NonNegativeMoney = Decimal("0")
    convenience_fee: NonNegativeMoney = Decimal("0")
    other_fees: NonNegativeMoney = Decimal("0")
    currency: CurrencyCode = "INR"

    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    scraper_version: str = Field(min_length=1, max_length=40)
    collection_run_id: UUID | None = None

    quality_status: QualityStatus = QualityStatus.PENDING
    quality_score: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("100"), decimal_places=2)

    @computed_field
    @property
    def total_fare(self) -> Decimal:
        return (
            self.base_fare
            + self.taxes
            + self.user_development_fee
            + self.convenience_fee
            + self.other_fees
        )

    @computed_field
    @property
    def advance_days(self) -> int:
        return (self.travel_date - self.collected_at.date()).days

    @model_validator(mode="after")
    def validate_observation(self) -> "FareObservation":
        if self.origin == self.destination:
            raise ValueError("origin and destination must differ")
        if self.travel_date < self.collected_at.date():
            raise ValueError("travel_date cannot be before collected_at date")
        if self.availability == AvailabilityStatus.SOLD_OUT and self.total_fare > 0:
            raise ValueError("sold-out observations must not carry a quoted fare")
        return self
