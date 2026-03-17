from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv as _load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    _load_dotenv = None


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
DEFAULT_ENV_PATH = PROJECT_DIR / ".env"
DEFAULT_REFERENCE_PATH = PROJECT_DIR / "sources" / "brand_model_trim_reference.json"


@dataclass(frozen=True, slots=True)
class AgentRuntimeConfig:
    api_key: str
    model: str = "openai/gpt-4o-mini"
    base_url: str = "https://openrouter.ai/api/v1"
    site_url: str | None = None
    app_name: str | None = None

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "AgentRuntimeConfig | None":
        load_environment(env_path)
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return None
        return cls(
            api_key=api_key,
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            site_url=os.getenv("OPENROUTER_SITE_URL") or None,
            app_name=os.getenv("OPENROUTER_APP_NAME") or "name-brand-model-trim-mapping-local",
        )


def is_agent_env_ready(env_path: Path | None = None) -> bool:
    load_environment(env_path)
    return bool(os.getenv("OPENROUTER_API_KEY"))


def resolve_reference_path(reference_path: str | Path | None = None, env_path: Path | None = None) -> Path:
    load_environment(env_path)
    if reference_path:
        candidate = Path(reference_path)
    else:
        candidate = Path(os.getenv("NAME_NORMALIZER_REFERENCE_PATH", str(DEFAULT_REFERENCE_PATH)))

    if candidate.is_absolute():
        return candidate

    return (PROJECT_DIR / candidate).resolve()


def load_environment(env_path: Path | None = None) -> Path:
    resolved_path = Path(env_path or DEFAULT_ENV_PATH).resolve()
    if resolved_path.exists():
        if _load_dotenv is not None:
            _load_dotenv(resolved_path, override=False)
        else:
            _load_env_file(resolved_path)
    return resolved_path


def _load_env_file(env_path: Path) -> None:
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
