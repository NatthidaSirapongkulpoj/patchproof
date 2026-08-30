from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_default_listing_returns_all_items() -> None:
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json()["total"] == 6
    assert [item["id"] for item in response.json()["items"]] == [1, 2, 3, 4, 5, 6]
