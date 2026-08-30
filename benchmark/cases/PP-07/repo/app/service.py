from .normalization import normalize_email
from .store import find_user, save_user


def create_user(name: str, email: str) -> dict:
    normalized = normalize_email(email)
    if find_user(normalized) is not None:
        raise ValueError("email already registered")
    user = {"name": name, "email": normalized}
    save_user(user)
    return user


def get_user_by_email(email: str) -> dict | None:
    return find_user(email)
