from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, cast

from external.db import MySQLClient, get_db_client
from sql_commands.vehicle_model_image import (
    SELECT_VEHICLE_MODEL_IMAGE_SQL,
    build_select_vehicle_model_image_meta_by_models_sql,
)


@dataclass(frozen=True)
class VehicleModelImage:
    brand_key: str
    model_name: str
    source_filename: str
    mime_type: str
    payload: bytes


@dataclass(frozen=True)
class VehicleModelImageMeta:
    brand_key: str
    model_name: str
    source_filename: str
    mime_type: str


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

    def get_image_metas(
        self,
        brand_key: str,
        model_names: list[str] | tuple[str, ...],
    ) -> dict[str, VehicleModelImageMeta]:
        normalized_brand_key = brand_key.strip()
        normalized_model_names = [model_name.strip() for model_name in model_names if model_name.strip()]
        if not normalized_brand_key:
            raise ValueError("brand_key is required")
        if not normalized_model_names:
            raise ValueError("model_names is required")

        sql = build_select_vehicle_model_image_meta_by_models_sql(len(normalized_model_names))
        query_params = (normalized_brand_key, *normalized_model_names)

        with self._client.connect() as active_connection:
            with cast(Any, active_connection).cursor() as cursor:
                cursor.execute(sql, query_params)
                rows = cursor.fetchall()

        image_metas: dict[str, VehicleModelImageMeta] = {}
        for brand_key_value, model_name_value, source_filename, mime_type in rows:
            image_metas[str(model_name_value)] = VehicleModelImageMeta(
                brand_key=str(brand_key_value),
                model_name=str(model_name_value),
                source_filename=str(source_filename),
                mime_type=str(mime_type),
            )
        return image_metas


@dataclass(frozen=True)
class VehicleModelImageCard:
    id: str
    brand: str
    model: str
    image_src: str


class VehicleModelImagePageService:
    def __init__(self, image_service: VehicleModelImageService) -> None:
        self._image_service = image_service

    def get_model_cards(
        self,
        *,
        brand_key: str,
        brand_label: str,
        model_names: list[str] | tuple[str, ...],
        image_url_builder: callable,
    ) -> list[VehicleModelImageCard]:
        normalized_model_names = [model_name.strip() for model_name in model_names if model_name.strip()]
        if not normalized_model_names:
            return []

        try:
            image_meta_map = self._image_service.get_image_metas(brand_key, normalized_model_names)
        except Exception as exc:
            print(
                "[vehicle_model_image] image meta lookup failed; using placeholder images",
                {
                    "brand_key": brand_key,
                    "error": type(exc).__name__,
                    "message": str(exc),
                },
            )
            image_meta_map = {}
        cards: list[VehicleModelImageCard] = []
        for index, model_name in enumerate(normalized_model_names, start=1):
            image_meta = image_meta_map.get(model_name)
            cards.append(
                VehicleModelImageCard(
                    id=f"{brand_key}-{model_name}-{index}",
                    brand=brand_label,
                    model=model_name,
                    image_src=(
                        image_url_builder(brand_key, model_name)
                        if image_meta
                        else _build_placeholder_image_src(brand_label=brand_label, model_name=model_name)
                    ),
                )
            )
        return cards


def _build_placeholder_image_src(*, brand_label: str, model_name: str) -> str:
    safe_brand = brand_label.strip() or "CARBODY"
    safe_model = model_name.strip() or "Model"
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0f172a"/>
          <stop offset="55%" stop-color="#165dff"/>
          <stop offset="100%" stop-color="#dbeafe"/>
        </linearGradient>
      </defs>
      <rect width="640" height="360" rx="28" fill="url(#bg)"/>
      <circle cx="512" cy="88" r="78" fill="rgba(255,255,255,0.10)"/>
      <circle cx="548" cy="286" r="94" fill="rgba(255,255,255,0.08)"/>
      <text x="36" y="72" fill="#dbeafe" font-size="22" font-family="Arial, sans-serif" font-weight="700">{safe_brand}</text>
      <text x="36" y="142" fill="#ffffff" font-size="34" font-family="Arial, sans-serif" font-weight="800">{safe_model}</text>
      <text x="36" y="196" fill="#dbeafe" font-size="16" font-family="Arial, sans-serif">대표 이미지가 준비되지 않아 임시 카드 이미지를 표시합니다.</text>
      <text x="36" y="312" fill="#bfdbfe" font-size="18" font-family="Arial, sans-serif" font-weight="700">CARBODY</text>
    </svg>
    """.strip()
    encoded_svg = b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded_svg}"


@lru_cache(maxsize=1)
def get_vehicle_model_image_service() -> VehicleModelImageService:
    return VehicleModelImageService(client=get_db_client())


@lru_cache(maxsize=1)
def get_vehicle_model_image_page_service() -> VehicleModelImagePageService:
    return VehicleModelImagePageService(image_service=get_vehicle_model_image_service())
