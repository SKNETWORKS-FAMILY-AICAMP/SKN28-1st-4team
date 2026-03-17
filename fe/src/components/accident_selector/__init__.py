import streamlit as st

from models.query import AccidentDetailFieldDTO


def render_accident_selector(accident_detail_fields: tuple[AccidentDetailFieldDTO, ...]) -> None:
    with st.container(border=True):
        st.markdown("##### 사고 부위 선택")
        st.caption("세부 부품 대신 큰 항목 기준으로 상태를 고릅니다.")
        columns = st.columns(2, gap="medium")
        for index, field in enumerate(accident_detail_fields):
            with columns[index % 2]:
                with st.container(border=True):
                    st.markdown(f"**{field.label}**")
                    st.radio(
                        field.label,
                        ["문제 없음", "문제 있음"],
                        key=field.key,
                        horizontal=True,
                        label_visibility="collapsed",
                    )
