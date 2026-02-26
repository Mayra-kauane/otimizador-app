import streamlit as st

from agents.ollama_agent import OllamaConfig, run_resume_agent
from components.llm_ui import render_rewrites
from components.widgets import metric_card
from core.db import (
    fetch_analise_ai_sections,
    fetch_analise_artifacts,
    fetch_analises,
    update_analise_ai_section,
)
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
                <div style="color:#93c5fd;font-size:12px;">Candidato em análise</div>
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
                <div style="color:#93c5fd;font-size:12px;">Área de interesse</div>
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


def _build_config() -> OllamaConfig:
    return OllamaConfig(
        model=st.session_state.get("ollama_model", "llama3.1:8b"),
        base_url=st.session_state.get("ollama_base_url", "http://localhost:11434"),
        temperature=float(st.session_state.get("ollama_temperature", 0.3)),
        top_p=float(st.session_state.get("ollama_top_p", 0.9)),
        num_predict=int(st.session_state.get("ollama_num_predict", 700)),
    )


def _run_llm(selected: dict, job_description: str) -> dict:
    parsed_map = st.session_state.get("parsed_by_analysis", {})
    metrics_map = st.session_state.get("metrics_by_analysis", {})
    parsed = parsed_map.get(selected["id"])
    metrics = metrics_map.get(selected["id"])
    if parsed is None or metrics is None:
        db_parsed, db_metrics = fetch_analise_artifacts(selected["id"])
        parsed = parsed if parsed is not None else db_parsed
        metrics = metrics if metrics is not None else db_metrics
        parsed_map[selected["id"]] = parsed
        metrics_map[selected["id"]] = metrics
        st.session_state["parsed_by_analysis"] = parsed_map
        st.session_state["metrics_by_analysis"] = metrics_map
    parsed = parsed or st.session_state.get("parsed", {})
    skills = parsed.get("habilidades", [])
    metrics = metrics or section_metrics(parsed)
    return run_resume_agent(
        candidate_name=selected["candidato"],
        area=selected["area"],
        resume_skills=skills,
        section_metrics=metrics,
        job_title="Vaga alvo",
        job_description=job_description,
        config=_build_config(),
    )


def _render_ai_block(section_key: str, selected: dict):
    st.markdown("---")
    st.markdown("### Otimização Inteligente")
    st.caption("Reescrita e recomendações geradas por LLM para esta seção.")

    input_key = f"analysis_job_desc_{selected['id']}_{section_key}"
    result_key = f"analysis_llm_result_{selected['id']}_{section_key}"

    saved_sections = fetch_analise_ai_sections(selected["id"])
    saved_section = saved_sections.get(section_key, {}) if isinstance(saved_sections, dict) else {}
    saved_result = saved_section.get("result")
    saved_job_desc = saved_section.get("job_description", "")

    if saved_job_desc and input_key not in st.session_state:
        st.session_state[input_key] = saved_job_desc
    if saved_result and result_key not in st.session_state:
        st.session_state[result_key] = saved_result

    job_desc = st.text_area(
        "Descrição da vaga para orientar a reescrita",
        key=input_key,
        placeholder="Cole aqui a descrição da vaga para gerar recomendações reais.",
    )

    if st.button("Gerar recomendações da seção", key=f"analysis_btn_{selected['id']}_{section_key}", type="primary"):
        if not job_desc.strip():
            st.warning("Cole a descrição da vaga para executar a IA.")
        else:
            try:
                with st.spinner("Pensando..."):
                    llm_result = _run_llm(selected, job_desc)
                    st.session_state[result_key] = llm_result
                    update_analise_ai_section(
                        analise_id=selected["id"],
                        section_key=section_key,
                        llm_result=llm_result,
                        job_description=job_desc,
                    )
            except Exception as exc:
                st.error(f"Falha na execução com Ollama: {exc}")

    result = st.session_state.get(result_key)
    if not result:
        return

    final = result.get("final", {})
    rewrites = final.get("section_rewrites", {})
    section_label = {
        "estrutura": "estrutura",
        "experiencia": "experiencia",
        "habilidades": "habilidades",
    }[section_key]

    st.markdown("**Resumo**")
    st.write(final.get("summary", "N/A"))

    st.markdown("**Reescrita sugerida para esta seção**")
    render_rewrites(rewrites, [("Reescrita", section_label)])

    updated_at = saved_section.get("updated_at")
    if updated_at:
        st.caption(f"Última recomendação salva em: {updated_at}")


def render():
    st.subheader("Análise por Seção")
    st.caption("Avaliação detalhada das seções do currículo com foco em clareza, impacto e aderência.")

    options = _candidate_options()
    if not options:
        st.info("Nenhuma análise encontrada para selecionar candidato.")
        return

    search = st.text_input("Buscar currículo por nome (opcional)")
    filtered_options = options
    if search.strip():
        term = search.strip().lower()
        filtered_options = [opt for opt in options if term in opt["candidato"].lower()]

    if not filtered_options:
        st.warning("Nenhum currículo encontrado para esse filtro.")
        return

    selected = st.selectbox(
        "Selecione o candidato para analisar",
        filtered_options,
        index=None,
        placeholder="Escolha um currículo para iniciar a análise",
        format_func=lambda o: f"{o['candidato']} | {o['area']} | {o['created_at']}",
    )

    if not selected:
        st.info("Selecione um currículo para visualizar as análises por seção.")
        return

    st.session_state["selected_analysis"] = selected["id"]
    parsed_map = st.session_state.get("parsed_by_analysis", {})
    metrics_map = st.session_state.get("metrics_by_analysis", {})
    selected_parsed = parsed_map.get(selected["id"])
    metrics = metrics_map.get(selected["id"])
    if selected_parsed is None or metrics is None:
        db_parsed, db_metrics = fetch_analise_artifacts(selected["id"])
        selected_parsed = selected_parsed if selected_parsed is not None else db_parsed
        metrics = metrics if metrics is not None else db_metrics
        parsed_map[selected["id"]] = selected_parsed
        metrics_map[selected["id"]] = metrics
        st.session_state["parsed_by_analysis"] = parsed_map
        st.session_state["metrics_by_analysis"] = metrics_map
    selected_parsed = selected_parsed or {}
    metrics = metrics or section_metrics(selected_parsed)
    st.session_state["parsed"] = selected_parsed
    st.session_state["section_metrics"] = metrics
    consolidated_score = score_from_metrics(metrics)

    _render_context_header(selected, consolidated_score)

    tabs = st.tabs(["Estrutura", "Experiência", "Habilidades"])

    with tabs[0]:
        _render_metrics_grid(metrics["estrutura"])
        _render_ai_block("estrutura", selected)

    with tabs[1]:
        _render_metrics_grid(metrics["experiencia"])
        _render_ai_block("experiencia", selected)

    with tabs[2]:
        _render_metrics_grid(metrics["habilidades"])
        _render_ai_block("habilidades", selected)
