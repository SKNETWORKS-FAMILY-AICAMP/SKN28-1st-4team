from __future__ import annotations

from functools import lru_cache

from env.settings import DatabaseSettings, load_database_settings

from .client import DBConnector, MySQLClient


def _create_db_client(
    config: DatabaseSettings,
    *,
    connector: DBConnector | None = None,
) -> MySQLClient:
    return MySQLClient.from_config(config=config, connector=connector)


@lru_cache(maxsize=1)
def _get_database_settings() -> DatabaseSettings:
    return load_database_settings()


@lru_cache(maxsize=1)
def get_db_client() -> MySQLClient:
    """Return the cached application-level ``MySQLClient`` instance.

    ``@lru_cache(maxsize=1)`` means this provider reuses the same client
    instance for repeated calls within the current Python process. This is a
    lightweight process-local singleton at the provider layer, not a singleton
    implemented by ``MySQLClient`` itself.

    The returned client is intended to be used with its context manager so the
    underlying DB connection is committed or rolled back and always closed.

    Example:
        with get_db_client().connect() as connection:
            ...
    """
    return _create_db_client(_get_database_settings())


def _clear_db_dependency_cache() -> None:
    get_db_client.cache_clear()
    _get_database_settings.cache_clear()
