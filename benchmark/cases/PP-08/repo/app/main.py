from flask import Flask, jsonify, request

app = Flask(__name__)
CATALOG = ["red apple", "green apple", "banana", "blueberry"]
CACHE: dict[str, dict] = {}


def reset_cache() -> None:
    CACHE.clear()


@app.get("/search")
def search():
    key = request.path
    if key not in CACHE:
        query = request.args.get("q", "").strip().lower()
        CACHE[key] = {"query": query, "results": [item for item in CATALOG if query in item]}
    return jsonify(CACHE[key])
