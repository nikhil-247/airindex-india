from fastapi.testclient import TestClient

from airindex.api.app import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_index_endpoint_returns_computed_index() -> None:
    response = client.get("/api/v1/demo/index")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "demo_replay"
    assert payload["national_index"] > 100
    assert set(payload["routes"]) == {"DEL-BOM", "DEL-BLR", "BOM-BLR"}


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
