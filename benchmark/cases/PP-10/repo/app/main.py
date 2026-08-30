from fastapi import FastAPI, Query
from .config import get_request_timeout

app = FastAPI()


@app.get("/timeout-check")
def timeout_check(elapsed: float = Query(ge=0)) -> dict:
    timeout = get_request_timeout()
    return {"timeout": timeout, "timed_out": elapsed > timeout}
