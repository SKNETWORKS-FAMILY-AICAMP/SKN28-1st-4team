from __future__ import annotations

from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from app import get_vehicle_model_image
from sql_commands.vehicle_model_image import SELECT_VEHICLE_MODEL_IMAGE_SQL
from services.vehicle_model_image import (
    VehicleModelImage,
    VehicleModelImageService,
)


pytestmark = pytest.mark.unit


class StubCursor:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self._row = row
        self.execute_calls: list[tuple[str, tuple[object, ...]]] = []

    def __enter__(self) -> StubCursor:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def execute(self, query: str, params: tuple[object, ...]) -> int:
        self.execute_calls.append((query, params))
        return 1

    def fetchone(self) -> tuple[object, ...] | None:
        return self._row


class StubActiveConnection:
    def __init__(self, cursor: StubCursor) -> None:
        self._cursor = cursor

    def cursor(self) -> StubCursor:
        return self._cursor


class StubClient:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self.cursor = StubCursor(row)
        self.connect_calls = 0

    @contextmanager
    def connect(self):
        self.connect_calls += 1
        yield StubActiveConnection(self.cursor)


def test_get_image_reads_vehicle_image_by_primary_key() -> None:
    client = StubClient(
        (
            "hyundai",
            "쏘나타 디 엣지",
            "hyundai_쏘나타 디 엣지.jpg",
            "image/png",
            b"png-bytes",
        )
    )
    service = VehicleModelImageService(client=client)  # type: ignore[arg-type]

    image = service.get_image("  hyundai  ", "  쏘나타 디 엣지  ")

    assert image == VehicleModelImage(
        brand_key="hyundai",
        model_name="쏘나타 디 엣지",
        source_filename="hyundai_쏘나타 디 엣지.jpg",
        mime_type="image/png",
        payload=b"png-bytes",
    )
    assert client.connect_calls == 1
    assert client.cursor.execute_calls == [
        (
            SELECT_VEHICLE_MODEL_IMAGE_SQL,
            ("hyundai", "쏘나타 디 엣지"),
        )
    ]


def test_get_image_returns_none_when_row_is_missing() -> None:
    service = VehicleModelImageService(client=StubClient(None))  # type: ignore[arg-type]

    assert service.get_image("hyundai", "없는 모델") is None


@pytest.mark.parametrize(
    ("brand_key", "model_name", "field_name"),
    [
        ("", "쏘나타 디 엣지", "brand_key"),
        ("hyundai", "", "model_name"),
    ],
)
def test_get_image_rejects_blank_lookup_values(
    brand_key: str,
    model_name: str,
    field_name: str,
) -> None:
    service = VehicleModelImageService(client=StubClient(None))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match=field_name):
        service.get_image(brand_key, model_name)


class StubVehicleModelImageService:
    def __init__(self, image: VehicleModelImage | None) -> None:
        self._image = image

    def get_image(self, brand_key: str, model_name: str) -> VehicleModelImage | None:
        return self._image


def test_get_vehicle_model_image_endpoint_returns_raw_image_response() -> None:
    response = get_vehicle_model_image(
        "hyundai",
        "쏘나타 디 엣지",
        StubVehicleModelImageService(
            VehicleModelImage(
                brand_key="hyundai",
                model_name="쏘나타 디 엣지",
                source_filename="hyundai_쏘나타 디 엣지.jpg",
                mime_type="image/png",
                payload=b"png-bytes",
            )
        ),
    )

    assert response.status_code == 200
    assert response.body == b"png-bytes"
    assert response.headers["content-type"] == "image/png"
    assert "filename*=UTF-8''hyundai_%EC%8F%98%EB%82%98%ED%83%80%20%EB%94%94%20%EC%97%A3%EC%A7%80.jpg" in response.headers["content-disposition"]


def test_get_vehicle_model_image_endpoint_raises_404_when_image_is_missing() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_vehicle_model_image(
            "hyundai",
            "없는 모델",
            StubVehicleModelImageService(None),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "vehicle model image not found"
