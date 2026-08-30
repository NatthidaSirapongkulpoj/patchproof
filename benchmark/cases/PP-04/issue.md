# PP-04 - Reject invalid JSON requests

## Bug report

`POST /profiles` handles valid JSON, but missing, malformed, or non-object JSON is not consistently returned using the API's JSON error contract.

## Expected behavior

- missing, malformed, and non-object JSON return HTTP 400,
- invalid requests return `{"error": "invalid JSON body"}`,
- valid profile creation remains HTTP 201 with its existing response schema.

## Scope

Make the smallest correct fix. Do not modify tests, benchmark files, or evaluator files.
