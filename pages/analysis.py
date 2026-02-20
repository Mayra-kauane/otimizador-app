import time

import streamlit as st

from components.widgets import metric_card
from core.db import fetch_analises
from core.logic import score_from_metrics, section_metrics


def _candidate_options():
    rows = fetch_analises()
    return [
        {
            "id": r[0],
            "candidato": r[1],
            "area": r[2],
            "status": r[3],
            "score": r[4],
            "created_at": r[5],
        }
        for r in rows
    ]


def _render_flow_steps():
    st.markdown(
        """
        <div style="
            border:1px solid #334155;
            background:#0b1220;
            border-radius:12px;
            padding:10px 12px;
            margin-bottom:12px;
            color:#cbd5e1;
            font-size:13px;
        ">
            Fluxo: <b>Upload</b> -> <b>Parsing</b> -> <b style="color:#93c5fd;">Analise</b> -> <b>Otimizacao</b>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_context_header(selected: dict, consolidated_score: int):
    c1, c2, c3 = st.columns([2.2, 1.4, 1])
    with c1:
        st.markdown(
            f"""
            <div style="
                border:1px solid #334155;
                border-radius:12px;
                padding:10px 12px;
                background:#111827;
                margin-bottom:10px;
            ">
                <div style="color:#93c5fd;font-size:12px;">Candidato em analise</div>
                <div style="color:#f8fafc;font-size:20px;font-weight:700;">{selected['candidato']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div style="
                border:1px solid #334155;
                border-radius:12px;
                padding:10px 12px;
                background:#111827;
                margin-bottom:10px;
            ">
                <div style="color:#93c5fd;font-size:12px;">Area de interesse</div>
                <div style="color:#f8fafc;font-size:18px;font-weight:700;">{selected['area']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.metric("Score geral", f"{consolidated_score}%")


def _render_metrics_grid(items: list[tuple]):
    for i in range(0, len(items), 2):
        cols = st.columns(2)
        with cols[0]:
            metric_card(*items[i])
        if i + 1 < len(items):
            with cols[1]:
                metric_card(*items[i + 1])


def _rewrite_mock(section_key: str, candidato: str, area: str):
    prompts = {
        "estrutura": "Ex.: reescrever resumo profissional para tom executivo e mais objetivo.",
        "experiencia": "Ex.: transformar bullets fracos em bullets fortes com impacto.",
        "habilidades": "Ex.: adaptar habilidades para vaga de analista de dados senior.",
    }
    outputs = {
        "estrutura": [
            "Resumo ajustado para tom mais profissional e direto.",
            f"Abertura contextualizada para a area de {area}.",
            "Ordem de informacoes otimizada para recrutador.",
        ],
        "experiencia": [
            "Bullets reescritos com verbos de acao e resultado.",
            "Resultados quantificados com metricas de impacto.",
            "Experiencias mais aderentes a vaga priorizadas.",
        ],
        "habilidades": [
            "Lista reescrita com foco nas habilidades da vaga.",
            "Separacao clara entre hard e soft skills.",
            "Termos tecnicos reforcados para leitura automatica.",
        ],
    }

    st.markdown("**IA na Reescrita Inteligente (mock)**")
    st.text_area(
        "Objetivo da reescrita",
        key=f"rw_obj_{section_key}",
        placeholder=prompts[section_key],
    )

    if st.button("Reescrever secao", key=f"rw_btn_{section_key}", type="primary"):
        with st.spinner("Gerando reescrita inteligente..."):
            time.sleep(1.0)
        st.session_state[f"rw_out_{section_key}"] = [
            f"Reescrita sugerida para {candidato}:",
            *outputs[section_key],
        ]

    result = st.session_state.get(f"rw_out_{section_key}")
    if result:
        st.info("\n".join(f"- {line}" for line in result))


def _ats_mock(section_key: str, candidato: str):
    outputs = {
        "estrutura": [
            "Ausencia de palavras-chave estrategicas detectada no resumo.",
            "Estrutura reorganizada para melhor escaneabilidade ATS.",
            "Titulos padronizados para leitura automatica.",
        ],
        "experiencia": [
            "Descricao de experiencia alinhada com palavras-chave da vaga.",
            "Bullets simplificados para maior escaneabilidade.",
            "Linguagem ajustada para filtros automaticos.",
        ],
        "habilidades": [
            "Palavras-chave tecnicas ausentes adicionadas.",
            "Ordem das habilidades ajustada por aderencia a vaga.",
            "Nomenclatura tecnica padronizada.",
        ],
    }

    st.markdown("**IA para Ajuste ATS (mock)**")
    st.text_area(
        "Descricao da vaga (base ATS)",
        key=f"ats_job_{section_key}",
        placeholder="Cole uma descricao da vaga para simular a adaptacao ATS.",
    )

    if st.button("Aplicar ajuste ATS", key=f"ats_btn_{section_key}", type="primary"):
        with st.spinner("Aplicando ajustes ATS..."):
            time.sleep(1.0)
        st.session_state[f"ats_out_{section_key}"] = [
            f"Ajustes ATS sugeridos para {candidato}:",
            *outputs[section_key],
        ]

    result = st.session_state.get(f"ats_out_{section_key}")
    if result:
        st.success("\n".join(f"- {line}" for line in result))


def _render_ai_block(section_key: str, candidato: str, area: str):
    st.markdown("---")
    st.markdown("### Otimizacao Inteligente (Simulacao de IA)")
    st.caption(
        "Quando integrada, a IA avaliara qualidade textual, reescrita contextual, adaptacao semantica a vaga e relatorios personalizados."
    )
    c1, c2 = st.columns(2)
    with c1:
        _rewrite_mock(section_key, candidato, area)
    with c2:
        _ats_mock(section_key, candidato)


def render():
    st.subheader("Analise por Secao")
    st.caption("Avaliacao detalhada das secoes do curriculo com foco em clareza, impacto e aderencia.")

    options = _candidate_options()
    if not options:
        st.info("Nenhuma analise encontrada para selecionar candidato.")
        return

    index = 0
    selected_id = st.session_state.get("selected_analysis")
    if selected_id:
        for i, opt in enumerate(options):
            if opt["id"] == selected_id:
                index = i
                break

    selected = st.selectbox(
        "Selecione o candidato para analisar",
        options,
        index=index,
        format_func=lambda o: f"{o['candidato']} | {o['area']} | {o['created_at']}",
    )
    st.session_state["selected_analysis"] = selected["id"]

    metrics = st.session_state.get("section_metrics", section_metrics())
    consolidated_score = score_from_metrics(metrics)

    _render_flow_steps()
    _render_context_header(selected, consolidated_score)

    tabs = st.tabs(["Estrutura", "Experiencia", "Habilidades"])

    with tabs[0]:
        _render_metrics_grid(metrics["estrutura"])
        _render_ai_block("estrutura", selected["candidato"], selected["area"])

    with tabs[1]:
        _render_metrics_grid(metrics["experiencia"])
        _render_ai_block("experiencia", selected["candidato"], selected["area"])

    with tabs[2]:
        _render_metrics_grid(metrics["habilidades"])
        _render_ai_block("habilidades", selected["candidato"], selected["area"])
