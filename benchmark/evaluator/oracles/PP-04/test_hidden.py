from app.main import app


def assert_invalid(response) -> None:
    assert response.status_code == 400
    assert response.get_json() == {"error": "invalid JSON body"}


def test_missing_json_body_returns_contract_error() -> None:
    assert_invalid(app.test_client().post("/profiles"))


def test_malformed_json_returns_contract_error() -> None:
    assert_invalid(app.test_client().post("/profiles", data="{broken", content_type="application/json"))


def test_non_object_json_returns_contract_error() -> None:
    assert_invalid(app.test_client().post("/profiles", json=["Mina"]))


def test_valid_request_contract_is_unchanged() -> None:
    response = app.test_client().post("/profiles", json={"name": "Sol"})
    assert response.status_code == 201
    assert response.get_json() == {"profile": {"name": "Sol"}, "status": "created"}
