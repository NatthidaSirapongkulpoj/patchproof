from app.main import app, reset_accounts


def setup_function() -> None:
    reset_accounts()


def test_valid_update_changes_account() -> None:
    response = app.test_client().patch("/accounts/1", json={"display_name": "Noor", "notifications": "weekly"})
    assert response.status_code == 200
    assert response.get_json() == {"account": {"id": 1, "display_name": "Noor", "notifications": "weekly"}}
