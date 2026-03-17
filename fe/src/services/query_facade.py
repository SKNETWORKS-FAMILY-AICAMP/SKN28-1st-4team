from functools import lru_cache

from core.settings import AppSettings, get_app_settings
from models.form import VehicleFormState
from models.price import PriceResult
from models.query import VehicleCatalogDTO, VehicleOptionsDTO
from services.mock_query_service import (
    build_mock_catalog_payload,
    build_mock_price_prediction_payload,
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

    def get_vehicle_catalog(self) -> VehicleCatalogDTO:
        if self._catalog_cache is None:
            if self._settings.is_development:
                payload = build_mock_catalog_payload()
            else:
                payload = self._query_helper.get_json(self._settings.query.catalog_path)
            self._catalog_cache = self._mapper.to_vehicle_catalog(payload)
        return self._catalog_cache

    def get_form_options(self) -> VehicleOptionsDTO:
        return self.get_vehicle_catalog().options

    def get_price_prediction(self, form_state: VehicleFormState) -> PriceResult:
        request_dto = self._mapper.to_price_prediction_request(form_state)
        if self._settings.is_development:
            payload = build_mock_price_prediction_payload(request_dto)
        else:
            payload = self._query_helper.post_json(
                self._settings.query.price_prediction_path,
                payload=self._mapper.to_price_prediction_payload(request_dto),
            )
        prediction_dto = self._mapper.to_price_prediction_response(payload)
        return self._mapper.to_price_result(prediction_dto)


@lru_cache(maxsize=1)
def get_frontend_query_facade() -> FrontendQueryFacade:
    return FrontendQueryFacade(
        settings=get_app_settings(),
        mapper=FrontendQueryMapper(),
    )
