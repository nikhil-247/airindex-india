from fastapi.testclient import TestClient

from airindex.api.app import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dashboard_route_returns_html() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "AirIndex India" in response.text


def test_demo_index_endpoint_returns_computed_index() -> None:
    response = client.get("/api/v1/demo/index")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "demo_replay"
    assert payload["national_index"] > 100
    assert set(payload["routes"]) == {"DEL-BOM", "DEL-BLR", "BOM-BLR"}


def test_demo_quality_endpoint_returns_audit() -> None:
    response = client.get("/api/v1/demo/quality")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "demo_replay_quality_audit"
    assert payload["source_count"] == 12
    assert payload["accepted_count"] == 9
    assert payload["rejected_count"] == 3
    assert payload["duplicate_count"] == 1
    assert payload["distinct_routes"] == 3


def test_demo_overview_combines_index_and_quality() -> None:
    response = client.get("/api/v1/demo/overview")
    assert response.status_code == 200
    payload = response.json()
    assert payload["index"]["status"] == "demo_replay"
    assert payload["quality"]["status"] == "demo_replay_quality_audit"


def test_ingest_endpoint_validates_n8n_payload_shape() -> None:
    response = client.post(
        "/api/v1/ingest/fare-observations",
        json={
            "observations": [
                {
                    "route": "DEL-BOM",
                    "observed_at": "2026-09-10T10:00:00Z",
                    "travel_date": "2026-10-10",
                    "carrier_code": "6E",
                    "total_fare": 5400,
                    "advance_days": 30,
                    "source": "demo-replay",
                }
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["observation_count"] == 1


def test_ingest_endpoint_rejects_invalid_route_and_non_positive_fare() -> None:
    response = client.post(
        "/api/v1/ingest/fare-observations",
        json={
            "observations": [
                {
                    "route": "BAD-1",
                    "observed_at": "2026-09-10T10:00:00Z",
                    "travel_date": "2026-10-10",
                    "carrier_code": "6E",
                    "total_fare": 0,
                    "advance_days": 30,
                    "source": "demo-replay",
                }
            ]
        },
    )
    assert response.status_code == 422
