from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
    )


class ApplicationSettings(EnvSettings):
    env: str = Field(default="development", validation_alias="APP_ENV")
    service_name: str = Field(default="be", validation_alias="SERVICE_NAME")
    format :str = Field(default="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
 validation_alias="LOG_FORMAT")


class DatabaseSettings(EnvSettings):
    host: str = Field(default="127.0.0.1", validation_alias="DB_HOST")
    port: int = Field(default=3306, validation_alias="DB_PORT")
    user: str = Field(default="app_user", validation_alias="DB_USER")
    password: str = Field(default="app_password", validation_alias="DB_PASSWORD")
    name: str = Field(default="app_db", validation_alias="DB_NAME")
    charset: str = Field(default="utf8mb4", validation_alias="DB_CHARSET")
    connect_timeout: int = Field(default=10, validation_alias="DB_CONNECT_TIMEOUT")
    ssl_ca_path: str | None = Field(default=None, validation_alias="DB_SSL_CA_PATH")


class PredictEngineSettings(EnvSettings):
    host: str = Field(default="127.0.0.1", validation_alias="PREDICT_ENGINE_GRPC_HOST")
    port: int = Field(default=50051, validation_alias="PREDICT_ENGINE_GRPC_PORT")
    timeout_seconds: float = Field(
        default=5.0,
        validation_alias="PREDICT_ENGINE_TIMEOUT_SECONDS",
    )

    @property
    def target(self) -> str:
        return f"{self.host}:{self.port}"


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    app: ApplicationSettings = Field(default_factory=ApplicationSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    predict_engine: PredictEngineSettings = Field(default_factory=PredictEngineSettings)


def load_application_settings() -> ApplicationSettings:
    return ApplicationSettings()


def load_database_settings() -> DatabaseSettings:
    return DatabaseSettings()


def load_predict_engine_settings() -> PredictEngineSettings:
    return PredictEngineSettings()


def load_settings() -> Settings:
    return Settings()
