from functools import lru_cache

from env.settings import AIAgentSettings, load_ai_agent_settings

from .client import AIAgentClient


def _create_ai_agent_client(config: AIAgentSettings) -> AIAgentClient:
    return AIAgentClient.from_config(config)


@lru_cache(maxsize=1)
def _get_ai_agent_settings() -> AIAgentSettings:
    return load_ai_agent_settings()


@lru_cache(maxsize=1)
def get_ai_agent_client() -> AIAgentClient:
    return _create_ai_agent_client(_get_ai_agent_settings())


def _clear_ai_agent_dependency_cache() -> None:
    get_ai_agent_client.cache_clear()
    _get_ai_agent_settings.cache_clear()
