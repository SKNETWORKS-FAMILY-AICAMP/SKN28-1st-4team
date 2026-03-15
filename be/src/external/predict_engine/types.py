from dataclasses import dataclass


PredictScalar = float | int | str | bool | None


@dataclass(frozen=True)
class PredictEngineManifest:
    target_column: str | None
    feature_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "target_column": self.target_column,
            "feature_columns": list(self.feature_columns),
            "categorical_columns": list(self.categorical_columns),
        }


@dataclass(frozen=True)
class PredictEngineHealth:
    status: str
    mode: str
    model_path: str
    model_exists: bool
    model_loaded: bool
    feature_manifest_path: str
    feature_manifest_exists: bool
    target_column: str | None
    feature_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]
    model_error: str | None = None
    manifest_error: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "mode": self.mode,
            "model_path": self.model_path,
            "model_exists": self.model_exists,
            "model_loaded": self.model_loaded,
            "feature_manifest_path": self.feature_manifest_path,
            "feature_manifest_exists": self.feature_manifest_exists,
            "target_column": self.target_column,
            "feature_columns": list(self.feature_columns),
            "categorical_columns": list(self.categorical_columns),
            "model_error": self.model_error,
            "manifest_error": self.manifest_error,
        }


@dataclass(frozen=True)
class PredictEnginePrediction:
    request_id: str
    predicted_price: float
    feature_columns: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "predicted_price": self.predicted_price,
            "feature_columns": list(self.feature_columns),
        }


@dataclass(frozen=True)
class PredictEngineProjectionPoint:
    label: str
    feature_name: str
    feature_value: PredictScalar
    predicted_price: float

    def as_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "feature_name": self.feature_name,
            "feature_value": self.feature_value,
            "predicted_price": self.predicted_price,
        }


@dataclass(frozen=True)
class PredictEngineProjection:
    request_id: str
    feature_name: str
    feature_columns: tuple[str, ...]
    points: tuple[PredictEngineProjectionPoint, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "feature_name": self.feature_name,
            "feature_columns": list(self.feature_columns),
            "points": [point.as_dict() for point in self.points],
        }
