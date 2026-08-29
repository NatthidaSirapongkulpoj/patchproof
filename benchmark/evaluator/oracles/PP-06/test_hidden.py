from fastapi.testclient import TestClient

from app.main import app


client = TestClient(
    app,
    raise_server_exceptions=False,
)


def test_missing_user_returns_404() -> None:
    response = client.get("/users/12345")

    assert response.status_code == 404

    assert response.json() == {
        "detail": "user not found",
    }


def test_existing_user_still_returns_200() -> None:
    response = client.get("/users/2")

    assert response.status_code == 200

    assert response.json() == {
        "id": 2,
        "name": "Grace",
    }


def test_unexpected_exception_is_not_mapped_to_404() -> None:
    response = client.get("/users/999")

    assert response.status_code == 500
