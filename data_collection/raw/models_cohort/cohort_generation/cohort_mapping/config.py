from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


@dataclass(frozen=True, slots=True)
class CohortAgentConfig:
    openrouter_api_key: str
    openrouter_model: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str | None = None
    openrouter_app_name: str | None = None
    max_search_results: int = 5

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "CohortAgentConfig":
        _load_env_file(env_path or DEFAULT_ENV_PATH)
        api_key = os.getenv("OPENROUTER_API_KEY")
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is missing. Fill cohort_generation/.env first.")
        return cls(
            openrouter_api_key=api_key,
            openrouter_model=model,
            openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            openrouter_site_url=os.getenv("OPENROUTER_SITE_URL") or None,
            openrouter_app_name=os.getenv("OPENROUTER_APP_NAME") or None,
            max_search_results=int(os.getenv("COHORT_AGENT_MAX_SEARCH_RESULTS", "5")),
        )


def is_agent_env_ready(env_path: Path | None = None) -> bool:
    _load_env_file(env_path or DEFAULT_ENV_PATH)
    return bool(os.getenv("OPENROUTER_API_KEY"))


def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
