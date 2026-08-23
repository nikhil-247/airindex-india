from datetime import date, datetime, timezone
from decimal import Decimal
from os import getenv
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from airindex.domain.models import FareObservation, QualityStatus, SourceType
from airindex.db.repository import FareObservationRepository


DATABASE_URL = getenv("DATABASE_URL", "postgresql+asyncpg://airindex:airindex@localhost:5432/airindex")
UTC = timezone.utc


def make_observation() -> FareObservation:
    return FareObservation(
        source_name="Integration Test Airline",
        source_type=SourceType.AIRLINE,
        collected_at=datetime(2026, 8, 23, 10, 0, tzinfo=UTC),
        origin="DEL",
        destination="BOM",
        travel_date=date(2026, 9, 7),
        carrier_code="6E",
        base_fare=Decimal("4000.00"),
        taxes=Decimal("720.00"),
        scraper_version="integration-1.0",
        quality_status=QualityStatus.PENDING,
    )


@pytest.mark.asyncio
async def test_migration_and_repository_round_trip() -> None:
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("SELECT 1"))
            source_id = uuid4()
            await connection.execute(
                text("""
                    INSERT INTO sources (id, code, name, source_type, policy_version)
                    VALUES (:id, :code, :name, :source_type, :policy_version)
                """),
                {
                    "id": source_id,
                    "code": f"test-{source_id.hex[:8]}",
                    "name": "Integration Test Airline",
                    "source_type": "airline",
                    "policy_version": "test-1",
                },
            )
            await connection.execute(
                text("INSERT INTO airports (iata_code, name, city) VALUES ('DEL', 'Delhi', 'Delhi'), ('BOM', 'Mumbai', 'Mumbai') ON CONFLICT DO NOTHING")
            )
            await connection.execute(
                text("INSERT INTO airlines (iata_code, name) VALUES ('6E', 'IndiGo') ON CONFLICT DO NOTHING")
            )
        async with engine.begin() as connection:
            repository = FareObservationRepository(connection)
            observation = make_observation()
            await repository.add(observation, source_id)
            count = await repository.count_for_route("DEL", "BOM", date(2026, 9, 7))
            assert count >= 1
    finally:
        await engine.dispose()
