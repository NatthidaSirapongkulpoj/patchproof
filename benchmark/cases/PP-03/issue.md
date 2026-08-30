# PP-03 - Return 404 for a missing resource

## Bug report

`GET /books/{book_id}` returns HTTP 200 with a null resource when the requested book does not exist.

## Expected behavior

- existing books keep returning HTTP 200 with the same JSON contract,
- a missing book returns HTTP 404,
- the error body contains `{"error": "book not found"}`.

## Scope

Make the smallest correct fix. Do not modify tests, benchmark files, or evaluator files.
