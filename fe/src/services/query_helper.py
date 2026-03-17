from typing import Any

import httpx


class QueryHelper:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def get_json(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request_json("GET", path, params=params)

    def post_json(self, path: str, *, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_json("POST", path, json_payload=payload)

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self._base_url:
            raise ValueError("FE_QUERY_BASE_URL must be configured for non-development environments.")

        with httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = client.request(method, path, params=params, json=json_payload)
            response.raise_for_status()
            payload = response.json()

        if not isinstance(payload, dict):
            raise TypeError(f"Expected JSON object from query layer, got {type(payload).__name__}.")
        return payload
