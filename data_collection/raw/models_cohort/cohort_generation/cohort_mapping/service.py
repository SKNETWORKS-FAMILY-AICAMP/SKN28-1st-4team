# pyright: reportMissingImports=false

from __future__ import annotations

import asyncio
from typing import Iterable

from agents import Agent, Runner, set_default_openai_api, set_tracing_disabled
from openai import AsyncOpenAI

from .config import CohortAgentConfig
from .prompt import SYSTEM_PROMPT, build_user_prompt
from .schemas import VehicleCategoryMappingInput, VehicleCategoryMappingOutput
from .search_tools import web_search


def get_input_schema() -> dict[str, object]:
    return VehicleCategoryMappingInput.model_json_schema()


def get_output_schema() -> dict[str, object]:
    return VehicleCategoryMappingOutput.model_json_schema()


def build_agent(config: CohortAgentConfig) -> Agent:
    _configure_openrouter(config)
    return Agent(
        name="vehicle_category_mapping_agent",
        instructions=SYSTEM_PROMPT,
        model=config.openrouter_model,
        output_type=VehicleCategoryMappingOutput,
        tools=[web_search],
    )


async def run_category_mapping(
    mapping_input: VehicleCategoryMappingInput,
    config: CohortAgentConfig,
) -> VehicleCategoryMappingOutput:
    agent = build_agent(config)
    prompt = build_user_prompt(
        brand=mapping_input.brand,
        model_name=mapping_input.model_name,
        class_name_examples=mapping_input.class_name_examples,
        level_name_examples=mapping_input.level_name_examples,
        context_summary=mapping_input.context_summary,
    )
    result = await Runner.run(agent, prompt)
    return result.final_output


async def run_category_mapping_batch(
    mapping_inputs: Iterable[VehicleCategoryMappingInput],
    config: CohortAgentConfig,
) -> list[VehicleCategoryMappingOutput]:
    outputs: list[VehicleCategoryMappingOutput] = []
    for mapping_input in mapping_inputs:
        outputs.append(await run_category_mapping(mapping_input, config))
    return outputs


def run_category_mapping_sync(
    mapping_input: VehicleCategoryMappingInput,
    config: CohortAgentConfig,
) -> VehicleCategoryMappingOutput:
    return asyncio.run(run_category_mapping(mapping_input, config))


def run_category_mapping_batch_sync(
    mapping_inputs: Iterable[VehicleCategoryMappingInput],
    config: CohortAgentConfig,
) -> list[VehicleCategoryMappingOutput]:
    return asyncio.run(run_category_mapping_batch(mapping_inputs, config))


def mapping_outputs_to_frame(outputs: Iterable[VehicleCategoryMappingOutput]):
    import pandas as pd

    rows = [output.model_dump(mode="json") for output in outputs]
    return pd.DataFrame(rows)


def _configure_openrouter(config: CohortAgentConfig) -> None:
    client = AsyncOpenAI(
        base_url=config.openrouter_base_url,
        api_key=config.openrouter_api_key,
        default_headers={
            key: value
            for key, value in {
                "HTTP-Referer": config.openrouter_site_url,
                "X-Title": config.openrouter_app_name,
            }.items()
            if value
        },
    )
    set_default_openai_api("chat_completions")
    set_tracing_disabled(True)
    from agents import set_default_openai_client

    set_default_openai_client(client)
