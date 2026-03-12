from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Protocol, cast

import pymysql as mysql

from env.settings import DatabaseSettings


class DBConnection(Protocol):
    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def close(self) -> None: ...


class DBConnector(Protocol):
    def __call__(self, **kwargs: Any) -> DBConnection: ...


class MySQLClient:
    def __init__(
        self,
        config: DatabaseSettings,
        *,
        connector: DBConnector | None = None,
    ) -> None:
        self._config = config
        self._connector = connector or cast(DBConnector, mysql.connect)

    @classmethod
    def from_config(
        cls,
        config: DatabaseSettings,
        *,
        connector: DBConnector | None = None,
    ) -> "MySQLClient":
        return cls(config=config, connector=connector)

    def _connection_kwargs(self) -> dict[str, object]:
        return {
            "host": self._config.host,
            "user": self._config.user,
            "password": self._config.password,
            "database": self._config.name,
            "port": self._config.port,
            "charset": self._config.charset,
            "connect_timeout": self._config.connect_timeout,
            "autocommit": False,
        }

    def _connect(self) -> DBConnection:
        return self._connector(**self._connection_kwargs())

    def connection_summary(self) -> dict[str, object]:
        return {
            "host": self._config.host,
            "port": self._config.port,
            "database": self._config.name,
            "user": self._config.user,
            "charset": self._config.charset,
            "connect_timeout": self._config.connect_timeout,
        }

    def health_summary(self) -> dict[str, object]:
        summary = self.connection_summary()
        try:
            with self.connect():
                return {
                    **summary,
                    "status": "available",
                }
        except Exception as exc:
            return {
                **summary,
                "status": "unavailable",
                "error": str(exc),
            }

    @contextmanager
    def connect(self) -> Iterator[DBConnection]:
        """Open a DB connection and wrap it in transaction-safe cleanup.

        Use this as a context manager whenever business logic needs a real DB
        connection. On successful exit the connection is committed. If an
        exception is raised, the transaction is rolled back, and the connection
        is always closed in both cases.

        Example:
            with client.connect() as connection:
                ...
        """
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
