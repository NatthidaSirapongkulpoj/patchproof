# PP-02 - Fix explicit pagination boundaries

## Bug report

`GET /items` returns the full collection correctly when pagination is omitted, but explicit `offset` and `limit` pagination skips the item at the requested offset.

## Expected behavior

- omitted pagination should keep returning the full collection,
- `offset=0` should begin with the first item,
- later offsets should begin at exactly the requested zero-based position,
- adjacent pages must not omit or duplicate items.

## Scope

Make the smallest correct fix. Do not modify tests, benchmark files, or evaluator files.
