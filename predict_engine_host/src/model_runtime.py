from collections.abc import Sequence
from dataclasses import dataclass
from threading import Lock

import numpy as np
import onnxruntime as ort

import predict_engine_pb2 as pb2
from settings import Settings, settings


@dataclass(frozen=True)
class ModelHealth:
    model_path: str
    model_exists: bool
    model_loaded: bool
    model_input_name: str
    model_output_names: tuple[str, ...]
    model_error: str | None = None


class PredictEngineRuntime:

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._session: ort.InferenceSession | None = None
        self._lock = Lock()

    def health(self) -> ModelHealth:
        path = self._settings.model.path
        health = ModelHealth(
            model_path=str(path),
            model_exists=path.is_file(),
            model_loaded=False,
            model_input_name=self._settings.model.input_name or "",
            model_output_names=self._settings.model.output_names,
        )

        if not path.is_file():
            return ModelHealth(
                model_path=health.model_path,
                model_exists=health.model_exists,
                model_loaded=health.model_loaded,
                model_input_name=health.model_input_name,
                model_output_names=health.model_output_names,
                model_error=f"model file not found at {path}",
            )

        try:
            session = self._get_session()
        except Exception as exc:
            return ModelHealth(
                model_path=health.model_path,
                model_exists=health.model_exists,
                model_loaded=health.model_loaded,
                model_input_name=health.model_input_name,
                model_output_names=health.model_output_names,
                model_error=str(exc),
            )

        return ModelHealth(
            model_path=str(path),
            model_exists=True,
            model_loaded=True,
            model_input_name=self._input_name(session),
            model_output_names=self._output_names(session),
        )

    def predict(
        self,
        *,
        request_id: str,
        feature_names: Sequence[str],
        rows: Sequence[pb2.FeatureRow],
    ) -> pb2.PredictResponse:
        session = self._get_session()
        resolved_feature_names = self._resolve_feature_names(feature_names)
        input_metadata = session.get_inputs()[0]
        input_tensor = self._build_input_tensor(
            resolved_feature_names,
            rows,
            onnx_input_type=input_metadata.type,
            onnx_input_shape=input_metadata.shape,
        )
        outputs = session.run(
            list(self._output_names(session)) or None,
            {self._input_name(session): input_tensor},
        )
        output_names = self._output_names(session)
        return pb2.PredictResponse(
            request_id=request_id,
            outputs=[
                pb2.ModelOutput(name=name, tensor=self._to_tensor_proto(value))
                for name, value in zip(output_names, outputs, strict=True)
            ],
        )

    def available_providers(self) -> list[str]:
        return ort.get_available_providers()

    def _get_session(self) -> ort.InferenceSession:
        if self._session is not None:
            return self._session

        with self._lock:
            if self._session is not None:
                return self._session

            model_path = self._settings.model.path
            if not model_path.is_file():
                raise FileNotFoundError(f"model file not found at {model_path}")

            providers = list(self._settings.model.providers) or self.available_providers()
            self._session = ort.InferenceSession(str(model_path), providers=providers)
            return self._session

    def _input_name(self, session: ort.InferenceSession) -> str:
        configured_name = self._settings.model.input_name
        if configured_name:
            return configured_name
        return session.get_inputs()[0].name

    def _output_names(self, session: ort.InferenceSession) -> tuple[str, ...]:
        if self._settings.model.output_names:
            return self._settings.model.output_names
        return tuple(output.name for output in session.get_outputs())

    def _resolve_feature_names(self, feature_names: Sequence[str]) -> tuple[str, ...]:
        if feature_names:
            return tuple(feature_names)
        if self._settings.model.feature_names:
            return self._settings.model.feature_names
        raise ValueError(
            "feature_names are required until the ONNX CatBoost input schema is finalized"
        )

    def _build_input_tensor(
        self,
        feature_names: Sequence[str],
        rows: Sequence[pb2.FeatureRow],
        *,
        onnx_input_type: str,
        onnx_input_shape: Sequence[object],
    ) -> np.ndarray:
        if not rows:
            raise ValueError("rows must contain at least one record")

        dtype = self._numpy_dtype_for_input(onnx_input_type)
        matrix: list[list[float | int | bool]] = []
        for row_index, row in enumerate(rows):
            if len(row.values) != len(feature_names):
                raise ValueError(
                    "row length does not match feature_names length "
                    f"for row {row_index}: expected {len(feature_names)}, got {len(row.values)}"
                )
            matrix.append(
                [
                    self._coerce_feature_value(
                        value,
                        row_index=row_index,
                        column_index=column_index,
                        feature_name=feature_names[column_index],
                    )
                    for column_index, value in enumerate(row.values)
                ]
            )

        tensor = np.asarray(matrix, dtype=dtype)
        expected_rank = len(onnx_input_shape)
        expected_feature_count = onnx_input_shape[-1] if onnx_input_shape else None
        if isinstance(expected_feature_count, int) and expected_feature_count != len(feature_names):
            raise ValueError(
                "feature_names length does not match the ONNX input width: "
                f"expected {expected_feature_count}, got {len(feature_names)}"
            )
        if expected_rank == 1:
            if tensor.shape[0] != 1:
                raise ValueError(
                    "model expects a single 1D record, but multiple rows were provided"
                )
            return tensor[0]
        return tensor

    @staticmethod
    def _numpy_dtype_for_input(onnx_input_type: str) -> np.dtype:
        mapping = {
            "tensor(float)": np.float32,
            "tensor(double)": np.float64,
            "tensor(int32)": np.int32,
            "tensor(int64)": np.int64,
            "tensor(bool)": np.bool_,
        }
        try:
            return np.dtype(mapping[onnx_input_type])
        except KeyError as exc:
            raise ValueError(
                "only numeric/bool tensor inputs are currently supported for ONNX inference; "
                f"got {onnx_input_type!r}"
            ) from exc

    @staticmethod
    def _coerce_feature_value(
        value: pb2.FeatureValue,
        *,
        row_index: int,
        column_index: int,
        feature_name: str,
    ) -> float | int | bool:
        kind = value.WhichOneof("kind")
        if kind == "double_value":
            return value.double_value
        if kind == "int_value":
            return value.int_value
        if kind == "bool_value":
            return value.bool_value
        if kind == "null_value":
            return np.nan
        if kind == "string_value":
            try:
                return float(value.string_value)
            except ValueError as exc:
                raise ValueError(
                    "string features are not yet mapped to the ONNX tensor input; "
                    f"row={row_index}, column={column_index}, feature={feature_name!r}, "
                    f"value={value.string_value!r}"
                ) from exc
        raise ValueError(
            "unsupported feature value received for "
            f"row={row_index}, column={column_index}, feature={feature_name!r}"
        )

    @staticmethod
    def _to_tensor_proto(value: object) -> pb2.Tensor:
        array = np.asarray(value)
        shape = list(array.shape)
        dtype = str(array.dtype)

        if array.dtype.kind == "b":
            return pb2.Tensor(
                dtype=dtype,
                shape=shape,
                bool_values=array.astype(np.bool_).ravel().tolist(),
            )
        if array.dtype.kind in {"i", "u"}:
            return pb2.Tensor(
                dtype=dtype,
                shape=shape,
                int64_values=array.astype(np.int64).ravel().tolist(),
            )
        if array.dtype.kind in {"U", "S", "O"}:
            return pb2.Tensor(
                dtype=dtype,
                shape=shape,
                string_values=[str(item) for item in array.ravel().tolist()],
            )
        return pb2.Tensor(
            dtype=dtype,
            shape=shape,
            double_values=array.astype(np.float64).ravel().tolist(),
        )


predict_engine_runtime = PredictEngineRuntime(settings=settings)
