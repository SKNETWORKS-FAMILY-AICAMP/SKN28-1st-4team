from __future__ import annotations

from typing import Callable

import streamlit as st


def render_entry_page(
    render_tree_card: Callable[[], None],
    render_accident_detail_selector: Callable[[], None],
    sync_mileage_text: Callable[[], None],
    sync_purchase_date_text: Callable[[], None],
    color_tone: dict[str, int],
    on_back: Callable[[], None],
    on_expect: Callable[[], None],
) -> None:
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

            col1, col2 = st.columns(2, gap="medium")
            with col1:
                st.text_input("차량 번호", key="plate")
                st.text_input("주행거리 (km)", key="mileage_input", on_change=sync_mileage_text)
                st.selectbox("차량 색상", list(color_tone.keys()), key="color")
            with col2:
                st.text_input("구매 일자", key="purchase_date_input", on_change=sync_purchase_date_text)
                st.selectbox("변속기", ["자동", "수동", "세미오토", "무단변속기", "기타"], key="transmission")
                st.toggle("중고 상태로 구매했어요", key="is_used_purchase")

            render_tree_card()

            with st.expander("더 자세히 입력하면 더 잘 알 수 있어요", expanded=False):
                tab1, tab2, tab3, tab4 = st.tabs(
                    ["사용 이력", "사고/이력", "옵션/서류", "컨디션"]
                )

                with tab1:
                    st.selectbox(
                        "사용 연료",
                        ["가솔린", "디젤", "LPG", "하이브리드", "전기", "수소전기", "기타"],
                        key="fuel",
                    )
                    st.selectbox(
                        "보증 유형",
                        ["보험사보증", "자가보증"],
                        key="warranty_type",
                    )
                    st.multiselect(
                        "용도 변경 이력",
                        ["렌트", "영업용"],
                        key="usage_change",
                    )
                    st.radio(
                        "리콜 상태",
                        ["리콜 이행", "리콜 미이행", "해당없음"],
                        key="recall_status",
                        horizontal=True,
                    )

                with tab2:
                    st.radio(
                        "차대번호 표기 상태",
                        ["양호", "부식", "훼손(오손)", "상이", "변조(변타)", "도말"],
                        key="vin_condition",
                        horizontal=True,
                    )
                    st.radio(
                        "주행거리 및 계기 상태",
                        ["양호", "불량"],
                        key="meter_condition",
                        horizontal=True,
                    )
                    st.radio(
                        "사고 이력",
                        ["없음", "있음"],
                        key="accident_history",
                        horizontal=True,
                    )
                    if st.session_state.accident_history == "있음":
                        render_accident_detail_selector()
                    st.radio(
                        "단순 수리",
                        ["없음", "있음"],
                        key="simple_repair",
                        horizontal=True,
                    )
                    st.multiselect(
                        "특별 이력",
                        ["침수", "화재"],
                        key="special_history",
                    )
                    st.multiselect(
                        "색상 변경 이력",
                        ["전체도색", "색상변경"],
                        key="color_history",
                    )

                with tab3:
                    st.multiselect(
                        "주요 옵션",
                        ["썬루프", "네비게이션", "헤드업 디스플레이", "드라이브 어시스트", "통풍시트"],
                        key="major_options",
                    )
                    st.multiselect(
                        "기본 품목 보유",
                        ["사용설명서", "안전삼각대", "잭", "스패너"],
                        key="documents",
                    )

                with tab4:
                    st.slider("외관 상태", min_value=1, max_value=5, key="body_condition")
                    st.slider("내장 상태", min_value=1, max_value=5, key="interior_condition")
                    st.slider("휠/타이어 상태", min_value=1, max_value=5, key="wheel_tire_condition")

        with right:
            with st.container(key="summary-float"):
                with st.container(border=True):
                    st.markdown("##### 입력 요약")
                    summary_rows = [
                        ("브랜드", st.session_state.brand),
                        ("모델", st.session_state.model),
                        ("연식", st.session_state.year),
                        ("세부 트림", st.session_state.trim_input),
                        ("차량 색상", st.session_state.color),
                    ]
                    for label, value in summary_rows:
                        label_col, value_col = st.columns([0.42, 0.58], gap="small")
                        with label_col:
                            st.caption(label)
                        with value_col:
                            st.markdown(f"**{value}**")
                if st.button("현재 차량 예측 가격 보러가기", type="primary", width="stretch", key="go-result-sticky"):
                    on_expect()
