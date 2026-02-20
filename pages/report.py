import json
from io import BytesIO

import streamlit as st

from core.db import fetch_analise_by_id, fetch_analises
from core.logic import make_report_text, score_from_metrics, section_metrics


def _score_classification(score: int) -> tuple[str, str]:
    if score >= 85:
        return "Excelente", "#16a34a"
    if score >= 70:
        return "Bom", "#f59e0b"
    return "Precisa melhorar", "#dc2626"


def _priority_from_score(section_score: int) -> str:
    if section_score < 60:
        return "Alta"
    if section_score < 75:
        return "Media"
    return "Baixa"


def _section_summary(metrics: dict) -> list[dict]:
    out = []
    for section_name, items in metrics.items():
        avg = int(sum(i[1] for i in items) / len(items)) if items else 0
        out.append(
            {
                "section": section_name,
                "score": avg,
                "priority": _priority_from_score(avg),
            }
        )
    return out


def _contextual_strengths(area: str) -> list[str]:
    base = [
        "Estrutura geral do curriculo favorece leitura rapida por recrutadores.",
        "Perfil apresenta coerencia entre experiencia, habilidades e objetivo profissional.",
    ]
    if "dado" in area.lower():
        base.append("Base tecnica com ferramentas relevantes para analise e BI.")
    elif "market" in area.lower():
        base.append("Boa aderencia a funcoes orientadas a performance e campanhas.")
    elif "vend" in area.lower():
        base.append("Historico com potencial para funis comerciais e negociacao.")
    else:
        base.append("Perfil apresenta base profissional consistente para evolucao.")
    return base


def _contextual_gaps(area: str) -> list[str]:
    base = [
        "Resumo profissional pode ser mais estrategico e orientado a resultados.",
        "Experiencias podem incluir mais impacto mensuravel com numeros concretos.",
    ]
    if "dado" in area.lower():
        base.append("Faltam evidencias de stack avancada e projetos com dados em escala.")
    elif "market" in area.lower():
        base.append("Faltam evidencias de metricas de negocio como CAC, LTV e ROI.")
    elif "vend" in area.lower():
        base.append("Falta detalhar metas batidas, ticket medio e ciclo de vendas.")
    else:
        base.append("Faltam exemplos de resultados diretamente conectados ao objetivo alvo.")
    return base


def _ai_generated_recommendations(area: str) -> list[str]:
    return [
        f"Reescrever resumo para tom mais profissional e foco em vagas de {area}.",
        "Reformular bullets de experiencia com verbos fortes e resultados quantificados.",
        "Adaptar habilidades e palavras-chave para a vaga alvo e filtros ATS.",
        "Gerar versao alternativa do curriculo priorizando aderencia semantica a descricao da vaga.",
    ]


def _render_score_panel(score: int, semantic_fit: int | None):
    label, color = _score_classification(score)
    semantic_text = f"{semantic_fit}%" if semantic_fit is not None else "N/A"
    st.markdown(
        f"""
        <div style="
            border:1px solid #334155;
            border-radius:14px;
            background:#111827;
            padding:14px;
            margin-bottom:12px;
        ">
            <div style="color:#93c5fd;font-size:12px;">Diagnostico consolidado</div>
            <div style="color:#f8fafc;font-size:34px;font-weight:800;line-height:1.1;">{score}%</div>
            <div style="color:{color};font-weight:700;">Classificacao: {label}</div>
            <div style="color:#cbd5e1;font-size:13px;margin-top:6px;">Fit semantico (mock IA): {semantic_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(score / 100)


def _render_section_panel(metrics: dict):
    st.markdown("### Analise por secao")
    for item in _section_summary(metrics):
        c1, c2, c3 = st.columns([2.2, 1.5, 1.3])
        with c1:
            st.markdown(f"**{item['section'].title()}**")
        with c2:
            st.progress(item["score"] / 100)
        with c3:
            st.markdown(f"**{item['score']}%** | Prioridade: `{item['priority']}`")


def _render_context_lists(area: str):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Pontos fortes contextualizados")
        st.success("\n".join(f"- {s}" for s in _contextual_strengths(area)))
    with c2:
        st.markdown("### Pontos de melhoria contextualizados")
        st.warning("\n".join(f"- {g}" for g in _contextual_gaps(area)))


def _render_ai_block(area: str):
    st.markdown("### Recomendacoes Geradas por IA (mock)")
    st.caption(
        "Simulacao do ponto de integracao futuro com IA generativa para reescrita, adaptacao semantica e otimizacao ATS."
    )
    if st.button("Gerar recomendacoes inteligentes", type="primary"):
        with st.spinner("Gerando recomendacoes de IA..."):
            pass
        st.session_state["report_ai_recs"] = _ai_generated_recommendations(area)

    recs = st.session_state.get("report_ai_recs", [])
    if recs:
        st.info("\n".join(f"- {r}" for r in recs))


def _render_version_compare(current_id: int | None):
    st.markdown("### Comparacao entre versoes")
    rows = fetch_analises()
    if len(rows) < 2:
        st.caption("Sao necessarias ao menos 2 analises para comparar versoes.")
        return

    options = [{"id": r[0], "candidato": r[1], "score": r[4], "date": r[5]} for r in rows]
    idx_new = 0
    if current_id:
        for i, o in enumerate(options):
            if o["id"] == current_id:
                idx_new = i
                break

    idx_old = 1 if len(options) > 1 else 0
    old_v = st.selectbox(
        "Versao base",
        options,
        index=idx_old,
        key="report_old",
        format_func=lambda o: f"#{o['id']} | {o['candidato']} | {o['date']} | {o['score']}%",
    )
    new_v = st.selectbox(
        "Versao comparada",
        options,
        index=idx_new,
        key="report_new",
        format_func=lambda o: f"#{o['id']} | {o['candidato']} | {o['date']} | {o['score']}%",
    )

    delta = new_v["score"] - old_v["score"]
    st.metric("Evolucao de score", f"{delta:+d} pontos")


def _render_exports(row, parsed, comparacao, score):
    st.markdown("### Exportacao")
    report_text = make_report_text(row, parsed, comparacao, score)
    txt_buffer = BytesIO(report_text.encode("utf-8"))
    json_buffer = BytesIO(
        json.dumps(
            {
                "analise": row,
                "parsed": parsed,
                "comparacao": comparacao,
                "score": score,
            },
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")
    )

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Exportar relatorio (TXT)",
            data=txt_buffer,
            file_name="relatorio_curriculo.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "Exportar dados (JSON)",
            data=json_buffer,
            file_name="relatorio_curriculo.json",
            mime="application/json",
            use_container_width=True,
        )


def render():
    st.subheader("Relatorio Final")
    st.caption("Painel analitico de diagnostico e otimizacao continua do curriculo.")

    rows = fetch_analises()
    if not rows:
        st.info("Nenhuma analise registrada para exibir o relatorio final.")
        return

    options = [{"id": r[0], "candidato": r[1], "area": r[2], "score": r[4], "date": r[5]} for r in rows]
    default_index = 0
    selected_id = st.session_state.get("selected_analysis")
    if selected_id:
        for i, opt in enumerate(options):
            if opt["id"] == selected_id:
                default_index = i
                break

    selected = st.selectbox(
        "Selecione o curriculo para ver o historico final",
        options,
        index=default_index,
        format_func=lambda o: f"#{o['id']} | {o['candidato']} | {o['area']} | {o['date']}",
    )
    analise_id = selected["id"]
    st.session_state["selected_analysis"] = analise_id
    row = fetch_analise_by_id(analise_id)

    metrics = st.session_state.get("section_metrics", section_metrics())
    score = st.session_state.get("final_score")
    if score is None:
        score = row[4] if row else score_from_metrics(metrics)

    comparacao = st.session_state.get("comparacao", {})
    semantic_fit = comparacao.get("semantic_fit")
    area = row[2] if row else "Dados"
    parsed = st.session_state.get("parsed", {})

    _render_score_panel(score, semantic_fit)
    _render_section_panel(metrics)
    _render_context_lists(area)
    _render_ai_block(area)
    _render_version_compare(analise_id)
    _render_exports(row, parsed, comparacao, score)
