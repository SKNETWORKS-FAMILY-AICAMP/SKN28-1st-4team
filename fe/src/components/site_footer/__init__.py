import streamlit as st

from core.routing import Route


def render_site_footer(route: Route) -> None:
    page_label = {"landing": "Landing", "entry": "Entry", "expect": "Expect"}[route]
    st.divider()
    with st.container(key="global-footer"):
        with st.container(border=True):
            left, center, right = st.columns([0.5, 0.18, 0.32], gap="medium")
            with left:
                st.markdown("##### 차량 예상 판매가")
                st.caption("중고차 시세 예측 서비스")
            with center:
                st.caption("Page")
                st.caption(page_label)
            with right:
                st.caption("Links")
                st.caption("이용약관 · 개인정보처리방침 · 문의")
            st.caption("Copyright 2026. Vehicle Price.")
