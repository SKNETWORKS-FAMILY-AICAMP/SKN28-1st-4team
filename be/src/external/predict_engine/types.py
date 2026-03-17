from dataclasses import dataclass
from datetime import datetime


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
    projected_at: datetime
    predicted_price: float

    def as_dict(self) -> dict[str, object]:
        return {
            "projected_at": self.projected_at.isoformat(),
            "predicted_price": self.predicted_price,
        }


@dataclass(frozen=True)
class PredictEngineProjection:
    request_id: str
    time_feature_name: str
    start_datetime: datetime
    interval_months: int
    feature_columns: tuple[str, ...]
    points: tuple[PredictEngineProjectionPoint, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "time_feature_name": self.time_feature_name,
            "start_datetime": self.start_datetime.isoformat(),
            "interval_months": self.interval_months,
            "feature_columns": list(self.feature_columns),
            "points": [point.as_dict() for point in self.points],
        }
