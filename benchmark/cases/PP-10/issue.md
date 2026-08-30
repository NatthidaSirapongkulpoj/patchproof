# PP-10 - Parse the configured timeout as a number

## Bug report

The request timeout is read from `REQUEST_TIMEOUT` as text. Code that compares elapsed numeric time against an environment-configured timeout therefore fails at runtime.

## Expected behavior

- numeric environment text is interpreted as a floating-point number,
- elapsed time above the configured timeout reports timed out,
- the default remains 5 seconds when the variable is absent,
- invalid configuration does not silently produce misleading behavior.

## Scope

Make the smallest correct fix. Do not modify tests, benchmark files, or evaluator files.
