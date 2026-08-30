from app.main import app


def test_missing_book_returns_404() -> None:
    response = app.test_client().get("/books/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "book not found"}


def test_existing_book_contract_is_unchanged() -> None:
    response = app.test_client().get("/books/2")
    assert response.status_code == 200
    assert response.get_json() == {"book": {"id": 2, "title": "Kindred"}}


def test_non_integer_path_keeps_framework_404() -> None:
    assert app.test_client().get("/books/not-an-id").status_code == 404
