import re
from datetime import datetime
from io import BytesIO


def normalize_words(text: str) -> set[str]:
    words = re.findall(r"[A-Za-z0-9\-\+]+", (text or "").lower())
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
    lower = (text or "").lower()
    if any(k in lower for k in ["sql", "python", "power bi", "etl", "dados", "analytics"]):
        return "Dados"
    if any(k in lower for k in ["seo", "ads", "campanha", "marketing", "crm"]):
        return "Marketing"
    if any(k in lower for k in ["vendas", "prospec", "pipeline", "negocia"]):
        return "Vendas"
    return "Dados"


def _extract_text_pdf(uploaded_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ""

    text_chunks: list[str] = []
    try:
        reader = PdfReader(BytesIO(uploaded_bytes))
        for page in reader.pages:
            text_chunks.append(page.extract_text() or "")
    except Exception:
        return ""
    return "\n".join(text_chunks)


def _extract_text_docx(uploaded_bytes: bytes) -> str:
    try:
        from docx import Document
    except Exception:
        return ""

    try:
        doc = Document(BytesIO(uploaded_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text and p.text.strip())
    except Exception:
        return ""


def _extract_resume_text(uploaded_name: str | None, uploaded_bytes: bytes | None) -> str:
    if not uploaded_bytes:
        return ""

    ext = ""
    if uploaded_name and "." in uploaded_name:
        ext = uploaded_name.rsplit(".", 1)[1].lower()

    if ext == "pdf":
        text = _extract_text_pdf(uploaded_bytes)
        if text.strip():
            return text
    if ext == "docx":
        text = _extract_text_docx(uploaded_bytes)
        if text.strip():
            return text

    return uploaded_bytes.decode("latin-1", errors="ignore")[:12000]


def _clean_lines(text: str) -> list[str]:
    raw = re.split(r"\r?\n+", text or "")
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw]
    return [line for line in lines if line]


def _extract_contact(lines: list[str]) -> dict[str, str]:
    joined = "\n".join(lines)
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", joined)
    phone_match = re.search(r"(\+?\d{1,3}\s*)?(\(?\d{2}\)?\s*)?\d{4,5}[\s\-]?\d{4}", joined)
    linkedin_match = re.search(r"(https?://)?(www\.)?linkedin\.com/[\w\-/]+", joined, flags=re.IGNORECASE)

    location = "Nao identificado"
    for line in lines[:20]:
        if "," in line and any(token in line.lower() for token in ["brasil", "sp", "rj", "mg", "rs", "sc", "pr"]):
            location = line
            break

    return {
        "Email": email_match.group(0) if email_match else "Nao identificado",
        "Telefone": phone_match.group(0) if phone_match else "Nao identificado",
        "LinkedIn": linkedin_match.group(0) if linkedin_match else "Nao identificado",
        "Localidade": location,
    }


def _detect_name(lines: list[str], uploaded_name: str | None) -> str:
    for line in lines[:6]:
        if re.search(r"@|linkedin|http|curriculo|resume", line.lower()):
            continue
        words = line.split()
        if 1 < len(words) <= 5 and all(re.match(r"^[A-Za-z'\-]+$", w) for w in words):
            return " ".join(w.title() for w in words)
    return _guess_name_from_filename(uploaded_name)


def _extract_section_block(lines: list[str], heading_patterns: list[str]) -> list[str]:
    normalized = [line.lower() for line in lines]
    start = -1
    for i, line in enumerate(normalized):
        if any(re.search(p, line) for p in heading_patterns):
            start = i + 1
            break
    if start < 0:
        return []

    end = len(lines)
    stop_patterns = [r"^experi", r"^educa", r"^habil", r"^skill", r"^certif", r"^resumo", r"^objetivo"]
    for j in range(start, len(lines)):
        lower = normalized[j]
        if any(re.search(p, lower) for p in stop_patterns):
            if j > start:
                end = j
                break
    return lines[start:end]


def _extract_skills(lines: list[str], full_text: str, area: str) -> list[str]:
    section = _extract_section_block(lines, [r"^habil", r"^skills", r"^compet"])
    tokens: list[str] = []
    for line in section:
        tokens.extend(re.split(r",|;|\||/", line))

    clean = []
    for token in tokens:
        t = token.strip(" -\t*")
        if 2 <= len(t) <= 40:
            clean.append(t)

    if clean:
        return list(dict.fromkeys(clean))[:20]

    area_skills = {
        "dados": ["Python", "SQL", "Power BI", "ETL", "Excel"],
        "marketing": ["SEO", "Google Ads", "CRM", "Analytics", "Conteudo"],
        "vendas": ["CRM", "Negociacao", "Prospeccao", "Pipeline", "Comercial"],
    }

    key = area.lower()
    if "dado" in key:
        return area_skills["dados"]
    if "market" in key:
        return area_skills["marketing"]
    if "vend" in key:
        return area_skills["vendas"]

    word_candidates = sorted(normalize_words(full_text))[:12]
    return [w.title() for w in word_candidates[:8]] or ["Comunicacao", "Excel"]


def _extract_experience(lines: list[str]) -> list[dict[str, str]]:
    section = _extract_section_block(lines, [r"^experi", r"^historico profissional"])
    if not section:
        return []

    items: list[dict[str, str]] = []
    for line in section:
        if len(items) >= 4:
            break
        if len(line) < 6:
            continue
        parts = [p.strip() for p in re.split(r" - |\||;", line) if p.strip()]
        if not parts:
            continue

        company = parts[0]
        role = parts[1] if len(parts) > 1 else "Nao identificado"
        period_match = re.search(r"(19|20)\d{2}\s*(-|ate|a)\s*((19|20)\d{2}|atual)", line.lower())
        period = period_match.group(0).replace("ate", "-") if period_match else "Nao identificado"
        items.append({"Empresa": company, "Cargo": role, "Periodo": period})

    return items[:2]


def _extract_education(lines: list[str]) -> list[dict[str, str]]:
    section = _extract_section_block(lines, [r"^educa", r"^formacao"])
    if not section:
        return []

    first = section[0]
    parts = [p.strip() for p in re.split(r" - |\||;", first) if p.strip()]
    course = parts[0] if parts else "Nao identificado"
    institution = parts[1] if len(parts) > 1 else "Nao identificado"
    period_match = re.search(r"(19|20)\d{2}\s*(-|ate|a)\s*((19|20)\d{2}|atual)", first.lower())
    period = period_match.group(0).replace("ate", "-") if period_match else "Nao identificado"

    return [{"Curso": course, "Instituicao": institution, "Periodo": period}]


def _extract_certifications(lines: list[str]) -> list[str]:
    section = _extract_section_block(lines, [r"^certif", r"^cursos"])
    certs = []
    for line in section:
        cleaned = line.strip(" -\t*")
        if cleaned and len(cleaned) <= 80:
            certs.append(cleaned)
    return certs[:6]


def parse_resume_real(uploaded_name: str | None, uploaded_bytes: bytes | None):
    raw_text = _extract_resume_text(uploaded_name, uploaded_bytes)
    lines = _clean_lines(raw_text)

    candidato = _detect_name(lines, uploaded_name)
    area = _infer_area(raw_text)
    contact = _extract_contact(lines)
    skills = _extract_skills(lines, raw_text, area)
    experience = _extract_experience(lines)
    education = _extract_education(lines)
    certifications = _extract_certifications(lines)

    if not experience:
        experience = [{"Empresa": "Nao identificado", "Cargo": "Nao identificado", "Periodo": "Nao identificado"}]
    if not education:
        education = [{"Curso": "Nao identificado", "Instituicao": "Nao identificado", "Periodo": "Nao identificado"}]

    return {
        "dados": {
            "Nome": candidato,
            "Email": contact["Email"],
            "Telefone": contact["Telefone"],
            "LinkedIn": contact["LinkedIn"],
            "Localidade": contact["Localidade"],
            "Area de interesse": area,
            "Arquivo": uploaded_name or "Nao enviado",
        },
        "experiencia": experience,
        "educacao": education,
        "habilidades": skills,
        "certificacoes": certifications,
    }


def _count_valid_entries(items: list[dict], keys: list[str]) -> int:
    total = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        row = " ".join(str(item.get(k, "")).strip().lower() for k in keys)
        if row and "nao identificado" not in row:
            total += 1
    return total


def section_metrics(parsed: dict | None = None):
    if parsed:
        experiencia = parsed.get("experiencia", []) if isinstance(parsed, dict) else []
        educacao = parsed.get("educacao", []) if isinstance(parsed, dict) else []
        habilidades = parsed.get("habilidades", []) if isinstance(parsed, dict) else []

        exp_validas = _count_valid_entries(experiencia, ["Empresa", "Cargo", "Periodo"])
        edu_valida = _count_valid_entries(educacao, ["Curso", "Instituicao", "Periodo"])
        hab_validas = len([h for h in habilidades if isinstance(h, str) and h.strip()])

        score_resumo = 80 if parsed.get("dados", {}).get("Area de interesse") else 60
        score_tamanho = 90 if 6 <= hab_validas <= 18 else 70
        score_ordem = 82 if exp_validas > 0 and edu_valida > 0 else 62

        score_qtd_exp = min(100, 55 + (exp_validas * 12))
        score_tempo = 78 if any(re.search(r"(19|20)\d{2}", str(e.get("Periodo", ""))) for e in experiencia) else 60
        score_verbos = 76 if any(re.search(r"(desenvolv|implem|lider|otimiz|aument|reduz)", str(e.get("Cargo", "")).lower()) for e in experiencia) else 58

        hard_keywords = {
            "python",
            "sql",
            "etl",
            "power bi",
            "aws",
            "tableau",
            "excel",
            "crm",
            "analytics",
            "dash",
        }
        soft_keywords = {
            "comunic",
            "lider",
            "colabor",
            "proativ",
            "organiza",
            "negocia",
        }
        hard_count = sum(1 for h in habilidades if any(k in h.lower() for k in hard_keywords))
        soft_count = sum(1 for h in habilidades if any(k in h.lower() for k in soft_keywords))

        score_hard = min(100, 55 + (hard_count * 8))
        score_soft = min(100, 55 + (soft_count * 10))
        score_aderencia = min(100, int((score_hard * 0.6) + (score_soft * 0.4)))

        return {
            "estrutura": [
                ("Resumo profissional", int(score_resumo), "Bom" if score_resumo >= 75 else "Regular", "Ajuste o resumo para foco no alvo da vaga."),
                ("Tamanho adequado", int(score_tamanho), "Bom" if score_tamanho >= 75 else "Regular", "Mantenha volume equilibrado de informações."),
                ("Ordem logica", int(score_ordem), "Bom" if score_ordem >= 75 else "Precisa melhorar", "Estruture experiência e educação em sequência clara."),
            ],
            "experiencia": [
                ("Quantidade de experiencias", int(score_qtd_exp), "Bom" if score_qtd_exp >= 75 else "Regular", "Inclua experiências relevantes para a vaga."),
                ("Tempo medio", int(score_tempo), "Bom" if score_tempo >= 75 else "Regular", "Informe períodos para dar contexto da evolução."),
                ("Verbos de acao", int(score_verbos), "Bom" if score_verbos >= 75 else "Precisa melhorar", "Use verbos de impacto no início dos bullets."),
            ],
            "habilidades": [
                ("Hard skills", int(score_hard), "Bom" if score_hard >= 75 else "Regular", "Evidencie stack técnica alinhada à vaga."),
                ("Soft skills", int(score_soft), "Bom" if score_soft >= 75 else "Precisa melhorar", "Mostre soft skills com exemplos concretos."),
                ("Aderencia ao alvo", int(score_aderencia), "Bom" if score_aderencia >= 75 else "Regular", "Priorize palavras-chave da vaga no currículo."),
            ],
        }

    return {
        "estrutura": [
            ("Resumo profissional", 70, "Regular", "Resumo pode ser mais objetivo e orientado a resultados."),
            ("Tamanho adequado", 86, "Bom", "Curriculo direto e com tamanho adequado para o perfil."),
            ("Ordem logica", 64, "Precisa melhorar", "Experiencia deve vir antes da educacao para este perfil."),
        ],
        "experiencia": [
            ("Quantidade de experiencias", 78, "Bom", "Quantidade coerente com o nivel atual."),
            ("Tempo medio", 66, "Regular", "Inclua contexto e impacto em cada periodo."),
            ("Verbos de acao", 58, "Precisa melhorar", "Trocar frases passivas por verbos de impacto."),
        ],
        "habilidades": [
            ("Hard skills", 74, "Bom", "Base tecnica competitiva para muitas vagas."),
            ("Soft skills", 57, "Precisa melhorar", "Citar exemplos praticos de colaboracao e lideranca."),
            ("Aderencia ao alvo", 68, "Regular", "Adicionar termos tecnicos da vaga-alvo."),
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
        "analise": "Analise",
        "dashboard": "Dashboard",
        "machine": "Machine Learning",
    }

    job_keywords = [label for token, label in canonical.items() if token in desc_words]
    if not job_keywords:
        job_keywords = ["SQL", "Python", "Excel", "Comunicacao", "Analise"]

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
    candidato = row[1] if row else parsed.get("dados", {}).get("Nome", "Nao informado")
    area = row[2] if row else "Nao informada"
    data = row[5] if row else datetime.now().strftime("%Y-%m-%d %H:%M")

    presentes = comparacao.get("presentes", [])
    ausentes = comparacao.get("ausentes", [])

    lines = [
        "RELATORIO FINAL - ANALISE DE CURRICULO",
        "",
        f"Candidato: {candidato}",
        f"Area: {area}",
        f"Data: {data}",
        f"Score geral: {score if score is not None else 'N/A'}%",
        "",
        "Pontos fortes:",
        "- Organizacao geral adequada",
        "- Base tecnica com potencial de aderencia",
        "- Estrutura clara para leitura inicial",
        "",
        "Pontos de melhoria:",
        "- Fortalecer resumo profissional com objetivo claro",
        "- Quantificar resultados na experiencia",
        "- Incluir palavras-chave da vaga no curriculo",
        "",
        "Palavras-chave encontradas:",
        ", ".join(presentes) if presentes else "Nenhuma",
        "",
        "Palavras-chave ausentes:",
        ", ".join(ausentes) if ausentes else "Nenhuma",
    ]
    return "\n".join(lines)
