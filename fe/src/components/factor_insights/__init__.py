from collections.abc import Callable
from html import escape

import streamlit as st

from models.price import PriceFactorResult


def render_factor_insights(factors: PriceFactorResult, on_back: Callable[[], None]) -> None:
    _render_factor_section(
        title="상승 요인",
        tone="positive",
        items=factors.positive_factors or ("현재 입력값 기준으로는 뚜렷한 상승 요인이 크지 않습니다.",),
    )
    _render_factor_section(
        title="하락 요인",
        tone="negative",
        items=factors.negative_factors or ("현재 입력값 기준으로는 뚜렷한 하락 요인이 크지 않습니다.",),
    )

    st.markdown(
        f"""
        <div class="insight-card">
          <strong>예측 로직 메모</strong>
          <p>{escape(factors.logic_note)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("차량 정보 다시 보기", width="stretch"):
        on_back()


def _render_factor_section(*, title: str, tone: str, items: tuple[str, ...]) -> None:
    list_markup = "".join(f"<li>{escape(item)}</li>" for item in items)
    st.markdown(
        f"""
        <div class="factor-section factor-section-{tone}">
          <div class="factor-badge factor-badge-{tone}">{escape(title)}</div>
          <ul class="factor-list">
            {list_markup}
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
