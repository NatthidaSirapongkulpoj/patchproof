from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_default_timeout_behavior(monkeypatch) -> None:
    monkeypatch.delenv("REQUEST_TIMEOUT", raising=False)
    response = client.get("/timeout-check", params={"elapsed": 4})
    assert response.status_code == 200
    assert response.json() == {"timeout": 5.0, "timed_out": False}
