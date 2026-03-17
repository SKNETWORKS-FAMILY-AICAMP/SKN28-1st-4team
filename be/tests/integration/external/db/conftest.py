"""Shared pytest fixtures for DB integration tests.

Pytest imports this local `conftest.py` before collecting test modules in the
same directory tree, so fixtures defined here are injected automatically into
integration tests that request them.
"""

import os
import time

import pytest

from env.settings import DatabaseSettings
from external.db.client import MySQLClient


def _read_int_env(name: str, default: int) -> int:
    """Read an integer environment variable used to configure the live test DB."""

    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def build_test_database_settings() -> DatabaseSettings:
    """Build live DB settings from the `TEST_DB_*` environment variables."""

    return DatabaseSettings(
        host=os.getenv("TEST_DB_HOST", "127.0.0.1"),
        port=_read_int_env("TEST_DB_PORT", 3307),
        user=os.getenv("TEST_DB_USER", "app_user"),
        password=os.getenv("TEST_DB_PASSWORD", "app_password"),
        name=os.getenv("TEST_DB_NAME", "app_db"),
        charset=os.getenv("TEST_DB_CHARSET", "utf8mb4"),
        collation=os.getenv("TEST_DB_COLLATION", "utf8mb4_unicode_ci"),
        connect_timeout=_read_int_env("TEST_DB_CONNECT_TIMEOUT", 10),
        ssl_ca_path=None,
    )


def wait_for_test_db(client: MySQLClient, timeout_seconds: float = 15.0) -> None:
    """Poll until `test_db_docker` accepts connections to avoid startup races."""

    deadline = time.monotonic() + timeout_seconds
    last_summary: dict[str, object] = {
        "status": "unavailable",
        "error": "test_db_docker has not been checked yet",
    }

    while time.monotonic() < deadline:
        last_summary = client.health_summary()
        if last_summary["status"] == "available":
            return
        time.sleep(1)

    pytest.fail(f"test_db_docker did not become ready: {last_summary}")


@pytest.fixture(scope="module")
def ready_test_db_client() -> MySQLClient:
    """Module-scoped live client fixture for DB integration tests."""

    client = MySQLClient.from_config(build_test_database_settings())
    wait_for_test_db(client)
    return client
