# DB Unit Tests

## Scope

This directory contains unit-scope tests for `be/src/external/db/client.py`.
The tests isolate `MySQLClient` from real infrastructure by replacing the DB
connector with in-memory test doubles.

## Files

- `test_client.py`: unit tests for construction, connection kwargs, transaction
  handling, cleanup behavior, and health summary responses

## What Is Verified

- `MySQLClient.from_config()` preserves the provided `DatabaseSettings`
- `connect()` forwards the expected connection kwargs to the connector
- successful context-manager usage commits and closes the connection
- failing context-manager usage rolls back and closes the connection
- `health_summary()` reports `available` and `unavailable` correctly

## How To Run

```bash
cd be
uv run pytest tests/unit/external/db/test_client.py
```

You can also run the whole DB unit scope with:

```bash
cd be
uv run pytest -m unit tests/unit/external/db
```

## Notes

- no Docker container is required
- no live MySQL server is required
- each test gets fresh fixtures so connector and connection state do not leak
