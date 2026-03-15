from functools import lru_cache

from env.settings import PredictEngineSettings, load_predict_engine_settings

from .client import PredictEngineClient
from .feature_vectorizer import build_default_transformers


def _create_predict_engine_client(
    config: PredictEngineSettings,
) -> PredictEngineClient:
    return PredictEngineClient.from_paths(
        model_path=config.model_path,
        feature_manifest_path=config.feature_manifest_path,
        transformers=build_default_transformers(),
    )


@lru_cache(maxsize=1)
def _get_predict_engine_settings() -> PredictEngineSettings:
    return load_predict_engine_settings()


@lru_cache(maxsize=1)
def get_predict_engine_client() -> PredictEngineClient:
    return _create_predict_engine_client(_get_predict_engine_settings())


def _clear_predict_engine_dependency_cache() -> None:
    get_predict_engine_client.cache_clear()
    _get_predict_engine_settings.cache_clear()
