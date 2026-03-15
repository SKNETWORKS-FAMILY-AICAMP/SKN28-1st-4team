from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

# global useages
from env import * # for simplicity , just Types and configueration getters

# external dependencies
from external.db import get_db_client, MySQLClient
from services.predict_engine import PredictEngineService, get_predict_engine_service

settings = load_settings()

app = FastAPI(title="BE API", version="0.1.0")

PredictValue = float | int | str | bool | None

class PredictEnginePredictRequest(BaseModel):
    request_id: str | None = None
    record: dict[str, PredictValue] = Field(default_factory=dict)


class PredictEngineProjectionRequest(BaseModel):
    request_id: str | None = None
    base_record: dict[str, PredictValue] = Field(default_factory=dict)
    feature_name: str
    feature_values: list[PredictValue] = Field(min_length=1)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Backend service is running",
        "app_env": settings.app.env,
        "service_name": settings.app.service_name,
        "db_host": settings.db.host,
        "db_name": settings.db.name,
        "predict_engine_model_path": str(settings.predict_engine.model_path),
    }


@app.get("/health")
def health(
    db_client: Annotated[MySQLClient, Depends(get_db_client)],
    predict_engine_service: Annotated[
        PredictEngineService,
        Depends(get_predict_engine_service),
    ],
) -> dict[str, object]:
    db_health = db_client.health_summary()
    return {
        "status": "ok" if db_health["status"] == "available" else "degraded",
        "service": settings.app.service_name,
        "db": db_health,
        "predict_engine": predict_engine_service.health_summary(),
    }


@app.get("/predict-engine/health")
def predict_engine_health(
    predict_engine_service: Annotated[
        PredictEngineService,
        Depends(get_predict_engine_service),
    ],
) -> dict[str, object]:
    return predict_engine_service.health_summary()


@app.post("/predict-engine/predict")
def predict_engine_predict(
    payload: PredictEnginePredictRequest,
    predict_engine_service: Annotated[
        PredictEngineService,
        Depends(get_predict_engine_service),
    ],
) -> dict[str, object]:
    prediction = predict_engine_service.predict(
        payload.record,
        request_id=payload.request_id,
    )
    return prediction.as_dict()


@app.post("/predict-engine/project")
def predict_engine_project(
    payload: PredictEngineProjectionRequest,
    predict_engine_service: Annotated[
        PredictEngineService,
        Depends(get_predict_engine_service),
    ],
) -> dict[str, object]:
    projection = predict_engine_service.project(
        payload.base_record,
        request_id=payload.request_id,
        feature_name=payload.feature_name,
        feature_values=payload.feature_values,
    )
    return projection.as_dict()
