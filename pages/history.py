import streamlit as st

from components.widgets import status_badge
from core.db import fetch_analises


def render():
    st.subheader("Histórico de Análises")
    st.caption("Consulte todas as análises já processadas.")

    rows = fetch_analises()
    if not rows:
        st.info("Nenhuma análise registrada.")
        return

    for analise_id, candidato, area, status, score, created_at in rows:
        left, right = st.columns([5, 1])
        with left:
            st.markdown(
                f"**#{analise_id} - {candidato}** | {area} | {created_at} | Score {score}<br>{status_badge(status)}",
                unsafe_allow_html=True,
            )
        with right:
            if st.button("Selecionar", key=f"hist_{analise_id}"):
                st.session_state["selected_analysis"] = analise_id
                st.success("Análise selecionada. Use o menu lateral para abrir Relatório Final.")
        st.divider()
