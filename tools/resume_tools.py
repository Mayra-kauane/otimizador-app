"""Tool definitions for resume analysis workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.logic import normalize_words


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


def extract_keywords(job_description: str, max_keywords: int = 20) -> dict[str, Any]:
    words = sorted(normalize_words(job_description))
    priority = [
        w
        for w in words
        if w
        in {
            "python",
            "sql",
            "etl",
            "aws",
            "azure",
            "power",
            "tableau",
            "excel",
            "crm",
            "analytics",
            "dashboard",
            "machine",
            "learning",
            "seo",
            "campanhas",
            "prospeccao",
            "negociacao",
            "pipeline",
        }
    ]
    merged = priority + [w for w in words if w not in priority]
    return {"keywords": merged[:max_keywords]}


def keyword_gap_analysis(resume_skills: list[str], job_keywords: list[str]) -> dict[str, Any]:
    resume_set = {s.lower().strip() for s in resume_skills if s}
    present = []
    missing = []
    for kw in job_keywords:
        token = kw.lower().strip()
        if token in resume_set:
            present.append(kw)
        else:
            missing.append(kw)
    compat = int((len(present) / len(job_keywords)) * 100) if job_keywords else 0
    return {"present": present, "missing": missing, "compatibility": compat}


def section_score_summary(section_metrics: dict[str, list[tuple]]) -> dict[str, Any]:
    summary = {}
    for section, items in section_metrics.items():
        if not items:
            summary[section] = 0
            continue
        avg = int(sum(int(i[1]) for i in items) / len(items))
        summary[section] = avg
    return {"section_scores": summary}


def prioritize_actions(missing_keywords: list[str], section_scores: dict[str, int]) -> dict[str, Any]:
    actions = []
    low_sections = [k for k, v in section_scores.items() if v < 70]

    if low_sections:
        for sec in low_sections:
            actions.append(f"Reescrever secao '{sec}' com foco em impacto e clareza.")

    if missing_keywords:
        actions.append(
            "Adicionar palavras-chave faltantes de forma natural: " + ", ".join(missing_keywords[:8])
        )

    if not actions:
        actions.append("Manter estrutura e ajustar pequenos detalhes de linguagem para a vaga alvo.")

    return {"actions": actions[:5]}


TOOL_REGISTRY = {
    "extract_keywords": extract_keywords,
    "keyword_gap_analysis": keyword_gap_analysis,
    "section_score_summary": section_score_summary,
    "prioritize_actions": prioritize_actions,
}


TOOL_SPECS = [
    ToolSpec(
        name="extract_keywords",
        description="Extrai palavras-chave relevantes da descricao da vaga.",
        input_schema={"job_description": "string", "max_keywords": "integer"},
    ),
    ToolSpec(
        name="keyword_gap_analysis",
        description="Compara skills do curriculo com palavras-chave da vaga e calcula compatibilidade.",
        input_schema={"resume_skills": "list[string]", "job_keywords": "list[string]"},
    ),
    ToolSpec(
        name="section_score_summary",
        description="Resume scores por secao com base nas metricas do curriculo.",
        input_schema={"section_metrics": "dict"},
    ),
    ToolSpec(
        name="prioritize_actions",
        description="Prioriza recomendacoes considerando gaps de palavras-chave e scores por secao.",
        input_schema={"missing_keywords": "list[string]", "section_scores": "dict[string,int]"},
    ),
]
