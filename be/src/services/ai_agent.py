from __future__ import annotations

from functools import lru_cache
from typing import Any

from external.ai_agent import AIAgentClient, get_ai_agent_client


class AIAgentService:
    def __init__(self, client: AIAgentClient) -> None:
        self._client = client

    def connection_summary(self) -> dict[str, object]:
        return self._client.connection_summary()

    def create_response(
        self,
        *,
        input_text: str,
        instructions: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> Any:
        return self._client.create_response(
            input_text=input_text,
            instructions=instructions,
            model=model,
            **kwargs,
        )


@lru_cache(maxsize=1)
def get_ai_agent_service() -> AIAgentService:
    return AIAgentService(client=get_ai_agent_client())
