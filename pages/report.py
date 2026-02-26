import streamlit as st

from agents.ollama_agent import OllamaConfig, run_resume_agent
from components.llm_ui import render_rewrites, stringify_value
from core.db import (
    fetch_analise_ai_payload,
    fetch_analise_artifacts,
    fetch_analise_by_id,
    fetch_analises,
    update_analise_ai_payload,
)
from core.logic import score_from_metrics, section_metrics


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
        return "Média"
    return "Baixa"


def _section_summary(metrics: dict) -> list[dict]:
    out = []
    for section_name, items in metrics.items():
        avg = int(sum(i[1] for i in items) / len(items)) if items else 0
        out.append({"section": section_name, "score": avg, "priority": _priority_from_score(avg)})
    return out


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
            <div style="color:#93c5fd;font-size:12px;">Diagnóstico consolidado</div>
            <div style="color:#f8fafc;font-size:34px;font-weight:800;line-height:1.1;">{score}%</div>
            <div style="color:{color};font-weight:700;">Classificação: {label}</div>
            <div style="color:#cbd5e1;font-size:13px;margin-top:6px;">Fit semântico: {semantic_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(score / 100)


def _render_section_panel(metrics: dict):
    st.markdown("### Análise por seção")
    for item in _section_summary(metrics):
        c1, c2, c3 = st.columns([2.2, 1.5, 1.3])
        with c1:
            st.markdown(f"**{item['section'].title()}**")
        with c2:
            st.progress(item["score"] / 100)
        with c3:
            st.markdown(f"**{item['score']}%** | Prioridade: `{item['priority']}`")


def _build_config() -> OllamaConfig:
    return OllamaConfig(
        model=st.session_state.get("ollama_model", "llama3.1:8b"),
        base_url=st.session_state.get("ollama_base_url", "http://localhost:11434"),
        temperature=float(st.session_state.get("ollama_temperature", 0.3)),
        top_p=float(st.session_state.get("ollama_top_p", 0.9)),
        num_predict=int(st.session_state.get("ollama_num_predict", 700)),
    )


def _render_ai_block(selected: dict, metrics: dict, parsed: dict):
    st.markdown("### Recomendações Geradas")
    st.caption("As recomendações ficam salvas para este currículo.")

    payload = fetch_analise_ai_payload(selected["id"], "report")
    saved_result = payload.get("llm_result")
    saved_desc = payload.get("job_description", "")

    text_key = f"report_job_desc_{selected['id']}"
    result_key = f"report_llm_result_{selected['id']}"
    if saved_desc and text_key not in st.session_state:
        st.session_state[text_key] = saved_desc
    if saved_result and result_key not in st.session_state:
        st.session_state[result_key] = saved_result

    job_desc = st.text_area(
        "Descrição da vaga para gerar recomendações finais",
        key=text_key,
        placeholder="Cole aqui a descrição da vaga para gerar recomendações reais.",
    )

    if st.button("Gerar recomendações", type="primary", key=f"report_btn_{selected['id']}"):
        if not job_desc.strip():
            st.warning("Cole a descrição da vaga para executar a IA.")
        else:
            skills = parsed.get("habilidades", [])
            try:
                with st.spinner("Pensando..."):
                    llm_result = run_resume_agent(
                        candidate_name=selected["candidato"],
                        area=selected["area"],
                        resume_skills=skills,
                        section_metrics=metrics,
                        job_title="Vaga alvo",
                        job_description=job_desc,
                        config=_build_config(),
                    )
                    st.session_state[result_key] = llm_result
                    update_analise_ai_payload(
                        selected["id"],
                        "report",
                        {"llm_result": llm_result, "job_description": job_desc},
                    )
            except Exception as exc:
                st.error(f"Erro na execução com Ollama: {exc}")

    llm_result = st.session_state.get(result_key)
    if not llm_result:
        return

    final = llm_result.get("final", {})
    st.markdown("**Resumo**")
    st.write(final.get("summary", "N/A"))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Forças**")
        st.write("\n".join(f"- {stringify_value(x)}" for x in final.get("strengths", [])) or "-")
    with c2:
        st.markdown("**Fraquezas**")
        st.write("\n".join(f"- {stringify_value(x)}" for x in final.get("weaknesses", [])) or "-")

    st.markdown("**Reescritas por seção**")
    render_rewrites(
        final.get("section_rewrites", {}),
        [("Estrutura", "estrutura"), ("Experiência", "experiencia"), ("Habilidades", "habilidades")],
    )


def render():
    st.subheader("Relatório Final")
    st.caption("Selecione usuário e currículo. As recomendações geradas ficam salvas.")

    rows = fetch_analises()
    if not rows:
        st.info("Nenhuma análise registrada para exibir o relatório final.")
        return

    options = [{"id": r[0], "candidato": r[1], "area": r[2], "score": r[4], "date": r[5]} for r in rows]
    candidatos = sorted({o["candidato"] for o in options})
    candidato_sel = st.selectbox(
        "Selecione o usuário (candidato)",
        candidatos,
        index=None,
        placeholder="Escolha um usuário para visualizar os relatórios",
    )
    if not candidato_sel:
        st.info("Selecione um usuário para carregar os relatórios finais.")
        return

    user_options = [o for o in options if o["candidato"] == candidato_sel]
    selected = st.selectbox(
        "Selecione o currículo desse usuário",
        user_options,
        index=None,
        placeholder="Escolha uma análise para abrir o relatório final",
        format_func=lambda o: f"#{o['id']} | {o['area']} | {o['date']} | Score {o['score']}%",
    )
    if not selected:
        st.info("Selecione uma análise para visualizar o relatório final.")
        return

    analise_id = selected["id"]
    st.session_state["selected_analysis"] = analise_id
    row = fetch_analise_by_id(analise_id)

    parsed_map = st.session_state.get("parsed_by_analysis", {})
    metrics_map = st.session_state.get("metrics_by_analysis", {})
    parsed = parsed_map.get(analise_id)
    metrics = metrics_map.get(analise_id)
    if parsed is None or metrics is None:
        db_parsed, db_metrics = fetch_analise_artifacts(analise_id)
        parsed = parsed if parsed is not None else db_parsed
        metrics = metrics if metrics is not None else db_metrics
        parsed_map[analise_id] = parsed
        metrics_map[analise_id] = metrics
        st.session_state["parsed_by_analysis"] = parsed_map
        st.session_state["metrics_by_analysis"] = metrics_map

    parsed = parsed or {}
    metrics = metrics or section_metrics(parsed)
    st.session_state["parsed"] = parsed
    st.session_state["section_metrics"] = metrics

    score = row[4] if row else score_from_metrics(metrics)
    semantic_fit = st.session_state.get(f"comparacao_{analise_id}", {}).get("semantic_fit")

    _render_score_panel(score, semantic_fit)
    _render_section_panel(metrics)
    _render_ai_block(selected, metrics, parsed)
