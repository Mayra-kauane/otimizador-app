import streamlit as st

from core.constants import STATUS_CONCLUIDA, STATUS_EM_ANALISE, STATUS_REVISAO


def status_badge(status: str) -> str:
    palette = {
        STATUS_EM_ANALISE: "#2563EB",
        STATUS_CONCLUIDA: "#16A34A",
        STATUS_REVISAO: "#F59E0B",
        "Em analise": "#2563EB",
        "Concluida": "#16A34A",
        "Revisao": "#F59E0B",
    }
    label_map = {"Em analise": STATUS_EM_ANALISE, "Concluida": STATUS_CONCLUIDA, "Revisao": STATUS_REVISAO}
    display_status = label_map.get(status, status)
    color = palette.get(status, "#64748B")
    return (
        "<span style='padding:3px 8px;border-radius:999px;"
        f"background:{color};color:white;font-size:12px'>{display_status}</span>"
    )


def metric_card(title: str, score: int, status: str, comment: str):
    color = {"Bom": "#16A34A", "Regular": "#F59E0B", "Precisa melhorar": "#DC2626"}.get(status, "#64748B")
    st.markdown(
        f"""
        <div style="border:1px solid #e5e7eb;border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-weight:600;">{title}</div>
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="flex:1;background:#f1f5f9;border-radius:999px;overflow:hidden;">
                    <div style="width:{score}%;background:{color};height:10px;"></div>
                </div>
                <div style="min-width:50px;text-align:right;">{score}%</div>
            </div>
            <div style="margin-top:6px;color:{color};font-weight:600;">{status}</div>
            <div style="color:#475569;font-size:13px;">{comment}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def small_metric_card(title: str, value: str):
    st.markdown(
        f"""
        <div class="soft-card">
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_app_header(title: str):
    st.markdown(
        f"""
        <div class="app-hero">
            <h1>{title}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Gerencie analises, acompanhe status e acesse relatorios.")


def render_sidebar(current_key: str, page_options: list[tuple[str, str]]) -> str:
    label_by_key = {k: label for label, k in page_options}
    key_by_label = {label: k for label, k in page_options}
    labels = [label for label, _ in page_options]

    st.sidebar.markdown("### Navegacao")
    st.sidebar.markdown(
        f"<div class='side-indicator'>Pagina atual: <b>{label_by_key[current_key]}</b></div>",
        unsafe_allow_html=True,
    )

    default_label = label_by_key[current_key]
    selected_label = st.sidebar.radio(
        "Ir para",
        labels,
        index=labels.index(default_label),
        label_visibility="collapsed",
    )
    return key_by_label[selected_label]
