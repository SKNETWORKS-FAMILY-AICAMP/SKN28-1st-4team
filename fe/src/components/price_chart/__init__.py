from html import escape

import pandas as pd
import streamlit as st

from models.price import PriceResult


def render_price_chart(price: PriceResult) -> None:
    chart_frame = _build_chart_frame(price)
    recent_price = int(chart_frame.loc[chart_frame["phase"] == "past", "예측가격"].iloc[0])

    st.subheader("향후 5년 가격 하락 그래프")
    st.caption(f"최근 시세 가이드 {recent_price:,}만원부터 현재 기준가와 향후 하락 폭을 같이 봅니다.")

    st.line_chart(
        chart_frame[["연도값", "예측가격"]].copy(),
        x="연도값",
        y="예측가격",
        color="#165DFF",
        height=360,
        width="stretch",
    )

    point_columns = st.columns(len(chart_frame), gap="small")
    for column, (_, row) in zip(point_columns, chart_frame.iterrows()):
        with column:
            with st.container(border=True):
                st.caption(str(row["시점"]))
                st.markdown(f"**{int(row['예측가격']):,}만원**")

    st.markdown(f'<div class="chart-caption">{escape(price.suggestion)}</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("##### 매도 타이밍 힌트")
        columns = st.columns(4, gap="small")
        for column, (label, value) in zip(columns, _build_timing_metrics(chart_frame)):
            with column:
                st.caption(label)
                st.markdown(f"**{value}**")


def _build_chart_frame(price: PriceResult) -> pd.DataFrame:
    chart_frame = pd.DataFrame(
        {
            "시점": point.label,
            "연도": point.year_label,
            "예측가격": point.price,
            "구간": point.segment,
            "phase": point.phase,
            "라벨표시": point.show_label,
        }
        for point in price.chart_points
    )
    chart_frame["연도값"] = chart_frame["연도"].str.replace("년", "", regex=False).astype(int)
    return chart_frame


def _build_timing_metrics(chart_frame: pd.DataFrame) -> tuple[tuple[str, str], ...]:
    biggest_window, biggest_drop = _biggest_drop_window(chart_frame)
    return (
        ("1년 후", f"{int(chart_frame.loc[chart_frame['시점'] == '1년 후', '예측가격'].iloc[0]):,}만원"),
        ("3년 후", f"{int(chart_frame.loc[chart_frame['시점'] == '3년 후', '예측가격'].iloc[0]):,}만원"),
        ("5년 후", f"{int(chart_frame.loc[chart_frame['시점'] == '5년 후', '예측가격'].iloc[0]):,}만원"),
        ("급격한 하락 구간", f"{biggest_window} ({biggest_drop:,}만원)"),
    )


def _biggest_drop_window(chart_frame: pd.DataFrame) -> tuple[str, int]:
    future_points = chart_frame[chart_frame["phase"].isin(["current", "future"])].copy()
    future_points["prev_price"] = future_points["예측가격"].shift(1)
    future_points["prev_label"] = future_points["시점"].shift(1)
    future_points["drop_amount"] = (future_points["prev_price"] - future_points["예측가격"]).abs()
    biggest = future_points.dropna(subset=["drop_amount"]).sort_values("drop_amount", ascending=False).iloc[0]
    return f"{biggest['prev_label']} -> {biggest['시점']}", int(biggest["drop_amount"])
