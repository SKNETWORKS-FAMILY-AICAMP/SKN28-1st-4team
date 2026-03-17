# pyright: reportMissingImports=false

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .config import AgentRuntimeConfig, DEFAULT_ENV_PATH, resolve_reference_path
from .prompt import build_user_prompt, get_system_prompt
from .reference import ReferenceStore, load_reference_store
from .schemas import BrandModelTrimMatch

if TYPE_CHECKING:
    from .agent_client import StructuredAgentClient


SHORTLIST_LIMIT = 8
MIN_CANDIDATE_SCORE = 0.25


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

    def map(self, raw_name: str, *, use_agent: bool = True) -> BrandModelTrimMatch:
        shortlist = self.reference_store.shortlist(
            raw_name,
            limit=SHORTLIST_LIMIT,
            min_score=MIN_CANDIDATE_SCORE,
        )
        fallback = _top_shortlist_or_empty(shortlist)

        if not shortlist or not use_agent or self.agent_client is None:
            return fallback

        agent_result = self.agent_client.run_sync(
            agent_name="string_to_bmt_mapper",
            instructions=get_system_prompt(),
            user_prompt=build_user_prompt(raw_name=raw_name, shortlist=shortlist),
            output_type=BrandModelTrimMatch,
        )

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

        return fallback


def string_to_bmt(
    raw_name: str,
    *,
    use_agent: bool = True,
    env_path: Path | None = DEFAULT_ENV_PATH,
    reference_path: str | Path | None = None,
) -> tuple[str | None, str | None, str | None]:
    mapper = _StringToBMTMapper.from_env(
        env_path=env_path,
        reference_path=reference_path,
    )
    return mapper.map(raw_name, use_agent=use_agent).as_tuple()


def _top_shortlist_or_empty(shortlist) -> BrandModelTrimMatch:
    if not shortlist:
        return BrandModelTrimMatch()
    return BrandModelTrimMatch.from_candidate(shortlist[0])
