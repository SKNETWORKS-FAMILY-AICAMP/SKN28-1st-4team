from __future__ import annotations
from pathlib import Path
from typing import Callable

import streamlit as st


def render_landing_page(on_entry: Callable[[], None], on_expect: Callable[[], None]) -> None:
    del on_expect

    logo_path = Path(__file__).with_name("carbody.png")
    expect_preview_path = Path(__file__).parent / "images" / "playwright" / "expect-factors-layout.png"

    with st.container(key="landing-nav"):
        nav_left, nav_right = st.columns([0.26, 0.74], gap="small")
        with nav_left:
            st.image(str(logo_path), width=180)
        with nav_right:
            st.empty()

    with st.container(key="landing-hero"):
        st.caption("현재 차량 예측 가격 서비스")
        st.title("내 차 판매가를 빠르게 예측하세요")
        st.markdown(
            "차량 번호와 기본 차량 정보, 세부 트림만 정리하면 현재 차량 예측 가격과  \n"
            "향후 가격 흐름, 매도 타이밍까지 한 번에 확인할 수 있습니다."
        )

        with st.container(key="landing-hero-actions"):
            _, hero_cta_left, hero_cta_right, _ = st.columns([1.2, 0.82, 0.82, 1.2], gap="small")
            with hero_cta_left:
                if st.button("예측 시작하기", type="primary", key="landing-hero-cta", width="stretch"):
                    on_entry()
            with hero_cta_right:
                st.link_button(
                    "프로젝트 문서 보기",
                    "https://sknetworks-family-aicamp.github.io/SKN28-1st-4team/",
                    width="stretch",
                )

    with st.container(key="landing-dark-cta"):
        dark_left, dark_right = st.columns([0.46, 0.54], gap="large")
        with dark_left:
            st.caption("빠르게 시작하기")
            st.title("차량 정보 입력부터 예상 판매가 확인까지 한 흐름으로 이어집니다")
            st.markdown(
                "기본 차량 정보와 세부 트림을 먼저 입력하고,  \n"
                "필요할 때만 추가 항목을 더해 예상 가격과 매도 타이밍을 확인할 수 있습니다."
            )
            with st.container(key="landing-dark-details"):
                preview_points = [
                    ("현재 차량 예측 가격", "기본 정보와 세부 트림 선택값을 바로 반영합니다."),
                    ("향후 가격 흐름", "감가 변화가 큰 시점을 빠르게 확인할 수 있습니다."),
                    ("추가 입력 확장", "사고 이력과 옵션은 필요할 때만 더해 결과를 좁힙니다."),
                ]
                for title, body in preview_points:
                    st.markdown(
                        f"""
                        <div class="landing-detail-card">
                          <strong>{title}</strong>
                          <p>{body}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            cta_a, cta_b = st.columns([0.42, 0.42], gap="small")
            with cta_a:
                if st.button("예측 시작하기", key="landing-dark-cta-primary", width="stretch"):
                    on_entry()
            with cta_b:
                st.link_button(
                    "프로젝트 문서 보기",
                    "https://sknetworks-family-aicamp.github.io/SKN28-1st-4team/",
                    width="stretch",
                )
        with dark_right:
            with st.container(key="landing-dark-preview"):
                st.caption("예측 결과 페이지 미리보기")
                st.image(str(expect_preview_path), use_container_width=True)
