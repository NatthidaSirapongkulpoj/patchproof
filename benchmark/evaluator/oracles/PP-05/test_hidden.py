from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_detailed_product_resolves_async_availability() -> None:
    response = client.get("/products/1", params={"include_availability": "true"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "desk lamp", "available": True}


def test_out_of_stock_product_resolves_false() -> None:
    response = client.get("/products/2", params={"include_availability": "true"})
    assert response.status_code == 200
    assert response.json()["available"] is False


def test_summary_contract_is_unchanged() -> None:
    response = client.get("/products/2")
    assert response.status_code == 200
    assert response.json() == {"id": 2, "name": "wall clock"}


def test_missing_product_remains_404() -> None:
    response = client.get("/products/999", params={"include_availability": "true"})
    assert response.status_code == 404
    assert response.json() == {"detail": "product not found"}
