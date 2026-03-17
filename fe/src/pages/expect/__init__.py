from collections.abc import Callable

import streamlit as st

from components.factor_insights import render_factor_insights
from components.price_chart import render_price_chart
from components.result_hero import render_result_hero
from core.state import read_form_state
from services.query_facade import FrontendQueryFacade


def render_expect_page(facade: FrontendQueryFacade, on_back: Callable[[], None]) -> None:
    form_state = read_form_state()
    price = facade.get_price_prediction(form_state)

    top_back_col, _ = st.columns([0.2, 0.8], gap="small")
    with top_back_col:
        if st.button("← 돌아가기", width="stretch", type="primary"):
            on_back()

    st.title("현재 차량 예측 가격")
    st.caption("선택한 차량 조건을 기준으로 현재 시세와 향후 5년 하락 흐름을 정리했습니다.")
    render_result_hero(form_state, price)

    left, right = st.columns([1.2, 0.8], gap="large")
    with left:
        render_price_chart(price)
    with right:
        render_factor_insights(form_state, on_back=on_back)
