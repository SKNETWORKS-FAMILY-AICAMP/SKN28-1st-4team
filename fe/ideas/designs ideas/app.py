from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List

import altair as alt
import pandas as pd
import streamlit as st

from entry_page import render_entry_page
from expect_page import render_expect_page
from landing_page import render_landing_page


st.set_page_config(
    page_title="차량 예측 가격 시뮬레이터",
    layout="wide",
    initial_sidebar_state="collapsed",
)


CATALOG: Dict[str, Dict[str, List[str]]] = {
    "현대": {
        "아반떼": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "쏘나타": ["2025년형", "2024년형", "2023년형", "2022년형", "2021년형"],
        "그랜저": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "투싼": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "싼타페": ["2025년형", "2024년형", "2023년형", "2022년형"],
    },
    "기아": {
        "K5": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "K8": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "쏘렌토": ["2025년형", "2024년형", "2023년형", "2022년형", "2021년형"],
        "스포티지": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "카니발": ["2025년형", "2024년형", "2023년형", "2022년형"],
    },
    "제네시스": {
        "G70": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "G80": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "GV70": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "GV80": ["2025년형", "2024년형", "2023년형", "2022년형"],
    },
    "쉐보레": {
        "트레일블레이저": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "말리부": ["2024년형", "2023년형", "2022년형", "2021년형"],
        "트래버스": ["2025년형", "2024년형", "2023년형", "2022년형"],
    },
    "BMW": {
        "3시리즈": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "5시리즈": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "X3": ["2025년형", "2024년형", "2023년형", "2022년형"],
    },
    "벤츠": {
        "C-클래스": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "E-클래스": ["2025년형", "2024년형", "2023년형", "2022년형"],
        "GLC": ["2025년형", "2024년형", "2023년형", "2022년형"],
    },
}


MODEL_BASE_PRICE = {
    "아반떼": 1780,
    "쏘나타": 2140,
    "그랜저": 3120,
    "투싼": 2480,
    "싼타페": 2970,
    "K5": 2090,
    "K8": 3250,
    "쏘렌토": 3180,
    "스포티지": 2360,
    "카니발": 3390,
    "G70": 3380,
    "G80": 4680,
    "GV70": 4550,
    "GV80": 6120,
    "트레일블레이저": 1940,
    "말리부": 1760,
    "트래버스": 3880,
    "3시리즈": 4510,
    "5시리즈": 6120,
    "X3": 5280,
    "C-클래스": 4980,
    "E-클래스": 6710,
    "GLC": 5890,
}


COLOR_TONE = {
    "화이트": 0,
    "블랙": 25,
    "실버": 12,
    "그레이": 8,
    "블루": -18,
    "레드": -25,
    "화이트 펄": 18,
    "미드나잇 블랙": 28,
    "티타늄 실버": 14,
    "어비스 블루": 10,
    "다크 그린": -12,
    "샴페인 골드": 6,
    "버건디": -14,
    "아이보리": 4,
}


ACCIDENT_DETAIL_FIELDS = [
    ("accident_front", "전면부"),
    ("accident_left_side", "좌측면"),
    ("accident_right_side", "우측면"),
    ("accident_rear", "후면부"),
    ("accident_roof_pillar", "루프·필러"),
    ("accident_underbody", "하부·서스펜션"),
    ("accident_frame", "주요 골격"),
]


CANDIDATE_LIBRARY: Dict[str, List[Dict[str, object]]] = {
    "쏘나타": [
        {"id": "sonata-1", "title": "쏘나타 디 엣지", "year": "2023년형", "trim": "2.0 가솔린 익스클루시브", "mileage": 58400, "fuel": "가솔린", "color": "화이트 펄"},
        {"id": "sonata-1b", "title": "쏘나타 디 엣지", "year": "2023년형", "trim": "2.0 가솔린 프리미엄", "mileage": 46300, "fuel": "가솔린", "color": "티타늄 실버"},
        {"id": "sonata-2", "title": "쏘나타 디 엣지", "year": "2024년형", "trim": "1.6 터보 인스퍼레이션", "mileage": 22100, "fuel": "가솔린", "color": "어비스 블루"},
        {"id": "sonata-3", "title": "쏘나타 센슈어스", "year": "2021년형", "trim": "1.6 터보 프리미엄 플러스", "mileage": 71200, "fuel": "가솔린", "color": "미드나잇 블랙"},
    ],
    "K5": [
        {"id": "k5-1", "title": "더 뉴 K5", "year": "2024년형", "trim": "2.0 가솔린 노블레스", "mileage": 31800, "fuel": "가솔린", "color": "미드나잇 블랙"},
        {"id": "k5-2", "title": "더 뉴 K5", "year": "2023년형", "trim": "1.6 터보 시그니처", "mileage": 42700, "fuel": "가솔린", "color": "화이트 펄"},
    ],
    "그랜저": [
        {"id": "grandeur-1", "title": "디 올 뉴 그랜저", "year": "2023년형", "trim": "2.5 캘리그래피", "mileage": 18600, "fuel": "가솔린", "color": "티타늄 실버"},
        {"id": "grandeur-2", "title": "디 올 뉴 그랜저", "year": "2024년형", "trim": "하이브리드 익스클루시브", "mileage": 9700, "fuel": "하이브리드", "color": "미드나잇 블랙"},
    ],
}


@dataclass
class PriceResult:
    current_price: int
    fair_price_min: int
    fair_price_max: int
    confidence: int
    suggestion: str
    chart_data: pd.DataFrame


def inject_style() -> None:
    css_path = Path(__file__).parent / "styles" / "theme.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def init_state() -> None:
    defaults = default_state_values()
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def default_state_values() -> dict[str, object]:
    return {
        "brand": "현대",
        "model": "쏘나타",
        "year": "2023년형",
        "plate": "128가 4321",
        "purchase_date": date(2021, 5, 14),
        "purchase_date_input": "2021/05/14",
        "is_used_purchase": True,
        "mileage": 58400,
        "mileage_input": "58400",
        "color": "화이트 펄",
        "trim_input": "2.0 가솔린 익스클루시브",
        "transmission": "자동",
        "fuel": "가솔린",
        "warranty_type": "보험사보증",
        "vin_condition": "양호",
        "meter_condition": "양호",
        "accident_history": "없음",
        "simple_repair": "있음",
        "special_history": [],
        "usage_change": [],
        "color_history": [],
        "major_options": ["네비게이션"],
        "recall_status": "리콜 이행",
        "body_condition": 4,
        "interior_condition": 4,
        "wheel_tire_condition": 4,
        "documents": ["사용설명서", "안전삼각대"],
        "selected_candidate_id": "sonata-1",
        "accident_front": "문제 없음",
        "accident_left_side": "문제 없음",
        "accident_right_side": "문제 없음",
        "accident_rear": "문제 없음",
        "accident_roof_pillar": "문제 없음",
        "accident_underbody": "문제 없음",
        "accident_frame": "문제 없음",
    }


def restore_demo_state() -> None:
    for key, value in default_state_values().items():
        st.session_state[key] = value


def sync_purchase_date_text() -> None:
    raw = str(st.session_state.purchase_date_input).strip()
    try:
        parsed = date.fromisoformat(raw.replace(".", "-").replace("/", "-"))
    except ValueError:
        return
    st.session_state.purchase_date = parsed
    st.session_state.purchase_date_input = parsed.strftime("%Y/%m/%d")


def sync_mileage_text() -> None:
    digits = "".join(ch for ch in str(st.session_state.mileage_input) if ch.isdigit())
    if not digits:
        return
    mileage = int(digits)
    st.session_state.mileage = mileage
    st.session_state.mileage_input = str(mileage)


def route_page(page_name: str) -> None:
    st.query_params["page"] = page_name
    st.session_state["page"] = page_name


def current_page() -> str:
    legacy_page_map = {
        "input": "entry",
        "result": "expect",
    }
    page = st.query_params.get("page", st.session_state.get("page", "landing"))
    page = legacy_page_map.get(page, page)
    if page not in {"landing", "entry", "expect"}:
        page = "landing"
    st.session_state["page"] = page
    return page


def get_candidate_pool(brand: str, model: str) -> List[Dict[str, object]]:
    candidates = CANDIDATE_LIBRARY.get(model)
    if candidates:
        filtered = [candidate for candidate in candidates if candidate["year"] == st.session_state.year]
        if filtered:
            return filtered
    years = CATALOG[brand][model]
    default_color = next(iter(COLOR_TONE.keys()))
    return [
        {
            "id": f"{brand}-{model}-1",
            "title": model,
            "year": st.session_state.year,
            "trim": "기본 트림",
            "mileage": 36200,
            "fuel": "가솔린",
            "color": default_color,
        },
        {
            "id": f"{brand}-{model}-2",
            "title": model,
            "year": st.session_state.year,
            "trim": "상위 트림",
            "mileage": 18700,
            "fuel": "가솔린",
            "color": "화이트 펄" if "화이트 펄" in COLOR_TONE else default_color,
        },
    ]


def sync_candidate_selection() -> None:
    candidate_pool = get_candidate_pool(st.session_state.brand, st.session_state.model)
    candidate_ids = [candidate["id"] for candidate in candidate_pool]
    if st.session_state.selected_candidate_id not in candidate_ids:
        st.session_state.selected_candidate_id = candidate_ids[0]


def apply_candidate(candidate: Dict[str, object]) -> None:
    st.session_state.selected_candidate_id = str(candidate["id"])
    st.session_state.trim_input = str(candidate["trim"])


def choose_trim(candidate_id: str) -> None:
    pool = get_candidate_pool(st.session_state.brand, st.session_state.model)
    for candidate in pool:
        if str(candidate["id"]) == candidate_id:
            apply_candidate(candidate)
            break


def render_accident_detail_selector() -> None:
    st.write("")
    with st.container(border=True):
        st.markdown("##### 사고 부위 선택")
        st.caption("세부 부품 대신 큰 항목 기준으로 상태를 고릅니다.")
        columns = st.columns(2, gap="medium")
        for index, (field_key, label) in enumerate(ACCIDENT_DETAIL_FIELDS):
            with columns[index % 2]:
                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    st.radio(
                        label,
                        ["문제 없음", "문제 있음"],
                        key=field_key,
                        horizontal=True,
                        label_visibility="collapsed",
                    )


def candidate_palette(brand: str) -> tuple[str, str]:
    return {
        "현대": ("#2A67F7", "#B9D1FF"),
        "기아": ("#2457D3", "#CFE0FF"),
        "제네시스": ("#163A6F", "#D2DDF6"),
        "쉐보레": ("#275CDB", "#D8E4FF"),
        "BMW": ("#1558E8", "#BFD6FF"),
        "벤츠": ("#24526B", "#D8E7F1"),
    }.get(brand, ("#2A67F7", "#B9D1FF"))


def build_candidate_image(candidate: Dict[str, object], brand: str) -> str:
    primary, secondary = candidate_palette(brand)
    svg = f"""
    <svg viewBox="0 0 320 150" xmlns="http://www.w3.org/2000/svg" fill="none">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="320" y2="150" gradientUnits="userSpaceOnUse">
          <stop stop-color="#F8FBFF"/>
          <stop offset="1" stop-color="#E1ECFF"/>
        </linearGradient>
        <linearGradient id="car" x1="18" y1="32" x2="284" y2="130" gradientUnits="userSpaceOnUse">
          <stop stop-color="{secondary}"/>
          <stop offset="1" stop-color="{primary}"/>
        </linearGradient>
      </defs>
      <rect width="320" height="150" rx="24" fill="url(#bg)"/>
      <circle cx="84" cy="120" r="18" fill="#213457"/>
      <circle cx="84" cy="120" r="8" fill="#EAF1FF"/>
      <circle cx="235" cy="120" r="18" fill="#213457"/>
      <circle cx="235" cy="120" r="8" fill="#EAF1FF"/>
      <path d="M54 100C62 75 78 56 109 48C137 40 186 40 213 47C239 54 261 74 272 95L286 96C293 97 300 103 300 112V119C300 127 293 134 285 134H276C271 146 260 150 246 150C232 150 221 146 216 134H104C99 146 88 150 74 150C60 150 49 146 44 134H34C26 134 20 128 20 120V108C20 102 24 97 31 96L54 100Z" fill="url(#car)"/>
      <path d="M95 58C110 47 191 45 213 53C230 59 248 73 256 90H73C77 79 84 67 95 58Z" fill="#F9FBFF"/>
      <path d="M110 65C123 57 184 57 201 63C214 68 228 79 234 90H88C92 81 100 71 110 65Z" fill="#DCE8FF"/>
      <rect x="227" y="72" width="28" height="7" rx="3.5" fill="{primary}"/>
      <rect x="31" y="102" width="25" height="8" rx="4" fill="#D1DFFF"/>
      <rect x="267" y="102" width="24" height="8" rx="4" fill="#D1DFFF"/>
    </svg>
    """
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def render_candidate_cards(candidate_pool: List[Dict[str, object]], brand: str) -> None:
    columns = st.columns(3, gap="small")
    for index, candidate in enumerate(candidate_pool):
        image_src = build_candidate_image(candidate, brand)
        button_key = f"trim-card-button-{candidate['id']}"
        selected = candidate["id"] == st.session_state.selected_candidate_id
        border_color = "rgba(22, 93, 255, 0.42)" if selected else "rgba(219, 231, 247, 0.96)"
        shadow_color = "0 12px 28px rgba(22, 93, 255, 0.12)" if selected else "0 6px 18px rgba(24, 54, 112, 0.05)"
        st.markdown(
            f"""
            <style>
            .st-key-{button_key} .stButton > button {{
              position: relative;
              min-height: 178px;
              padding: 124px 14px 16px 14px;
              border-radius: 24px;
              border: 1px solid {border_color};
              box-shadow: {shadow_color};
              background:
                linear-gradient(180deg, #f4f8ff 0 110px, #ffffff 110px 100%),
                url("{image_src}");
              background-repeat: no-repeat, no-repeat;
              background-position: top left, center 10px;
              background-size: 100% 100%, calc(100% - 28px) 92px;
              align-items: flex-end;
              justify-content: flex-start;
              text-align: left;
              color: #132342;
            }}
            .st-key-{button_key} .stButton > button:hover {{
              transform: translateY(-2px);
              box-shadow: 0 12px 24px rgba(37, 73, 150, 0.10);
              border-color: rgba(22, 93, 255, 0.28);
            }}
            .st-key-{button_key} .stButton > button p {{
              margin: 0;
              white-space: pre-line;
              line-height: 1.4;
              font-size: 13px;
              font-weight: 700;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        with columns[index % 3]:
            st.button(
                f"{candidate['title']} · {candidate['year']}\n{candidate['trim']}",
                key=button_key,
                on_click=choose_trim,
                args=(str(candidate["id"]),),
                width="stretch",
                type="secondary",
            )


def compute_price() -> PriceResult:
    base_price = MODEL_BASE_PRICE.get(st.session_state.model, 2200)
    mileage_penalty = max(st.session_state.mileage - 30000, 0) * 0.0028
    used_penalty = 95 if st.session_state.is_used_purchase else 0
    color_delta = COLOR_TONE.get(st.session_state.color, 0)
    accident_detail_penalty = sum(
        34
        for field_key, _ in ACCIDENT_DETAIL_FIELDS
        if st.session_state.get(field_key) == "문제 있음"
    )
    frame_penalty = 90 if st.session_state.get("accident_frame") == "문제 있음" else 0
    accident_penalty = (180 + accident_detail_penalty + frame_penalty) if st.session_state.accident_history == "있음" else 0
    repair_penalty = 55 if st.session_state.simple_repair == "있음" else 0
    special_penalty = len(st.session_state.special_history) * 120
    usage_penalty = len(st.session_state.usage_change) * 80
    color_history_penalty = len(st.session_state.color_history) * 40
    option_bonus = len(st.session_state.major_options) * 22
    doc_bonus = len(st.session_state.documents) * 6
    condition_bonus = (
        st.session_state.body_condition
        + st.session_state.interior_condition
        + st.session_state.wheel_tire_condition
    ) * 9

    current_price = int(
        max(
            650,
            round(
                base_price
                - mileage_penalty
                - used_penalty
                - accident_penalty
                - repair_penalty
                - special_penalty
                - usage_penalty
                - color_history_penalty
                + option_bonus
                + doc_bonus
                + condition_bonus
                + color_delta
            ),
        )
    )

    confidence = 72 + min(len(st.session_state.major_options) * 2, 8)
    confidence += 6 if st.session_state.vin_condition == "양호" else 0
    confidence += 4 if st.session_state.meter_condition == "양호" else 0
    confidence = min(confidence, 94)

    current_year = date.today().year
    chart_points = [
        {
            "시점": "최근 시세",
            "연도": f"{current_year - 1}년",
            "예측가격": int(round(current_price * 0.94)),
            "구간": "과거 더미",
            "phase": "past",
            "순서": 0,
            "라벨표시": False,
        },
        {
            "시점": "현재",
            "연도": f"{current_year}년",
            "예측가격": current_price,
            "구간": "기준 시점",
            "phase": "current",
            "순서": 1,
            "라벨표시": True,
        },
    ]
    decline_rates = [0.18, 0.15, 0.17, 0.16, 0.14]
    projected_price = current_price
    for offset, decline_rate in enumerate(decline_rates, start=1):
        projected_price = int(round(projected_price * (1 - decline_rate)))
        chart_points.append(
            {
                "시점": f"{offset}년 후",
                "연도": f"{current_year + offset}년",
                "예측가격": projected_price,
                "구간": "완만한 하락" if offset <= 2 else "하락 폭 확대",
                "phase": "future",
                "순서": offset + 1,
                "라벨표시": True,
            }
        )

    chart_data = pd.DataFrame(chart_points)
    fair_span = 110 + len(st.session_state.major_options) * 12

    third_year_price = int(chart_data.loc[chart_data["시점"] == "3년 후", "예측가격"].iloc[0])
    if third_year_price < current_price * 0.65:
        suggestion = "2~3년 차부터 감가가 더 가팔라지는 설정이라, 중기 이전 매도 시점을 먼저 보는 편이 유리합니다."
    else:
        suggestion = "감가 추세가 완만한 편이라 1~2년 내 매도 압박은 크지 않습니다."

    return PriceResult(
        current_price=current_price,
        fair_price_min=current_price - fair_span,
        fair_price_max=current_price + fair_span,
        confidence=confidence,
        suggestion=suggestion,
        chart_data=chart_data,
    )


def render_header(price: PriceResult, page: str) -> None:
    if page == "input":
        title = "입력과 선택을 먼저 정리하는 1페이지"
        desc = (
            "기본 차량 정보와 브랜드/모델 선택을 먼저 배치하고, 성능상태점검기록부에 가까운 추가 항목은 "
            "확장 입력으로 분리해 사용자가 필요할 때만 더 자세히 입력할 수 있게 구성했습니다."
        )
        badge = "1페이지 · 정보 입력"
    else:
        title = "현재 차량 예측 가격과 5년 하락 흐름을 보는 2페이지"
        desc = (
            "입력이 끝난 뒤에는 현재 차량 예측 가격을 크게 보여주고, 앞으로 5년 동안 언제 가격 하락 폭이 커지는지 "
            "그래프로 바로 판단할 수 있도록 결과 화면을 분리했습니다."
        )
        badge = "2페이지 · 결과 보기"

    st.caption(badge)
    st.title(title)
    st.write(desc)
    st.write("")


def render_footer(page: str) -> None:
    page_label = {
        "landing": "Landing",
        "entry": "Entry",
        "expect": "Expect",
    }.get(page, page)

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


def render_tree_card() -> None:
    st.subheader("브랜드 · 모델 · 연식 선택")
    st.caption("브랜드부터 모델, 연식, 세부 트림까지 실제 선택 흐름처럼 드롭다운으로 정리했습니다.")

    brand = st.selectbox("브랜드", list(CATALOG.keys()), key="brand")
    models = list(CATALOG[brand].keys())
    if st.session_state.model not in models:
        st.session_state.model = models[0]
    model = st.selectbox("모델", models, key="model")
    years = CATALOG[brand][model]
    if st.session_state.year not in years:
        st.session_state.year = years[0]
    st.selectbox("연식", years, key="year")
    st.text_input("세부 트림", key="trim_input")
    sync_candidate_selection()

    candidate_pool = get_candidate_pool(brand, model)
    st.markdown("#### 선택 가능한 트림")
    render_candidate_cards(candidate_pool, brand)


def render_input_page(price: PriceResult) -> None:
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
                st.selectbox("차량 색상", list(COLOR_TONE.keys()), key="color")
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
                    route_page("result")
                    st.rerun()


def render_result_page(price: PriceResult) -> None:
    top_back_col, _ = st.columns([0.18, 0.82], gap="small")
    with top_back_col:
        if st.button("돌아가기", width="stretch"):
            route_page("input")
            st.rerun()

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

    left, right = st.columns([1.2, 0.8], gap="large")

    with left:
        st.markdown(
            """
            <div class="section-card">
              <h3 class="section-title">향후 5년 가격 하락 그래프</h3>
              <div class="section-subtitle">
                기본 뷰는 향후 5년입니다. 어느 시점부터 하락폭이 커지는지 바로 확인할 수 있게 구간 색을 나눴습니다.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        data = price.chart_data
        labels_order = data["시점"].tolist()
        y_min = max(int(data["예측가격"].min() * 0.88), 400)
        y_max = int(data["예측가격"].max() * 1.08)

        future_data = data[data["phase"].isin(["current", "future"])]
        past_data = data[data["phase"].isin(["past", "current"])]
        label_data = data[data["라벨표시"]]

        x_encoding = alt.X(
            "시점:N",
            sort=labels_order,
            axis=alt.Axis(labelAngle=0, labelColor="#5D6F90", title=None, tickSize=0, domain=False),
        )
        y_encoding = alt.Y(
            "예측가격:Q",
            axis=alt.Axis(labelColor="#5D6F90", title=None, gridColor="#E8F0FF", tickCount=5),
            scale=alt.Scale(domain=[y_min, y_max], nice=False),
        )

        base = alt.Chart(data).encode(
            x=x_encoding,
            y=y_encoding,
        )

        area = alt.Chart(future_data).mark_area(
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="#2E63F6", offset=0),
                    alt.GradientStop(color="#DCE8FF", offset=1),
                ],
                x1=1,
                x2=1,
                y1=1,
                y2=0,
            ),
            opacity=0.32,
        ).encode(x=x_encoding, y=y_encoding)

        future_line = alt.Chart(future_data).mark_line(
            color="#2D5BEB",
            strokeWidth=3.2,
            interpolate="monotone",
        ).encode(x=x_encoding, y=y_encoding)

        past_line = alt.Chart(past_data).mark_line(
            color="#9FB7F6",
            strokeWidth=2.3,
            strokeDash=[6, 6],
            interpolate="monotone",
        ).encode(x=x_encoding, y=y_encoding)

        future_points = alt.Chart(future_data[future_data["phase"] == "future"]).mark_circle(
            size=95,
            color="#3E6DFF",
            stroke="#FFFFFF",
            strokeWidth=2,
        ).encode(x=x_encoding, y=y_encoding)

        current_point = alt.Chart(data[data["phase"] == "current"]).mark_circle(
            size=250,
            color="#123FB8",
            stroke="#FFFFFF",
            strokeWidth=3,
        ).encode(x=x_encoding, y=y_encoding)

        current_rule = alt.Chart(data[data["phase"] == "current"]).mark_rule(
            color="#B9CDFC",
            strokeWidth=1.5,
            strokeDash=[4, 4],
        ).encode(x=x_encoding)

        labels = alt.Chart(label_data).mark_text(
            dy=-18,
            color="#0E42BD",
            fontWeight="bold",
            fontSize=13,
        ).encode(
            x=x_encoding,
            y=y_encoding,
            text=alt.Text("예측가격:Q", format=","),
        )
        chart = (
            alt.layer(current_rule, area, past_line, future_line, future_points, current_point, labels)
            .properties(height=268)
            .configure_view(stroke=None)
            .configure_axis(labelFontSize=12, titleFontSize=12)
        )
        st.altair_chart(chart, width="stretch")

        st.markdown(
            f"""
            <div class="chart-caption">
              {price.suggestion}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        first_year = int(data.loc[data["시점"] == "1년 후", "예측가격"].iloc[0])
        third_year = int(data.loc[data["시점"] == "3년 후", "예측가격"].iloc[0])
        fifth_year = int(data.loc[data["시점"] == "5년 후", "예측가격"].iloc[0])

        st.markdown(
            f"""
            <div class="summary-card">
              <div class="pill active">매도 타이밍 힌트</div>
              <div class="meta-grid" style="margin-top:18px;">
                <div class="meta-item">
                  <span>1년 후</span>
                  <strong>{first_year:,}만원</strong>
                </div>
                <div class="meta-item">
                  <span>3년 후</span>
                  <strong>{third_year:,}만원</strong>
                </div>
                <div class="meta-item">
                  <span>5년 후</span>
                  <strong>{fifth_year:,}만원</strong>
                </div>
                <div class="meta-item">
                  <span>하락 구간</span>
                  <strong>{data.loc[data["시점"] == "3년 후", "구간"].iloc[0]}</strong>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="insight-card">
              <strong>예측 로직 메모</strong>
              <p>
                모델 기준가, 주행거리, 사고/수리 이력, 특별 이력, 서류 보유, 주요 옵션, 외관/내장/휠 상태를 반영해 현재 차량 예측 가격을 계산합니다.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2, gap="small")
        with col1:
            if st.button("1페이지로 돌아가기", width="stretch"):
                route_page("input")
                st.rerun()
        with col2:
            st.button("PDF 저장 준비", width="stretch", disabled=True)


def main() -> None:
    inject_style()
    init_state()
    page = current_page()

    def go(page_name: str) -> None:
        route_page(page_name)
        st.rerun()

    if page == "landing":
        render_landing_page(
            on_entry=lambda: (restore_demo_state(), go("entry")),
            on_expect=lambda: (restore_demo_state(), go("expect")),
        )
    elif page == "entry":
        render_entry_page(
            render_tree_card=render_tree_card,
            render_accident_detail_selector=render_accident_detail_selector,
            sync_mileage_text=sync_mileage_text,
            sync_purchase_date_text=sync_purchase_date_text,
            color_tone=COLOR_TONE,
            on_back=lambda: go("landing"),
            on_expect=lambda: go("expect"),
        )
    else:
        price = compute_price()
        render_expect_page(
            price=price,
            on_back=lambda: go("entry"),
        )
    render_footer(page)


if __name__ == "__main__":
    main()
