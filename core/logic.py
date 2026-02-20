import re
from datetime import datetime


def normalize_words(text: str) -> set[str]:
    words = re.findall(r"[A-Za-z0-9\-\+]+", text.lower())
    return {w for w in words if len(w) > 2}


def _guess_name_from_filename(uploaded_name: str | None) -> str:
    if not uploaded_name:
        return "Candidato(a)"
    base = re.sub(r"\.(pdf|docx)$", "", uploaded_name, flags=re.IGNORECASE)
    base = re.sub(r"[_\-]+", " ", base).strip()
    if not base:
        return "Candidato(a)"
    words = [w for w in base.split() if len(w) > 1]
    if len(words) >= 2:
        return f"{words[0].title()} {words[1].title()}"
    return words[0].title()


def _infer_area(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ["sql", "python", "power bi", "etl", "dados", "analytics"]):
        return "Dados"
    if any(k in lower for k in ["seo", "ads", "campanha", "marketing", "crm"]):
        return "Marketing"
    if any(k in lower for k in ["vendas", "prospec", "pipeline", "negocia"]):
        return "Vendas"
    return "Dados"


def _extract_resume_text_heuristic(uploaded_name: str | None, uploaded_bytes: bytes | None) -> str:
    if not uploaded_bytes:
        return uploaded_name or ""
    # Heurística simples sem dependências externas: tenta achar trechos legíveis no binário.
    text = uploaded_bytes.decode("latin-1", errors="ignore")
    return f"{uploaded_name or ''} {text[:5000]}"


def parse_resume_mock(uploaded_name: str | None, uploaded_bytes: bytes | None):
    raw_text = _extract_resume_text_heuristic(uploaded_name, uploaded_bytes)
    candidato = _guess_name_from_filename(uploaded_name)
    area = _infer_area(raw_text)

    base_skills = {
        "dados": ["Python", "SQL", "Power BI", "ETL", "Excel"],
        "marketing": ["SEO", "Google Ads", "CRM", "Canva", "Analytics"],
        "vendas": ["CRM", "Negociacao", "Prospeccao", "Pipeline", "PowerPoint"],
    }
    area_key = area.lower()
    if "dado" in area_key:
        skills = base_skills["dados"]
    elif "market" in area_key:
        skills = base_skills["marketing"]
    elif "vend" in area_key:
        skills = base_skills["vendas"]
    else:
        skills = ["Comunicação", "Excel", "Organização", "Análise", "Planejamento"]

    return {
        "dados": {
            "Nome": candidato,
            "Email": "candidato@email.com",
            "Telefone": "+55 (11) 99999-0000",
            "LinkedIn": "linkedin.com/in/candidato",
            "Localidade": "São Paulo, SP",
            "Área de interesse": area,
            "Arquivo": uploaded_name or "Não enviado",
        },
        "experiencia": [
            {"Empresa": "TechNova", "Cargo": "Analista", "Período": "2022 - Atual"},
            {"Empresa": "DataUp", "Cargo": "Assistente", "Período": "2020 - 2022"},
        ],
        "educacao": [
            {"Curso": "Graduação", "Instituição": "Universidade Exemplo", "Período": "2018 - 2022"}
        ],
        "habilidades": skills,
        "certificacoes": ["Curso de Excel", "Fundamentos de Análise de Dados"],
    }


def section_metrics():
    return {
        "estrutura": [
            ("Resumo profissional", 70, "Regular", "Resumo pode ser mais objetivo e orientado a resultados."),
            ("Tamanho adequado", 86, "Bom", "Currículo direto e com tamanho adequado para o perfil."),
            ("Ordem lógica", 64, "Precisa melhorar", "Experiência deve vir antes da educação para este perfil."),
        ],
        "experiencia": [
            ("Quantidade de experiências", 78, "Bom", "Quantidade coerente com o nível atual."),
            ("Tempo médio", 66, "Regular", "Inclua contexto e impacto em cada período."),
            ("Verbos de ação", 58, "Precisa melhorar", "Trocar frases passivas por verbos de impacto."),
        ],
        "habilidades": [
            ("Hard skills", 74, "Bom", "Base técnica competitiva para muitas vagas."),
            ("Soft skills", 57, "Precisa melhorar", "Citar exemplos práticos de colaboração e liderança."),
            ("Aderência ao alvo", 68, "Regular", "Adicionar termos técnicos da vaga-alvo."),
        ],
    }


def score_from_metrics(metrics: dict) -> int:
    values = [item[1] for group in metrics.values() for item in group]
    return int(sum(values) / len(values)) if values else 0


def compare_with_job(description: str, resume_skills: list[str]):
    skill_terms = {s.lower() for s in resume_skills}
    desc_words = normalize_words(description)

    canonical = {
        "python": "Python",
        "sql": "SQL",
        "etl": "ETL",
        "aws": "AWS",
        "power": "Power BI",
        "tableau": "Tableau",
        "excel": "Excel",
        "crm": "CRM",
        "analise": "Análise",
        "dashboard": "Dashboard",
        "machine": "Machine Learning",
    }

    job_keywords = [label for token, label in canonical.items() if token in desc_words]
    if not job_keywords:
        job_keywords = ["SQL", "Python", "Excel", "Comunicação", "Análise"]

    presentes = []
    ausentes = []
    for kw in job_keywords:
        kw_tokens = normalize_words(kw)
        if kw.lower() in skill_terms or kw_tokens.intersection(skill_terms):
            presentes.append(kw)
        else:
            ausentes.append(kw)

    compat = int((len(presentes) / len(job_keywords)) * 100) if job_keywords else 0
    return {"compat": compat, "presentes": presentes, "ausentes": ausentes, "job_keywords": job_keywords}


def make_report_text(row, parsed, comparacao, score) -> str:
    candidato = row[1] if row else parsed.get("dados", {}).get("Nome", "Não informado")
    area = row[2] if row else "Não informada"
    data = row[5] if row else datetime.now().strftime("%Y-%m-%d %H:%M")

    presentes = comparacao.get("presentes", [])
    ausentes = comparacao.get("ausentes", [])

    lines = [
        "RELATÓRIO FINAL - ANÁLISE DE CURRÍCULO",
        "",
        f"Candidato: {candidato}",
        f"Área: {area}",
        f"Data: {data}",
        f"Score geral: {score if score is not None else 'N/A'}%",
        "",
        "Pontos fortes:",
        "- Organização geral adequada",
        "- Base técnica com potencial de aderência",
        "- Estrutura clara para leitura inicial",
        "",
        "Pontos de melhoria:",
        "- Fortalecer resumo profissional com objetivo claro",
        "- Quantificar resultados na experiência",
        "- Incluir palavras-chave da vaga no currículo",
        "",
        "Palavras-chave encontradas:",
        ", ".join(presentes) if presentes else "Nenhuma",
        "",
        "Palavras-chave ausentes:",
        ", ".join(ausentes) if ausentes else "Nenhuma",
    ]
    return "\n".join(lines)
