from collections.abc import Callable
from html import escape

import streamlit as st

from models.form import VehicleFormState


def render_factor_insights(form_state: VehicleFormState, on_back: Callable[[], None]) -> None:
    positive_factors, negative_factors = _build_factor_lists(form_state)
    logic_note = (
        "현재는 facade가 development에서는 mock payload를, 다른 환경에서는 query helper를 통해 실제 API 응답을 받아오도록 구성돼 있습니다."
    )

    with st.container(border=True):
        st.markdown('<div class="factor-badge factor-badge-positive">상승 요인</div>', unsafe_allow_html=True)
        for item in positive_factors:
            st.markdown(f"- {item}")

    with st.container(border=True):
        st.markdown('<div class="factor-badge factor-badge-negative">하락 요인</div>', unsafe_allow_html=True)
        for item in negative_factors:
            st.markdown(f"- {item}")

    st.markdown(
        f"""
        <div class="insight-card">
          <strong>예측 로직 메모</strong>
          <p>{escape(logic_note)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2, gap="small")
    with col1:
        if st.button("차량 정보 다시 보기", width="stretch"):
            on_back()
    with col2:
        st.button("PDF 저장 준비", width="stretch", disabled=True)


def _build_factor_lists(form_state: VehicleFormState) -> tuple[tuple[str, ...], tuple[str, ...]]:
    positive: list[str] = []
    negative: list[str] = []

    if form_state.accident_history == "없음":
        positive.append("사고 이력이 없어 외판/골격 감가 요인이 상대적으로 적습니다.")
    else:
        negative.append("사고 이력이 있어 실제 매입 단계에서 추가 감가 가능성이 큽니다.")

    if form_state.mileage <= 40000:
        positive.append("주행거리가 낮은 편이라 동일 연식 대비 잔존가치 방어에 유리합니다.")
    elif form_state.mileage >= 70000:
        negative.append("주행거리가 높은 편이라 연식 대비 체감 감가가 크게 반영될 수 있습니다.")
    else:
        negative.append("주행거리가 누적 구간에 들어가 있어 시세 방어폭이 다소 줄어듭니다.")

    if len(form_state.major_options) >= 2:
        positive.append("선호 옵션이 갖춰져 있어 비교 매물 대비 관심도를 확보하기 좋습니다.")
    else:
        negative.append("선택 옵션 구성이 단순해 상위 트림 매물과 비교 시 매력도가 약할 수 있습니다.")

    if form_state.documents:
        positive.append("기본 서류 보유 항목이 있어 거래 신뢰도를 설명하기 수월합니다.")

    if form_state.is_used_purchase:
        negative.append("중고 구매 이력이 있어 매수자 관점에서는 추가 확인 포인트가 생깁니다.")
    else:
        positive.append("신차 구매 이력이라 소유 이력 설명이 단순하고 신뢰도를 주기 좋습니다.")

    if form_state.color in {"화이트 펄", "미드나잇 블랙", "블랙"}:
        positive.append("무난한 인기 색상 계열이라 재판매 시 수요 저항이 적은 편입니다.")
    else:
        negative.append("비선호 색상 계열로 분류될 수 있어 비교 매물 대비 선택폭이 좁아질 수 있습니다.")

    return tuple(positive[:4]), tuple(negative[:4])
