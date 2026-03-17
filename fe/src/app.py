import sys
from pathlib import Path

import streamlit as st

SRC_ROOT = Path(__file__).resolve().parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from components.site_footer import render_site_footer
from core.routing import Route, get_current_route, reroute
from core.state import initialize_state, reset_demo_state
from core.styles import inject_global_styles
from pages.entry import render_entry_page
from pages.expect import render_expect_page
from pages.landing import render_landing_page
from services.query_facade import get_frontend_query_facade


def main() -> None:
    st.set_page_config(
        page_title="차량 예측 가격 시뮬레이터",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_global_styles()
    facade = get_frontend_query_facade()
    initialize_state(facade)
    route = get_current_route()

    def go(page: Route, *, reset: bool = False) -> None:
        if reset:
            reset_demo_state(facade)
        reroute(page)

    if route == "landing":
        render_landing_page(on_entry=lambda: go("entry", reset=True))
    elif route == "entry":
        render_entry_page(
            facade=facade,
            on_back=lambda: go("landing"),
            on_expect=lambda: go("expect"),
        )
    else:
        render_expect_page(
            facade=facade,
            on_back=lambda: go("entry"),
            on_home=lambda: go("landing", reset=True),
        )

    render_site_footer(route)


if __name__ == "__main__":
    main()
