from fastapi.testclient import TestClient

from airindex.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_metadata() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["health"] == "/health"
