# PP-05 - Await the asynchronous availability service

## Bug report

The detailed `GET /products/{product_id}` path calls the asynchronous inventory service without awaiting it, causing a server error when availability is requested.

## Expected behavior

- detailed requests return the resolved boolean availability value,
- the normal summary response remains unchanged,
- missing products continue to return HTTP 404.

## Scope

Make the smallest correct fix. Do not modify tests, benchmark files, or evaluator files.
