from fastapi.testclient import TestClient

from app.main import app
from app.store import list_jobs, reset_store


client = TestClient(app)


def setup_function() -> None:
    reset_store()


def test_retry_after_timeout_does_not_duplicate_job() -> None:
    first = client.post(
        "/jobs",
        headers={
            "Idempotency-Key": "retry-key",
        },
        json={
            "name": "nightly-report",
            "simulate_timeout": True,
        },
    )

    assert first.status_code == 504
    assert len(list_jobs()) == 1

    retry = client.post(
        "/jobs",
        headers={
            "Idempotency-Key": "retry-key",
        },
        json={
            "name": "nightly-report",
        },
    )

    assert retry.status_code == 201

    assert retry.json() == {
        "id": 1,
        "name": "nightly-report",
    }

    assert len(list_jobs()) == 1


def test_same_key_returns_original_job() -> None:
    first = client.post(
        "/jobs",
        headers={
            "Idempotency-Key": "same-key",
        },
        json={
            "name": "export",
        },
    )

    second = client.post(
        "/jobs",
        headers={
            "Idempotency-Key": "same-key",
        },
        json={
            "name": "export",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert second.json() == first.json()
    assert len(list_jobs()) == 1


def test_different_keys_create_different_jobs() -> None:
    first = client.post(
        "/jobs",
        headers={
            "Idempotency-Key": "key-a",
        },
        json={
            "name": "sync-a",
        },
    )

    second = client.post(
        "/jobs",
        headers={
            "Idempotency-Key": "key-b",
        },
        json={
            "name": "sync-b",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json()["id"] != second.json()["id"]
    assert len(list_jobs()) == 2
