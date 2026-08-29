# PP-01 — Reject non-positive order quantity

## Bug report

The `POST /orders` endpoint currently accepts a quantity of `0` or a negative quantity and returns `201 Created`.

The API contract requires any order quantity less than `1` to be rejected with HTTP `422`.

## Expected behavior

- `quantity = 1` or greater should create the order normally.
- `quantity = 0` should return HTTP `422`.
- negative quantity should return HTTP `422`.
- the successful response schema must remain unchanged.

## Scope

Make the smallest correct fix.

Do not modify benchmark or evaluator files.
