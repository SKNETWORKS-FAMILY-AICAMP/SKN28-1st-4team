from collections.abc import Callable
from html import escape

import streamlit as st

from models.form import VehicleFormState


def render_input_summary(form_state: VehicleFormState, on_expect: Callable[[], None]) -> None:
    lines_markup = "".join(
        f'<div class="summary-line"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'
        for label, value in (
            ("브랜드", form_state.brand),
            ("모델", form_state.model),
            ("연식", form_state.year),
            ("세부 트림", form_state.trim_input),
            ("차량 색상", form_state.color),
        )
    )

    with st.container(key="summary-float"):
        with st.container(border=True):
            st.markdown("##### 입력 요약")
            st.markdown(f'<div class="summary-stack">{lines_markup}</div>', unsafe_allow_html=True)
        if st.button("현재 차량 예측 가격 보러가기", type="primary", width="stretch"):
            on_expect()
