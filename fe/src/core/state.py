from copy import deepcopy
from datetime import date
from typing import TYPE_CHECKING, Any

import streamlit as st

from models.form import VehicleFormState

if TYPE_CHECKING:
    from services.query_facade import FrontendQueryFacade


def default_session_values(facade: "FrontendQueryFacade | None" = None) -> dict[str, Any]:
    if facade is None:
        from services.query_facade import get_frontend_query_facade

        facade = get_frontend_query_facade()

    catalog = facade.get_vehicle_catalog()
    options = catalog.options

    brand = "현대" if "현대" in catalog.brands else catalog.brands[0]
    model_options = tuple(catalog.catalog[brand].keys())
    model = "쏘나타" if "쏘나타" in model_options else model_options[0]
    year_options = catalog.catalog[brand][model]
    year = "2023년형" if "2023년형" in year_options else year_options[0]
    candidate_options = [candidate for candidate in catalog.candidates_by_model.get(model, ()) if candidate.year == year]
    selected_candidate = next(
        (candidate for candidate in candidate_options if candidate.id == "sonata-1"),
        candidate_options[0] if candidate_options else None,
    )
    color = selected_candidate.color if selected_candidate else (
        "화이트 펄" if "화이트 펄" in options.color_options else options.color_options[0]
    )
    transmission = "자동" if "자동" in options.transmission_options else options.transmission_options[0]
    fuel = selected_candidate.fuel if selected_candidate else (
        "가솔린" if "가솔린" in options.fuel_options else options.fuel_options[0]
    )
    warranty_type = "보험사보증" if "보험사보증" in options.warranty_options else options.warranty_options[0]
    recall_status = "리콜 이행" if "리콜 이행" in options.recall_options else options.recall_options[0]
    vin_condition = "양호" if "양호" in options.vin_condition_options else options.vin_condition_options[0]
    meter_condition = "양호" if "양호" in options.meter_condition_options else options.meter_condition_options[0]
    accident_history = "없음" if "없음" in options.accident_history_options else options.accident_history_options[0]
    simple_repair = "있음" if "있음" in options.simple_repair_options else options.simple_repair_options[0]
    major_options = ["네비게이션"] if "네비게이션" in options.major_option_options else list(options.major_option_options[:1])
    documents = ["사용설명서", "안전삼각대"] if all(
        item in options.document_options for item in ("사용설명서", "안전삼각대")
    ) else list(options.document_options[:2])
    accident_detail_keys = tuple(field.key for field in options.accident_detail_fields)

    defaults: dict[str, Any] = {
        "brand": brand,
        "model": model,
        "year": year,
        "plate": "128가 4321",
        "purchase_date": date(2021, 5, 14),
        "purchase_date_input": "2021/05/14",
        "is_used_purchase": True,
        "mileage": selected_candidate.mileage if selected_candidate else 58400,
        "mileage_input": str(selected_candidate.mileage if selected_candidate else 58400),
        "color": color,
        "trim_input": selected_candidate.trim if selected_candidate else "기본 트림",
        "transmission": transmission,
        "fuel": fuel,
        "warranty_type": warranty_type,
        "vin_condition": vin_condition,
        "meter_condition": meter_condition,
        "accident_history": accident_history,
        "simple_repair": simple_repair,
        "special_history": [],
        "usage_change": [],
        "color_history": [],
        "major_options": major_options,
        "recall_status": recall_status,
        "body_condition": 4,
        "interior_condition": 4,
        "wheel_tire_condition": 4,
        "documents": documents,
        "selected_candidate_id": selected_candidate.id if selected_candidate else f"{brand}-{model}-{year}-basic",
        "_accident_detail_keys": accident_detail_keys,
    }
    for field_key in accident_detail_keys:
        defaults[field_key] = "문제 없음"
    return defaults


def initialize_state(facade: "FrontendQueryFacade | None" = None) -> None:
    for key, value in default_session_values(facade).items():
        st.session_state.setdefault(key, deepcopy(value))


def reset_demo_state(facade: "FrontendQueryFacade | None" = None) -> None:
    for key, value in default_session_values(facade).items():
        st.session_state[key] = deepcopy(value)


def sync_purchase_date_text() -> None:
    raw_value = str(st.session_state.purchase_date_input).strip()
    try:
        parsed = date.fromisoformat(raw_value.replace(".", "-").replace("/", "-"))
    except ValueError:
        return

    st.session_state.purchase_date = parsed
    st.session_state.purchase_date_input = parsed.strftime("%Y/%m/%d")


def sync_mileage_text() -> None:
    digits = "".join(ch for ch in str(st.session_state.mileage_input) if ch.isdigit())
    if not digits:
        return

    mileage = int(digits)
    st.session_state.mileage = mileage
    st.session_state.mileage_input = str(mileage)


def read_form_state() -> VehicleFormState:
    accident_detail_keys = tuple(st.session_state.get("_accident_detail_keys", ()))
    accident_details = {
        field_key: str(st.session_state.get(field_key, "문제 없음"))
        for field_key in accident_detail_keys
    }
    return VehicleFormState(
        brand=str(st.session_state.brand),
        model=str(st.session_state.model),
        year=str(st.session_state.year),
        plate=str(st.session_state.plate),
        purchase_date=st.session_state.purchase_date,
        purchase_date_input=str(st.session_state.purchase_date_input),
        is_used_purchase=bool(st.session_state.is_used_purchase),
        mileage=int(st.session_state.mileage),
        mileage_input=str(st.session_state.mileage_input),
        color=str(st.session_state.color),
        trim_input=str(st.session_state.trim_input),
        transmission=str(st.session_state.transmission),
        fuel=str(st.session_state.fuel),
        warranty_type=str(st.session_state.warranty_type),
        vin_condition=str(st.session_state.vin_condition),
        meter_condition=str(st.session_state.meter_condition),
        accident_history=str(st.session_state.accident_history),
        simple_repair=str(st.session_state.simple_repair),
        special_history=list(st.session_state.special_history),
        usage_change=list(st.session_state.usage_change),
        color_history=list(st.session_state.color_history),
        major_options=list(st.session_state.major_options),
        recall_status=str(st.session_state.recall_status),
        body_condition=int(st.session_state.body_condition),
        interior_condition=int(st.session_state.interior_condition),
        wheel_tire_condition=int(st.session_state.wheel_tire_condition),
        documents=list(st.session_state.documents),
        selected_candidate_id=str(st.session_state.selected_candidate_id),
        accident_details=accident_details,
    )
