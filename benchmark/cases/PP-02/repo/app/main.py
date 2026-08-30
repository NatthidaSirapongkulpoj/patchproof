from fastapi import FastAPI, Query

app = FastAPI()

ITEMS = [
    {"id": 1, "name": "alpha"}, {"id": 2, "name": "bravo"},
    {"id": 3, "name": "charlie"}, {"id": 4, "name": "delta"},
    {"id": 5, "name": "echo"}, {"id": 6, "name": "foxtrot"},
]


@app.get("/items")
def list_items(offset: int | None = Query(default=None, ge=0), limit: int | None = Query(default=None, ge=1)) -> dict:
    if offset is None and limit is None:
        selected = ITEMS
    else:
        start = (offset or 0) + 1
        selected = ITEMS[start : start + (limit or len(ITEMS))]
    return {"items": selected, "total": len(ITEMS)}
