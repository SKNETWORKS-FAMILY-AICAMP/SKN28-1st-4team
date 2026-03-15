from pathlib import Path
from threading import Lock

from catboost import CatBoostRegressor
import pandas as pd

from ..vector_models import PredictEngineFeatureVector


class PredictEngineRuntime:
    def __init__(self, model_path: Path) -> None:
        self._model_path = model_path
        self._model: CatBoostRegressor | None = None
        self._lock = Lock()

    @property
    def model_path(self) -> Path:
        return self._model_path

    def model_exists(self) -> bool:
        return self._model_path.is_file()

    def is_loaded(self) -> bool:
        return self._model is not None

    def get_model(self) -> CatBoostRegressor:
        if self._model is not None:
            return self._model

        with self._lock:
            if self._model is not None:
                return self._model

            if not self._model_path.is_file():
                raise FileNotFoundError(
                    f"predict engine model not found at {self._model_path}"
                )

            model = CatBoostRegressor()
            model.load_model(str(self._model_path), format="cbm")
            self._model = model
            return self._model

    def predict(
        self,
        feature_vector: PredictEngineFeatureVector,
    ) -> float:
        frame = pd.DataFrame(
            [feature_vector.as_dict()],
            columns=list(feature_vector.feature_names),
        )

        raw_predictions = self.get_model().predict(frame)
        if hasattr(raw_predictions, "tolist"):
            raw_predictions = raw_predictions.tolist()
        if not isinstance(raw_predictions, list):
            raw_predictions = [raw_predictions]
        return float(raw_predictions[0])
