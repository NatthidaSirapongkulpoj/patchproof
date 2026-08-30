import pytest
from fastapi.testclient import TestClient
from app.config import get_request_timeout
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_environment_timeout_has_numeric_semantics(monkeypatch) -> None:
    monkeypatch.setenv("REQUEST_TIMEOUT", "2.5")
    response = client.get("/timeout-check", params={"elapsed": 3})
    assert response.status_code == 200
    assert response.json() == {"timeout": 2.5, "timed_out": True}


def test_default_timeout_still_works(monkeypatch) -> None:
    monkeypatch.delenv("REQUEST_TIMEOUT", raising=False)
    assert get_request_timeout() == 5.0
    response = client.get("/timeout-check", params={"elapsed": 5})
    assert response.status_code == 200
    assert response.json() == {"timeout": 5.0, "timed_out": False}


def test_fractional_value_is_preserved(monkeypatch) -> None:
    monkeypatch.setenv("REQUEST_TIMEOUT", "0.25")
    assert get_request_timeout() == pytest.approx(0.25)


def test_invalid_configuration_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("REQUEST_TIMEOUT", "soon")
    with pytest.raises(ValueError):
        get_request_timeout()
