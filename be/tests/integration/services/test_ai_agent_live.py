from __future__ import annotations

import os
import re

from openai import AuthenticationError
import pytest

from services.ai_agent import get_ai_agent_service


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_AI_AGENT_TESTS") != "1",
        reason="requires RUN_LIVE_AI_AGENT_TESTS=1 and a configured AI agent API key",
    ),
    pytest.mark.skipif(
        not (os.getenv("AI_AGENT_API_KEY") or "").strip(),
        reason="requires AI_AGENT_API_KEY to call the live AI agent",
    ),
]


def _normalize_output_text(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.strip(" \n\t\r\"'`.,!?;:")
    return normalized


def test_ai_agent_service_returns_live_response_text() -> None:
    get_ai_agent_service.cache_clear()
    service = get_ai_agent_service()

    try:
        response = service.create_response(
            input_text="Reply with exactly: say my name",
            instructions="Return only the exact requested phrase in lowercase English with no extra words and no punctuation.",
            max_output_tokens=300,
        )
    except AuthenticationError as exc:
        pytest.fail(
            "Live AI agent authentication failed. Check AI_AGENT_API_KEY and AI_AGENT_BASE_URL in be/.env.",
            pytrace=False,
        )
        return

    output_text = getattr(response, "output_text", None)
    assert isinstance(output_text, str)
    assert output_text.strip() != ""
    assert _normalize_output_text(output_text) == "say my name"
