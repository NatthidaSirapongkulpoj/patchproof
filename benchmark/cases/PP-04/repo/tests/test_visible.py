from app.main import app


def test_valid_json_creates_profile() -> None:
    response = app.test_client().post("/profiles", json={"name": "Mina"})
    assert response.status_code == 201
    assert response.get_json() == {"profile": {"name": "Mina"}, "status": "created"}
