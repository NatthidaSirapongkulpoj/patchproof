from app.main import app


def test_existing_book_is_returned() -> None:
    response = app.test_client().get("/books/1")
    assert response.status_code == 200
    assert response.get_json() == {"book": {"id": 1, "title": "The Left Hand of Darkness"}}
