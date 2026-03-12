from collections.abc import Mapping, Sequence

import grpc
from fastapi import HTTPException

from external.predict_engine.client import PredictEngineClient, predict_engine_client
from external.predict_engine.types import PredictEnginePrediction, PredictScalar


class PredictEngineService:

    def __init__(self, client: PredictEngineClient) -> None:
        self._client = client

    def connection_summary(self) -> dict[str, object]:
        return self._client.connection_summary()

    def health_summary(self) -> dict[str, object]:
        try:
            health = self._client.health()
        except grpc.RpcError as exc:
            return {
                **self._client.connection_summary(),
                "status": "unavailable",
                "error": self._rpc_error_message(exc),
            }
        return {
            **self._client.connection_summary(),
            **health.as_dict(),
        }

    def predict(
        self,
        records: Sequence[Mapping[str, PredictScalar]],
        *,
        feature_names: Sequence[str] | None = None,
        request_id: str | None = None,
    ) -> PredictEnginePrediction:
        try:
            return self._client.predict(
                records,
                feature_names=feature_names,
                request_id=request_id,
            )
        except grpc.RpcError as exc:
            raise HTTPException(
                status_code=self._http_status_for_rpc(exc),
                detail=self._rpc_error_message(exc),
            ) from exc

    @staticmethod
    def _http_status_for_rpc(exc: grpc.RpcError) -> int:
        mapping = {
            grpc.StatusCode.INVALID_ARGUMENT: 400,
            grpc.StatusCode.NOT_FOUND: 404,
            grpc.StatusCode.FAILED_PRECONDITION: 412,
            grpc.StatusCode.DEADLINE_EXCEEDED: 504,
            grpc.StatusCode.UNAVAILABLE: 503,
        }
        return mapping.get(exc.code(), 502)

    @staticmethod
    def _rpc_error_message(exc: grpc.RpcError) -> str:
        details = exc.details()
        if details:
            return details
        return f"predict engine call failed with status {exc.code().name}"


predict_engine_service = PredictEngineService(client=predict_engine_client)
