from pathlib import Path

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
    collation: str = Field(default="utf8mb4_unicode_ci", validation_alias="DB_COLLATION")
    connect_timeout: int = Field(default=10, validation_alias="DB_CONNECT_TIMEOUT")
    ssl_ca_path: str | None = Field(default=None, validation_alias="DB_SSL_CA_PATH")


class PredictEngineSettings(EnvSettings):
    model_path: Path = Field(
        default=Path("../predict_engine_research/images/model.cbm"),
        validation_alias="PREDICT_ENGINE_MODEL_PATH",
    )
    feature_manifest_path: Path = Field(
        default=Path("../predict_engine_research/images/feature_manifest.json"),
        validation_alias="PREDICT_ENGINE_FEATURE_MANIFEST_PATH",
    )

    @field_validator("model_path", "feature_manifest_path", mode="before")
    @classmethod
    def _resolve_project_relative_path(cls, value: str | Path) -> Path:
        path = Path(value).expanduser()
        if path.is_absolute():
            return path
        return (_PROJECT_ROOT / path).resolve()


class AIAgentSettings(EnvSettings):
    api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AI_AGENT_API_KEY", "OPENROUTER_API_KEY"),
    )
    model: str = Field(
        default="gpt-5.4",
        validation_alias=AliasChoices("AI_AGENT_MODEL", "OPENROUTER_MODEL"),
    )
    base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AI_AGENT_BASE_URL", "OPENROUTER_BASE_URL"),
    )
    site_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AI_AGENT_SITE_URL", "OPENROUTER_SITE_URL"),
    )
    app_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AI_AGENT_APP_NAME", "OPENROUTER_APP_NAME"),
    )
    organization: str | None = Field(default=None, validation_alias="AI_AGENT_ORGANIZATION")
    project: str | None = Field(default=None, validation_alias="AI_AGENT_PROJECT")
    timeout_seconds: float = Field(
        default=30.0,
        validation_alias="AI_AGENT_TIMEOUT_SECONDS",
    )
    max_retries: int = Field(default=2, validation_alias="AI_AGENT_MAX_RETRIES")

    @field_validator(
        "api_key",
        "base_url",
        "site_url",
        "app_name",
        "organization",
        "project",
        mode="before",
    )
    @classmethod
    def _normalize_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("model", mode="before")
    @classmethod
    def _normalize_required_string(cls, value: str) -> str:
        normalized = value.strip()
        if normalized == "":
            raise ValueError("AI_AGENT_MODEL must not be blank")
        return normalized


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    app: ApplicationSettings = Field(default_factory=ApplicationSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    predict_engine: PredictEngineSettings = Field(default_factory=PredictEngineSettings)
    ai_agent: AIAgentSettings = Field(default_factory=AIAgentSettings)


def load_application_settings() -> ApplicationSettings:
    return ApplicationSettings()


def load_database_settings() -> DatabaseSettings:
    return DatabaseSettings()


def load_predict_engine_settings() -> PredictEngineSettings:
    return PredictEngineSettings()


def load_ai_agent_settings() -> AIAgentSettings:
    return AIAgentSettings()


def load_settings() -> Settings:
    return Settings()
