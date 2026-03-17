"""Unit-scope pytest coverage for `external.db.client.MySQLClient`.

Pytest collects each `test_*` function in this module and runs it in-process as
an isolated unit test. The tests replace the real DB connector with lightweight
test doubles so no live MySQL server is required.
"""

import pytest

from env.settings import DatabaseSettings
from external.db.client import MySQLClient


pytestmark = pytest.mark.unit


class StubConnection:
    """Minimal connection double for commit, rollback, and close assertions."""

    def __init__(self) -> None:
        self.commit_calls = 0
        self.rollback_calls = 0
        self.close_calls = 0

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1

    def close(self) -> None:
        self.close_calls += 1


class RecordingConnector:
    """Connector double that records the kwargs passed by `MySQLClient`."""

    def __init__(self, connection: StubConnection) -> None:
        self.connection = connection
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs: object) -> StubConnection:
        self.calls.append(kwargs)
        return self.connection


class FailingConnector:
    """Connector double that always fails to simulate an unavailable DB."""

    def __call__(self, **kwargs: object) -> StubConnection:
        raise RuntimeError("cannot connect to test database")


@pytest.fixture(scope="function")
def database_settings() -> DatabaseSettings:
    """Function-scoped settings fixture for deterministic unit-test inputs."""

    return DatabaseSettings(
        host="db.internal",
        port=3307,
        user="app_user",
        password="secret",
        name="app_db",
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
        connect_timeout=15,
        ssl_ca_path=None,
    )


@pytest.fixture(scope="function")
def stub_connection() -> StubConnection:
    """Function-scoped connection double so each test starts with clean counters."""

    return StubConnection()


@pytest.fixture(scope="function")
def recording_connector(stub_connection: StubConnection) -> RecordingConnector:
    """Function-scoped connector double bound to the fresh stub connection."""

    return RecordingConnector(stub_connection)


def test_from_config_builds_mysql_client_from_database_settings(
    database_settings: DatabaseSettings,
) -> None:
    """Unit scope: `from_config()` should preserve the provided DB settings."""

    client = MySQLClient.from_config(database_settings)

    assert isinstance(client, MySQLClient)
    assert client.connection_summary() == {
        "host": "db.internal",
        "port": 3307,
        "database": "app_db",
        "user": "app_user",
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "connect_timeout": 15,
        "ssl_ca_path": None,
    }


def test_connect_uses_configured_connection_kwargs(
    database_settings: DatabaseSettings,
    stub_connection: StubConnection,
    recording_connector: RecordingConnector,
) -> None:
    """Unit scope: `connect()` should forward the expected kwargs to the connector."""

    client = MySQLClient.from_config(
        database_settings,
        connector=recording_connector,
    )

    with client.connect() as active_connection:
        assert active_connection is stub_connection

    assert recording_connector.calls == [
        {
            "host": "db.internal",
            "user": "app_user",
            "password": "secret",
            "database": "app_db",
            "port": 3307,
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
            "connect_timeout": 15,
            "autocommit": False,
        }
    ]


def test_connect_commits_and_closes_after_success(
    database_settings: DatabaseSettings,
    stub_connection: StubConnection,
    recording_connector: RecordingConnector,
) -> None:
    """Unit scope: a successful context-manager exit should commit and close once."""

    client = MySQLClient(database_settings, connector=recording_connector)

    with client.connect() as active_connection:
        assert active_connection is stub_connection

    assert stub_connection.commit_calls == 1
    assert stub_connection.rollback_calls == 0
    assert stub_connection.close_calls == 1


def test_connect_includes_ssl_ca_path_when_configured(
    database_settings: DatabaseSettings,
    stub_connection: StubConnection,
    recording_connector: RecordingConnector,
) -> None:
    """Unit scope: `connect()` should forward the configured CA path when present."""

    client = MySQLClient(
        database_settings.model_copy(
            update={"ssl_ca_path": "certs/aws-global-bundle.pem"}
        ),
        connector=recording_connector,
    )

    with client.connect() as active_connection:
        assert active_connection is stub_connection

    assert recording_connector.calls == [
        {
            "host": "db.internal",
            "user": "app_user",
            "password": "secret",
            "database": "app_db",
            "port": 3307,
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
            "connect_timeout": 15,
            "autocommit": False,
            "ssl_ca": "certs/aws-global-bundle.pem",
        }
    ]


def test_connect_rolls_back_and_closes_after_error(
    database_settings: DatabaseSettings,
    stub_connection: StubConnection,
    recording_connector: RecordingConnector,
) -> None:
    """Unit scope: an error inside the context manager should roll back and close."""

    client = MySQLClient(database_settings, connector=recording_connector)

    with pytest.raises(RuntimeError, match="boom"):
        with client.connect():
            raise RuntimeError("boom")

    assert stub_connection.commit_calls == 0
    assert stub_connection.rollback_calls == 1
    assert stub_connection.close_calls == 1


def test_health_summary_reports_available_after_successful_connection(
    database_settings: DatabaseSettings,
    stub_connection: StubConnection,
    recording_connector: RecordingConnector,
) -> None:
    """Unit scope: a successful health check should report the DB as available."""

    client = MySQLClient(database_settings, connector=recording_connector)

    assert client.health_summary() == {
        "host": "db.internal",
        "port": 3307,
        "database": "app_db",
        "user": "app_user",
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "connect_timeout": 15,
        "ssl_ca_path": None,
        "status": "available",
    }
    assert stub_connection.commit_calls == 1
    assert stub_connection.rollback_calls == 0
    assert stub_connection.close_calls == 1


def test_health_summary_reports_unavailable_after_connection_error(
    database_settings: DatabaseSettings,
) -> None:
    """Unit scope: a failed health check should expose the connector error."""

    client = MySQLClient(database_settings, connector=FailingConnector())

    assert client.health_summary() == {
        "host": "db.internal",
        "port": 3307,
        "database": "app_db",
        "user": "app_user",
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "connect_timeout": 15,
        "ssl_ca_path": None,
        "status": "unavailable",
        "error": "cannot connect to test database",
    }
