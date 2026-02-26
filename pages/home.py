from datetime import datetime

import streamlit as st

from components.widgets import small_metric_card, status_badge
from core.db import delete_analise, fetch_analise_by_id, fetch_analises


@st.dialog("Confirmar exclusão")
def confirm_delete_dialog(analise_id: int, candidato: str):
    st.write(f"Deseja mesmo excluir a análise de **{candidato}**?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.pop("pending_delete", None)
            st.rerun()
    with col2:
        if st.button("Excluir", type="primary", use_container_width=True):
            delete_analise(analise_id)
            if st.session_state.get("selected_analysis") == analise_id:
                st.session_state.pop("selected_analysis", None)
            st.session_state.pop("pending_delete", None)
            st.rerun()


@st.dialog("Relatório da análise")
def view_report_dialog(analise_id: int):
    row = fetch_analise_by_id(analise_id)
    if not row:
        st.warning("Análise não encontrada.")
        if st.button("Fechar", use_container_width=True):
            st.session_state.pop("pending_view", None)
            st.rerun()
        return

    _, candidato, area, status, score, created_at = row
    st.markdown(f"**Candidato:** {candidato}")
    st.markdown(f"**Área:** {area}")
    st.markdown(f"**Data da análise:** {created_at}")
    st.markdown(f"**Status:** {status_badge(status)}", unsafe_allow_html=True)
    st.markdown("---")
    st.metric("Score geral", f"{score}%")
    st.progress(score / 100)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Pontos fortes**")
        st.write("- Estrutura geral clara\n- Boa aderência ao perfil da vaga\n- Organização visual adequada")
    with c2:
        st.markdown("**Pontos de melhoria**")
        st.write("- Reforçar palavras-chave técnicas\n- Quantificar resultados em experiências\n- Tornar o resumo mais objetivo")

    if st.button("Fechar", use_container_width=True):
        st.session_state.pop("pending_view", None)
        st.rerun()


def _go_to_upload():
    st.session_state["pending_nav"] = "upload"
    st.rerun()


def render():
    rows = fetch_analises()
    now = datetime.now().strftime("%Y-%m")
    mes_atual = [r for r in rows if r[5].startswith(now)]
    score_medio = int(sum(r[4] for r in rows) / len(rows)) if rows else 0

    top_left, top_right = st.columns([5, 2])
    with top_left:
        col1, col2 = st.columns([1, 1])
        with col1:
            small_metric_card("Análises no mês", str(len(mes_atual)))
        with col2:
            small_metric_card("Score médio", f"{score_medio}%")
    with top_right:
        spacer, action = st.columns([1.4, 1])
        with spacer:
            st.write("")
        with action:
            if st.button("Nova análise", type="primary"):
                _go_to_upload()

    st.markdown("---")
    st.markdown("**Análises anteriores**")
    if not rows:
        st.info("Nenhuma análise encontrada.")
        return

    for analise_id, candidato, area, status, score, created_at in rows[:10]:
        left, right = st.columns([5, 2])
        with left:
            st.markdown(
                f"**{candidato}** | {area} | {created_at} | Score {score}<br>{status_badge(status)}",
                unsafe_allow_html=True,
            )
        with right:
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Visualizar", key=f"view_{analise_id}"):
                    st.session_state["selected_analysis"] = analise_id
                    st.session_state["pending_view"] = {"id": analise_id}
                    st.rerun()
            with b2:
                if st.button("Excluir", key=f"del_{analise_id}"):
                    st.session_state["pending_delete"] = {"id": analise_id, "candidato": candidato}
                    st.rerun()
        st.divider()

    pending = st.session_state.get("pending_delete")
    if pending:
        confirm_delete_dialog(pending["id"], pending["candidato"])

    pending_view = st.session_state.get("pending_view")
    if pending_view:
        view_report_dialog(pending_view["id"])
