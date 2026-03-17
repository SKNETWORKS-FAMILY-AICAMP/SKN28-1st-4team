from collections.abc import Callable
from html import escape
from pathlib import Path

import streamlit as st


_DOCS_URL = "https://sknetworks-family-aicamp.github.io/SKN28-1st-4team/"
_LOGO_PATH = Path(__file__).resolve().parents[3] / "assets" / "Carbody_logo.png"
_DETAIL_CARDS = (
    ("현재 차량 예측 가격", "기본 정보와 세부 트림 선택값을 바로 반영합니다."),
    ("향후 가격 흐름", "감가 변화가 큰 시점을 빠르게 확인할 수 있습니다."),
    ("추가 입력 확장", "사고 이력과 옵션은 필요할 때만 더해 결과를 좁힙니다."),
)
_PREVIEW_METRICS = (
    ("현재 예측가", "2,186만원"),
    ("1년 후", "1,792만원"),
    ("주요 강점", "서류 보유 · 무사고"),
)


def render_landing_page(on_entry: Callable[[], None]) -> None:
    with st.container(key="landing-nav"):
        left, right = st.columns([0.28, 0.72], gap="small")
        with left:
            st.image(str(_LOGO_PATH), width=164)
        with right:
            st.empty()

    with st.container(key="landing-hero"):
        st.caption("차량 판매가 예측 서비스")
        st.title("내 차 판매가를 빠르게 예측하세요")
        st.markdown(
            "차량을 선택하고 몇 가지 기본 정보만 입력하면 현재 예측 가격과 "
            "향후 가격 흐름을 바로 확인할 수 있습니다."
        )

        _, action_left, action_right, _ = st.columns([1.1, 0.82, 0.82, 1.1], gap="small")
        with action_left:
            if st.button("예측 시작하기", type="primary", key="landing-hero-cta", width="stretch"):
                on_entry()
        with action_right:
            st.link_button("프로젝트 문서 보기", _DOCS_URL, width="stretch")

    with st.container(key="landing-showcase"):
        left, right = st.columns([0.48, 0.52], gap="large")
        with left:
            st.caption("가볍게 시작하기")
            st.subheader("차량을 선택하고 내 차 가격을 바로 확인해보세요")
            st.markdown(
                "브랜드, 모델, 세부 트림과 기본 차량 정보만 입력하면 "
                "현재 예측 가격과 향후 가격 흐름을 빠르게 살펴볼 수 있습니다."
            )
            for title, body in _DETAIL_CARDS:
                st.markdown(
                    f"""
                    <div class="landing-detail-card">
                      <strong>{escape(title)}</strong>
                      <p>{escape(body)}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        with right:
            st.markdown(_build_preview_markup(_PREVIEW_METRICS), unsafe_allow_html=True)


def _build_preview_markup(metrics: tuple[tuple[str, str], ...]) -> str:
    metric_markup = "".join(
        f'<div class="landing-preview-metric"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'
        for label, value in metrics
    )
    return f"""
    <div class="landing-preview-shell">
      <div class="landing-preview-pill">결과 카드 미리보기</div>
      <div class="landing-preview-price">2,186만원</div>
      <p class="landing-preview-copy">현재 시세, 향후 하락 흐름, 핵심 요인을 한 화면에서 바로 확인할 수 있게 구성했습니다.</p>
      <div class="landing-preview-metrics">{metric_markup}</div>
    </div>
    """
