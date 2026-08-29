from __future__ import annotations

from .store import create_job


def submit_job(
    name: str,
    idempotency_key: str,
    simulate_timeout: bool = False,
) -> dict:
    job = create_job(name)

    if simulate_timeout:
        raise TimeoutError("response interrupted after persistence")

    return job
