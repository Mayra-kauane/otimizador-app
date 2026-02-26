import streamlit as st

from core.constants import STATUS_EM_ANALISE
from core.db import insert_analise, update_analise_artifacts
from core.logic import parse_resume_real, score_from_metrics, section_metrics


def _clear_upload_state():
    st.session_state.pop("parsed", None)
    st.session_state.pop("parsed_source_sig", None)


def render():
    st.subheader("Upload e Parsing")
    st.caption("Envie o currículo e gere uma extração estruturada (parser real PDF/DOCX).")

    uploaded_file = st.file_uploader("Upload de PDF ou DOCX", type=["pdf", "docx"], key="upload_curriculo")
    if not uploaded_file:
        _clear_upload_state()

    current_sig = None
    if uploaded_file:
        current_sig = f"{uploaded_file.name}:{uploaded_file.size}"
        previous_sig = st.session_state.get("parsed_source_sig")
        if previous_sig and previous_sig != current_sig:
            _clear_upload_state()

    if st.button("Processar currículo", type="primary"):
        if not uploaded_file:
            st.warning("Envie um arquivo PDF ou DOCX.")
        else:
            parsed = parse_resume_real(uploaded_file.name, uploaded_file.getvalue())
            metrics = section_metrics(parsed)
            score_secao = score_from_metrics(metrics)
            candidato = parsed["dados"].get("Nome", "Candidato(a)")
            area = parsed["dados"].get("Area de interesse", "Dados")
            analise_id = insert_analise(
                candidato,
                area,
                STATUS_EM_ANALISE,
                score_secao,
                parsed_data=parsed,
                metrics_data=metrics,
            )
            st.session_state["parsed"] = parsed
            st.session_state["parsed_source_sig"] = current_sig
            st.session_state["section_metrics"] = metrics
            st.session_state["selected_analysis"] = analise_id
            st.session_state.setdefault("parsed_by_analysis", {})[analise_id] = parsed
            st.session_state.setdefault("metrics_by_analysis", {})[analise_id] = metrics
            st.success("Currículo processado com sucesso.")

    parsed = st.session_state.get("parsed")
    show_form = bool(parsed and uploaded_file and st.session_state.get("parsed_source_sig") == current_sig)
    if not show_form:
        return

    st.markdown("---")
    st.markdown("**Extração estruturada (formulário)**")
    with st.form("form_extracao_estruturada"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Dados pessoais**")
            nome = st.text_input("Nome", value=parsed["dados"].get("Nome", ""))
            email = st.text_input("E-mail", value=parsed["dados"].get("Email", ""))
            telefone = st.text_input("Telefone", value=parsed["dados"].get("Telefone", ""))
            linkedin = st.text_input("LinkedIn", value=parsed["dados"].get("LinkedIn", ""))
            localidade = st.text_input("Localidade", value=parsed["dados"].get("Localidade", ""))
            area_interesse = st.text_input("Área de interesse", value=parsed["dados"].get("Area de interesse", ""))
            arquivo = st.text_input("Arquivo de origem", value=parsed["dados"].get("Arquivo", ""))

        with c2:
            st.markdown("**Experiência**")
            exp1_empresa = st.text_input("Experiência 1 - Empresa", value=parsed["experiencia"][0].get("Empresa", "") if parsed["experiencia"] else "")
            exp1_cargo = st.text_input("Experiência 1 - Cargo", value=parsed["experiencia"][0].get("Cargo", "") if parsed["experiencia"] else "")
            exp1_periodo = st.text_input(
                "Experiência 1 - Período",
                value=parsed["experiencia"][0].get("Periodo", parsed["experiencia"][0].get("Per?odo", "")) if parsed["experiencia"] else "",
            )
            exp2_empresa = st.text_input("Experiência 2 - Empresa", value=parsed["experiencia"][1].get("Empresa", "") if len(parsed["experiencia"]) > 1 else "")
            exp2_cargo = st.text_input("Experiência 2 - Cargo", value=parsed["experiencia"][1].get("Cargo", "") if len(parsed["experiencia"]) > 1 else "")
            exp2_periodo = st.text_input(
                "Experiência 2 - Período",
                value=parsed["experiencia"][1].get("Periodo", parsed["experiencia"][1].get("Per?odo", "")) if len(parsed["experiencia"]) > 1 else "",
            )

        st.markdown("**Educação**")
        ed1_curso = st.text_input("Curso", value=parsed["educacao"][0].get("Curso", "") if parsed["educacao"] else "")
        ed1_inst = st.text_input(
            "Instituição",
            value=parsed["educacao"][0].get("Instituicao", parsed["educacao"][0].get("Institui??o", "")) if parsed["educacao"] else "",
        )
        ed1_per = st.text_input(
            "Período",
            value=parsed["educacao"][0].get("Periodo", parsed["educacao"][0].get("Per?odo", "")) if parsed["educacao"] else "",
        )
        habilidades = st.text_area("Habilidades", value=", ".join(parsed.get("habilidades", [])))
        certificacoes = st.text_area("Certificações", value=", ".join(parsed.get("certificacoes", [])))
        salvar = st.form_submit_button("Atualizar extração")

    if not salvar:
        return

    parsed["dados"].update(
        {
            "Nome": nome,
            "Email": email,
            "Telefone": telefone,
            "LinkedIn": linkedin,
            "Localidade": localidade,
            "Area de interesse": area_interesse,
            "Arquivo": arquivo,
        }
    )
    parsed["experiencia"] = [
        {"Empresa": exp1_empresa, "Cargo": exp1_cargo, "Periodo": exp1_periodo},
        {"Empresa": exp2_empresa, "Cargo": exp2_cargo, "Periodo": exp2_periodo},
    ]
    parsed["educacao"] = [{"Curso": ed1_curso, "Instituicao": ed1_inst, "Periodo": ed1_per}]
    parsed["habilidades"] = [s.strip() for s in habilidades.split(",") if s.strip()]
    parsed["certificacoes"] = [s.strip() for s in certificacoes.split(",") if s.strip()]

    metrics = section_metrics(parsed)
    score_secao = score_from_metrics(metrics)
    analise_id = st.session_state.get("selected_analysis")
    if analise_id:
        update_analise_artifacts(
            analise_id=analise_id,
            parsed_data=parsed,
            metrics_data=metrics,
            candidato=parsed["dados"].get("Nome", "Candidato(a)"),
            area=parsed["dados"].get("Area de interesse", "Dados"),
            score=score_secao,
        )

    st.session_state["parsed"] = parsed
    st.session_state["section_metrics"] = metrics
    if analise_id:
        st.session_state.setdefault("parsed_by_analysis", {})[analise_id] = parsed
        st.session_state.setdefault("metrics_by_analysis", {})[analise_id] = metrics
    st.success("Extração atualizada.")
