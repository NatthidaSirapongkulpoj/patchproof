from fastapi.testclient import TestClient

from app.main import app
from app.store import reset_store


client = TestClient(app)


def setup_function() -> None:
    reset_store()


def test_normal_job_creation() -> None:
    response = client.post(
        "/jobs",
        headers={
            "Idempotency-Key": "key-normal",
        },
        json={
            "name": "reindex",
        },
    )

    assert response.status_code == 201

    assert response.json() == {
        "id": 1,
        "name": "reindex",
    }
