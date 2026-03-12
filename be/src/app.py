import importlib
from typing import Annotated
from pydantic import BaseModel, Field

# global useages
from env import * # for simplicity , just Types and configueration getters
from observability import * # for simplicity , just Types and explicitit accessor for logger

# external dependencies
from external.db import get_db_client, MySQLClient
from services.predict_engine import predict_engine_service


fastapi = importlib.import_module("fastapi")
Depends = fastapi.Depends
FastAPI = fastapi.FastAPI

app = FastAPI(title="BE API", version="0.1.0")

PredictValue = float | int | str | bool | None

class PredictEngineProxyRequest(BaseModel):
    request_id: str | None = None
    feature_names: list[str] | None = None
    records: list[dict[str, PredictValue]] = Field(min_length=1)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Backend service is running",
        "app_env": settings.app.env,
        "service_name": settings.app.service_name,
        "db_host": settings.db.host,
        "db_name": settings.db.name,
        "predict_engine_target": settings.predict_engine.target,
    }


@app.get("/health")
def health(
    db_client: Annotated[MySQLClient, Depends(get_db_client)],
) -> dict[str, object]:
    db_health = db_client.health_summary()
    return {
        "status": "ok" if db_health["status"] == "available" else "degraded",
        "service": settings.app.service_name,
        "db": db_health,
        "predict_engine": predict_engine_service.connection_summary(),
    }


@app.get("/predict-engine/health")
def predict_engine_health() -> dict[str, object]:
    return predict_engine_service.health_summary()


@app.post("/predict-engine/predict")
def predict_engine_predict(payload: PredictEngineProxyRequest) -> dict[str, object]:
    prediction = predict_engine_service.predict(
        payload.records,
        feature_names=payload.feature_names,
        request_id=payload.request_id,
    )
    return prediction.as_dict()
