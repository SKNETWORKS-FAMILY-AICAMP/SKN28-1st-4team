"""Integration-scope pytest coverage for live MySQL connectivity.

Pytest collects this module like any other `test_*.py` file, but the module is
guarded by `RUN_DOCKER_DB_TESTS=1` so it only runs when the `test_db_docker`
container is intentionally available.
"""

import os
from typing import Any, cast

import pytest

from external.db.client import MySQLClient


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_DOCKER_DB_TESTS") != "1",
        reason="requires RUN_DOCKER_DB_TESTS=1 and the test_db_docker container",
    ),
]


def test_connects_to_test_db_docker(ready_test_db_client: MySQLClient) -> None:
    """Integration scope: verify a real query can read the seeded docker test row."""

    with ready_test_db_client.connect() as active_connection:
        with cast(Any, active_connection).cursor() as cursor:
            cursor.execute(
                "SELECT label FROM connectivity_check ORDER BY id ASC LIMIT 1"
            )
            row = cursor.fetchone()

    assert row == ("test_db_docker",)
