from __future__ import annotations


JOBS: list[dict] = []
NEXT_ID = 1


def reset_store() -> None:
    global NEXT_ID

    JOBS.clear()
    NEXT_ID = 1


def create_job(name: str) -> dict:
    global NEXT_ID

    job = {
        "id": NEXT_ID,
        "name": name,
    }

    NEXT_ID += 1
    JOBS.append(job)

    return job


def list_jobs() -> list[dict]:
    return list(JOBS)
