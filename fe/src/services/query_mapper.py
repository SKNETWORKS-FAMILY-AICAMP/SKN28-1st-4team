from typing import Any, cast

from models.form import VehicleFormState
from models.price import PriceFactorResult, PricePoint, PriceResult
from models.query import (
    AccidentDetailFieldDTO,
    PriceFactorResponseDTO,
    PricePredictionPointDTO,
    PricePredictionRequestDTO,
    PricePredictionResponseDTO,
    VehicleCandidateDTO,
    VehicleCatalogDTO,
    VehicleModelOptionDTO,
    VehicleOptionsDTO,
)


class FrontendQueryMapper:
    def to_price_prediction_request(
        self,
        form_state: VehicleFormState,
        *,
        brand_key: str,
    ) -> PricePredictionRequestDTO:
        return PricePredictionRequestDTO(
            brand_key=brand_key,
            brand_label=form_state.brand,
            model_name=form_state.model,
            trim_name=form_state.trim_input,
            plate=form_state.plate,
            purchase_date=form_state.purchase_date.isoformat(),
            is_used_purchase=form_state.is_used_purchase,
            mileage_km=form_state.mileage,
            color=form_state.color,
            transmission=form_state.transmission,
        )

    def to_price_prediction_payload(self, request_dto: PricePredictionRequestDTO) -> dict[str, Any]:
        return {
            "brand_key": request_dto.brand_key,
            "brand_label": request_dto.brand_label,
            "model_name": request_dto.model_name,
            "trim_name": request_dto.trim_name,
            "plate": request_dto.plate,
            "purchase_date": request_dto.purchase_date,
            "is_used_purchase": request_dto.is_used_purchase,
            "mileage_km": request_dto.mileage_km,
            "color": request_dto.color,
            "transmission": request_dto.transmission,
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
            brand_keys_by_label={
                str(label): str(key)
                for label, key in cast(dict[str, Any], payload["brand_keys_by_label"]).items()
            },
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

    def to_vehicle_model_options(self, payload: dict[str, Any]) -> tuple[VehicleModelOptionDTO, ...]:
        models_payload = cast(list[dict[str, Any]], payload["models"])
        return tuple(
            VehicleModelOptionDTO(
                id=str(model["id"]),
                brand=str(model["brand"]),
                model=str(model["model"]),
                image_src=str(model["image_src"]),
            )
            for model in models_payload
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

    def to_price_factor_response(self, payload: dict[str, Any]) -> PriceFactorResponseDTO:
        return PriceFactorResponseDTO(
            positive_factors=tuple(str(item) for item in cast(list[Any], payload["positive_factors"])),
            negative_factors=tuple(str(item) for item in cast(list[Any], payload["negative_factors"])),
            logic_note=str(payload["logic_note"]),
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

    def to_price_factor_result(self, dto: PriceFactorResponseDTO) -> PriceFactorResult:
        return PriceFactorResult(
            positive_factors=dto.positive_factors,
            negative_factors=dto.negative_factors,
            logic_note=dto.logic_note,
        )
