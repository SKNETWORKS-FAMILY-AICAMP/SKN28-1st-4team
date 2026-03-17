# pyright: reportMissingImports=false

from __future__ import annotations

import asyncio
from concurrent.futures import Future
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING

from .config import AgentRuntimeConfig, DEFAULT_ENV_PATH, resolve_reference_path
from .prompt import build_user_prompt, get_system_prompt
from .reference import ReferenceStore, load_reference_store
from .schemas import BrandModelTrimMatch

if TYPE_CHECKING:
    from .agent_client import StructuredAgentClient


SHORTLIST_LIMIT = 8
MIN_CANDIDATE_SCORE = 0.25
DEFAULT_MAX_CONCURRENCY = 25
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_BACKOFF_SECONDS = 1.0


class _StringToBMTMapper:
    def __init__(
        self,
        *,
        reference_store: ReferenceStore,
        agent_client: "StructuredAgentClient | None" = None,
    ) -> None:
        self.reference_store = reference_store
        self.agent_client = agent_client

    @classmethod
    def from_env(
        cls,
        *,
        env_path: Path | None = DEFAULT_ENV_PATH,
        reference_path: str | Path | None = None,
    ) -> "_StringToBMTMapper":
        resolved_reference_path = resolve_reference_path(reference_path, env_path)
        agent_config = AgentRuntimeConfig.from_env(env_path)
        agent_client = None
        if agent_config is not None:
            from .agent_client import StructuredAgentClient

            agent_client = StructuredAgentClient(agent_config)
        return cls(
            reference_store=load_reference_store(resolved_reference_path),
            agent_client=agent_client,
        )

    async def aclose(self) -> None:
        if self.agent_client is None:
            return
        await self.agent_client.aclose()

    def close(self) -> None:
        _run_coroutine_sync(self.aclose())

    def map(self, raw_name: str, *, use_agent: bool = True) -> BrandModelTrimMatch:
        return _run_coroutine_sync(
            self.map_async(
                raw_name,
                use_agent=use_agent,
                max_retries=DEFAULT_MAX_RETRIES,
                retry_backoff_seconds=DEFAULT_RETRY_BACKOFF_SECONDS,
            )
        )

    async def map_async(
        self,
        raw_name: str,
        *,
        use_agent: bool = True,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
    ) -> BrandModelTrimMatch:
        shortlist, fallback = self._prepare_shortlist(raw_name)

        if not shortlist or not use_agent or self.agent_client is None:
            return fallback

        return await self._map_with_agent_retry(
            raw_name,
            shortlist=shortlist,
            fallback=fallback,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
        )

    def map_many(
        self,
        raw_names: list[str],
        *,
        use_agent: bool = True,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
    ) -> list[BrandModelTrimMatch]:
        return _run_coroutine_sync(
            self.map_many_async(
                raw_names,
                use_agent=use_agent,
                max_concurrency=max_concurrency,
                max_retries=max_retries,
                retry_backoff_seconds=retry_backoff_seconds,
            )
        )

    async def map_many_async(
        self,
        raw_names: list[str],
        *,
        use_agent: bool = True,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
    ) -> list[BrandModelTrimMatch]:
        if not raw_names:
            return []

        unique_raw_names = list(dict.fromkeys(raw_names))
        prepared: dict[str, tuple[list, BrandModelTrimMatch]] = {
            raw_name: self._prepare_shortlist(raw_name)
            for raw_name in unique_raw_names
        }

        results_by_name: dict[str, BrandModelTrimMatch] = {}
        pending_raw_names: list[str] = []

        for raw_name in unique_raw_names:
            shortlist, fallback = prepared[raw_name]
            if not shortlist or not use_agent or self.agent_client is None:
                results_by_name[raw_name] = fallback
            else:
                pending_raw_names.append(raw_name)

        if pending_raw_names:
            semaphore = asyncio.Semaphore(max(1, max_concurrency))

            async def worker(raw_name: str) -> tuple[str, BrandModelTrimMatch]:
                shortlist, fallback = prepared[raw_name]
                async with semaphore:
                    result = await self._map_with_agent_retry(
                        raw_name,
                        shortlist=shortlist,
                        fallback=fallback,
                        max_retries=max_retries,
                        retry_backoff_seconds=retry_backoff_seconds,
                    )
                return (raw_name, result)

            completed = await asyncio.gather(*(worker(raw_name) for raw_name in pending_raw_names))
            for raw_name, result in completed:
                results_by_name[raw_name] = result

        return [results_by_name[raw_name] for raw_name in raw_names]

    def _prepare_shortlist(self, raw_name: str) -> tuple[list, BrandModelTrimMatch]:
        shortlist = self.reference_store.shortlist(
            raw_name,
            limit=SHORTLIST_LIMIT,
            min_score=MIN_CANDIDATE_SCORE,
        )
        fallback = _top_shortlist_or_empty(shortlist)
        return (shortlist, fallback)

    async def _map_with_agent_retry(
        self,
        raw_name: str,
        *,
        shortlist,
        fallback: BrandModelTrimMatch,
        max_retries: int,
        retry_backoff_seconds: float,
    ) -> BrandModelTrimMatch:
        assert self.agent_client is not None

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            runtime_instructions = None
            if attempt > 0:
                runtime_instructions = (
                    "Retry mode. Choose exactly one shortlist row when there is a reliable match. "
                    "Otherwise return null for all fields."
                )

            try:
                agent_result = await self.agent_client.run(
                    agent_name="string_to_bmt_mapper",
                    instructions=get_system_prompt(runtime_instructions=runtime_instructions),
                    user_prompt=build_user_prompt(raw_name=raw_name, shortlist=shortlist),
                    output_type=BrandModelTrimMatch,
                )
            except Exception as exc:  # pragma: no cover - network/runtime failure
                last_error = exc
            else:
                canonical = self.reference_store.resolve(
                    brand=agent_result.brand,
                    model_name=agent_result.model_name,
                    trim_name=agent_result.trim_name,
                )
                if canonical[0] and canonical[1]:
                    return BrandModelTrimMatch(
                        brand=canonical[0],
                        model_name=canonical[1],
                        trim_name=canonical[2],
                    )
                last_error = ValueError("Agent output did not resolve to a canonical shortlist tuple.")

            if attempt < max_retries:
                await asyncio.sleep(retry_backoff_seconds * (2**attempt))

        del last_error
        return fallback


def string_to_bmt(
    raw_name: str,
    *,
    use_agent: bool = True,
    env_path: Path | None = DEFAULT_ENV_PATH,
    reference_path: str | Path | None = None,
) -> tuple[str | None, str | None, str | None]:
    mapper = load_string_to_bmt_mapper(
        env_path=env_path,
        reference_path=reference_path,
    )
    return mapper.map(raw_name, use_agent=use_agent).as_tuple()


def string_to_bmt_batch(
    raw_names: list[str],
    *,
    use_agent: bool = True,
    env_path: Path | None = DEFAULT_ENV_PATH,
    reference_path: str | Path | None = None,
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
) -> list[tuple[str | None, str | None, str | None]]:
    mapper = load_string_to_bmt_mapper(
        env_path=env_path,
        reference_path=reference_path,
    )
    matches = mapper.map_many(
        raw_names,
        use_agent=use_agent,
        max_concurrency=max_concurrency,
        max_retries=max_retries,
        retry_backoff_seconds=retry_backoff_seconds,
    )
    return [match.as_tuple() for match in matches]


def load_string_to_bmt_mapper(
    *,
    env_path: Path | None = DEFAULT_ENV_PATH,
    reference_path: str | Path | None = None,
) -> _StringToBMTMapper:
    return _StringToBMTMapper.from_env(
        env_path=env_path,
        reference_path=reference_path,
    )


def _top_shortlist_or_empty(shortlist) -> BrandModelTrimMatch:
    if not shortlist:
        return BrandModelTrimMatch()
    return BrandModelTrimMatch.from_candidate(shortlist[0])


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
