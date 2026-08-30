from fastapi.testclient import TestClient
from app.main import app
from app.store import reset_store

client = TestClient(app)


def setup_function() -> None:
    reset_store()


def test_lookup_normalizes_case_and_whitespace() -> None:
    client.post("/users", json={"name": "Ari", "email": " Ari@Example.COM "})
    response = client.get("/users/by-email", params={"email": "  ARI@example.com "})
    assert response.status_code == 200
    assert response.json() == {"name": "Ari", "email": "ari@example.com"}


def test_normalized_duplicate_is_rejected() -> None:
    client.post("/users", json={"name": "Ari", "email": "ari@example.com"})
    response = client.post("/users", json={"name": "Other", "email": " ARI@EXAMPLE.COM "})
    assert response.status_code == 409
    assert response.json() == {"detail": "email already registered"}


def test_success_contract_remains_201_and_normalized() -> None:
    response = client.post("/users", json={"name": "Bea", "email": " Bea@Example.com "})
    assert response.status_code == 201
    assert response.json() == {"name": "Bea", "email": "bea@example.com"}


def test_unknown_email_remains_404() -> None:
    assert client.get("/users/by-email", params={"email": "missing@example.com"}).status_code == 404
