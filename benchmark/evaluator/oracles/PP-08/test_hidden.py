from app.main import app, reset_cache


def setup_function() -> None:
    reset_cache()


def test_different_queries_do_not_collide_in_cache() -> None:
    client = app.test_client()
    first = client.get("/search", query_string={"q": "apple"})
    second = client.get("/search", query_string={"q": "berry"})
    assert first.get_json()["results"] == ["red apple", "green apple"]
    assert second.get_json() == {"query": "berry", "results": ["blueberry"]}


def test_repeated_query_is_stable() -> None:
    client = app.test_client()
    assert client.get("/search", query_string={"q": "banana"}).get_json() == client.get("/search", query_string={"q": "banana"}).get_json()


def test_empty_query_keeps_response_contract() -> None:
    response = app.test_client().get("/search")
    assert response.status_code == 200
    assert response.get_json() == {"query": "", "results": ["red apple", "green apple", "banana", "blueberry"]}
