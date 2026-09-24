from fastapi.testclient import TestClient

from airindex.api.app import app

client = TestClient(app)


def test_public_portal_pages_are_available() -> None:
    paths = [
        "/",
        "/dashboard",
        "/routes",
        "/compare",
        "/airlines",
        "/intelligence",
        "/sources",
        "/airports",
        "/quality",
        "/methodology",
        "/catalogue",
        "/releases",
        "/api",
        "/about",
    ]

    for path in paths:
        response = client.get(path)
        assert response.status_code == 200
        assert "AirIndex India" in response.text
        assert "portal.css" in response.text


def test_rich_portal_demo_dataset_is_available() -> None:
    response = client.get("/api/v1/demo/portal")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "demo_replay"
    assert payload["data_mode"] == "DEMO DATABASE"
    assert payload["storage_mode"] == "SQLite demo backend"
    assert payload["observation_count"] >= 18000
    assert len(payload["daily_series"]) == 30
    assert len(payload["routes"]) == 12
    assert len(payload["airlines"]) == 7
    assert len(payload["airports"]) == 10
    assert len(payload["lead_time"]) == 5
    assert len(payload["source_registry"]) >= 4
    assert len(payload["catalogue"]) >= 6
    assert payload["national_index"] > 100
    assert len(payload["market_pulse"]) >= 5
    assert len(payload["fare_distribution"]) >= 5
    assert len(payload["volatility"]) >= 5
    assert len(payload["alerts"]) >= 4
    assert payload["rejected_count"] >= 40
    assert payload["anomaly_count"] >= 300
    assert any("MoSPI" in row["name"] for row in payload["source_registry"])


def test_dynamic_stats_endpoints_are_database_backed() -> None:
    assert client.get("/api/v1/stats/summary").status_code == 200
    assert client.get("/api/v1/stats/routes").json()
    assert client.get("/api/v1/stats/airlines").json()
    assert client.get("/api/v1/stats/airports").json()
    assert client.get("/api/v1/stats/sources").json()
    assert client.get("/api/v1/stats/releases").json()
    assert client.get("/api/v1/stats/alerts").json()
    assert len(client.get("/api/v1/stats/observations?limit=5").json()) == 5


def test_ingest_persists_demo_observation() -> None:
    before_payload = client.get("/api/v1/stats/summary").json()
    before = before_payload["observation_count"]
    before_index = before_payload["national_index"]
    response = client.post(
        "/api/v1/ingest/fare-observations",
        json={
            "observations": [
                {
                    "route": "DEL-BOM",
                    "observed_at": "2026-09-25T10:00:00Z",
                    "travel_date": "2026-10-25",
                    "carrier_code": "6E",
                    "total_fare": 15000,
                    "advance_days": 30,
                    "source": "test-browser",
                }
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["persisted_count"] == 1
    after = client.get("/api/v1/stats/summary").json()["observation_count"]
    assert after == before + 1
    after_index = client.get("/api/v1/stats/summary").json()["national_index"]
    assert after_index > before_index


def test_quality_filters_return_real_backend_rows() -> None:
    rejected = client.get(
        "/api/v1/stats/observations?status=rejected&limit=5"
    )
    assert rejected.status_code == 200
    assert rejected.json()
    assert all(row["quality_status"] == "rejected" for row in rejected.json())

    anomalies = client.get(
        "/api/v1/stats/observations?anomaly=true&limit=5"
    )
    assert anomalies.status_code == 200
    assert anomalies.json()
    assert all(row["anomaly_flag"] == 1 for row in anomalies.json())
