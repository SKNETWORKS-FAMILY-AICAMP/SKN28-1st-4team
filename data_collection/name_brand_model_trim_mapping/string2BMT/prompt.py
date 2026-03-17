# pyright: reportMissingImports=false

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .schemas import BrandModelTrimCandidate


PROMPT_PATH = Path(__file__).with_name("prompt.md")


def get_system_prompt(runtime_instructions: str | None = None) -> str:
    prompt = PROMPT_PATH.read_text(encoding="utf-8").strip()
    if runtime_instructions:
        prompt = f"{prompt}\n\nRuntime instructions:\n{runtime_instructions.strip()}"
    return prompt


def build_user_prompt(
    *,
    raw_name: str,
    shortlist: Iterable[BrandModelTrimCandidate],
) -> str:
    candidate_lines = []
    for index, candidate in enumerate(shortlist, start=1):
        trim_value = candidate.trim_name if candidate.trim_name is not None else "null"
        candidate_lines.append(
            f"{index}. brand={candidate.brand}; model_name={candidate.model_name}; trim_name={trim_value}; "
            f"score={candidate.score:.3f}; basis={candidate.match_basis or 'n/a'}"
        )

    candidate_block = "\n".join(candidate_lines) if candidate_lines else "(empty shortlist)"

    return f"""Choose the best canonical brand/model/trim tuple for the raw vehicle name.

raw_name: {raw_name}

candidate_shortlist:
{candidate_block}

Guidance:
- Choose only from the shortlist.
- If one row clearly fits, return that row exactly.
- If trim is unclear but the model is clear, set trim_name to null.
- If the shortlist does not contain a reliable match, return null for all fields.

Return JSON only.
"""
