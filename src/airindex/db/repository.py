from datetime import date
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from airindex.domain.models import FareObservation


class FareObservationRepository:
    """Persistence boundary for canonical fare observations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, observation: FareObservation, source_id: UUID) -> UUID:
        values = {
            "id": observation.observation_id,
            "source_id": source_id,
            "collection_run_id": observation.collection_run_id,
            "collected_at": observation.collected_at,
            "origin": observation.origin,
            "destination": observation.destination,
            "travel_date": observation.travel_date,
            "carrier_code": observation.carrier_code,
            "flight_number": observation.flight_number,
            "fare_class": observation.fare_class,
            "fare_family": observation.fare_family,
            "departure_time": observation.departure_time,
            "arrival_time": observation.arrival_time,
            "stops": observation.stops,
            "base_fare": observation.base_fare,
            "taxes": observation.taxes,
            "user_development_fee": observation.user_development_fee,
            "convenience_fee": observation.convenience_fee,
            "other_fees": observation.other_fees,
            "currency": observation.currency,
            "availability": observation.availability.value,
            "scraper_version": observation.scraper_version,
            "source_url": observation.source_url,
            "quality_status": observation.quality_status.value,
            "quality_score": observation.quality_score,
        }
        await self.session.execute(
            text(
                """
                INSERT INTO fare_observations (
                    id, source_id, collection_run_id, collected_at, origin, destination, travel_date,
                    carrier_code, flight_number, fare_class, fare_family, departure_time, arrival_time,
                    stops, base_fare, taxes, user_development_fee, convenience_fee, other_fees, currency,
                    availability, scraper_version, source_url, quality_status, quality_score
                ) VALUES (
                    :id, :source_id, :collection_run_id, :collected_at, :origin, :destination, :travel_date,
                    :carrier_code, :flight_number, :fare_class, :fare_family, :departure_time, :arrival_time,
                    :stops, :base_fare, :taxes, :user_development_fee, :convenience_fee, :other_fees, :currency,
                    :availability, :scraper_version, :source_url, :quality_status, :quality_score
                )
                """
            ),
            values,
        )
        return observation.observation_id

    async def count_for_route(self, origin: str, destination: str, travel_date: date) -> int:
        result = await self.session.execute(
            text(
                """
                SELECT COUNT(*) FROM fare_observations
                WHERE origin = :origin AND destination = :destination AND travel_date = :travel_date
                """
            ),
            {"origin": origin, "destination": destination, "travel_date": travel_date},
        )
        return int(result.scalar_one())
