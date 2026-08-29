# PP-06 - Map domain NotFoundError to HTTP 404

## Bug report

`GET /users/{user_id}` currently allows the domain-level
`NotFoundError` to escape from the service layer.

As a result, a request for a missing user becomes an internal
server error instead of the API's documented `404 Not Found`.

## Expected behavior

- an existing user should still return HTTP 200,
- a missing user should return HTTP 404,
- the error response should contain `"detail": "user not found"`,
- unrelated unexpected exceptions must not be converted into 404 responses.

## Scope

Make the smallest correct fix.

Do not modify tests, benchmark files, or evaluator files.
