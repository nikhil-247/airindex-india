"""FastAPI surface for the AirIndex demonstration and deployment prototype."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from airindex.analytics.index_engine import (
    IndexCalculationError,
    aggregate_route_indices,
    calculate_jevons_index,
)
from airindex.analytics.quality_engine import QualityEngineError, assess_observations

ROOT = Path(__file__).resolve().parents[3]
DEMO_PATH = ROOT / "data" / "demo" / "index_demo.json"
REPLAY_PATH = ROOT / "data" / "demo" / "replay_source.json"
PORTAL_ROOT = ROOT / "portal"
STATIC_PATH = ROOT / "static"

app = FastAPI(title="AirIndex India API", version="0.5.0")

if STATIC_PATH.exists():
    app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")


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


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise HTTPException(status_code=500, detail=f"Missing demo asset: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid JSON asset: {path.name}") from exc


def _calculate_demo() -> dict[str, Any]:
    payload = _read_json(DEMO_PATH)
    route_indices: dict[str, Decimal] = {}
    route_details: dict[str, dict[str, Any]] = {}

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
            "change_percent": round(float(result.value) - 100.0, 4),
            "weighted_contribution": round(
                (float(result.value) - 100.0) * float(route["weight"]),
                4,
            ),
            "observation_count": result.observation_count,
            "weight": route["weight"],
            "reference_prices": route["reference"],
            "current_prices": route["current"],
        }

    weights = {
        route["route"]: Decimal(str(route["weight"]))
        for route in payload["routes"]
    }
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
        "note": (
            "Demonstration replay data only; not live market data "
            "or an official CPI measure."
        ),
    }


def _page(name: str) -> FileResponse:
    filename = "home.html" if not name else f"{name}.html"
    path = PORTAL_ROOT / filename
    if not path.exists():
        raise HTTPException(status_code=500, detail=f"Portal page is missing: {filename}")
    return FileResponse(path)


@app.get("/", include_in_schema=False)
def homepage() -> FileResponse:
    return _page("home")


@app.get("/dashboard", include_in_schema=False)
def dashboard() -> FileResponse:
    return _page("dashboard")


@app.get("/routes", include_in_schema=False)
def routes_page() -> FileResponse:
    return _page("routes")


@app.get("/airlines", include_in_schema=False)
def airlines_page() -> FileResponse:
    return _page("airlines")


@app.get("/airports", include_in_schema=False)
def airports_page() -> FileResponse:
    return _page("airports")


@app.get("/quality", include_in_schema=False)
def quality_page() -> FileResponse:
    return _page("quality")


@app.get("/methodology", include_in_schema=False)
def methodology_page() -> FileResponse:
    return _page("methodology")


@app.get("/catalogue", include_in_schema=False)
def catalogue_page() -> FileResponse:
    return _page("catalogue")


@app.get("/releases", include_in_schema=False)
def releases_page() -> FileResponse:
    return _page("releases")


@app.get("/api", include_in_schema=False)
def api_portal_page() -> FileResponse:
    return _page("api")


@app.get("/about", include_in_schema=False)
def about_page() -> FileResponse:
    return _page("about")


@app.get("/explorer", include_in_schema=False)
def explorer_legacy() -> FileResponse:
    return _page("routes")


@app.get("/pipeline", include_in_schema=False)
def pipeline_legacy() -> FileResponse:
    return _page("api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/demo/portal")
def demo_portal() -> dict[str, Any]:
    return _read_json(ROOT / "data" / "demo" / "portal_demo.json")


@app.get("/api/v1/demo/index")
def demo_index() -> dict[str, Any]:
    return _calculate_demo()


@app.get("/api/v1/demo/quality")
def demo_quality() -> dict[str, Any]:
    payload = _read_json(REPLAY_PATH)
    try:
        assessment = assess_observations(payload["observations"])
    except QualityEngineError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "status": "demo_replay_quality_audit",
        "source": payload.get("source", "unknown"),
        "currency": payload.get("currency", "INR"),
        "source_count": assessment.source_count,
        "accepted_count": len(assessment.accepted),
        "rejected_count": len(assessment.rejected),
        "duplicate_count": assessment.duplicate_count,
        "anomaly_count": assessment.anomaly_count,
        "anomaly_rate_pct": assessment.anomaly_rate_pct,
        "quality_avg": assessment.quality_avg,
        "distinct_routes": assessment.distinct_routes,
        "lead_time_windows": assessment.window_counts,
        "rejected_examples": assessment.rejected[:10],
        "anomaly_examples": [
            row
            for row in assessment.accepted
            if row["anomaly_flag"]
        ][:10],
        "note": (
            "Deterministic replay audit for prototype demonstration. "
            "No claim of live-market completeness is made."
        ),
    }


@app.get("/api/v1/demo/overview")
def demo_overview() -> dict[str, Any]:
    return {"index": _calculate_demo(), "quality": demo_quality()}


@app.post("/api/v1/ingest/fare-observations")
def ingest_fare_observations(request: IngestRequest) -> dict[str, int | str]:
    """Validate an n8n-compatible observation batch without claiming persistence."""
    return {
        "status": "accepted_for_demo_pipeline",
        "observation_count": len(request.observations),
    }
