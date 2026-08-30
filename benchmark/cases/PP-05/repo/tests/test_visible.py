from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_product_summary_is_returned() -> None:
    response = client.get("/products/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "desk lamp"}
