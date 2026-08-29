# PP-12 - Prevent duplicate job creation after retry

## Bug report

`POST /jobs` accepts an `Idempotency-Key` header.

When the first request persists a job but the response is interrupted,
a client may retry the same request with the same key.

The current implementation can create a second job during that retry.

## Expected behavior

- a normal request creates one job,
- retrying with the same `Idempotency-Key` must return the original job,
- the same key must never create a duplicate stored job,
- a different key must create a different job,
- normal requests must continue to work.

## Scope

Make the smallest correct fix.

Do not modify tests, benchmark files, or evaluator files.
