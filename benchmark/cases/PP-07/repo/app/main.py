from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from .service import create_user, get_user_by_email

app = FastAPI()


class UserRequest(BaseModel):
    name: str
    email: str


@app.post("/users", status_code=201)
def post_user(payload: UserRequest) -> dict:
    try:
        return create_user(payload.name, payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/users/by-email")
def read_user(email: str = Query()) -> dict:
    user = get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return user
