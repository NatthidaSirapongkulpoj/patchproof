from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .service import submit_job


app = FastAPI()


class JobRequest(BaseModel):
    name: str
    simulate_timeout: bool = False


@app.post("/jobs", status_code=201)
def create_job_endpoint(
    payload: JobRequest,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> dict:
    try:
        return submit_job(
            name=payload.name,
            idempotency_key=idempotency_key,
            simulate_timeout=payload.simulate_timeout,
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail=str(exc),
        ) from exc
