# pyright: reportMissingImports=false

from __future__ import annotations

import asyncio
from concurrent.futures import Future
from threading import Thread
from typing import Any, TypeVar

from agents import Agent, Runner, set_default_openai_api, set_default_openai_client, set_tracing_disabled
from openai import AsyncOpenAI
from pydantic import BaseModel

from .config import AgentRuntimeConfig


ModelT = TypeVar("ModelT", bound=BaseModel)


class StructuredAgentClient:
    def __init__(self, config: AgentRuntimeConfig) -> None:
        self.config = config
        self._client: AsyncOpenAI | None = None

    async def run(
        self,
        *,
        agent_name: str,
        instructions: str,
        user_prompt: str,
        output_type: type[ModelT],
        tools: list[Any] | None = None,
        model: str | None = None,
    ) -> ModelT:
        self._configure()
        agent = Agent(
            name=agent_name,
            instructions=instructions,
            model=model or self.config.model,
            output_type=output_type,
            tools=list(tools or ()),
        )
        result = await Runner.run(agent, user_prompt)
        return result.final_output

    async def aclose(self) -> None:
        if self._client is None:
            return
        await self._client.close()
        self._client = None

    def run_sync(
        self,
        *,
        agent_name: str,
        instructions: str,
        user_prompt: str,
        output_type: type[ModelT],
        tools: list[Any] | None = None,
        model: str | None = None,
    ) -> ModelT:
        return _run_coroutine_sync(
            self.run(
                agent_name=agent_name,
                instructions=instructions,
                user_prompt=user_prompt,
                output_type=output_type,
                tools=tools,
                model=model,
            )
        )

    def _configure(self) -> None:
        if self._client is None:
            self._client = AsyncOpenAI(
                base_url=self.config.base_url,
                api_key=self.config.api_key,
                default_headers={
                    key: value
                    for key, value in {
                        "HTTP-Referer": self.config.site_url,
                        "X-Title": self.config.app_name,
                    }.items()
                    if value
                },
            )
        set_default_openai_api("chat_completions")
        set_tracing_disabled(True)
        set_default_openai_client(self._client)


def _run_coroutine_sync(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        future: Future = Future()

        def runner() -> None:
            try:
                result = asyncio.run(coro)
            except Exception as exc:  # pragma: no cover - runtime propagation
                future.set_exception(exc)
            else:
                future.set_result(result)

        thread = Thread(target=runner, daemon=True)
        thread.start()
        thread.join()
        return future.result()

    return asyncio.run(coro)
