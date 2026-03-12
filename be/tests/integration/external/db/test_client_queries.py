"""Integration-scope pytest coverage for DB query execution.

This module verifies that `MySQLClient.connect()` can be used as the actual
transaction boundary for write/read/delete flows against the live MySQL test
container.
"""

import os
from typing import Any, cast
from uuid import uuid4

import pytest

from external.db.client import MySQLClient


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_DOCKER_DB_TESTS") != "1",
        reason="requires RUN_DOCKER_DB_TESTS=1 and the test_db_docker container",
    ),
]


def test_executes_insert_select_and_delete_with_context_manager(
    ready_test_db_client: MySQLClient,
) -> None:
    """Integration scope: verify context-managed transactions can write and read."""

    label = f"pytest-write-read-{uuid4().hex}"

    with ready_test_db_client.connect() as active_connection:
        with cast(Any, active_connection).cursor() as cursor:
            inserted_rows = cursor.execute(
                "INSERT INTO connectivity_check (label) VALUES (%s)",
                (label,),
            )

    assert inserted_rows == 1

    with ready_test_db_client.connect() as active_connection:
        with cast(Any, active_connection).cursor() as cursor:
            cursor.execute(
                "SELECT label FROM connectivity_check WHERE label = %s LIMIT 1",
                (label,),
            )
            row = cursor.fetchone()

    assert row == (label,)

    with ready_test_db_client.connect() as active_connection:
        with cast(Any, active_connection).cursor() as cursor:
            deleted_rows = cursor.execute(
                "DELETE FROM connectivity_check WHERE label = %s",
                (label,),
            )

    assert deleted_rows == 1
