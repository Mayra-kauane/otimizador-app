import streamlit as st

from components.styles import inject_global_css
from components.widgets import render_app_header, render_sidebar
from core.constants import APP_TITLE, PAGE_OPTIONS
from core.db import init_db, seed_if_empty
from pages import analysis, comparison, history, home, report, upload


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    inject_global_css()
    render_app_header(APP_TITLE)

    init_db()
    seed_if_empty()

    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    valid_keys = {key for _, key in PAGE_OPTIONS}
    if st.session_state["page"] not in valid_keys:
        st.session_state["page"] = "home"

    if "pending_nav" in st.session_state:
        next_page = st.session_state.pop("pending_nav")
        if next_page in valid_keys:
            st.session_state["page"] = next_page
            st.rerun()

    previous_page = st.session_state.get("_previous_page", st.session_state["page"])
    selected_page = render_sidebar(st.session_state["page"], PAGE_OPTIONS)

    if selected_page != st.session_state["page"]:
        st.session_state["page"] = selected_page
        st.rerun()

    page = st.session_state["page"]

    if previous_page == "upload" and page != "upload":
        st.session_state.pop("parsed", None)
        st.session_state.pop("parsed_source_sig", None)

    st.session_state["_previous_page"] = page

    if page == "home":
        home.render()
    elif page == "upload":
        upload.render()
    elif page == "analise":
        analysis.render()
    elif page == "comparacao":
        comparison.render()
    elif page == "relatorio":
        report.render()
    elif page == "historico":
        history.render()


if __name__ == "__main__":
    main()
