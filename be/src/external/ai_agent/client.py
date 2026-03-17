from __future__ import annotations

from typing import Any, Self

from openai import OpenAI

from env.settings import AIAgentSettings


class AIAgentClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None = None,
        site_url: str | None = None,
        app_name: str | None = None,
        organization: str | None = None,
        project: str | None = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        sdk_client: OpenAI | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._site_url = site_url
        self._app_name = app_name
        self._organization = organization
        self._project = project
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        default_headers = {
            key: value
            for key, value in {
                "HTTP-Referer": site_url,
                "X-Title": app_name,
            }.items()
            if value
        }
        self._sdk_client = sdk_client or OpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers=default_headers,
            organization=organization,
            project=project,
            timeout=timeout_seconds,
            max_retries=max_retries,
        )

    @classmethod
    def from_config(cls, config: AIAgentSettings) -> Self:
        if config.api_key is None or config.api_key.strip() == "":
            raise ValueError("AI_AGENT_API_KEY is required to create the AI agent client")

        return cls(
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url,
            site_url=config.site_url,
            app_name=config.app_name,
            organization=config.organization,
            project=config.project,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
        )

    @property
    def sdk(self) -> OpenAI:
        return self._sdk_client

    def connection_summary(self) -> dict[str, object]:
        return {
            "provider": "openai",
            "model": self._model,
            "base_url": self._base_url,
            "site_url": self._site_url,
            "app_name": self._app_name,
            "organization": self._organization,
            "project": self._project,
            "timeout_seconds": self._timeout_seconds,
            "max_retries": self._max_retries,
            "api_key_configured": self._api_key.strip() != "",
        }

    def create_response(
        self,
        *,
        input_text: str,
        instructions: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> Any:
        request: dict[str, Any] = {
            "model": model or self._model,
            "input": input_text,
        }
        if instructions is not None:
            request["instructions"] = instructions
        request.update(kwargs)
        return self._sdk_client.responses.create(**request)
