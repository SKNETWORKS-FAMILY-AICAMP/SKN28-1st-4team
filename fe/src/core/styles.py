from pathlib import Path

import streamlit as st


def inject_global_styles() -> None:
    css_path = Path(__file__).resolve().parents[1] / "styles" / "theme.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
