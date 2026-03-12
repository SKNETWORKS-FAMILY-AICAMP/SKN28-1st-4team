# DB Integration Tests

## Scope

This directory contains integration-scope tests for the external DB boundary.
Unlike the unit tests, these tests exercise `MySQLClient` against a real MySQL
container so connection setup, transaction handling, and query execution are
verified end to end.

## Files

- `conftest.py`: shared integration fixtures and live test DB settings
- `test_client_connection.py`: connectivity test against the seeded MySQL
  container
- `test_client_queries.py`: context-managed write/read/delete query execution
  test against the live MySQL container
- `docker-compose.yml`: Compose override for the DB integration environment
- `docker/test-db/Dockerfile`: custom MySQL test image definition
- `docker/test-db/initdb/01-create-test-schema.sql`: schema and seed data for
  the connectivity check

## What Is Verified

- the Docker-backed MySQL test container becomes reachable
- `MySQLClient.connect()` can open a real connection
- a real query can read the seeded `connectivity_check` row
- a real transaction can insert, select, and delete rows through the context
  manager

## How To Start The Test DB

Run this from the repository root:

```bash
docker compose -f docker-compose.yml -f be/tests/integration/external/db/docker-compose.yml up -d --build test_db_docker
```

## How To Run

```bash
cd be
RUN_DOCKER_DB_TESTS=1 TEST_DB_HOST=127.0.0.1 TEST_DB_PORT=3307 uv run pytest tests/integration/external/db/test_client_connection.py
```

You can also run the whole DB integration scope with:

```bash
cd be
RUN_DOCKER_DB_TESTS=1 TEST_DB_HOST=127.0.0.1 TEST_DB_PORT=3307 uv run pytest -m integration tests/integration/external/db
```

## Notes

- tests are skipped unless `RUN_DOCKER_DB_TESTS=1`
- the default container name is `test_db_docker`
- the seeded query currently expects the row `('test_db_docker',)`
- stop and clean up when finished:

```bash
docker compose -f docker-compose.yml -f be/tests/integration/external/db/docker-compose.yml down -v
```
