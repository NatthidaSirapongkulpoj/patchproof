from app.main import app, reset_cache


def setup_function() -> None:
    reset_cache()


def test_single_search_returns_matches() -> None:
    response = app.test_client().get("/search", query_string={"q": "apple"})
    assert response.status_code == 200
    assert response.get_json() == {"query": "apple", "results": ["red apple", "green apple"]}
