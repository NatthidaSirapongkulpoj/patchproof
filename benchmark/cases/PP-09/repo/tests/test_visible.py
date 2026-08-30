from fastapi.testclient import TestClient
from app.main import app, reset_reservations

client = TestClient(app)


def setup_function() -> None:
    reset_reservations()


def test_new_reservation_is_created() -> None:
    response = client.post("/reservations", json={"seat": "B2"})
    assert response.status_code == 201
    assert response.json() == {"reservation": {"seat": "B2", "status": "confirmed"}}
