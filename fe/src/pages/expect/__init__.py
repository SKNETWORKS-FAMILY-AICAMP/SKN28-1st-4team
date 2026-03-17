from collections.abc import Callable
import time

import streamlit as st

from components.factor_insights import render_factor_insights
from components.price_chart import render_price_chart
from components.result_hero import render_result_hero
from core.state import read_form_state
from models.form import VehicleFormState
from models.price import PriceFactorResult, PriceResult
from services.query_facade import FrontendQueryFacade


def render_expect_page(
    facade: FrontendQueryFacade,
    on_back: Callable[[], None],
    on_home: Callable[[], None],
) -> None:
    form_state = read_form_state()
    if not _has_required_prediction_inputs(form_state):
        st.title("현재 차량 예측 가격")
        st.warning("모델과 세부 트림을 먼저 선택한 뒤 다시 예측을 진행해주세요.")
        if st.button("입력 페이지로 돌아가기", width="stretch"):
            on_back()
        return

    price, factors = _load_expect_results(facade, form_state)

    top_back_col, _, top_home_col = st.columns([0.18, 0.56, 0.26], gap="small")
    with top_back_col:
        if st.button("← 돌아가기", width="stretch"):
            on_back()
    with top_home_col:
        if st.button("처음으로 돌아가기", key="expect-go-home", width="stretch"):
            on_home()

    st.title("현재 차량 예측 가격")
    st.caption("선택한 차량 조건을 기준으로 현재 시세와 향후 5년 하락 흐름을 정리했습니다.")
    render_result_hero(form_state, price)

    left, right = st.columns([1.2, 0.8], gap="large")
    with left:
        render_price_chart(price)
    with right:
        render_factor_insights(factors, on_back=on_back)


def _load_expect_results(
    facade: FrontendQueryFacade,
    form_state: VehicleFormState,
) -> tuple[PriceResult, PriceFactorResult]:
    request_key = _build_expect_request_key(form_state)
    cached_key = st.session_state.get("expect_result_key")
    loading_requested = bool(st.session_state.get("expect_loading_requested", False))

    if cached_key != request_key or loading_requested:
        started_at = time.monotonic()
        loading_anchor = st.empty()
        with loading_anchor.container():
            st.info("예측 데이터를 불러오는 중입니다. 잠시만 기다려주세요.")

        with st.status("예측 데이터를 불러오는 중입니다...", expanded=True) as status:
            status.update(label="현재 차량 예측가를 계산하는 중입니다...", state="running")
            price = facade.get_price_prediction(form_state)
            status.update(label="가격 상승/하락 요인을 분석하는 중입니다...", state="running")
            factors = facade.get_price_factors(form_state)
            minimum_visible_seconds = 0.8
            elapsed = time.monotonic() - started_at
            if elapsed < minimum_visible_seconds:
                time.sleep(minimum_visible_seconds - elapsed)
            status.update(label="예측 결과를 모두 불러왔습니다.", state="complete", expanded=True)

        loading_anchor.empty()

        st.session_state.expect_result_key = request_key
        st.session_state.expect_price_result = price
        st.session_state.expect_factor_result = factors
        st.session_state.expect_loading_requested = False

    return (
        st.session_state.expect_price_result,
        st.session_state.expect_factor_result,
    )


def _build_expect_request_key(form_state: VehicleFormState) -> tuple[object, ...]:
    return (
        form_state.brand,
        form_state.model,
        form_state.trim_input,
        form_state.plate,
        form_state.purchase_date.isoformat(),
        form_state.is_used_purchase,
        form_state.mileage,
        form_state.color,
        form_state.transmission,
    )


def _has_required_prediction_inputs(form_state: VehicleFormState) -> bool:
    return bool(
        form_state.brand.strip()
        and form_state.model.strip()
        and form_state.trim_input.strip()
        and form_state.color.strip()
    )
