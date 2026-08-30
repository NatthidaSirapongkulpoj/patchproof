# PP-07 - Normalize email identity consistently

## Bug report

User creation normalizes an email before storing it, but lookup uses the raw query value. The same email therefore cannot always be found when casing or surrounding whitespace differs.

## Expected behavior

- email identity is case-insensitive and ignores surrounding whitespace at every boundary,
- a normalized duplicate is rejected with HTTP 409,
- successful creation keeps its HTTP 201 response contract.

## Scope

Make the smallest correct fix across the relevant production files. Do not modify tests, benchmark files, or evaluator files.
