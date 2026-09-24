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
    assert payload["data_mode"] == "DEMO DATASET"
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
    assert any("MoSPI" in row["name"] for row in payload["source_registry"])
