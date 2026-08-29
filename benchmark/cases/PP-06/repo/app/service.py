from .errors import NotFoundError


USERS = {
    1: {
        "id": 1,
        "name": "Ada",
    },
    2: {
        "id": 2,
        "name": "Grace",
    },
}


def get_user(user_id: int) -> dict:
    if user_id == 999:
        raise RuntimeError("database unavailable")

    try:
        return USERS[user_id]
    except KeyError as exc:
        raise NotFoundError("user not found") from exc
