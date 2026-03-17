# pyright: reportMissingImports=false

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .schemas import BrandModelTrimCandidate


PROMPT_PATH = Path(__file__).with_name("prompt.md")
TITLE_BRAND_ALIAS_MAP: dict[str, str] = {
    "현대": "hyundai",
    "제네시스": "hyundai",
    "기아": "kia",
    "KG모빌리티(쌍용)": "kgm",
    "르노(삼성)": "renault",
    "쉐보레(대우)": "chevrolet",
    "쉐보레": "chevrolet",
}


def extract_title_brand(raw_name: str) -> str | None:
    match = re.match(r"^\s*\[([^\]]+)\]", raw_name)
    if not match:
        return None
    return match.group(1).strip() or None


def build_brand_alias_hint(raw_name: str) -> str:
    raw_brand = extract_title_brand(raw_name)
    canonical_brand = TITLE_BRAND_ALIAS_MAP.get(raw_brand) if raw_brand else None

    alias_lines = [
        f"- {alias_brand} -> {canonical_brand_name}"
        for alias_brand, canonical_brand_name in TITLE_BRAND_ALIAS_MAP.items()
    ]
    alias_block = "\n".join(alias_lines)

    return f"""brand_alias_hint:
- raw_title_brand={raw_brand or 'null'}
- canonical_brand={canonical_brand or 'null'}

brand_alias_map:
{alias_block}
"""


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
    brand_alias_hint = build_brand_alias_hint(raw_name)

    return f"""Choose the best canonical brand/model/trim tuple for the raw vehicle name.

raw_name: {raw_name}

{brand_alias_hint}

candidate_shortlist:
{candidate_block}

Guidance:
- Choose only from the shortlist.
- Apply the brand_alias_hint before comparing shortlist rows.
- If canonical_brand is not null, prefer shortlist rows from that canonical brand.
- If one row clearly fits, return that row exactly.
- If trim is unclear but the model is clear, set trim_name to null.
- If the shortlist does not contain a reliable match, return null for all fields.

Return JSON only.
"""
