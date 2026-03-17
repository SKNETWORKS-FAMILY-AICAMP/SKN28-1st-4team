import streamlit as st

from components.accident_selector import render_accident_selector
from models.query import VehicleOptionsDTO


def render_history_tabs(options: VehicleOptionsDTO) -> None:
    show_accident_details = st.session_state.accident_history == "있음"

    with st.expander("더 자세히 입력하면 더 잘 알 수 있어요", expanded=False):
        tab1, tab2, tab3, tab4 = st.tabs(["사용 이력", "사고/이력", "옵션/서류", "컨디션"])

        with tab1:
            st.selectbox("사용 연료", list(options.fuel_options), key="fuel")
            st.selectbox("보증 유형", list(options.warranty_options), key="warranty_type")
            st.multiselect("용도 변경 이력", list(options.usage_change_options), key="usage_change")
            st.radio("리콜 상태", list(options.recall_options), key="recall_status", horizontal=True)

        with tab2:
            st.radio("차대번호 표기 상태", list(options.vin_condition_options), key="vin_condition", horizontal=True)
            st.radio("주행거리 및 계기 상태", list(options.meter_condition_options), key="meter_condition", horizontal=True)
            st.radio("사고 이력", list(options.accident_history_options), key="accident_history", horizontal=True)
            if show_accident_details:
                render_accident_selector(options.accident_detail_fields)
            st.radio("단순 수리", list(options.simple_repair_options), key="simple_repair", horizontal=True)
            st.multiselect("특별 이력", list(options.special_history_options), key="special_history")
            st.multiselect("색상 변경 이력", list(options.color_history_options), key="color_history")

        with tab3:
            st.multiselect("주요 옵션", list(options.major_option_options), key="major_options")
            st.multiselect("기본 품목 보유", list(options.document_options), key="documents")

        with tab4:
            st.slider("외관 상태", min_value=1, max_value=5, key="body_condition")
            st.slider("내장 상태", min_value=1, max_value=5, key="interior_condition")
            st.slider("휠/타이어 상태", min_value=1, max_value=5, key="wheel_tire_condition")
