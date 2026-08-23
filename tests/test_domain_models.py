from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from airindex.domain.models import (
    AvailabilityStatus,
    FareObservation,
    FareSearchRequest,
    QualityStatus,
    SourceType,
)


UTC = timezone.utc


def make_observation(**overrides: object) -> FareObservation:
    values: dict[str, object] = {
        "source_name": "Example Airline",
        "source_type": SourceType.AIRLINE,
        "collected_at": datetime(2026, 8, 23, 10, 0, tzinfo=UTC),
        "origin": "DEL",
        "destination": "BOM",
        "travel_date": date(2026, 9, 7),
        "carrier_code": "6E",
        "base_fare": Decimal("4000.00"),
        "taxes": Decimal("720.00"),
        "user_development_fee": Decimal("150.00"),
        "convenience_fee": Decimal("99.00"),
        "scraper_version": "test-1.0",
        "quality_status": QualityStatus.PENDING,
    }
    values.update(overrides)
    return FareObservation(**values)


def test_total_fare_and_advance_days_are_derived() -> None:
    observation = make_observation()

    assert observation.total_fare == Decimal("4969.00")
    assert observation.advance_days == 15


def test_search_request_uses_requested_date_for_advance_window() -> None:
    request = FareSearchRequest(
        origin="DEL",
        destination="BLR",
        travel_date=date(2026, 8, 30),
        requested_at=datetime(2026, 8, 23, 10, 0, tzinfo=UTC),
    )

    assert request.advance_days == 7


def test_same_airport_route_is_rejected() -> None:
    with pytest.raises(ValidationError, match="origin and destination must differ"):
        FareSearchRequest(
            origin="DEL",
            destination="DEL",
            travel_date=date(2026, 8, 30),
            requested_at=datetime(2026, 8, 23, 10, 0, tzinfo=UTC),
        )


def test_past_travel_date_is_rejected() -> None:
    with pytest.raises(ValidationError, match="travel_date cannot be before"):
        make_observation(travel_date=date(2026, 8, 22))


def test_sold_out_observation_cannot_have_positive_fare() -> None:
    with pytest.raises(ValidationError, match="sold-out observations"):
        make_observation(
            availability=AvailabilityStatus.SOLD_OUT,
            base_fare=Decimal("1000.00"),
        )


def test_model_is_immutable() -> None:
    observation = make_observation()

    with pytest.raises(ValidationError):
        observation.base_fare = Decimal("1.00")
