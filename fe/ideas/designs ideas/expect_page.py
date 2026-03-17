from __future__ import annotations

import pandas as pd
import streamlit as st


def build_demo_factors() -> tuple[list[str], list[str]]:
    positive: list[str] = []
    negative: list[str] = []

    if st.session_state.accident_history == "없음":
        positive.append("사고 이력이 없어 외판/골격 감가 요인이 상대적으로 적습니다.")
    else:
        negative.append("사고 이력이 있어 실제 매입 단계에서 추가 감가 가능성이 큽니다.")

    if st.session_state.mileage <= 40000:
        positive.append("주행거리가 낮은 편이라 동일 연식 대비 잔존가치 방어에 유리합니다.")
    elif st.session_state.mileage >= 70000:
        negative.append("주행거리가 높은 편이라 연식 대비 체감 감가가 크게 반영될 수 있습니다.")
    else:
        negative.append("주행거리가 누적 구간에 들어가 있어 시세 방어폭이 다소 줄어듭니다.")

    if len(st.session_state.major_options) >= 2:
        positive.append("선호 옵션이 갖춰져 있어 비교 매물 대비 관심도를 확보하기 좋습니다.")
    else:
        negative.append("선택 옵션 구성이 단순해 상위 트림 매물과 비교 시 매력도가 약할 수 있습니다.")

    if st.session_state.documents:
        positive.append("기본 서류 보유 항목이 있어 거래 신뢰도를 설명하기 수월합니다.")

    if st.session_state.is_used_purchase:
        negative.append("중고 구매 이력이 있어 매수자 관점에서는 추가 확인 포인트가 생깁니다.")
    else:
        positive.append("신차 구매 이력이라 소유 이력 설명이 단순하고 신뢰도를 주기 좋습니다.")

    if st.session_state.color in {"화이트 펄", "미드나잇 블랙", "블랙"}:
        positive.append("무난한 인기 색상 계열이라 재판매 시 수요 저항이 적은 편입니다.")
    else:
        negative.append("비선호 색상 계열로 분류될 수 있어 비교 매물 대비 선택폭이 좁아질 수 있습니다.")

    return positive[:4], negative[:4]


def biggest_drop_window(data: pd.DataFrame) -> tuple[str, int]:
    future_points = data[data["phase"].isin(["current", "future"])].copy()
    future_points["prev_price"] = future_points["예측가격"].shift(1)
    future_points["prev_label"] = future_points["시점"].shift(1)
    future_points["drop_amount"] = (future_points["prev_price"] - future_points["예측가격"]).abs()
    biggest = future_points.dropna(subset=["drop_amount"]).sort_values("drop_amount", ascending=False).iloc[0]
    return f"{biggest['prev_label']} -> {biggest['시점']}", int(biggest["drop_amount"])


def render_expect_page(price, on_back) -> None:
    top_back_col, _ = st.columns([0.2, 0.8], gap="small")
    with top_back_col:
        if st.button("← 돌아가기", width="stretch", type="primary"):
            on_back()

    st.title("현재 차량 예측 가격")
    st.caption("선택한 차량 조건을 기준으로 현재 시세와 향후 5년 하락 흐름을 정리했습니다.")

    st.markdown(
        f"""
        <div class="result-hero">
          <div class="result-panel">
            <div class="eyebrow">결과 요약</div>
            <div class="section-title" style="margin-top:18px;">현재 차량 예측 가격</div>
            <div class="result-price">
              <div class="big">{price.current_price:,}만원</div>
              <div class="drop-tag">신뢰도 {price.confidence}점</div>
            </div>
            <div class="section-subtitle" style="max-width:680px;">
              {st.session_state.brand} {st.session_state.model} {st.session_state.year} · {st.session_state.trim_input} 기준입니다.
              선택 입력이 늘수록 가격 범위와 하락 시점 해석이 더 구체적으로 좁혀집니다.
            </div>
            <div class="mini-note" style="margin-top:18px;">
              적정 매도 범위 {price.fair_price_min:,}만원 ~ {price.fair_price_max:,}만원
            </div>
          </div>
          <div class="result-panel">
            <div class="section-title">차량 스냅샷</div>
            <div class="section-subtitle">{st.session_state.plate} · {st.session_state.color} · {st.session_state.mileage:,}km</div>
            <div class="meta-grid" style="margin-top:20px;">
              <div class="meta-item">
                <span>구매 형태</span>
                <strong>{"중고 구매" if st.session_state.is_used_purchase else "신차 구매"}</strong>
              </div>
              <div class="meta-item">
                <span>사용 연료</span>
                <strong>{st.session_state.fuel}</strong>
              </div>
              <div class="meta-item">
                <span>사고 이력</span>
                <strong>{st.session_state.accident_history}</strong>
              </div>
              <div class="meta-item">
                <span>주요 옵션</span>
                <strong>{", ".join(st.session_state.major_options) if st.session_state.major_options else "기본형"}</strong>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    data = price.chart_data
    sharpest_window, sharpest_drop = biggest_drop_window(data)
    left, right = st.columns([1.2, 0.8], gap="large")

    with left:
        st.subheader("향후 5년 가격 하락 그래프")
        recent_price = int(data.loc[data["phase"] == "past", "예측가격"].iloc[0])
        st.caption(f"최근 시세 가이드 {recent_price:,}만원부터 현재 기준가와 향후 하락 폭을 같이 봅니다.")
        chart_data = data.copy()
        chart_data["연도값"] = chart_data["연도"].str.replace("년", "", regex=False).astype(int)
        st.line_chart(
            chart_data,
            x="연도값",
            y="예측가격",
            color="#165DFF",
            height=420,
            width="stretch",
        )

        first_year = int(data.loc[data["시점"] == "1년 후", "예측가격"].iloc[0])
        third_year = int(data.loc[data["시점"] == "3년 후", "예측가격"].iloc[0])
        fifth_year = int(data.loc[data["시점"] == "5년 후", "예측가격"].iloc[0])
        point_cols = st.columns(len(chart_data), gap="small")
        point_items = [
            ("최근", recent_price),
            ("현재", price.current_price),
            ("+1년", first_year),
            ("+2년", int(data.loc[data["시점"] == "2년 후", "예측가격"].iloc[0])),
            ("+3년", third_year),
            ("+4년", int(data.loc[data["시점"] == "4년 후", "예측가격"].iloc[0])),
            ("+5년", fifth_year),
        ]
        for column, (label, value) in zip(point_cols, point_items):
            with column:
                with st.container(border=True):
                    st.caption(label)
                    st.markdown(f"**{value:,}만원**")

        st.write("")
        with st.container(border=True):
            st.markdown("##### 매도 타이밍 힌트")
            timing_cols = st.columns(4, gap="small")
            timing_items = [
                ("1년 후", f"{first_year:,}만원"),
                ("3년 후", f"{third_year:,}만원"),
                ("5년 후", f"{fifth_year:,}만원"),
                ("급격한 하락 구간", f"{sharpest_window} ({sharpest_drop:,}만원)"),
            ]
            for column, (label, value) in zip(timing_cols, timing_items):
                with column:
                    st.caption(label)
                    st.markdown(f"**{value}**")

    with right:
        positive_factors, negative_factors = build_demo_factors()

        with st.container(border=True):
            st.markdown('<div class="factor-badge factor-badge-positive">상승 요인</div>', unsafe_allow_html=True)
            for item in positive_factors:
                st.markdown(f"- {item}")

        with st.container(border=True):
            st.markdown('<div class="factor-badge factor-badge-negative">하락 요인</div>', unsafe_allow_html=True)
            for item in negative_factors:
                st.markdown(f"- {item}")

        with st.container(border=True):
            st.markdown("##### 예측 로직 메모")
            st.caption(
                "LLM 요약이 들어갈 영역입니다. 현재는 입력값을 기준으로 만든 데모 문구를 노출하고 있습니다."
            )

        col1, col2 = st.columns(2, gap="small")
        with col1:
            if st.button("차량 정보 다시 보기", width="stretch"):
                on_back()
        with col2:
            st.button("PDF 저장 준비", width="stretch", disabled=True)
