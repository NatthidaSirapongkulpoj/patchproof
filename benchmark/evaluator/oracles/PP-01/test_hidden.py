from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_zero_quantity_is_rejected() -> None:
    response = client.post(
        "/orders",
        json={
            "item": "keyboard",
            "quantity": 0,
        },
    )

    assert response.status_code == 422


def test_negative_quantity_is_rejected() -> None:
    response = client.post(
        "/orders",
        json={
            "item": "keyboard",
            "quantity": -3,
        },
    )

    assert response.status_code == 422


def test_valid_quantity_still_works() -> None:
    response = client.post(
        "/orders",
        json={
            "item": "keyboard",
            "quantity": 1,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "item": "keyboard",
        "quantity": 1,
        "status": "created",
    }
