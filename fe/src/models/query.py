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
    catalog: dict[str, dict[str, tuple[str, ...]]]
    candidates_by_model: dict[str, tuple[VehicleCandidateDTO, ...]]
    base_prices_by_model: dict[str, int]
    color_tones: dict[str, int]
    options: VehicleOptionsDTO


@dataclass(frozen=True)
class PricePredictionRequestDTO:
    brand: str
    model: str
    year: str
    plate: str
    purchase_date: str
    is_used_purchase: bool
    mileage: int
    color: str
    trim: str
    transmission: str
    fuel: str
    warranty_type: str
    vin_condition: str
    meter_condition: str
    accident_history: str
    simple_repair: str
    special_history: tuple[str, ...]
    usage_change: tuple[str, ...]
    color_history: tuple[str, ...]
    major_options: tuple[str, ...]
    recall_status: str
    body_condition: int
    interior_condition: int
    wheel_tire_condition: int
    documents: tuple[str, ...]
    selected_candidate_id: str
    accident_details: dict[str, str]


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
