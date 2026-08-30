import os


def get_request_timeout():
    return os.getenv("REQUEST_TIMEOUT", 5.0)
