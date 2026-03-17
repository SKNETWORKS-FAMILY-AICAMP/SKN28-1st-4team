from datetime import date
from typing import Any

from mock_data.vehicle_catalog import (
    ACCIDENT_DETAIL_FIELDS,
    ACCIDENT_HISTORY_OPTIONS,
    BRAND_KEY_BY_LABEL,
    CATALOG,
    COLOR_HISTORY_OPTIONS,
    COLOR_OPTIONS,
    COLOR_TONE,
    DOCUMENT_OPTIONS,
    FUEL_OPTIONS,
    MAJOR_OPTION_OPTIONS,
    METER_CONDITION_OPTIONS,
    MODEL_BASE_PRICE,
    RECALL_OPTIONS,
    SIMPLE_REPAIR_OPTIONS,
    SPECIAL_HISTORY_OPTIONS,
    TRANSMISSION_OPTIONS,
    USAGE_CHANGE_OPTIONS,
    VIN_CONDITION_OPTIONS,
    WARRANTY_OPTIONS,
    _CANDIDATE_LIBRARY,
    build_model_options_for_page,
)
from models.query import PricePredictionRequestDTO


def build_mock_catalog_payload() -> dict[str, Any]:
    return {
        "catalog": {
            brand: {model: list(years) for model, years in models.items()}
            for brand, models in CATALOG.items()
        },
        "brand_keys_by_label": dict(BRAND_KEY_BY_LABEL),
        "candidates_by_model": {
            model: [
                {
                    "id": candidate.id,
                    "title": candidate.title,
                    "year": candidate.year,
                    "trim": candidate.trim,
                    "mileage": candidate.mileage,
                    "fuel": candidate.fuel,
                    "color": candidate.color,
                }
                for candidate in candidates
            ]
            for model, candidates in _CANDIDATE_LIBRARY.items()
        },
        "base_prices_by_model": dict(MODEL_BASE_PRICE),
        "color_tones": dict(COLOR_TONE),
        "options": {
            "colors": list(COLOR_OPTIONS),
            "transmissions": list(TRANSMISSION_OPTIONS),
            "fuels": list(FUEL_OPTIONS),
            "warranty_types": list(WARRANTY_OPTIONS),
            "usage_changes": list(USAGE_CHANGE_OPTIONS),
            "recall_statuses": list(RECALL_OPTIONS),
            "vin_conditions": list(VIN_CONDITION_OPTIONS),
            "meter_conditions": list(METER_CONDITION_OPTIONS),
            "accident_history_options": list(ACCIDENT_HISTORY_OPTIONS),
            "simple_repair_options": list(SIMPLE_REPAIR_OPTIONS),
            "special_history_options": list(SPECIAL_HISTORY_OPTIONS),
            "color_history_options": list(COLOR_HISTORY_OPTIONS),
            "major_option_options": list(MAJOR_OPTION_OPTIONS),
            "document_options": list(DOCUMENT_OPTIONS),
            "accident_detail_fields": [
                {"key": field_key, "label": label}
                for field_key, label in ACCIDENT_DETAIL_FIELDS
            ],
        },
    }


def build_mock_model_image_page_payload(
    brand_key: str,
    brand_label: str,
    model_names: list[str],
) -> dict[str, Any]:
    return {
        "brand_key": brand_key,
        "brand_label": brand_label,
        "models": [
            {
                "id": item.id,
                "brand": item.brand,
                "model": item.model,
                "image_src": item.image_src,
            }
            for item in build_model_options_for_page(brand_label, model_names)
        ],
    }


def build_mock_price_prediction_payload(request: PricePredictionRequestDTO) -> dict[str, Any]:
    purchase_age_days = max((date.today() - date.fromisoformat(request.purchase_date)).days, 0)
    vehicle_age_years = max(round(purchase_age_days / 365.25, 2), 0.1)
    annual_mileage_km = request.mileage_km / max(vehicle_age_years, 1.0)

    mileage_penalty = max(request.mileage_km - 30000, 0) * 0.0028
    used_penalty = 95 if request.is_used_purchase else 0
    color_delta = COLOR_TONE.get(request.color, 0)

    current_price = int(
        max(
            650,
            round(
                MODEL_BASE_PRICE.get(request.model_name, 2200)
                - mileage_penalty
                - used_penalty
                + color_delta
            ),
        )
    )

    confidence = 78

    current_year = date.today().year
    chart_points = [
        {
            "label": "현재",
            "year_label": f"{current_year}년",
            "price": current_price,
            "segment": "기준 시점",
            "phase": "current",
            "show_label": True,
        },
    ]

    projected_price = current_price
    projected_mileage = float(request.mileage_km)
    for offset, decline_rate in enumerate((0.18, 0.15, 0.17, 0.16, 0.14), start=1):
        projected_mileage += annual_mileage_km
        projected_price = int(round(projected_price * (1 - decline_rate) - (annual_mileage_km * 0.0006)))
        chart_points.append(
            {
                "label": f"{offset}년 후",
                "year_label": f"{current_year + offset}년",
                "price": projected_price,
                "segment": "연식·주행거리 반영" if offset <= 2 else "연식·주행거리 누적",
                "phase": "future",
                "show_label": True,
            }
        )

    fair_span = 256
    third_year_price = next(point["price"] for point in chart_points if point["label"] == "3년 후")
    suggestion = (
        "구매일 기준 차량 경과 연수와 누적 주행거리를 함께 반영한 단순 예측입니다."
        if third_year_price < current_price * 0.65
        else "현재 정보 기준으로는 단기 급락보다는 점진적 감가 흐름에 가깝습니다."
    )

    return {
        "current_price": current_price,
        "fair_price_min": current_price - fair_span,
        "fair_price_max": current_price + fair_span,
        "confidence": confidence,
        "suggestion": suggestion,
        "chart_points": chart_points,
    }


def build_mock_price_factor_payload(request: PricePredictionRequestDTO) -> dict[str, Any]:
    purchase_age_days = max((date.today() - date.fromisoformat(request.purchase_date)).days, 0)
    vehicle_age_years = max(round(purchase_age_days / 365.25, 2), 0.1)
    annual_mileage_km = request.mileage_km / max(vehicle_age_years, 1.0)

    positive_factors: list[str] = []
    negative_factors: list[str] = []

    if annual_mileage_km <= 13140 * 0.85:
        positive_factors.append("연간 주행거리 추정치가 평균보다 낮아 주행거리 부담이 적은 편입니다.")
    elif annual_mileage_km >= 13140 * 1.15:
        negative_factors.append("연간 주행거리 추정치가 평균보다 높아 감가 압력이 크게 반영될 수 있습니다.")
    else:
        positive_factors.append("연간 주행거리 추정치가 평균 구간에 가까워 과도한 주행 부담은 아닌 편입니다.")

    if request.color in {"흰색", "진주색", "화이트 펄", "검정", "검정색"}:
        positive_factors.append("무난한 인기 색상 계열이라 재판매 수요 확보에 유리한 편입니다.")
    else:
        negative_factors.append("비주류 색상 계열일 수 있어 비교 매물 대비 선택 폭이 좁아질 수 있습니다.")

    if vehicle_age_years <= 3.0:
        positive_factors.append("구매일 기준 경과 연수가 짧아 최근 연식 체감에 유리한 편입니다.")
    elif vehicle_age_years >= 7.0:
        negative_factors.append("구매일 기준 경과 연수가 길어 연식 감가 압력이 누적된 상태입니다.")

    if request.transmission == "자동":
        positive_factors.append("자동 변속기 기준이라 일반적인 중고차 수요와 맞는 편입니다.")

    return {
        "positive_factors": positive_factors[:3],
        "negative_factors": negative_factors[:3],
        "logic_note": "구매일 기준 경과 연수, 추정 연간 주행거리, 색상 선호도, 변속기를 기준으로 더미 분석을 생성했습니다.",
    }
