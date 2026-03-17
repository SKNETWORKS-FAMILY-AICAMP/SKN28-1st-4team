from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class VehicleFormState:
    brand: str
    model: str
    plate: str
    purchase_date: date
    purchase_date_input: str
    is_used_purchase: bool
    mileage: int
    mileage_input: str
    color: str
    trim_input: str
    transmission: str
    fuel: str
    warranty_type: str
    vin_condition: str
    meter_condition: str
    accident_history: str
    simple_repair: str
    special_history: list[str]
    usage_change: list[str]
    color_history: list[str]
    major_options: list[str]
    recall_status: str
    body_condition: int
    interior_condition: int
    wheel_tire_condition: int
    documents: list[str]
    selected_candidate_id: str
    accident_details: dict[str, str]
