from collections.abc import Callable

import streamlit as st

from components.basic_vehicle_form import render_basic_vehicle_form
from components.history_tabs import render_history_tabs
from components.input_summary import render_input_summary
from components.vehicle_selector import render_vehicle_selector
from core.state import read_form_state, sync_mileage_text, sync_purchase_date_text
from services.query_facade import FrontendQueryFacade


def render_entry_page(
    facade: FrontendQueryFacade,
    on_back: Callable[[], None],
    on_expect: Callable[[], None],
) -> None:
    catalog = facade.get_vehicle_catalog()
    options = catalog.options

    nav_col, _ = st.columns([0.2, 0.8], gap="small")
    with nav_col:
        if st.button("← 돌아가기", width="stretch", type="primary"):
            on_back()

    st.title("차량 정보 입력")

    with st.container(key="page-frame"):
        left, right = st.columns([1.42, 0.82], gap="large")

        with left:
            st.subheader("기본 차량 정보")
            st.caption("차량 번호, 구매 일자, 중고 구매 여부, 주행거리, 차량 색상부터 먼저 입력합니다.")
            st.info("더 자세히 입력하면 더 잘 알 수 있어요. 선택 입력은 아래 확장 영역에서 이어집니다.")
            render_basic_vehicle_form(
                color_options=options.color_options,
                transmission_options=options.transmission_options,
                on_mileage_change=sync_mileage_text,
                on_purchase_date_change=sync_purchase_date_text,
            )
            render_vehicle_selector(catalog)
            render_history_tabs(options)

        with right:
            render_input_summary(read_form_state(), on_expect=on_expect)
