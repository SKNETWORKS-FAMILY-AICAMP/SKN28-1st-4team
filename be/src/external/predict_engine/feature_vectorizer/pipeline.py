from collections.abc import Mapping, Sequence
import json
from pathlib import Path

from ..types import PredictEngineManifest, PredictScalar
from ..vector_models import PredictEngineFeatureVector
from .transformers import FeatureTransformer


def load_feature_manifest(path: Path) -> PredictEngineManifest:
    if not path.is_file():
        raise FileNotFoundError(f"feature manifest not found at {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    feature_columns = tuple(payload.get("feature_columns", []))
    categorical_columns = tuple(payload.get("categorical_columns", []))
    if not feature_columns:
        raise ValueError("feature manifest must contain non-empty feature_columns")

    return PredictEngineManifest(
        target_column=payload.get("target_column"),
        feature_columns=feature_columns,
        categorical_columns=categorical_columns,
    )


class PredictEngineFeatureVectorizer:
    def __init__(
        self,
        manifest: PredictEngineManifest,
        *,
        transformers: Sequence[FeatureTransformer] | None = None,
    ) -> None:
        self._manifest = manifest
        self._transformers = list(transformers or [])

    @classmethod
    def from_manifest_path(
        cls,
        path: Path,
        *,
        transformers: Sequence[FeatureTransformer] | None = None,
    ) -> "PredictEngineFeatureVectorizer":
        return cls(load_feature_manifest(path), transformers=transformers)

    @property
    def manifest(self) -> PredictEngineManifest:
        return self._manifest

    def add_transformer(self, transformer: FeatureTransformer) -> None:
        self._transformers.append(transformer)

    def vectorize(
        self,
        record: Mapping[str, PredictScalar] | None = None,
        **kwargs: PredictScalar,
    ) -> PredictEngineFeatureVector:
        resolved = self._resolve_record(record, kwargs)
        transformed = self._apply_pipeline(resolved)
        validated = self._ensure_feature_columns(transformed)
        ordered_items = tuple(
            (column, validated[column]) for column in self._manifest.feature_columns
        )
        return PredictEngineFeatureVector(ordered_items=ordered_items)

    def _apply_pipeline(
        self,
        record: dict[str, PredictScalar],
    ) -> dict[str, PredictScalar]:
        current = dict(record)
        for transformer in self._transformers:
            current = transformer(current)
        return current

    def _resolve_record(
        self,
        record: Mapping[str, PredictScalar] | None,
        kwargs: dict[str, PredictScalar],
    ) -> dict[str, PredictScalar]:
        resolved = {} if record is None else dict(record)
        if kwargs:
            resolved.update(kwargs)

        return resolved

    def _ensure_feature_columns(
        self,
        record: dict[str, PredictScalar],
    ) -> dict[str, PredictScalar]:
        missing = [
            column
            for column in self._manifest.feature_columns
            if column not in record
        ]
        if missing:
            raise ValueError(f"missing required predict-engine features: {missing}")
        
        return record
