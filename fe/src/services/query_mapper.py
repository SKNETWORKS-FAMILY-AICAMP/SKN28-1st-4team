from typing import Any, cast

from models.form import VehicleFormState
from models.price import PricePoint, PriceResult
from models.query import (
    AccidentDetailFieldDTO,
    PricePredictionPointDTO,
    PricePredictionRequestDTO,
    PricePredictionResponseDTO,
    VehicleCandidateDTO,
    VehicleCatalogDTO,
    VehicleOptionsDTO,
)


class FrontendQueryMapper:
    def to_price_prediction_request(self, form_state: VehicleFormState) -> PricePredictionRequestDTO:
        return PricePredictionRequestDTO(
            brand=form_state.brand,
            model=form_state.model,
            year=form_state.year,
            plate=form_state.plate,
            purchase_date=form_state.purchase_date.isoformat(),
            is_used_purchase=form_state.is_used_purchase,
            mileage=form_state.mileage,
            color=form_state.color,
            trim=form_state.trim_input,
            transmission=form_state.transmission,
            fuel=form_state.fuel,
            warranty_type=form_state.warranty_type,
            vin_condition=form_state.vin_condition,
            meter_condition=form_state.meter_condition,
            accident_history=form_state.accident_history,
            simple_repair=form_state.simple_repair,
            special_history=tuple(form_state.special_history),
            usage_change=tuple(form_state.usage_change),
            color_history=tuple(form_state.color_history),
            major_options=tuple(form_state.major_options),
            recall_status=form_state.recall_status,
            body_condition=form_state.body_condition,
            interior_condition=form_state.interior_condition,
            wheel_tire_condition=form_state.wheel_tire_condition,
            documents=tuple(form_state.documents),
            selected_candidate_id=form_state.selected_candidate_id,
            accident_details=dict(form_state.accident_details),
        )

    def to_price_prediction_payload(self, request_dto: PricePredictionRequestDTO) -> dict[str, Any]:
        return {
            "brand": request_dto.brand,
            "model": request_dto.model,
            "year": request_dto.year,
            "plate": request_dto.plate,
            "purchase_date": request_dto.purchase_date,
            "is_used_purchase": request_dto.is_used_purchase,
            "mileage": request_dto.mileage,
            "color": request_dto.color,
            "trim": request_dto.trim,
            "transmission": request_dto.transmission,
            "fuel": request_dto.fuel,
            "warranty_type": request_dto.warranty_type,
            "vin_condition": request_dto.vin_condition,
            "meter_condition": request_dto.meter_condition,
            "accident_history": request_dto.accident_history,
            "simple_repair": request_dto.simple_repair,
            "special_history": list(request_dto.special_history),
            "usage_change": list(request_dto.usage_change),
            "color_history": list(request_dto.color_history),
            "major_options": list(request_dto.major_options),
            "recall_status": request_dto.recall_status,
            "body_condition": request_dto.body_condition,
            "interior_condition": request_dto.interior_condition,
            "wheel_tire_condition": request_dto.wheel_tire_condition,
            "documents": list(request_dto.documents),
            "selected_candidate_id": request_dto.selected_candidate_id,
            "accident_details": dict(request_dto.accident_details),
        }

    def to_vehicle_catalog(self, payload: dict[str, Any]) -> VehicleCatalogDTO:
        catalog_payload = cast(dict[str, dict[str, list[str]]], payload["catalog"])
        candidates_payload = cast(dict[str, list[dict[str, Any]]], payload["candidates_by_model"])
        options_payload = cast(dict[str, Any], payload["options"])

        catalog = {
            brand: {model: tuple(years) for model, years in models.items()}
            for brand, models in catalog_payload.items()
        }
        candidates_by_model = {
            model: tuple(
                VehicleCandidateDTO(
                    id=str(candidate["id"]),
                    title=str(candidate["title"]),
                    year=str(candidate["year"]),
                    trim=str(candidate["trim"]),
                    mileage=int(candidate["mileage"]),
                    fuel=str(candidate["fuel"]),
                    color=str(candidate["color"]),
                )
                for candidate in candidates
            )
            for model, candidates in candidates_payload.items()
        }
        options = VehicleOptionsDTO(
            color_options=tuple(str(item) for item in options_payload["colors"]),
            transmission_options=tuple(str(item) for item in options_payload["transmissions"]),
            fuel_options=tuple(str(item) for item in options_payload["fuels"]),
            warranty_options=tuple(str(item) for item in options_payload["warranty_types"]),
            usage_change_options=tuple(str(item) for item in options_payload["usage_changes"]),
            recall_options=tuple(str(item) for item in options_payload["recall_statuses"]),
            vin_condition_options=tuple(str(item) for item in options_payload["vin_conditions"]),
            meter_condition_options=tuple(str(item) for item in options_payload["meter_conditions"]),
            accident_history_options=tuple(str(item) for item in options_payload["accident_history_options"]),
            simple_repair_options=tuple(str(item) for item in options_payload["simple_repair_options"]),
            special_history_options=tuple(str(item) for item in options_payload["special_history_options"]),
            color_history_options=tuple(str(item) for item in options_payload["color_history_options"]),
            major_option_options=tuple(str(item) for item in options_payload["major_option_options"]),
            document_options=tuple(str(item) for item in options_payload["document_options"]),
            accident_detail_fields=tuple(
                AccidentDetailFieldDTO(
                    key=str(item["key"]),
                    label=str(item["label"]),
                )
                for item in options_payload["accident_detail_fields"]
            ),
        )
        return VehicleCatalogDTO(
            brands=tuple(catalog.keys()),
            catalog=catalog,
            candidates_by_model=candidates_by_model,
            base_prices_by_model={
                str(model): int(price)
                for model, price in cast(dict[str, Any], payload["base_prices_by_model"]).items()
            },
            color_tones={
                str(color): int(delta)
                for color, delta in cast(dict[str, Any], payload["color_tones"]).items()
            },
            options=options,
        )

    def to_price_prediction_response(self, payload: dict[str, Any]) -> PricePredictionResponseDTO:
        return PricePredictionResponseDTO(
            current_price=int(payload["current_price"]),
            fair_price_min=int(payload["fair_price_min"]),
            fair_price_max=int(payload["fair_price_max"]),
            confidence=int(payload["confidence"]),
            suggestion=str(payload["suggestion"]),
            chart_points=tuple(
                PricePredictionPointDTO(
                    label=str(point["label"]),
                    year_label=str(point["year_label"]),
                    price=int(point["price"]),
                    segment=str(point["segment"]),
                    phase=str(point["phase"]),
                    show_label=bool(point["show_label"]),
                )
                for point in cast(list[dict[str, Any]], payload["chart_points"])
            ),
        )

    def to_price_result(self, dto: PricePredictionResponseDTO) -> PriceResult:
        return PriceResult(
            current_price=dto.current_price,
            fair_price_min=dto.fair_price_min,
            fair_price_max=dto.fair_price_max,
            confidence=dto.confidence,
            suggestion=dto.suggestion,
            chart_points=tuple(
                PricePoint(
                    label=point.label,
                    year_label=point.year_label,
                    price=point.price,
                    segment=point.segment,
                    phase=point.phase,
                    show_label=point.show_label,
                )
                for point in dto.chart_points
            ),
        )
