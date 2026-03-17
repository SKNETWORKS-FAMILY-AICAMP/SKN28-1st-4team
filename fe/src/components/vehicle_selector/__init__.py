from dataclasses import dataclass
import unicodedata

import streamlit as st

from models.query import VehicleCandidateDTO, VehicleCatalogDTO, VehicleModelOptionDTO
from services.query_facade import FrontendQueryFacade

MODEL_CARDS_PER_PAGE = 9
SEARCH_NORMALIZATION_MAP = {
    "ᅢ": "ᅦ",
    "ᅤ": "ᅨ",
    "ᄊ": "ᄉ",
    "ᆻ": "ᆺ",
}


@dataclass(frozen=True)
class ModelCardView:
    id: str
    brand: str
    model: str
    image_src: str
    selected: bool


@dataclass(frozen=True)
class TrimCardView:
    id: str
    trim: str
    selected: bool


def render_vehicle_selector(
    catalog: VehicleCatalogDTO,
    facade: FrontendQueryFacade,
) -> None:
    brand_options = catalog.brands
    if st.session_state.get("brand") not in brand_options:
        st.session_state.brand = brand_options[0]

    if "model_search_query_draft" not in st.session_state:
        st.session_state.model_search_query_draft = ""
    if "model_search_query" not in st.session_state:
        st.session_state.model_search_query = ""
    if "model_picker_open" not in st.session_state:
        st.session_state.model_picker_open = True
    if "model_picker_page" not in st.session_state:
        st.session_state.model_picker_page = 0
    if "model_picker_prev_brand" not in st.session_state:
        st.session_state.model_picker_prev_brand = ""
    if "model_picker_prev_query" not in st.session_state:
        st.session_state.model_picker_prev_query = ""

    st.subheader("브랜드 · 모델 · 세부 트림 선택")
    st.caption("브랜드를 고른 뒤 모델을 검색하고 카드를 선택하면, 해당 모델의 세부 트림만 바로 선택할 수 있게 구성했습니다.")

    st.selectbox("브랜드", list(brand_options), key="brand")
    brand = str(st.session_state.brand)

    model_names = tuple(catalog.catalog.get(brand, {}).keys())
    current_model = str(st.session_state.get("model", ""))
    if current_model and current_model not in model_names:
        print(
            "[vehicle_selector] reset invalid selected model",
            {
                "brand": brand,
                "invalid_model": current_model,
            },
        )
        _reset_model_selection()

    with st.form("model-search-form", border=False):
        search_col, search_action_col, search_reset_col = st.columns([0.72, 0.14, 0.14], gap="small")
        with search_col:
            st.text_input(
                "모델 검색",
                key="model_search_query_draft",
                placeholder="예: 쏘나타, 소나타, 팰리세이드",
            )
        with search_action_col:
            st.form_submit_button("검색", width="stretch", on_click=_apply_model_search)
        with search_reset_col:
            st.form_submit_button("초기화", width="stretch", on_click=_clear_model_search)

    search_query = str(st.session_state.get("model_search_query", "")).strip()
    if (
        st.session_state.model_picker_prev_brand != brand
        or st.session_state.model_picker_prev_query != search_query
    ):
        st.session_state.model_picker_page = 0
        st.session_state.model_picker_prev_brand = brand
        st.session_state.model_picker_prev_query = search_query
        print(
            "[vehicle_selector] search state changed",
            {
                "brand": brand,
                "search_query": search_query,
                "page": st.session_state.model_picker_page,
            },
        )

    selected_model = str(st.session_state.model)
    _render_selected_model_panel(brand, selected_model)

    if selected_model:
        action_col, spacer_col = st.columns([0.22, 0.78], gap="small")
        with action_col:
            st.button(
                "모델 다시 선택",
                key="reopen-model-picker",
                width="stretch",
                on_click=_reopen_model_picker,
            )

    show_model_picker = bool(st.session_state.model_picker_open or search_query or not selected_model)
    if show_model_picker:
        filtered_model_names = _filter_model_names(model_names, search_query)
        print(
            "[vehicle_selector] filtered models",
            {
                "brand": brand,
                "search_query": search_query,
                "filtered_count": len(filtered_model_names),
                "preview": list(filtered_model_names[:9]),
            },
        )
        if not filtered_model_names:
            st.info("검색 결과가 없습니다. 다른 키워드로 다시 검색해보세요.")
            filtered_model_names = model_names

        _render_model_cards(
            facade=facade,
            brand_key=catalog.brand_keys_by_label[brand],
            brand_label=brand,
            model_names=filtered_model_names,
        )

    if not selected_model:
        st.info("모델 카드를 눌러 차량 모델을 먼저 선택하세요.")
        return

    trim_options = catalog.catalog.get(brand, {}).get(selected_model, ())
    candidates = _get_candidate_pool(catalog, brand, selected_model)
    candidate_ids = {candidate.id for candidate in candidates}

    if st.session_state.get("selected_candidate_id") not in candidate_ids:
        st.session_state.selected_candidate_id = ""

    if st.session_state.get("trim_input") not in trim_options:
        st.session_state.trim_input = ""

    if trim_options:
        st.markdown("#### 선택 가능한 트림")
        st.caption("모델별로 등록된 세부 트림만 카드로 노출합니다.")
        _render_trim_cards(candidates)


def _render_selected_model_panel(brand: str, model: str) -> None:
    if not model:
        return

    st.markdown(
        f"""
        <div style="
            margin: 8px 0 14px 0;
            padding: 14px 16px;
            border: 1px solid rgba(22, 93, 255, 0.18);
            border-radius: 18px;
            background: linear-gradient(180deg, #f6f9ff 0%, #ffffff 100%);
            color: #132342;
        ">
          <div style="font-size:12px; color:#5a6f95; margin-bottom:6px;">선택된 모델</div>
          <div style="font-size:18px; font-weight:700;">{model}</div>
          <div style="font-size:13px; color:#48628e; margin-top:4px;">브랜드: {brand}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _reopen_model_picker() -> None:
    st.session_state.model_picker_open = True
    st.session_state.model_search_query_draft = ""
    st.session_state.model_search_query = ""
    st.session_state.model_picker_page = 0


def _reset_model_selection() -> None:
    st.session_state.model = ""
    st.session_state.selected_candidate_id = ""
    st.session_state.trim_input = ""
    st.session_state.model_picker_open = True
    st.session_state.model_search_query_draft = ""
    st.session_state.model_search_query = ""
    st.session_state.model_picker_page = 0


def _select_model(model: str) -> None:
    st.session_state.model = model
    st.session_state.selected_candidate_id = ""
    st.session_state.trim_input = ""
    st.session_state.model_picker_open = False
    st.session_state.model_search_query_draft = ""
    st.session_state.model_search_query = ""


def _apply_model_search() -> None:
    st.session_state.model_search_query = str(
        st.session_state.get("model_search_query_draft", "")
    ).strip()
    st.session_state.model_picker_page = 0
    st.session_state.model_picker_open = True
    print(
        "[vehicle_selector] apply search",
        {
            "brand": str(st.session_state.get("brand", "")),
            "search_query": st.session_state.model_search_query,
        },
    )


def _clear_model_search() -> None:
    st.session_state.model_search_query_draft = ""
    st.session_state.model_search_query = ""
    st.session_state.model_picker_page = 0
    st.session_state.model_picker_open = True
    print(
        "[vehicle_selector] clear search",
        {
            "brand": str(st.session_state.get("brand", "")),
        },
    )


def _filter_model_names(
    model_names: tuple[str, ...],
    search_query: str,
) -> tuple[str, ...]:
    if not search_query:
        return model_names

    normalized_query = search_query.casefold()
    search_query_token = _normalize_search_token(search_query)
    return tuple(
        model_name
        for model_name in model_names
        if normalized_query in model_name.casefold()
        or search_query_token in _normalize_search_token(model_name)
    )


def _normalize_search_token(value: str) -> str:
    normalized_characters: list[str] = []
    for character in unicodedata.normalize("NFD", value.casefold()):
        remapped_character = SEARCH_NORMALIZATION_MAP.get(character, character)
        if remapped_character.isalnum() or "ᄀ" <= remapped_character <= "ᇿ":
            normalized_characters.append(remapped_character)
    return "".join(normalized_characters)


def _render_model_cards(
    *,
    facade: FrontendQueryFacade,
    brand_key: str,
    brand_label: str,
    model_names: tuple[str, ...],
) -> None:
    total_count = len(model_names)
    current_page = int(st.session_state.get("model_picker_page", 0))
    max_page = max((total_count - 1) // MODEL_CARDS_PER_PAGE, 0)
    current_page = max(0, min(current_page, max_page))
    st.session_state.model_picker_page = current_page

    start_index = current_page * MODEL_CARDS_PER_PAGE
    end_index = start_index + MODEL_CARDS_PER_PAGE
    visible_model_names = model_names[start_index:end_index]
    print(
        "[vehicle_selector] page slice",
        {
            "page": current_page + 1,
            "max_page": max_page + 1,
            "visible_model_names": list(visible_model_names),
        },
    )
    visible_model_options = facade.get_vehicle_model_images(
        brand_key=brand_key,
        brand_label=brand_label,
        model_names=tuple(visible_model_names),
    )

    model_cards = tuple(
        ModelCardView(
            id=item.id,
            brand=item.brand,
            model=item.model,
            image_src=item.image_src,
            selected=item.model == st.session_state.get("model"),
        )
        for item in visible_model_options
    )

    st.markdown("#### 모델 선택")
    st.caption(
        f"총 {total_count}개 모델 중 {start_index + 1}~{min(end_index, total_count)}개를 보고 있습니다."
    )

    pager_left, pager_center, pager_right = st.columns([0.2, 0.6, 0.2], gap="small")
    with pager_left:
        st.button(
            "이전",
            key="model-page-prev",
            width="stretch",
            disabled=current_page == 0,
            on_click=_change_model_page,
            args=(-1, max_page),
        )
    with pager_center:
        st.markdown(
            f"<div style='text-align:center; padding-top:8px; color:#5a6f95;'>페이지 {current_page + 1} / {max_page + 1}</div>",
            unsafe_allow_html=True,
        )
    with pager_right:
        st.button(
            "다음",
            key="model-page-next",
            width="stretch",
            disabled=current_page >= max_page,
            on_click=_change_model_page,
            args=(1, max_page),
        )

    for start in range(0, len(model_cards), 3):
        columns = st.columns(3, gap="small")
        for offset, card in enumerate(model_cards[start:start + 3]):
            button_key = f"model-card-{card.id}"
            shell_key = f"model-card-shell-{card.id}"
            st.markdown(
                f"""
                <style>
                .st-key-{shell_key} [data-testid="stImage"] {{
                  width: 100%;
                  margin-bottom: 10px;
                }}
                .st-key-{shell_key} [data-testid="stImage"] img {{
                  width: 100%;
                  height: 170px;
                  object-fit: cover;
                  border-radius: 16px;
                  background: #eef4ff;
                }}
                .st-key-{shell_key} [data-testid="stImage"] > div {{
                  width: 100%;
                }}
                .st-key-{shell_key} [data-testid="stCaptionContainer"] p {{
                  min-height: 20px;
                  margin-bottom: 8px;
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )
            with columns[offset]:
                with st.container(key=shell_key, border=True):
                    if card.image_src:
                        st.image(card.image_src, width="stretch")
                    else:
                        st.caption("이미지 없음")
                    st.caption(card.brand)
                    st.button(
                        card.model,
                        key=button_key,
                        type="primary" if card.selected else "secondary",
                        width="stretch",
                        on_click=_select_model,
                        args=(card.model,),
                    )


def _change_model_page(delta: int, max_page: int) -> None:
    current_page = int(st.session_state.get("model_picker_page", 0))
    next_page = max(0, min(current_page + delta, max_page))
    st.session_state.model_picker_page = next_page


def _render_trim_cards(candidates: list[VehicleCandidateDTO]) -> None:
    trim_cards = tuple(
        TrimCardView(
            id=candidate.id,
            trim=candidate.trim,
            selected=candidate.id == st.session_state.get("selected_candidate_id"),
        )
        for candidate in candidates
    )

    columns = st.columns(4, gap="small")
    for index, card in enumerate(trim_cards):
        button_key = f"trim-card-{card.id}"
        border_color = "rgba(22, 93, 255, 0.44)" if card.selected else "rgba(219, 231, 247, 0.96)"
        background_color = "linear-gradient(180deg, #edf4ff 0%, #ffffff 100%)" if card.selected else "#ffffff"
        st.markdown(
            f"""
            <style>
            .st-key-{button_key} .stButton > button {{
              min-height: 92px;
              padding: 16px 14px;
              border-radius: 18px;
              border: 1px solid {border_color};
              background: {background_color};
              box-shadow: 0 6px 16px rgba(24, 54, 112, 0.05);
              align-items: center;
              justify-content: center;
              text-align: center;
              color: #132342;
            }}
            .st-key-{button_key} .stButton > button p {{
              margin: 0;
              white-space: normal;
              line-height: 1.35;
              font-size: 14px;
              font-weight: 700;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        with columns[index % 4]:
            if st.button(card.trim, key=button_key, type="secondary", width="stretch"):
                st.session_state.selected_candidate_id = card.id
                st.session_state.trim_input = card.trim


def _get_candidate_pool(
    catalog: VehicleCatalogDTO,
    brand: str,
    model: str,
) -> list[VehicleCandidateDTO]:
    candidates = list(catalog.candidates_by_model.get(model, ()))
    if candidates:
        return candidates

    default_color = catalog.options.color_options[0]
    return [
        VehicleCandidateDTO(
            id=f"{brand}-{model}-basic",
            title=model,
            year="",
            trim="기본 트림",
            mileage=0,
            fuel="가솔린",
            color=default_color,
        )
    ]
