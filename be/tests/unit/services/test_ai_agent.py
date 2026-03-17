from __future__ import annotations

import pytest

from services.ai_agent import AIAgentService


pytestmark = pytest.mark.unit


class StubAIAgentClient:
    def __init__(self) -> None:
        self.create_response_calls: list[dict[str, object]] = []

    def connection_summary(self) -> dict[str, object]:
        return {
            "provider": "openai",
            "model": "gpt-5.4",
            "api_key_configured": True,
        }

    def create_response(self, **kwargs: object) -> dict[str, object]:
        self.create_response_calls.append(kwargs)
        return {
            "id": "resp_service_123",
            "input": kwargs["input_text"],
            "model": kwargs.get("model") or "gpt-5.4",
        }


def test_connection_summary_delegates_to_client() -> None:
    service = AIAgentService(client=StubAIAgentClient())  # type: ignore[arg-type]

    assert service.connection_summary() == {
        "provider": "openai",
        "model": "gpt-5.4",
        "api_key_configured": True,
    }


def test_create_response_returns_client_response_and_forwards_arguments() -> None:
    client = StubAIAgentClient()
    service = AIAgentService(client=client)  # type: ignore[arg-type]

    response = service.create_response(
        input_text="What affects used-car resale value?",
        instructions="Answer with bullet points.",
        model="gpt-5.4",
        temperature=0.1,
    )

    assert response == {
        "id": "resp_service_123",
        "input": "What affects used-car resale value?",
        "model": "gpt-5.4",
    }
    assert client.create_response_calls == [
        {
            "input_text": "What affects used-car resale value?",
            "instructions": "Answer with bullet points.",
            "model": "gpt-5.4",
            "temperature": 0.1,
        }
    ]
