from typing import Literal, cast

import streamlit as st

Route = Literal["landing", "entry", "expect"]

_VALID_ROUTES = {"landing", "entry", "expect"}
_LEGACY_ROUTE_MAP = {
    "input": "entry",
    "result": "expect",
}


def get_current_route() -> Route:
    raw_page = st.query_params.get("page", st.session_state.get("page", "landing"))
    if isinstance(raw_page, list):
        raw_page = raw_page[0] if raw_page else "landing"

    page = _LEGACY_ROUTE_MAP.get(str(raw_page), str(raw_page))
    if page not in _VALID_ROUTES:
        page = "landing"

    st.session_state["page"] = page
    st.query_params["page"] = page
    return cast(Route, page)


def set_route(route: Route) -> None:
    st.session_state["page"] = route
    st.query_params["page"] = route


def reroute(route: Route) -> None:
    set_route(route)
    st.rerun()
