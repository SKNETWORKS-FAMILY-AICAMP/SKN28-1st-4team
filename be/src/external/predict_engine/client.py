from collections.abc import Mapping, Sequence
from typing import Self

import grpc
from google.protobuf import struct_pb2

import predict_engine_pb2 as pb2
import predict_engine_pb2_grpc as pb2_grpc

from env.settings import Settings, load_settings
from .types import PredictEngineHealth, PredictEnginePrediction, PredictEngineTensor, PredictScalar


class PredictEngineClient:

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._channel = grpc.insecure_channel(self._settings.predict_engine.target)
        self._stub = pb2_grpc.PredictEngineStub(self._channel)

    def connection_summary(self) -> dict[str, object]:
        return {
            "target": self._settings.predict_engine.target,
            "timeout_seconds": self._settings.predict_engine.timeout_seconds,
        }

    def close(self) -> None:
        self._channel.close()

    def health(self) -> PredictEngineHealth:
        response = self._stub.Health(
            pb2.HealthRequest(),
            timeout=self._settings.predict_engine.timeout_seconds,
        )
        return PredictEngineHealth(
            status=response.status,
            service_name=response.service_name,
            model_path=response.model_path,
            model_exists=response.model_exists,
            model_loaded=response.model_loaded,
            model_input_name=response.model_input_name,
            model_output_names=tuple(response.model_output_names),
            model_error=response.model_error or None,
        )

    def predict(
        self,
        records: Sequence[Mapping[str, PredictScalar]],
        *,
        feature_names: Sequence[str] | None = None,
        request_id: str | None = None,
    ) -> PredictEnginePrediction:
        request = pb2.PredictRequest(
            request_id=request_id or "",
            feature_names=self._resolve_feature_names(records, feature_names),
            rows=self._build_rows(records, feature_names),
        )
        response = self._stub.Predict(
            request,
            timeout=self._settings.predict_engine.timeout_seconds,
        )
        return PredictEnginePrediction(
            request_id=response.request_id,
            outputs=tuple(self._parse_output(output) for output in response.outputs),
        )

    @staticmethod
    def _resolve_feature_names(
        records: Sequence[Mapping[str, PredictScalar]],
        feature_names: Sequence[str] | None,
    ) -> list[str]:
        if feature_names is not None:
            names = [name for name in feature_names if name]
            if not names:
                raise ValueError("feature_names must not be empty when provided")
            return names

        if not records:
            raise ValueError("records must contain at least one item")

        names = list(records[0].keys())
        if not names:
            raise ValueError("records must contain at least one feature")
        return names

    def _build_rows(
        self,
        records: Sequence[Mapping[str, PredictScalar]],
        feature_names: Sequence[str] | None,
    ) -> list[pb2.FeatureRow]:
        names = self._resolve_feature_names(records, feature_names)
        rows: list[pb2.FeatureRow] = []
        for row_index, record in enumerate(records):
            missing = [name for name in names if name not in record]
            if missing:
                raise ValueError(
                    f"record at index {row_index} is missing required features: {missing}"
                )
            rows.append(
                pb2.FeatureRow(
                    values=[self._to_feature_value(record[name]) for name in names]
                )
            )
        return rows

    @staticmethod
    def _to_feature_value(value: PredictScalar) -> pb2.FeatureValue:
        if value is None:
            return pb2.FeatureValue(null_value=struct_pb2.NULL_VALUE)
        if isinstance(value, bool):
            return pb2.FeatureValue(bool_value=value)
        if isinstance(value, int):
            return pb2.FeatureValue(int_value=value)
        if isinstance(value, float):
            return pb2.FeatureValue(double_value=value)
        if isinstance(value, str):
            return pb2.FeatureValue(string_value=value)
        raise TypeError(f"unsupported feature value type: {type(value)!r}")

    @staticmethod
    def _parse_output(output: pb2.ModelOutput) -> PredictEngineTensor:
        tensor = output.tensor
        values: tuple[float | int | str | bool, ...]

        if tensor.bool_values:
            values = tuple(tensor.bool_values)
        elif tensor.string_values:
            values = tuple(tensor.string_values)
        elif tensor.int64_values:
            values = tuple(tensor.int64_values)
        else:
            values = tuple(tensor.double_values)

        return PredictEngineTensor(
            name=output.name,
            dtype=tensor.dtype,
            shape=tuple(tensor.shape),
            values=values,
        )

    @classmethod
    def get_client(cls) -> Self:
        return cls(settings=load_settings())


predict_engine_client = PredictEngineClient.get_client()
