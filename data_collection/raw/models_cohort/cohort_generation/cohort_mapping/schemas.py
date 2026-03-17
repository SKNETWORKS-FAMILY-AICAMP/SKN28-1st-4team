from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class MajorCategory(StrEnum):
    SEDAN = "sedan"
    SUV = "suv"
    HATCHBACK = "hatchback"
    WAGON = "wagon"
    VAN = "van"
    TRUCK = "truck"
    BUS = "bus"
    COUPE_CONVERTIBLE = "coupe_convertible"
    OTHER = "other"
    UNKNOWN = "unknown"


class MarketFamily(StrEnum):
    SEDAN = "sedan"
    SUV = "suv"
    OTHER = "other"
    UNKNOWN = "unknown"


class VehicleCategoryMappingInput(BaseModel):
    brand: str = Field(description="Vehicle brand")
    model_name: str = Field(description="Vehicle model name")
    class_name_examples: list[str] = Field(
        default_factory=list,
        description="Trim name examples collected from the source table",
    )
    level_name_examples: list[str] = Field(
        default_factory=list,
        description="Submodel or powertrain line examples collected from the source table",
    )
    context_summary: str | None = Field(
        default=None,
        description="Optional compact numeric summary to help web lookups",
    )


class VehicleCategoryMappingOutput(BaseModel):
    brand: str
    model_name: str
    major_category: MajorCategory
    market_family: MarketFamily
    search_used: bool = False
    note: str | None = None
