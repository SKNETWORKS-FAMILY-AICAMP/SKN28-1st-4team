from dataclasses import dataclass


@dataclass(frozen=True)
class AccidentDetailFieldDTO:
    key: str
    label: str


@dataclass(frozen=True)
class VehicleCandidateDTO:
    id: str
    title: str
    year: str
    trim: str
    mileage: int
    fuel: str
    color: str


@dataclass(frozen=True)
class VehicleModelOptionDTO:
    id: str
    brand: str
    model: str
    image_src: str


@dataclass(frozen=True)
class VehicleOptionsDTO:
    color_options: tuple[str, ...]
    transmission_options: tuple[str, ...]
    fuel_options: tuple[str, ...]
    warranty_options: tuple[str, ...]
    usage_change_options: tuple[str, ...]
    recall_options: tuple[str, ...]
    vin_condition_options: tuple[str, ...]
    meter_condition_options: tuple[str, ...]
    accident_history_options: tuple[str, ...]
    simple_repair_options: tuple[str, ...]
    special_history_options: tuple[str, ...]
    color_history_options: tuple[str, ...]
    major_option_options: tuple[str, ...]
    document_options: tuple[str, ...]
    accident_detail_fields: tuple[AccidentDetailFieldDTO, ...]


@dataclass(frozen=True)
class VehicleCatalogDTO:
    brands: tuple[str, ...]
    brand_keys_by_label: dict[str, str]
    catalog: dict[str, dict[str, tuple[str, ...]]]
    candidates_by_model: dict[str, tuple[VehicleCandidateDTO, ...]]
    base_prices_by_model: dict[str, int]
    color_tones: dict[str, int]
    options: VehicleOptionsDTO


@dataclass(frozen=True)
class PricePredictionRequestDTO:
    brand_key: str
    brand_label: str
    model_name: str
    trim_name: str
    plate: str
    purchase_date: str
    is_used_purchase: bool
    mileage_km: int
    color: str
    transmission: str


@dataclass(frozen=True)
class PricePredictionPointDTO:
    label: str
    year_label: str
    price: int
    segment: str
    phase: str
    show_label: bool


@dataclass(frozen=True)
class PricePredictionResponseDTO:
    current_price: int
    fair_price_min: int
    fair_price_max: int
    confidence: int
    suggestion: str
    chart_points: tuple[PricePredictionPointDTO, ...]


@dataclass(frozen=True)
class PriceFactorResponseDTO:
    positive_factors: tuple[str, ...]
    negative_factors: tuple[str, ...]
    logic_note: str
