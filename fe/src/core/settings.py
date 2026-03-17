from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class QuerySettings:
    base_url: str
    catalog_path: str
    price_prediction_path: str
    timeout_seconds: float


@dataclass(frozen=True)
class AppSettings:
    app_env: str
    service_name: str
    query: QuerySettings

    @property
    def is_development(self) -> bool:
        normalized = self.app_env.strip().lower()
        return normalized in {"development", "developement", "dev", "local"}


@lru_cache(maxsize=1)
def get_app_settings() -> AppSettings:
    return AppSettings(
        app_env=os.environ.get("APP_ENV", "development"),
        service_name=os.environ.get("SERVICE_NAME", "fe"),
        query=QuerySettings(
            base_url=os.environ.get("FE_QUERY_BASE_URL", "http://127.0.0.1:8000"),
            catalog_path=os.environ.get("FE_QUERY_CATALOG_PATH", "/api/v1/frontend/catalog"),
            price_prediction_path=os.environ.get(
                "FE_QUERY_PRICE_PATH",
                "/api/v1/frontend/price-prediction",
            ),
            timeout_seconds=float(os.environ.get("FE_QUERY_TIMEOUT_SECONDS", "10.0")),
        ),
    )
