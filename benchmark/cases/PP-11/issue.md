# PP-11 - Make failed updates atomic

## Bug report

`PATCH /accounts/{account_id}` writes the submitted display name before validating the notification setting. An invalid request returns HTTP 400 but leaves the stored account partially changed.

## Expected behavior

- validation failure returns HTTP 400 without changing any stored field,
- a valid update changes all requested fields,
- missing accounts remain HTTP 404,
- successful response JSON remains unchanged.

## Scope

Make the smallest correct fix. Do not modify tests, benchmark files, or evaluator files.
