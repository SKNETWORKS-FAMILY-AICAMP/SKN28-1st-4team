from datetime import date
from typing import Any

from mock_data.vehicle_catalog import (
    ACCIDENT_DETAIL_FIELDS,
    ACCIDENT_HISTORY_OPTIONS,
    CATALOG,
    COLOR_HISTORY_OPTIONS,
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
)
from models.query import PricePredictionRequestDTO


def build_mock_catalog_payload() -> dict[str, Any]:
    return {
        "catalog": {
            brand: {model: list(years) for model, years in models.items()}
            for brand, models in CATALOG.items()
        },
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
            "colors": list(COLOR_TONE.keys()),
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


def build_mock_price_prediction_payload(request: PricePredictionRequestDTO) -> dict[str, Any]:
    mileage_penalty = max(request.mileage - 30000, 0) * 0.0028
    used_penalty = 95 if request.is_used_purchase else 0
    color_delta = COLOR_TONE.get(request.color, 0)
    accident_detail_penalty = sum(
        34
        for field_key, _ in ACCIDENT_DETAIL_FIELDS
        if request.accident_details.get(field_key) == "문제 있음"
    )
    frame_penalty = 90 if request.accident_details.get("accident_frame") == "문제 있음" else 0
    accident_penalty = (180 + accident_detail_penalty + frame_penalty) if request.accident_history == "있음" else 0
    repair_penalty = 55 if request.simple_repair == "있음" else 0
    special_penalty = len(request.special_history) * 120
    usage_penalty = len(request.usage_change) * 80
    color_history_penalty = len(request.color_history) * 40
    option_bonus = len(request.major_options) * 22
    document_bonus = len(request.documents) * 6
    condition_bonus = (
        request.body_condition + request.interior_condition + request.wheel_tire_condition
    ) * 9

    current_price = int(
        max(
            650,
            round(
                MODEL_BASE_PRICE.get(request.model, 2200)
                - mileage_penalty
                - used_penalty
                - accident_penalty
                - repair_penalty
                - special_penalty
                - usage_penalty
                - color_history_penalty
                + option_bonus
                + document_bonus
                + condition_bonus
                + color_delta
            ),
        )
    )

    confidence = 72 + min(len(request.major_options) * 2, 8)
    confidence += 6 if request.vin_condition == "양호" else 0
    confidence += 4 if request.meter_condition == "양호" else 0
    confidence = min(confidence, 94)

    current_year = date.today().year
    chart_points = [
        {
            "label": "최근 시세",
            "year_label": f"{current_year - 1}년",
            "price": int(round(current_price * 0.94)),
            "segment": "과거 더미",
            "phase": "past",
            "show_label": False,
        },
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
    for offset, decline_rate in enumerate((0.18, 0.15, 0.17, 0.16, 0.14), start=1):
        projected_price = int(round(projected_price * (1 - decline_rate)))
        chart_points.append(
            {
                "label": f"{offset}년 후",
                "year_label": f"{current_year + offset}년",
                "price": projected_price,
                "segment": "완만한 하락" if offset <= 2 else "하락 폭 확대",
                "phase": "future",
                "show_label": True,
            }
        )

    fair_span = 110 + len(request.major_options) * 12
    third_year_price = next(point["price"] for point in chart_points if point["label"] == "3년 후")
    suggestion = (
        "2~3년 차부터 감가가 더 가팔라지는 설정이라, 중기 이전 매도 시점을 먼저 보는 편이 유리합니다."
        if third_year_price < current_price * 0.65
        else "감가 추세가 완만한 편이라 1~2년 내 매도 압박은 크지 않습니다."
    )

    return {
        "current_price": current_price,
        "fair_price_min": current_price - fair_span,
        "fair_price_max": current_price + fair_span,
        "confidence": confidence,
        "suggestion": suggestion,
        "chart_points": chart_points,
    }
