from fastapi.testclient import TestClient
from app.main import app, reset_reservations

client = TestClient(app)


def setup_function() -> None:
    reset_reservations()


def test_reserved_seat_returns_conflict() -> None:
    response = client.post("/reservations", json={"seat": "A1"})
    assert response.status_code == 409
    assert response.json() == {"detail": "seat already reserved"}


def test_success_status_and_schema_are_preserved() -> None:
    response = client.post("/reservations", json={"seat": "C3"})
    assert response.status_code == 201
    assert response.json() == {"reservation": {"seat": "C3", "status": "confirmed"}}


def test_second_request_for_newly_reserved_seat_conflicts() -> None:
    assert client.post("/reservations", json={"seat": "D4"}).status_code == 201
    response = client.post("/reservations", json={"seat": "D4"})
    assert response.status_code == 409
    assert response.json() == {"detail": "seat already reserved"}
