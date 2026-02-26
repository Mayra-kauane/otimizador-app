import streamlit as st

from agents.ollama_agent import OllamaConfig, run_resume_agent
from components.llm_ui import render_rewrites, stringify_value
from core.constants import STATUS_CONCLUIDA
from core.db import (
    fetch_analise_ai_payload,
    fetch_analise_artifacts,
    fetch_analises,
    fetch_comparacoes_by_analise,
    insert_comparacao,
    update_analise,
    update_analise_ai_payload,
)
from core.logic import compare_with_job, score_from_metrics, section_metrics

DEFAULT_VAGAS = [
    {"titulo": "Analista de Dados Pleno", "descricao": "Python SQL ETL Dashboard Power BI Analise de dados Comunicacao"},
    {"titulo": "Especialista em Marketing Digital", "descricao": "SEO Google Ads CRM Analytics Conteudo Campanhas Relatorios"},
    {"titulo": "Executivo de Vendas B2B", "descricao": "Prospeccao Pipeline Negociacao CRM Metas Relacionamento Comercial"},
]


def _ensure_vagas_state():
    if "vagas_cadastradas" not in st.session_state:
        st.session_state["vagas_cadastradas"] = DEFAULT_VAGAS.copy()

    normalized = []
    for vaga in st.session_state.get("vagas_cadastradas", []):
        if not isinstance(vaga, dict):
            continue
        titulo = str(vaga.get("titulo", "")).strip() or "Vaga sem titulo"
        descricao = (
            vaga.get("descricao")
            or vaga.get("descrição")
            or vaga.get("descriçao")
            or next((v for k, v in vaga.items() if "descr" in str(k).lower()), "")
        )
        normalized.append({"titulo": titulo, "descricao": str(descricao or "").strip()})
    st.session_state["vagas_cadastradas"] = normalized


def _resume_skills_from_area(area: str):
    area_l = (area or "").lower()
    if "dado" in area_l:
        return ["Python", "SQL", "Power BI", "ETL", "Excel", "Dashboard"]
    if "market" in area_l:
        return ["SEO", "Google Ads", "CRM", "Analytics", "Conteudo"]
    if "vend" in area_l:
        return ["Prospeccao", "Pipeline", "Negociacao", "CRM", "Comercial"]
    return ["Comunicacao", "Excel", "Analise"]


def _risk_to_semantic_fit(ats_risk: str, compat: int) -> int:
    risk_score = {"baixo": 88, "medio": 72, "alto": 55}.get((ats_risk or "").lower(), 70)
    return int((risk_score + compat) / 2)


def _load_artifacts(analise_id: int):
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
    return parsed, metrics


def _render_llm_panel(selected: dict, vaga_titulo: str, vaga_descricao: str):
    st.markdown("---")
    st.markdown("### IA Generativa para Comparação")
    st.caption("Recomendações de comparação e adaptação do currículo.")

    payload = fetch_analise_ai_payload(selected["id"], "comparison")
    saved_llm = payload.get("llm_result")
    if saved_llm:
        st.session_state[f"comparison_llm_{selected['id']}"] = saved_llm

    with st.expander("Configuração do modelo", expanded=False):
        model = st.text_input("Modelo Ollama", value=st.session_state.get("ollama_model", "llama3.1:8b"))
        base_url = st.text_input("Base URL", value=st.session_state.get("ollama_base_url", "http://localhost:11434"))
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
        top_p = st.slider("Top-p", min_value=0.1, max_value=1.0, value=0.9, step=0.1)
        num_predict = st.number_input("Max tokens (num_predict)", min_value=100, max_value=4000, value=700)
        st.session_state["ollama_temperature"] = float(temperature)
        st.session_state["ollama_top_p"] = float(top_p)
        st.session_state["ollama_num_predict"] = int(num_predict)

    if st.button("Gerar análise", type="primary", key=f"comparison_llm_btn_{selected['id']}"):
        if not vaga_descricao.strip():
            st.warning("Forneça descrição da vaga para rodar a análise.")
            return

        parsed, metrics = _load_artifacts(selected["id"])
        resume_skills = parsed.get("habilidades") or _resume_skills_from_area(selected["area"])
        config = OllamaConfig(
            model=model.strip(),
            base_url=base_url.strip(),
            temperature=float(temperature),
            top_p=float(top_p),
            num_predict=int(num_predict),
        )
        with st.spinner("Pensando..."):
            try:
                result = run_resume_agent(
                    candidate_name=selected["candidato"],
                    area=selected["area"],
                    resume_skills=resume_skills,
                    section_metrics=metrics,
                    job_title=vaga_titulo or "Vaga sem título",
                    job_description=vaga_descricao,
                    config=config,
                )
                st.session_state[f"comparison_llm_{selected['id']}"] = result
                update_analise_ai_payload(
                    selected["id"],
                    "comparison",
                    {"llm_result": result, "vaga_titulo": vaga_titulo, "vaga_descricao": vaga_descricao},
                )
                st.session_state["ollama_model"] = model.strip()
                st.session_state["ollama_base_url"] = base_url.strip()
            except Exception as exc:
                st.error(f"Erro na execução com Ollama: {exc}")

    result = st.session_state.get(f"comparison_llm_{selected['id']}")
    if not result:
        return

    final = result.get("final", {})
    st.success("Análise generativa carregada.")
    st.markdown("**Resumo**")
    st.write(final.get("summary", "N/A"))
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Forças**")
        st.write("\n".join(f"- {stringify_value(x)}" for x in final.get("strengths", [])) or "-")
    with c2:
        st.markdown("**Fraquezas**")
        st.write("\n".join(f"- {stringify_value(x)}" for x in final.get("weaknesses", [])) or "-")
    st.markdown("**Sugestões de reescrita por seção**")
    render_rewrites(final.get("section_rewrites", {}), [("Estrutura", "estrutura"), ("Experiência", "experiencia"), ("Habilidades", "habilidades")])


def render():
    st.subheader("Comparação com a Vaga")
    st.caption("Compare o currículo com a vaga e mantenha os resultados salvos.")
    _ensure_vagas_state()

    rows = fetch_analises()
    if not rows:
        st.info("Nenhum currículo salvo para comparar.")
        return

    options = [{"id": r[0], "candidato": r[1], "area": r[2], "created_at": r[5]} for r in rows]
    selected = st.selectbox(
        "Selecione o currículo",
        options,
        index=0,
        format_func=lambda o: f"{o['candidato']} | {o['area']} | {o['created_at']}",
    )
    st.session_state["selected_analysis"] = selected["id"]

    saved_payload = fetch_analise_ai_payload(selected["id"], "comparison")
    if saved_payload.get("comparacao"):
        st.session_state[f"comparacao_{selected['id']}"] = saved_payload.get("comparacao")
    if saved_payload.get("final_score") is not None:
        st.session_state[f"final_score_{selected['id']}"] = saved_payload.get("final_score")

    modo = st.radio("Origem da vaga", ["Escolher vaga cadastrada", "Inserir nova vaga"], horizontal=True)
    vaga_titulo = ""
    vaga_descricao = ""
    if modo == "Escolher vaga cadastrada":
        vaga = st.selectbox("Vagas cadastradas", st.session_state["vagas_cadastradas"], format_func=lambda v: v.get("titulo", "Vaga"))
        vaga_titulo = str(vaga.get("titulo", "Vaga sem título"))
        vaga_descricao = str(vaga.get("descricao", ""))
        st.text_area("Descrição da vaga", value=vaga_descricao, height=140, disabled=True)
    else:
        vaga_titulo = st.text_input("Título da vaga")
        vaga_descricao = st.text_area("Descrição da vaga", height=160)

    salvar_resultado = st.checkbox("Salvar resultado no histórico", value=True)
    if st.button("Executar comparação", type="primary", key=f"comparison_run_{selected['id']}"):
        if not vaga_descricao.strip():
            st.warning("Forneça descrição da vaga para executar a comparação.")
        else:
            parsed, metrics = _load_artifacts(selected["id"])
            resume_skills = parsed.get("habilidades") or _resume_skills_from_area(selected["area"])
            resultado = compare_with_job(vaga_descricao, resume_skills)
            try:
                llm_data = run_resume_agent(
                    candidate_name=selected["candidato"],
                    area=selected["area"],
                    resume_skills=resume_skills,
                    section_metrics=metrics,
                        job_title=vaga_titulo or "Vaga sem título",
                    job_description=vaga_descricao,
                    config=OllamaConfig(
                        model=st.session_state.get("ollama_model", "llama3.1:8b"),
                        base_url=st.session_state.get("ollama_base_url", "http://localhost:11434"),
                        temperature=float(st.session_state.get("ollama_temperature", 0.3)),
                        top_p=float(st.session_state.get("ollama_top_p", 0.9)),
                        num_predict=int(st.session_state.get("ollama_num_predict", 700)),
                    ),
                )
            except Exception as exc:
                st.error(f"Ollama indisponível. {exc}")
                return

            final = llm_data.get("final", {})
            semantic_fit = _risk_to_semantic_fit(final.get("ats_risk", "medio"), resultado["compat"])
            comparacao = {
                **resultado,
                "semantic_fit": semantic_fit,
                "lacunas": final.get("weaknesses", []),
                "recomendacoes": final.get("next_actions", []),
                "vaga_titulo": vaga_titulo or "Vaga sem título",
            }
            base_score = score_from_metrics(metrics)
            final_score = int((base_score * 0.5) + (resultado["compat"] * 0.25) + (semantic_fit * 0.25))
            st.session_state[f"comparacao_{selected['id']}"] = comparacao
            st.session_state[f"final_score_{selected['id']}"] = final_score
            st.session_state[f"comparison_llm_{selected['id']}"] = llm_data
            update_analise(selected["id"], STATUS_CONCLUIDA, final_score)
            update_analise_ai_payload(
                selected["id"],
                "comparison",
                {
                    "comparacao": comparacao,
                    "final_score": final_score,
                    "llm_result": llm_data,
                    "vaga_titulo": vaga_titulo,
                    "vaga_descricao": vaga_descricao,
                },
            )
            if salvar_resultado:
                insert_comparacao(
                    analise_id=selected["id"],
                    vaga_titulo=vaga_titulo or "Vaga sem título",
                    vaga_descricao=vaga_descricao,
                    compat=resultado["compat"],
                    semantic_fit=semantic_fit,
                    presentes=resultado["presentes"],
                    ausentes=resultado["ausentes"],
                    lacunas=final.get("weaknesses", []),
                    recomendacoes=final.get("next_actions", []),
                )

    resultado = st.session_state.get(f"comparacao_{selected['id']}")
    if resultado:
        st.markdown("---")
        st.markdown("### Resultado da comparação")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Compatibilidade ATS", f"{resultado['compat']}%")
        with m2:
            st.metric("Fit semântico", f"{resultado['semantic_fit']}%")
        with m3:
            final_score = st.session_state.get(f"final_score_{selected['id']}", 0)
            st.metric("Score consolidado", f"{final_score}%")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Palavras-chave encontradas**")
            st.success("\n".join(f"- {kw}" for kw in resultado.get("presentes", [])) or "-")
        with c2:
            st.markdown("**Palavras-chave ausentes**")
            st.error("\n".join(f"- {kw}" for kw in resultado.get("ausentes", [])) or "-")

    _render_llm_panel(selected, vaga_titulo, vaga_descricao)

    st.markdown("---")
    st.markdown("### Histórico de comparações deste currículo")
    historico = fetch_comparacoes_by_analise(selected["id"])
    if not historico:
        st.caption("Nenhuma comparação salva para este currículo.")
    else:
        for comp_id, h_vaga_titulo, compat, semantic_fit, created_at in historico[:10]:
            st.markdown(f"**#{comp_id}** | {h_vaga_titulo} | {created_at} | ATS {compat}% | Semântico {semantic_fit}%")
