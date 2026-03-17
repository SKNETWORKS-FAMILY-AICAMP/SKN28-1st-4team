from dataclasses import dataclass


@dataclass(frozen=True)
class PricePoint:
    label: str
    year_label: str
    price: int
    segment: str
    phase: str
    show_label: bool


@dataclass(frozen=True)
class PriceResult:
    current_price: int
    fair_price_min: int
    fair_price_max: int
    confidence: int
    suggestion: str
    chart_points: tuple[PricePoint, ...]
