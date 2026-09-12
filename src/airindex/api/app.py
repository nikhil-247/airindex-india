"""FastAPI surface for the AirIndex demonstration prototype."""

import json
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from airindex.analytics.index_engine import (
    IndexCalculationError,
    aggregate_route_indices,
    calculate_jevons_index,
)

ROOT = Path(__file__).resolve().parents[3]
DEMO_PATH = ROOT / "data" / "demo" / "index_demo.json"
DASHBOARD_PATH = ROOT / "demo" / "index-dashboard.html"

app = FastAPI(title="AirIndex India API", version="0.3.0")


class FareObservationPayload(BaseModel):
    route: str = Field(pattern=r"^[A-Z]{3}-[A-Z]{3}$")
    observed_at: str
    travel_date: str
    carrier_code: str = Field(min_length=2, max_length=3)
    total_fare: Decimal = Field(gt=Decimal("0"))
    advance_days: int = Field(ge=1, le=365)
    source: str = Field(min_length=1, max_length=120)


class IngestRequest(BaseModel):
    observations: list[FareObservationPayload] = Field(min_length=1, max_length=500)


def _load_demo() -> dict:
    if not DEMO_PATH.exists():
        raise HTTPException(status_code=500, detail="Demo dataset is missing")
    return json.loads(DEMO_PATH.read_text(encoding="utf-8"))


def _calculate_demo() -> dict:
    payload = _load_demo()
    route_indices: dict[str, Decimal] = {}
    route_details: dict[str, dict] = {}

    for route in payload["routes"]:
        reference = {key: Decimal(str(value)) for key, value in route["reference"].items()}
        current = {key: Decimal(str(value)) for key, value in route["current"].items()}
        try:
            result = calculate_jevons_index(reference, current, minimum_observations=3)
        except IndexCalculationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        route_indices[route["route"]] = result.value
        route_details[route["route"]] = {
            "index": float(result.value),
            "observation_count": result.observation_count,
            "weight": route["weight"],
            "reference_prices": route["reference"],
            "current_prices": route["current"],
        }

    weights = {route["route"]: Decimal(str(route["weight"])) for route in payload["routes"]}
    try:
        national_index = aggregate_route_indices(route_indices, weights)
    except IndexCalculationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "status": "demo_replay",
        "methodology_version": payload["methodology_version"],
        "base_level": payload["base_level"],
        "national_index": float(national_index),
        "change_percent": round(float(national_index) - 100.0, 4),
        "routes": route_details,
        "lead_time_windows": [1, 7, 15, 30, 45],
        "note": "Demonstration replay data only; not live market data or an official CPI measure.",
    }


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    if not DASHBOARD_PATH.exists():
        raise HTTPException(status_code=500, detail="Dashboard file is missing")
    return FileResponse(DASHBOARD_PATH)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/demo/index")
def demo_index() -> dict:
    return _calculate_demo()


@app.post("/api/v1/ingest/fare-observations")
def ingest_fare_observations(request: IngestRequest) -> dict[str, int | str]:
    """Validate an n8n-compatible observation batch without claiming persistence."""
    return {
        "status": "accepted_for_demo_pipeline",
        "observation_count": len(request.observations),
    }
