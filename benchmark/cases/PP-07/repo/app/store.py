USERS: dict[str, dict] = {}


def reset_store() -> None:
    USERS.clear()


def save_user(user: dict) -> None:
    USERS[user["email"]] = user


def find_user(email: str) -> dict | None:
    return USERS.get(email)
