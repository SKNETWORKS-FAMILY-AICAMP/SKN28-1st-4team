from collections.abc import Mapping, Sequence
from pathlib import Path
from threading import Lock
from typing import Self

from .feature_vectorizer import (
    FeatureTransformer,
    PredictEngineFeatureVectorizer,
)
from .model_runtime import PredictEngineRuntime
from .types import PredictEngineHealth, PredictEnginePrediction, PredictScalar


class PredictEngineClient:
    def __init__(
        self,
        *,
        model_path: Path,
        feature_manifest_path: Path,
        runtime: PredictEngineRuntime | None = None,
        transformers: Sequence[FeatureTransformer] | None = None,
    ) -> None:
        self._model_path = model_path
        self._feature_manifest_path = feature_manifest_path
        self._runtime = runtime or PredictEngineRuntime(self._model_path)
        self._transformers = tuple(transformers or ())
        self._feature_vectorizer: PredictEngineFeatureVectorizer | None = None
        self._feature_vectorizer_lock = Lock()

    @classmethod
    def from_paths(
        cls,
        *,
        model_path: Path,
        feature_manifest_path: Path,
        transformers: Sequence[FeatureTransformer] | None = None,
    ) -> Self:
        return cls(
            model_path=model_path,
            feature_manifest_path=feature_manifest_path,
            transformers=transformers,
        )

    def connection_summary(self) -> dict[str, object]:
        return {
            "mode": "local_cbm",
            "model_path": str(self._model_path),
            "feature_manifest_path": str(self._feature_manifest_path),
        }

    def health(self) -> PredictEngineHealth:
        manifest_exists = self._feature_manifest_path.is_file()
        manifest = None
        manifest_error = None
        try:
            manifest = self._get_feature_vectorizer().manifest
        except Exception as exc:
            manifest_error = str(exc)

        model_exists = self._runtime.model_exists()
        model_loaded = False
        model_error = None
        if model_exists:
            try:
                self._runtime.get_model()
                model_loaded = True
            except Exception as exc:
                model_error = str(exc)
        else:
            model_error = f"predict engine model not found at {self._runtime.model_path}"

        status = "available" if manifest is not None and model_loaded else "unavailable"
        return PredictEngineHealth(
            status=status,
            mode="local_cbm",
            model_path=str(self._runtime.model_path),
            model_exists=model_exists,
            model_loaded=model_loaded,
            feature_manifest_path=str(self._feature_manifest_path),
            feature_manifest_exists=manifest_exists,
            target_column=None if manifest is None else manifest.target_column,
            feature_columns=() if manifest is None else manifest.feature_columns,
            categorical_columns=() if manifest is None else manifest.categorical_columns,
            model_error=model_error,
            manifest_error=manifest_error,
        )

    def predict(
        self,
        record: Mapping[str, PredictScalar] | None = None,
        *,
        request_id: str | None = None,
        **kwargs: PredictScalar,
    ) -> PredictEnginePrediction:
        feature_vectorizer = self._get_feature_vectorizer()
        feature_vector = feature_vectorizer.vectorize(record, **kwargs)
        predicted_price = self._runtime.predict(feature_vector)
        return PredictEnginePrediction(
            request_id=request_id or "",
            predicted_price=predicted_price,
            feature_columns=feature_vector.feature_names,
        )

    def _get_feature_vectorizer(self) -> PredictEngineFeatureVectorizer:
        if self._feature_vectorizer is not None:
            return self._feature_vectorizer

        with self._feature_vectorizer_lock:
            if self._feature_vectorizer is not None:
                return self._feature_vectorizer

            self._feature_vectorizer = PredictEngineFeatureVectorizer.from_manifest_path(
                self._feature_manifest_path,
                transformers=self._transformers,
            )
            return self._feature_vectorizer
