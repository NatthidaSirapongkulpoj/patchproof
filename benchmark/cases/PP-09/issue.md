# PP-09 - Return a conflict without changing creation responses

## Bug report

`POST /reservations` reports an already reserved seat as a successful creation. The API contract requires a conflict response for that failing case.

## Expected behavior

- an already reserved seat returns HTTP 409 with `{"detail": "seat already reserved"}`,
- a new reservation remains HTTP 201,
- successful response JSON remains `{"reservation": {"seat": ..., "status": "confirmed"}}`.

## Scope

Make the smallest correct fix. Preserve the successful status and response contract. Do not modify tests, benchmark files, or evaluator files.
