from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, cast

from external.db import MySQLClient, get_db_client
from sql_commands.vehicle_model_image import SELECT_VEHICLE_MODEL_IMAGE_SQL


@dataclass(frozen=True)
class VehicleModelImage:
    brand_key: str
    model_name: str
    source_filename: str
    mime_type: str
    payload: bytes


class VehicleModelImageService:
    def __init__(self, client: MySQLClient) -> None:
        self._client = client

    def get_image(
        self,
        brand_key: str,
        model_name: str,
    ) -> VehicleModelImage | None:
        normalized_brand_key = brand_key.strip()
        normalized_model_name = model_name.strip()
        if not normalized_brand_key:
            raise ValueError("brand_key is required")
        if not normalized_model_name:
            raise ValueError("model_name is required")

        with self._client.connect() as active_connection:
            with cast(Any, active_connection).cursor() as cursor:
                cursor.execute(
                    SELECT_VEHICLE_MODEL_IMAGE_SQL,
                    (normalized_brand_key, normalized_model_name),
                )
                row = cursor.fetchone()

        if row is None:
            return None

        brand_key_value, model_name_value, source_filename, mime_type, payload = row
        return VehicleModelImage(
            brand_key=str(brand_key_value),
            model_name=str(model_name_value),
            source_filename=str(source_filename),
            mime_type=str(mime_type),
            payload=bytes(payload),
        )


@lru_cache(maxsize=1)
def get_vehicle_model_image_service() -> VehicleModelImageService:
    return VehicleModelImageService(client=get_db_client())
