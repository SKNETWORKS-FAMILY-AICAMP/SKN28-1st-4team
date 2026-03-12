from .settings import (
    ApplicationSettings,
    DatabaseSettings,
    PredictEngineSettings,
    Settings,
    load_application_settings,
    load_database_settings,
    load_predict_engine_settings,
    load_settings,
)

settings: Settings = load_settings()
