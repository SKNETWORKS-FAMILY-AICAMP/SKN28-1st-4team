import base64
from dataclasses import dataclass

import streamlit as st

from models.query import VehicleCandidateDTO, VehicleCatalogDTO


@dataclass(frozen=True)
class VehicleCardModel:
    id: str
    title: str
    subtitle: str
    description: str
    image_src: str
    selected: bool


def render_vehicle_selector(catalog: VehicleCatalogDTO) -> None:
    brand_options = catalog.brands
    if st.session_state.get("brand") not in brand_options:
        st.session_state.brand = brand_options[0]

    brand = str(st.session_state.brand)
    model_options = tuple(catalog.catalog[brand].keys())
    if st.session_state.get("model") not in model_options:
        st.session_state.model = model_options[0]

    model = str(st.session_state.model)
    year_options = catalog.catalog[brand][model]
    if st.session_state.get("year") not in year_options:
        st.session_state.year = year_options[0]

    year = str(st.session_state.year)
    candidates = _get_candidate_pool(catalog, brand, model, year)
    candidate_ids = {candidate.id for candidate in candidates}

    if st.session_state.get("selected_candidate_id") not in candidate_ids:
        selected_candidate = candidates[0]
        st.session_state.selected_candidate_id = selected_candidate.id
        st.session_state.trim_input = selected_candidate.trim

    selected_candidate_id = str(st.session_state.selected_candidate_id)
    cards = tuple(
        VehicleCardModel(
            id=candidate.id,
            title=f"{candidate.title} · {candidate.year}",
            subtitle=candidate.trim,
            description=f"{candidate.mileage:,}km · {candidate.fuel} · {candidate.color}",
            image_src=_build_candidate_image(candidate, brand),
            selected=candidate.id == selected_candidate_id,
        )
        for candidate in candidates
    )

    st.subheader("브랜드 · 모델 · 연식 선택")
    st.caption("브랜드부터 모델, 연식, 세부 트림까지 실제 선택 흐름처럼 드롭다운과 후보 카드로 정리했습니다.")

    st.selectbox("브랜드", list(brand_options), key="brand")
    st.selectbox("모델", list(model_options), key="model")
    st.selectbox("연식", list(year_options), key="year")
    st.text_input("세부 트림", key="trim_input")

    st.markdown("#### 선택 가능한 트림")
    columns = st.columns(3, gap="small")
    for index, card in enumerate(cards):
        button_key = f"trim-card-{card.id}"
        border_color = "rgba(22, 93, 255, 0.44)" if card.selected else "rgba(219, 231, 247, 0.96)"
        shadow_color = "0 12px 28px rgba(22, 93, 255, 0.12)" if card.selected else "0 6px 18px rgba(24, 54, 112, 0.05)"
        st.markdown(
            f"""
            <style>
            .st-key-{button_key} .stButton > button {{
              min-height: 186px;
              padding: 126px 14px 16px 14px;
              border-radius: 24px;
              border: 1px solid {border_color};
              box-shadow: {shadow_color};
              background:
                linear-gradient(180deg, #f4f8ff 0 112px, #ffffff 112px 100%),
                url("{card.image_src}");
              background-repeat: no-repeat, no-repeat;
              background-position: top left, center 12px;
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
              line-height: 1.42;
              font-size: 13px;
              font-weight: 700;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        with columns[index % 3]:
            if st.button(
                f"{card.title}\n{card.subtitle}\n{card.description}",
                key=button_key,
                type="secondary",
                width="stretch",
            ):
                _choose_candidate(card.id, catalog)


def _choose_candidate(candidate_id: str, catalog: VehicleCatalogDTO) -> None:
    brand = str(st.session_state.brand)
    model = str(st.session_state.model)
    year = str(st.session_state.year)
    for candidate in _get_candidate_pool(catalog, brand, model, year):
        if candidate.id == candidate_id:
            st.session_state.selected_candidate_id = candidate.id
            st.session_state.trim_input = candidate.trim
            break


def _get_candidate_pool(
    catalog: VehicleCatalogDTO,
    brand: str,
    model: str,
    year: str,
) -> list[VehicleCandidateDTO]:
    candidates = [candidate for candidate in catalog.candidates_by_model.get(model, ()) if candidate.year == year]
    if candidates:
        return candidates

    default_color = catalog.options.color_options[0]
    return [
        VehicleCandidateDTO(
            id=f"{brand}-{model}-{year}-basic",
            title=model,
            year=year,
            trim="기본 트림",
            mileage=36200,
            fuel="가솔린",
            color=default_color,
        ),
        VehicleCandidateDTO(
            id=f"{brand}-{model}-{year}-premium",
            title=model,
            year=year,
            trim="상위 트림",
            mileage=18700,
            fuel="가솔린",
            color="화이트 펄" if "화이트 펄" in catalog.color_tones else default_color,
        ),
    ]


def _candidate_palette(brand: str) -> tuple[str, str]:
    return {
        "현대": ("#2A67F7", "#B9D1FF"),
        "기아": ("#2457D3", "#CFE0FF"),
        "제네시스": ("#163A6F", "#D2DDF6"),
        "쉐보레": ("#275CDB", "#D8E4FF"),
        "BMW": ("#1558E8", "#BFD6FF"),
        "벤츠": ("#24526B", "#D8E7F1"),
    }.get(brand, ("#2A67F7", "#B9D1FF"))


def _build_candidate_image(candidate: VehicleCandidateDTO, brand: str) -> str:
    primary, secondary = _candidate_palette(brand)
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
      <text x="24" y="28" fill="#36548B" font-size="12" font-family="Arial, sans-serif">{candidate.year}</text>
    </svg>
    """
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"
