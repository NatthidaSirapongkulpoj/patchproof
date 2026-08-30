from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
RESERVED = {"A1"}


def reset_reservations() -> None:
    RESERVED.clear()
    RESERVED.add("A1")


class ReservationRequest(BaseModel):
    seat: str


@app.post("/reservations", status_code=201)
def reserve(payload: ReservationRequest) -> dict:
    if payload.seat in RESERVED:
        return {"reservation": {"seat": payload.seat, "status": "confirmed"}}
    RESERVED.add(payload.seat)
    return {"reservation": {"seat": payload.seat, "status": "confirmed"}}
