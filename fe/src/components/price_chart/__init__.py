from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from models.price import PriceResult


def render_price_chart(price: PriceResult) -> None:
    chart_frame = _build_chart_frame(price)

    st.subheader("향후 5년 가격 하락 그래프")
    st.caption("현재 예측가를 기준으로 향후 5년 감가 흐름을 함께 봅니다.")

    st.plotly_chart(
        _build_price_figure(chart_frame),
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
    )

    st.markdown(_build_projection_cards_markup(chart_frame), unsafe_allow_html=True)

    st.markdown(f'<div class="chart-caption">{escape(price.suggestion)}</div>', unsafe_allow_html=True)

    st.markdown(_build_timing_cards_markup(chart_frame), unsafe_allow_html=True)


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
    chart_frame["순서"] = range(len(chart_frame))
    return chart_frame


def _build_price_figure(chart_frame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=chart_frame["시점"],
            y=chart_frame["예측가격"],
            mode="lines+markers",
            line={"color": "#165DFF", "width": 3},
            marker={"color": "#165DFF", "size": 8},
            hovertemplate="<b>%{x}</b><br>%{y:,}만원<extra></extra>",
        )
    )
    figure.update_layout(
        height=360,
        margin={"l": 20, "r": 20, "t": 18, "b": 20},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        showlegend=False,
        font={"color": "#132342", "family": "Plus Jakarta Sans, Noto Sans KR, sans-serif"},
    )
    figure.update_xaxes(
        title_text="시점",
        showgrid=False,
        linecolor="#dbe7f7",
        tickfont={"color": "#475569"},
        title_font={"color": "#475569"},
    )
    figure.update_yaxes(
        title_text="예측가격(만원)",
        gridcolor="#e7eefb",
        zeroline=False,
        linecolor="#dbe7f7",
        tickfont={"color": "#475569"},
        title_font={"color": "#475569"},
    )
    return figure


def _build_projection_cards_markup(chart_frame: pd.DataFrame) -> str:
    card_markup = "".join(
        (
            '<div class="projection-card">'
            f'<span>{escape(str(row["시점"]))}</span>'
            f'<strong>{int(row["예측가격"]):,}만원</strong>'
            "</div>"
        )
        for _, row in chart_frame.iterrows()
    )
    return f'<div class="projection-card-grid">{card_markup}</div>'


def _build_timing_cards_markup(chart_frame: pd.DataFrame) -> str:
    metric_markup = "".join(
        (
            '<div class="timing-card">'
            f"<span>{escape(label)}</span>"
            f"<strong>{escape(value)}</strong>"
            "</div>"
        )
        for label, value in _build_timing_metrics(chart_frame)
    )
    return (
        '<div class="timing-card-shell">'
        '<div class="timing-card-title">매도 타이밍 힌트</div>'
        f'<div class="timing-card-grid">{metric_markup}</div>'
        "</div>"
    )


def _build_timing_metrics(chart_frame: pd.DataFrame) -> tuple[tuple[str, str], ...]:
    biggest_window, biggest_drop = _biggest_drop_window(chart_frame)
    return (
        ("현재", f"{int(chart_frame.loc[chart_frame['시점'] == '현재', '예측가격'].iloc[0]):,}만원"),
        ("1년 후", f"{int(chart_frame.loc[chart_frame['시점'] == '1년 후', '예측가격'].iloc[0]):,}만원"),
        ("3년 후", f"{int(chart_frame.loc[chart_frame['시점'] == '3년 후', '예측가격'].iloc[0]):,}만원"),
        ("5년 후", f"{int(chart_frame.loc[chart_frame['시점'] == '5년 후', '예측가격'].iloc[0]):,}만원"),
        ("급격한 하락 구간", f"{biggest_window} ({biggest_drop:,}만원)"),
    )


def _biggest_drop_window(chart_frame: pd.DataFrame) -> tuple[str, int]:
    comparison_points = chart_frame[chart_frame["phase"].isin(["current", "future"])].copy()
    comparison_points["prev_price"] = comparison_points["예측가격"].shift(1)
    comparison_points["prev_label"] = comparison_points["시점"].shift(1)
    comparison_points["drop_amount"] = (
        comparison_points["prev_price"] - comparison_points["예측가격"]
    ).abs()
    biggest = comparison_points.dropna(subset=["drop_amount"]).sort_values("drop_amount", ascending=False).iloc[0]
    return f"{biggest['prev_label']} -> {biggest['시점']}", int(biggest["drop_amount"])
