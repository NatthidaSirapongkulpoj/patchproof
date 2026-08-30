# PP-08 - Include query parameters in the search cache key

## Bug report

`GET /search?q=...` caches by request path only. Sequential searches with different `q` values can return the first query's cached result.

## Expected behavior

- different query values produce their own correct results,
- repeating the same query remains stable,
- the response schema remains unchanged.

## Scope

Make the smallest correct fix. Do not modify tests, benchmark files, or evaluator files.
