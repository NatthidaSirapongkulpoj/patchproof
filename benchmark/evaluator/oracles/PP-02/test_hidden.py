from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_first_explicit_page_starts_at_first_item() -> None:
    response = client.get("/items", params={"offset": 0, "limit": 2})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [1, 2]


def test_later_offset_is_zero_based() -> None:
    response = client.get("/items", params={"offset": 4, "limit": 2})
    assert [item["id"] for item in response.json()["items"]] == [5, 6]


def test_adjacent_pages_have_no_gap_or_overlap() -> None:
    first = client.get("/items", params={"offset": 0, "limit": 3}).json()["items"]
    second = client.get("/items", params={"offset": 3, "limit": 3}).json()["items"]
    assert [item["id"] for item in first + second] == [1, 2, 3, 4, 5, 6]


def test_default_contract_is_unchanged() -> None:
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json()["total"] == 6
