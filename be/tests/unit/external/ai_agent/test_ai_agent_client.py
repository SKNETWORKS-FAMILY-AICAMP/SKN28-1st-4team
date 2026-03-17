from __future__ import annotations

import pytest

from env.settings import AIAgentSettings
from external.ai_agent.client import AIAgentClient


pytestmark = pytest.mark.unit


class StubResponsesAPI:
    def __init__(self, response: object) -> None:
        self._response = response
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return self._response


class StubOpenAISDK:
    def __init__(self, response: object) -> None:
        self.responses = StubResponsesAPI(response)


def test_from_config_requires_api_key() -> None:
    with pytest.raises(ValueError, match="AI_AGENT_API_KEY"):
        AIAgentClient.from_config(
            AIAgentSettings(
                api_key="",
                model="gpt-5.4",
            )
        )


def test_connection_summary_reports_ai_agent_configuration() -> None:
    client = AIAgentClient(
        api_key="test-key",
        model="gpt-5.4",
        base_url="https://api.openai.com/v1",
        site_url="https://example.com",
        app_name="be-local",
        organization="org_123",
        project="proj_123",
        timeout_seconds=45.0,
        max_retries=3,
        sdk_client=StubOpenAISDK({"ok": True}),
    )

    assert client.connection_summary() == {
        "provider": "openai",
        "model": "gpt-5.4",
        "base_url": "https://api.openai.com/v1",
        "site_url": "https://example.com",
        "app_name": "be-local",
        "organization": "org_123",
        "project": "proj_123",
        "timeout_seconds": 45.0,
        "max_retries": 3,
        "api_key_configured": True,
    }


def test_create_response_returns_sdk_response_and_forwards_request_arguments() -> None:
    fake_response = {"id": "resp_123", "output_text": "hello"}
    sdk_client = StubOpenAISDK(fake_response)
    client = AIAgentClient(
        api_key="test-key",
        model="gpt-5.4",
        sdk_client=sdk_client,
    )

    response = client.create_response(
        input_text="Summarize this car listing.",
        instructions="Respond in Korean.",
        temperature=0.2,
        metadata={"source": "unit-test"},
    )

    assert response == fake_response
    assert sdk_client.responses.calls == [
        {
            "model": "gpt-5.4",
            "input": "Summarize this car listing.",
            "instructions": "Respond in Korean.",
            "temperature": 0.2,
            "metadata": {"source": "unit-test"},
        }
    ]


def test_create_response_allows_overriding_model_per_request() -> None:
    sdk_client = StubOpenAISDK({"id": "resp_456"})
    client = AIAgentClient(
        api_key="test-key",
        model="gpt-5.4",
        sdk_client=sdk_client,
    )

    client.create_response(
        input_text="Explain residual value impact.",
        model="gpt-4.1-mini",
    )

    assert sdk_client.responses.calls == [
        {
            "model": "gpt-4.1-mini",
            "input": "Explain residual value impact.",
        }
    ]
