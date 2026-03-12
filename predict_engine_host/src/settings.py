from dataclasses import dataclass
import os
from pathlib import Path


def _read_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer, got {value!r}") from exc


def _read_csv(name: str) -> tuple[str, ...]:
    value = os.getenv(name, "")
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class ApplicationSettings:
    _env: str
    _service_name: str
    _host: str
    _port: int

    @property
    def env(self) -> str:
        return self._env

    @property
    def service_name(self) -> str:
        return self._service_name

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port


@dataclass(frozen=True)
class GrpcSettings:
    _host: str
    _port: int
    _max_workers: int

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def max_workers(self) -> int:
        return self._max_workers

    @property
    def bind_address(self) -> str:
        return f"{self._host}:{self._port}"


@dataclass(frozen=True)
class ModelSettings:
    _path: Path
    _input_name: str | None
    _feature_names: tuple[str, ...]
    _output_names: tuple[str, ...]
    _providers: tuple[str, ...]

    @property
    def path(self) -> Path:
        return self._path

    @property
    def input_name(self) -> str | None:
        return self._input_name

    @property
    def feature_names(self) -> tuple[str, ...]:
        return self._feature_names

    @property
    def output_names(self) -> tuple[str, ...]:
        return self._output_names

    @property
    def providers(self) -> tuple[str, ...]:
        return self._providers


@dataclass(frozen=True)
class Settings:
    app: ApplicationSettings
    grpc: GrpcSettings
    model: ModelSettings


def load_settings() -> Settings:
    input_name = os.getenv("MODEL_INPUT_NAME") or None
    model_path = Path(_read_str("MODEL_PATH", "./models/model.onnx")).expanduser()
    return Settings(
        app=ApplicationSettings(
            _env=_read_str("APP_ENV", "development"),
            _service_name=_read_str("SERVICE_NAME", "predict_engine_host"),
            _host=_read_str("HOST", "0.0.0.0"),
            _port=_read_int("PORT", 8001),
        ),
        grpc=GrpcSettings(
            _host=_read_str("GRPC_HOST", "0.0.0.0"),
            _port=_read_int("GRPC_PORT", 50051),
            _max_workers=_read_int("GRPC_MAX_WORKERS", 10),
        ),
        model=ModelSettings(
            _path=model_path,
            _input_name=input_name,
            _feature_names=_read_csv("MODEL_FEATURE_NAMES"),
            _output_names=_read_csv("MODEL_OUTPUT_NAMES"),
            _providers=_read_csv("MODEL_EXECUTION_PROVIDERS"),
        ),
    )


settings = load_settings()
