from collections.abc import Callable

import streamlit as st


def render_basic_vehicle_form(
    color_options: tuple[str, ...],
    transmission_options: tuple[str, ...],
    on_mileage_change: Callable[[], None],
    on_purchase_date_change: Callable[[], None],
) -> None:
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.text_input("차량 번호", key="plate")
        st.text_input("주행거리 (km)", key="mileage_input", on_change=on_mileage_change)
        st.selectbox("차량 색상", list(color_options), key="color")
    with col2:
        st.date_input(
            "구매 일자",
            key="purchase_date",
            format="YYYY/MM/DD",
            on_change=on_purchase_date_change,
        )
        st.selectbox("변속기", list(transmission_options), key="transmission")
        st.toggle("중고 상태로 구매했어요", key="is_used_purchase")
