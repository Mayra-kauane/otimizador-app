import streamlit as st

from core.constants import STATUS_CONCLUIDA
from core.db import fetch_analises, fetch_comparacoes_by_analise, insert_comparacao, update_analise
from core.logic import compare_with_job, score_from_metrics, section_metrics


DEFAULT_VAGAS = [
    {
        "titulo": "Analista de Dados Pleno",
        "descricao": "Python SQL ETL Dashboard Power BI Analise de dados Comunicacao",
    },
    {
        "titulo": "Especialista em Marketing Digital",
        "descricao": "SEO Google Ads CRM Analytics Conteudo Campanhas Relatorios",
    },
    {
        "titulo": "Executivo de Vendas B2B",
        "descricao": "Prospeccao Pipeline Negociacao CRM Metas Relacionamento Comercial",
    },
]


def _ensure_vagas_state():
    if "vagas_cadastradas" not in st.session_state:
        st.session_state["vagas_cadastradas"] = DEFAULT_VAGAS.copy()


def _resume_skills_from_area(area: str):
    area_l = (area or "").lower()
    if "dado" in area_l:
        return ["Python", "SQL", "Power BI", "ETL", "Excel", "Dashboard"]
    if "market" in area_l:
        return ["SEO", "Google Ads", "CRM", "Analytics", "Conteudo"]
    if "vend" in area_l:
        return ["Prospeccao", "Pipeline", "Negociacao", "CRM", "Comercial"]
    return ["Comunicacao", "Excel", "Analise"]


def _semantic_mock(area: str):
    area_l = (area or "").lower()
    if "dado" in area_l:
        return 78, [
            "Falta aprofundar Modelagem Estatistica.",
            "Baixa evidencia de cloud (AWS/Azure).",
        ], [
            "Adicionar projeto com ETL ponta a ponta.",
            "Incluir experiencia com analise preditiva e metricas de negocio.",
        ]
    if "market" in area_l:
        return 74, [
            "Pouca evidencia de funil completo.",
            "Ausencia de casos com ROI detalhado.",
        ], [
            "Destacar campanhas com CAC, LTV e ROI.",
            "Relacionar resultados por canal e audiencia.",
        ]
    if "vend" in area_l:
        return 76, [
            "Nao explicita ticket medio e ciclo de venda.",
            "Pouca evidencia de estrategia de account management.",
        ], [
            "Adicionar metas batidas por periodo.",
            "Incluir exemplos de negociacao complexa B2B.",
        ]
    return 70, ["Faltam evidencias de impacto mensuravel."], ["Incluir resultados quantificados por secao."]


def render():
    st.subheader("Comparacao com a Vaga")
    st.caption("Fluxo estruturado para comparar curriculos salvos com vagas e gerar recomendacoes.")

    _ensure_vagas_state()

    # Etapa 1
    st.markdown("### Etapa 1 - Selecione o curriculo")
    rows = fetch_analises()
    if not rows:
        st.info("Nenhum curriculo salvo para comparar.")
        return

    options = [
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

    default_index = 0
    selected_id = st.session_state.get("selected_analysis")
    if selected_id:
        for i, opt in enumerate(options):
            if opt["id"] == selected_id:
                default_index = i
                break

    selected = st.selectbox(
        "Curriculo salvo",
        options,
        index=default_index,
        format_func=lambda o: f"{o['candidato']} | {o['area']} | {o['created_at']}",
    )
    st.session_state["selected_analysis"] = selected["id"]

    # Etapa 2
    st.markdown("### Etapa 2 - Escolha ou cadastre a vaga")
    modo = st.radio(
        "Origem da vaga",
        ["Escolher vaga cadastrada", "Inserir nova vaga"],
        horizontal=True,
    )

    vaga_titulo = ""
    vaga_descricao = ""

    if modo == "Escolher vaga cadastrada":
        vaga = st.selectbox(
            "Vagas cadastradas",
            st.session_state["vagas_cadastradas"],
            format_func=lambda v: v["titulo"],
        )
        vaga_titulo = vaga["titulo"]
        vaga_descricao = vaga["descricao"]
        st.text_area("Descricao da vaga", value=vaga_descricao, height=140, disabled=True)
    else:
        vaga_titulo = st.text_input("Titulo da vaga")
        vaga_descricao = st.text_area("Descricao da vaga", height=160)
        csave1, csave2 = st.columns([1, 3])
        with csave1:
            if st.button("Salvar vaga"):
                if vaga_titulo.strip() and vaga_descricao.strip():
                    st.session_state["vagas_cadastradas"].append(
                        {"titulo": vaga_titulo.strip(), "descricao": vaga_descricao.strip()}
                    )
                    st.success("Vaga cadastrada com sucesso.")
                else:
                    st.warning("Preencha titulo e descricao para salvar a vaga.")

    # Etapa 3
    st.markdown("### Etapa 3 - Execute a analise")
    salvar_resultado = st.checkbox("Salvar resultado no historico de comparacoes", value=True)

    if st.button("Executar comparacao", type="primary"):
        if not vaga_descricao.strip():
            st.warning("Forneca uma descricao de vaga para executar a comparacao.")
        else:
            resume_skills = _resume_skills_from_area(selected["area"])
            resultado = compare_with_job(vaga_descricao, resume_skills)

            semantic_fit, lacunas, recomendacoes = _semantic_mock(selected["area"])

            st.session_state["comparacao"] = {
                **resultado,
                "semantic_fit": semantic_fit,
                "lacunas": lacunas,
                "recomendacoes": recomendacoes,
                "vaga_titulo": vaga_titulo or "Vaga sem titulo",
            }

            metrics = st.session_state.get("section_metrics", section_metrics())
            base_score = score_from_metrics(metrics)
            final_score = int((base_score * 0.5) + (resultado["compat"] * 0.25) + (semantic_fit * 0.25))
            st.session_state["final_score"] = final_score

            update_analise(selected["id"], STATUS_CONCLUIDA, final_score)

            if salvar_resultado:
                insert_comparacao(
                    analise_id=selected["id"],
                    vaga_titulo=vaga_titulo or "Vaga sem titulo",
                    vaga_descricao=vaga_descricao,
                    compat=resultado["compat"],
                    semantic_fit=semantic_fit,
                    presentes=resultado["presentes"],
                    ausentes=resultado["ausentes"],
                    lacunas=lacunas,
                    recomendacoes=recomendacoes,
                )

    resultado = st.session_state.get("comparacao")
    if resultado:
        st.markdown("---")
        st.markdown("### Resultado da comparacao")

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Compatibilidade ATS", f"{resultado['compat']}%")
        with m2:
            st.metric("Correspondencia semantica (mock)", f"{resultado['semantic_fit']}%")
        with m3:
            st.metric("Score consolidado", f"{st.session_state.get('final_score', 0)}%")

        st.progress(resultado["compat"] / 100)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Palavras-chave encontradas**")
            if resultado["presentes"]:
                st.success("\n".join(f"- {kw}" for kw in resultado["presentes"]))
            else:
                st.info("Nenhuma palavra-chave encontrada.")

        with c2:
            st.markdown("**Palavras-chave ausentes**")
            if resultado["ausentes"]:
                st.error("\n".join(f"- {kw}" for kw in resultado["ausentes"]))
            else:
                st.success("Nenhuma palavra-chave ausente.")

        c3, c4 = st.columns(2)
        with c3:
            st.markdown("**Lacunas estrategicas (mock semantico)**")
            st.warning("\n".join(f"- {i}" for i in resultado.get("lacunas", [])))
        with c4:
            st.markdown("**Sugestoes de adaptacao do curriculo (mock IA)**")
            st.info("\n".join(f"- {i}" for i in resultado.get("recomendacoes", [])))

    st.markdown("---")
    st.markdown("### Historico de comparacoes deste curriculo")
    historico = fetch_comparacoes_by_analise(selected["id"])
    if not historico:
        st.caption("Nenhuma comparacao salva para este curriculo.")
    else:
        for comp_id, vaga_titulo, compat, semantic_fit, created_at in historico[:10]:
            st.markdown(
                f"**#{comp_id}** | {vaga_titulo} | {created_at} | ATS {compat}% | Semantico {semantic_fit}%"
            )
