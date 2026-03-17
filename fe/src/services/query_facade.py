from functools import lru_cache

from core.settings import AppSettings, get_app_settings
from models.form import VehicleFormState
from models.price import PriceFactorResult, PriceResult
from models.query import VehicleCatalogDTO, VehicleModelOptionDTO, VehicleOptionsDTO
from services.mock_query_service import (
    build_mock_catalog_payload,
)
from services.query_helper import QueryHelper
from services.query_mapper import FrontendQueryMapper


class FrontendQueryFacade:
    def __init__(
        self,
        settings: AppSettings,
        mapper: FrontendQueryMapper,
        query_helper: QueryHelper | None = None,
    ) -> None:
        self._settings = settings
        self._mapper = mapper
        self._query_helper = query_helper or QueryHelper(
            base_url=settings.query.base_url,
            timeout_seconds=settings.query.timeout_seconds,
        )
        self._catalog_cache: VehicleCatalogDTO | None = None
        self._model_option_cache: dict[tuple[str, tuple[str, ...]], tuple[VehicleModelOptionDTO, ...]] = {}

    def get_vehicle_catalog(self) -> VehicleCatalogDTO:
        if self._catalog_cache is None:
            payload = build_mock_catalog_payload()
            self._catalog_cache = self._mapper.to_vehicle_catalog(payload)
        return self._catalog_cache

    def get_form_options(self) -> VehicleOptionsDTO:
        return self.get_vehicle_catalog().options

    def get_vehicle_model_images(
        self,
        *,
        brand_key: str,
        brand_label: str,
        model_names: tuple[str, ...],
    ) -> tuple[VehicleModelOptionDTO, ...]:
        cache_key = (brand_key, model_names)
        if cache_key not in self._model_option_cache:
            print(
                "[query_facade] loading vehicle model images",
                {
                    "mode": "backend",
                    "brand_key": brand_key,
                    "brand_label": brand_label,
                    "model_names": list(model_names),
                },
            )
            payload = self._query_helper.get_vehicle_model_images(
                self._settings.query.model_image_page_path,
                brand_key=brand_key,
                brand_label=brand_label,
                model_names=list(model_names),
            )
            self._model_option_cache[cache_key] = self._mapper.to_vehicle_model_options(payload)
        else:
            print(
                "[query_facade] vehicle model images cache hit",
                {
                    "brand_key": brand_key,
                    "model_names": list(model_names),
                },
            )
        return self._model_option_cache[cache_key]

    def get_price_prediction(self, form_state: VehicleFormState) -> PriceResult:
        catalog = self.get_vehicle_catalog()
        brand_key = catalog.brand_keys_by_label.get(form_state.brand, form_state.brand)
        request_dto = self._mapper.to_price_prediction_request(
            form_state,
            brand_key=brand_key,
        )
        payload = self._query_helper.post_json(
            self._settings.query.price_prediction_path,
            payload=self._mapper.to_price_prediction_payload(request_dto),
        )
        prediction_dto = self._mapper.to_price_prediction_response(payload)
        return self._mapper.to_price_result(prediction_dto)

    def get_price_factors(self, form_state: VehicleFormState) -> PriceFactorResult:
        catalog = self.get_vehicle_catalog()
        brand_key = catalog.brand_keys_by_label.get(form_state.brand, form_state.brand)
        request_dto = self._mapper.to_price_prediction_request(
            form_state,
            brand_key=brand_key,
        )
        payload = self._query_helper.post_json(
            self._settings.query.price_factors_path,
            payload=self._mapper.to_price_prediction_payload(request_dto),
        )
        factor_dto = self._mapper.to_price_factor_response(payload)
        return self._mapper.to_price_factor_result(factor_dto)


@lru_cache(maxsize=1)
def get_frontend_query_facade() -> FrontendQueryFacade:
    return FrontendQueryFacade(
        settings=get_app_settings(),
        mapper=FrontendQueryMapper(),
    )
