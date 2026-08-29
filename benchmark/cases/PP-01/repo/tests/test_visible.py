from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_valid_order_is_created() -> None:
    response = client.post(
        "/orders",
        json={
            "item": "keyboard",
            "quantity": 2,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "item": "keyboard",
        "quantity": 2,
        "status": "created",
    }
