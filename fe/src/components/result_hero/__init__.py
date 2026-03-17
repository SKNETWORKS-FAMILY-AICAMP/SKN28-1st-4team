from html import escape

import streamlit as st

from models.form import VehicleFormState
from models.price import PriceResult


def render_result_hero(form_state: VehicleFormState, price: PriceResult) -> None:
    meta_markup = "".join(
        f'<div class="meta-item"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'
        for label, value in (
            ("구매 형태", "중고 구매" if form_state.is_used_purchase else "신차 구매"),
            ("사용 연료", form_state.fuel),
            ("사고 이력", form_state.accident_history),
            ("주요 옵션", ", ".join(form_state.major_options) if form_state.major_options else "기본형"),
        )
    )
    st.markdown(
        f"""
        <div class="result-hero">
          <div class="result-panel">
            <div class="eyebrow-tag">결과 요약</div>
            <div class="hero-price">{price.current_price:,}만원</div>
            <p class="section-subtitle">{escape(f'{form_state.brand} {form_state.model} · {form_state.trim_input}')} 기준 예측가입니다.</p>
            <div class="fair-range">{escape(f'적정 매도 범위 {price.fair_price_min:,}만원 ~ {price.fair_price_max:,}만원')}</div>
          </div>
          <div class="result-panel">
            <div class="section-title">차량 스냅샷</div>
            <p class="section-subtitle">{escape(f'{form_state.plate} · {form_state.color} · {form_state.mileage:,}km')}</p>
            <div class="meta-grid">{meta_markup}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
