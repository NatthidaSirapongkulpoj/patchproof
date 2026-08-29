from fastapi import FastAPI

from .service import get_user


app = FastAPI()


@app.get("/users/{user_id}")
def read_user(user_id: int) -> dict:
    return get_user(user_id)
