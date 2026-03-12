from dataclasses import dataclass
from ._utils import _read_str, _read_int, _read_float, _read_optional_str


@dataclass(frozen=True)
class ApplicationSettings:
    env: str
    service_name: str


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    user: str
    password: str
    name: str
    charset: str
    connect_timeout: int
    ssl_ca_path: str | None = None


@dataclass(frozen=True)
class PredictEngineSettings:
    host: str
    port: int
    timeout_seconds: float

    @property
    def target(self) -> str:
        return f"{self.host}:{self.port}"


@dataclass(frozen=True)
class Settings:
    app: ApplicationSettings
    db: DatabaseSettings
    predict_engine: PredictEngineSettings


def load_application_settings() -> ApplicationSettings:
    return ApplicationSettings(
        env=_read_str("APP_ENV", "development"),
        service_name=_read_str("SERVICE_NAME", "be"),
    )


def load_database_settings() -> DatabaseSettings:
    return DatabaseSettings(
        host=_read_str("DB_HOST", "127.0.0.1"),
        port=_read_int("DB_PORT", 3306),
        user=_read_str("DB_USER", "app_user"),
        password=_read_str("DB_PASSWORD", "app_password"),
        name=_read_str("DB_NAME", "app_db"),
        charset=_read_str("DB_CHARSET", "utf8mb4"),
        connect_timeout=_read_int("DB_CONNECT_TIMEOUT", 10),
        ssl_ca_path=_read_optional_str("DB_SSL_CA_PATH"),
    )


def load_predict_engine_settings() -> PredictEngineSettings:
    return PredictEngineSettings(
        host=_read_str("PREDICT_ENGINE_GRPC_HOST", "127.0.0.1"),
        port=_read_int("PREDICT_ENGINE_GRPC_PORT", 50051),
        timeout_seconds=_read_float("PREDICT_ENGINE_TIMEOUT_SECONDS", 5.0),
    )


def load_settings() -> Settings:
    return Settings(
        app=load_application_settings(),
        db=load_database_settings(),
        predict_engine=load_predict_engine_settings(),
    )
