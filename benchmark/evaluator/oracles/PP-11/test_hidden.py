from app.main import app, reset_accounts


def setup_function() -> None:
    reset_accounts()


def test_invalid_update_does_not_partially_mutate_account() -> None:
    client = app.test_client()
    response = client.patch("/accounts/1", json={"display_name": "Changed", "notifications": "hourly"})
    assert response.status_code == 400
    assert response.get_json() == {"error": "invalid notification frequency"}
    assert client.get("/accounts/1").get_json() == {"account": {"id": 1, "display_name": "Nora", "notifications": "daily"}}


def test_valid_update_changes_all_fields() -> None:
    response = app.test_client().patch("/accounts/1", json={"display_name": "Noor", "notifications": "never"})
    assert response.status_code == 200
    assert response.get_json() == {"account": {"id": 1, "display_name": "Noor", "notifications": "never"}}


def test_single_field_update_keeps_other_field() -> None:
    response = app.test_client().patch("/accounts/1", json={"display_name": "Nori"})
    assert response.status_code == 200
    assert response.get_json() == {"account": {"id": 1, "display_name": "Nori", "notifications": "daily"}}


def test_missing_account_remains_404() -> None:
    response = app.test_client().patch("/accounts/999", json={"display_name": "Nobody"})
    assert response.status_code == 404
    assert response.get_json() == {"error": "account not found"}
