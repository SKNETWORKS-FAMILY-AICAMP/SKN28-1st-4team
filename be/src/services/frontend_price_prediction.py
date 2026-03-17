from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import lru_cache
import json
from pathlib import Path

from env.settings import load_predict_engine_settings
from external.predict_engine import (
    PredictScalar,
    get_major_category_from_tuple,
    get_size_score,
)

from .predict_engine import PredictEngineService, get_predict_engine_service


@dataclass(frozen=True)
class FrontendPricePredictionInput:
    brand_key: str
    brand_label: str
    model_name: str
    trim_name: str
    plate: str
    purchase_date: date
    is_used_purchase: bool
    mileage_km: int
    color: str
    transmission: str


@dataclass(frozen=True)
class FrontendPricePredictionPoint:
    label: str
    year_label: str
    price: int
    segment: str
    phase: str
    show_label: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "year_label": self.year_label,
            "price": self.price,
            "segment": self.segment,
            "phase": self.phase,
            "show_label": self.show_label,
        }


@dataclass(frozen=True)
class FrontendPricePredictionResult:
    current_price: int
    fair_price_min: int
    fair_price_max: int
    confidence: int
    suggestion: str
    chart_points: tuple[FrontendPricePredictionPoint, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "current_price": self.current_price,
            "fair_price_min": self.fair_price_min,
            "fair_price_max": self.fair_price_max,
            "confidence": self.confidence,
            "suggestion": self.suggestion,
            "chart_points": [point.as_dict() for point in self.chart_points],
        }


class FrontendPricePredictionService:
    def __init__(
        self,
        predict_engine_service: PredictEngineService,
        *,
        fair_price_margin_manwon: int | None = None,
    ) -> None:
        self._predict_engine_service = predict_engine_service
        self._fair_price_margin_manwon = fair_price_margin_manwon

    def predict(
        self,
        request: FrontendPricePredictionInput,
        *,
        request_id: str | None = None,
    ) -> FrontendPricePredictionResult:
        today = date.today()
        if request.purchase_date > today:
            raise ValueError("purchase_date cannot be in the future")
        if request.mileage_km < 0:
            raise ValueError("mileage_km must be non-negative")

        base_record = self._build_base_record(request)
        current_age_years = _calculate_vehicle_age_years(request.purchase_date, today)
        annual_mileage_km = request.mileage_km / max(current_age_years, 1.0)
        current_year = today.year

        current_price = self._predict_price(
            base_record,
            vehicle_age_years=current_age_years,
            mileage_km=float(request.mileage_km),
            request_id=request_id,
        )

        future_prices: list[int] = []
        chart_points = [
            FrontendPricePredictionPoint(
                label="현재",
                year_label=f"{current_year}년",
                price=current_price,
                segment="기준 시점",
                phase="current",
                show_label=True,
            ),
        ]

        for offset in range(1, 6):
            projected_age_years = current_age_years + offset
            projected_mileage_km = float(request.mileage_km) + (annual_mileage_km * offset)
            projected_price = self._predict_price(
                base_record,
                vehicle_age_years=projected_age_years,
                mileage_km=projected_mileage_km,
                request_id=request_id,
            )
            future_prices.append(projected_price)
            chart_points.append(
                FrontendPricePredictionPoint(
                    label=f"{offset}년 후",
                    year_label=f"{current_year + offset}년",
                    price=projected_price,
                    segment="연식·주행거리 반영" if offset <= 2 else "연식·주행거리 누적",
                    phase="future",
                    show_label=True,
                )
            )

        fair_span = self._resolve_fair_price_span(current_price)
        confidence = _estimate_confidence(
            current_age_years=current_age_years,
            annual_mileage_km=annual_mileage_km,
            color=request.color,
        )
        suggestion = _build_suggestion(
            current_price=current_price,
            future_prices=future_prices,
        )

        return FrontendPricePredictionResult(
            current_price=current_price,
            fair_price_min=max(current_price - fair_span, 0),
            fair_price_max=current_price + fair_span,
            confidence=confidence,
            suggestion=suggestion,
            chart_points=tuple(chart_points),
        )

    def _resolve_fair_price_span(self, current_price: int) -> int:
        if self._fair_price_margin_manwon is not None:
            return self._fair_price_margin_manwon
        return max(90, round(current_price * 0.05))

    def _build_base_record(
        self,
        request: FrontendPricePredictionInput,
    ) -> dict[str, PredictScalar]:
        brand_key = request.brand_key.strip()
        model_name = request.model_name.strip()
        trim_name = request.trim_name.strip()
        color = request.color.strip()
        if not brand_key or not model_name or not trim_name:
            raise ValueError("brand_key, model_name, and trim_name are required")
        if not color:
            raise ValueError("color is required")

        major_category = get_major_category_from_tuple(brand_key, model_name, trim_name)
        if major_category is None:
            raise ValueError(
                f"major_category not found for tuple: {brand_key} / {model_name} / {trim_name}"
            )

        size_score = get_size_score(brand_key, model_name, trim_name)
        if size_score is None:
            raise ValueError(
                f"size_score not found for tuple: {brand_key} / {model_name} / {trim_name}"
            )

        return {
            "brand": brand_key,
            "model_name": model_name,
            "trim_name": trim_name,
            "major_category": major_category,
            "size_score": float(size_score),
            "color": color,
        }

    def _predict_price(
        self,
        base_record: dict[str, PredictScalar],
        *,
        vehicle_age_years: float,
        mileage_km: float,
        request_id: str | None,
    ) -> int:
        prediction = self._predict_engine_service.predict(
            {
                **base_record,
                "vehicle_age_years": round(max(vehicle_age_years, 0.1), 2),
                "mileage_km": round(max(mileage_km, 0.0), 2),
            },
            request_id=request_id,
        )
        return int(round(prediction.predicted_price))


def _calculate_vehicle_age_years(purchase_date: date, today: date) -> float:
    age_days = max((today - purchase_date).days, 0)
    return max(round(age_days / 365.25, 2), 0.1)


def _estimate_confidence(
    *,
    current_age_years: float,
    annual_mileage_km: float,
    color: str,
) -> int:
    confidence = 78
    if current_age_years < 1.0:
        confidence -= 6
    if annual_mileage_km > 25000:
        confidence -= 5
    if not color.strip():
        confidence -= 4
    return max(60, min(confidence, 89))


def _build_suggestion(*, current_price: int, future_prices: list[int]) -> str:
    if len(future_prices) < 3:
        return "현재 입력값 기준의 단순 가격 추정입니다."

    third_year_price = future_prices[2]
    if third_year_price < current_price * 0.65:
        return "구매일 기준 경과 연수와 추정 연간 주행거리를 반영하면 향후 3년 내 감가 폭이 큰 편입니다."
    if future_prices[-1] < current_price * 0.8:
        return "향후 5년 동안 점진적인 감가 흐름이 예상되며, 단기 급락보다는 완만한 하락에 가깝습니다."
    return "현재 입력값 기준으로는 비교적 완만한 감가 흐름이 예상됩니다."


def _load_fair_price_margin_from_metrics() -> int | None:
    config = load_predict_engine_settings()
    metrics_path = Path(config.model_path).with_name("metrics.json")
    if not metrics_path.is_file():
        return None

    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    aggregate_metrics = payload.get("aggregate_metrics")
    if not isinstance(aggregate_metrics, dict):
        return None

    mae = aggregate_metrics.get("mae_price_manwon")
    if not isinstance(mae, (int, float)):
        return None

    return max(int(round(mae)), 90)


@lru_cache(maxsize=1)
def get_frontend_price_prediction_service() -> FrontendPricePredictionService:
    return FrontendPricePredictionService(
        predict_engine_service=get_predict_engine_service(),
        fair_price_margin_manwon=_load_fair_price_margin_from_metrics(),
    )
