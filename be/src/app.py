from datetime import date
from typing import Annotated
from urllib.parse import quote

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

# global useages
from env import * # for simplicity , just Types and configueration getters

# external dependencies
from external.db import get_db_client, MySQLClient
from services.predict_engine import PredictEngineService, get_predict_engine_service
from services.frontend_price_prediction import (
    FrontendPricePredictionInput,
    FrontendPricePredictionService,
    get_frontend_price_prediction_service,
)
from services.frontend_price_factors import (
    FrontendPriceFactorService,
    get_frontend_price_factor_service,
)
from services.vehicle_model_image import (
    VehicleModelImagePageService,
    VehicleModelImageService,
    get_vehicle_model_image_page_service,
    get_vehicle_model_image_service,
)

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


class FrontendModelImagePageRequest(BaseModel):
    brand_key: str = Field(min_length=1)
    brand_label: str = Field(min_length=1)
    model_names: list[str] = Field(min_length=1)


class FrontendPricePredictionRequest(BaseModel):
    request_id: str | None = None
    brand_key: str = Field(min_length=1)
    brand_label: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    trim_name: str = Field(min_length=1)
    plate: str = ""
    purchase_date: date
    is_used_purchase: bool = False
    mileage_km: int = Field(ge=0)
    color: str = Field(min_length=1)
    transmission: str = ""


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


@app.get("/vehicle-model-image")
def get_vehicle_model_image(
    brand_key: Annotated[str, Query(min_length=1)],
    model_name: Annotated[str, Query(min_length=1)],
    vehicle_model_image_service: Annotated[
        VehicleModelImageService,
        Depends(get_vehicle_model_image_service),
    ],
) -> Response:
    try:
        image = vehicle_model_image_service.get_image(brand_key, model_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if image is None:
        raise HTTPException(status_code=404, detail="vehicle model image not found")

    filename = quote(image.source_filename)
    return Response(
        content=image.payload,
        media_type=image.mime_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{filename}",
        },
    )


@app.post("/api/v1/frontend/model-images")
def get_frontend_model_images(
    payload: FrontendModelImagePageRequest,
    request: Request,
    vehicle_model_image_page_service: Annotated[
        VehicleModelImagePageService,
        Depends(get_vehicle_model_image_page_service),
    ],
) -> dict[str, object]:
    try:
        models = vehicle_model_image_page_service.get_model_cards(
            brand_key=payload.brand_key,
            brand_label=payload.brand_label,
            model_names=payload.model_names,
            image_url_builder=lambda brand_key, model_name: str(
                request.url_for("get_vehicle_model_image")
                .include_query_params(brand_key=brand_key, model_name=model_name)
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "brand_key": payload.brand_key,
        "brand_label": payload.brand_label,
        "models": [
            {
                "id": model.id,
                "brand": model.brand,
                "model": model.model,
                "image_src": model.image_src,
            }
            for model in models
        ],
    }


@app.post("/api/v1/frontend/price-prediction")
def get_frontend_price_prediction(
    payload: FrontendPricePredictionRequest,
    frontend_price_prediction_service: Annotated[
        FrontendPricePredictionService,
        Depends(get_frontend_price_prediction_service),
    ],
) -> dict[str, object]:
    try:
        result = frontend_price_prediction_service.predict(
            FrontendPricePredictionInput(
                brand_key=payload.brand_key,
                brand_label=payload.brand_label,
                model_name=payload.model_name,
                trim_name=payload.trim_name,
                plate=payload.plate,
                purchase_date=payload.purchase_date,
                is_used_purchase=payload.is_used_purchase,
                mileage_km=payload.mileage_km,
                color=payload.color,
                transmission=payload.transmission,
            ),
            request_id=payload.request_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result.as_dict()


@app.post("/api/v1/frontend/price-factors")
def get_frontend_price_factors(
    payload: FrontendPricePredictionRequest,
    frontend_price_factor_service: Annotated[
        FrontendPriceFactorService,
        Depends(get_frontend_price_factor_service),
    ],
) -> dict[str, object]:
    result = frontend_price_factor_service.analyze(
        FrontendPricePredictionInput(
            brand_key=payload.brand_key,
            brand_label=payload.brand_label,
            model_name=payload.model_name,
            trim_name=payload.trim_name,
            plate=payload.plate,
            purchase_date=payload.purchase_date,
            is_used_purchase=payload.is_used_purchase,
            mileage_km=payload.mileage_km,
            color=payload.color,
            transmission=payload.transmission,
        )
    )
    return result.as_dict()
