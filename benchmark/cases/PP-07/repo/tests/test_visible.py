from fastapi.testclient import TestClient
from app.main import app
from app.store import reset_store

client = TestClient(app)


def setup_function() -> None:
    reset_store()


def test_create_and_exact_lookup() -> None:
    created = client.post("/users", json={"name": "Ari", "email": "ari@example.com"})
    found = client.get("/users/by-email", params={"email": "ari@example.com"})
    assert created.status_code == 201
    assert created.json() == {"name": "Ari", "email": "ari@example.com"}
    assert found.json() == created.json()
