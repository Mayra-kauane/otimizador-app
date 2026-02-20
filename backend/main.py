from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.constants import STATUS_CONCLUIDA, STATUS_EM_ANALISE
from core.db import (
    delete_analise,
    fetch_analise_by_id,
    fetch_analises,
    fetch_comparacao_by_id,
    fetch_comparacoes_by_analise,
    init_db,
    insert_analise,
    insert_comparacao,
    load_json_field,
    seed_if_empty,
    update_analise,
)
from core.logic import compare_with_job, make_report_text, score_from_metrics, section_metrics


class AnaliseCreate(BaseModel):
    candidato: str = Field(min_length=1)
    area: str = Field(min_length=1)


class ComparacaoRunRequest(BaseModel):
    analise_id: int
    vaga_titulo: str = Field(min_length=1)
    vaga_descricao: str = Field(min_length=1)
    salvar_resultado: bool = True


app = FastAPI(title="Resume AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    seed_if_empty()


def _resume_skills_from_area(area: str) -> list[str]:
    area_l = (area or "").lower()
    if "dado" in area_l:
        return ["Python", "SQL", "Power BI", "ETL", "Excel", "Dashboard"]
    if "market" in area_l:
        return ["SEO", "Google Ads", "CRM", "Analytics", "Conteudo"]
    if "vend" in area_l:
        return ["Prospeccao", "Pipeline", "Negociacao", "CRM", "Comercial"]
    return ["Comunicacao", "Excel", "Analise"]


def _semantic_mock(area: str) -> tuple[int, list[str], list[str]]:
    area_l = (area or "").lower()
    if "dado" in area_l:
        return 78, [
            "Falta aprofundar modelagem estatistica.",
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/analises")
def list_analises() -> list[dict[str, Any]]:
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


@app.get("/analises/{analise_id}")
def get_analise(analise_id: int) -> dict[str, Any]:
    row = fetch_analise_by_id(analise_id)
    if not row:
        raise HTTPException(status_code=404, detail="Analise nao encontrada")
    return {
        "id": row[0],
        "candidato": row[1],
        "area": row[2],
        "status": row[3],
        "score": row[4],
        "created_at": row[5],
    }


@app.post("/analises")
def create_analise(payload: AnaliseCreate) -> dict[str, Any]:
    analise_id = insert_analise(payload.candidato.strip(), payload.area.strip(), STATUS_EM_ANALISE, 0)
    row = fetch_analise_by_id(analise_id)
    return {
        "id": row[0],
        "candidato": row[1],
        "area": row[2],
        "status": row[3],
        "score": row[4],
        "created_at": row[5],
    }


@app.delete("/analises/{analise_id}")
def remove_analise(analise_id: int) -> dict[str, Any]:
    row = fetch_analise_by_id(analise_id)
    if not row:
        raise HTTPException(status_code=404, detail="Analise nao encontrada")
    delete_analise(analise_id)
    return {"deleted": True, "id": analise_id}


@app.post("/comparacoes/run")
def run_comparacao(payload: ComparacaoRunRequest) -> dict[str, Any]:
    analise = fetch_analise_by_id(payload.analise_id)
    if not analise:
        raise HTTPException(status_code=404, detail="Analise nao encontrada")

    area = analise[2]
    resume_skills = _resume_skills_from_area(area)
    kw_result = compare_with_job(payload.vaga_descricao, resume_skills)
    semantic_fit, lacunas, recomendacoes = _semantic_mock(area)

    metrics = section_metrics()
    base_score = score_from_metrics(metrics)
    final_score = int((base_score * 0.5) + (kw_result["compat"] * 0.25) + (semantic_fit * 0.25))

    update_analise(payload.analise_id, STATUS_CONCLUIDA, final_score)

    if payload.salvar_resultado:
        insert_comparacao(
            analise_id=payload.analise_id,
            vaga_titulo=payload.vaga_titulo,
            vaga_descricao=payload.vaga_descricao,
            compat=kw_result["compat"],
            semantic_fit=semantic_fit,
            presentes=kw_result["presentes"],
            ausentes=kw_result["ausentes"],
            lacunas=lacunas,
            recomendacoes=recomendacoes,
        )

    return {
        "analise_id": payload.analise_id,
        "vaga_titulo": payload.vaga_titulo,
        "compat": kw_result["compat"],
        "presentes": kw_result["presentes"],
        "ausentes": kw_result["ausentes"],
        "semantic_fit": semantic_fit,
        "lacunas": lacunas,
        "recomendacoes": recomendacoes,
        "final_score": final_score,
    }


@app.get("/comparacoes/analise/{analise_id}")
def list_comparacoes_by_analise(analise_id: int) -> list[dict[str, Any]]:
    rows = fetch_comparacoes_by_analise(analise_id)
    return [
        {
            "id": r[0],
            "vaga_titulo": r[1],
            "compat": r[2],
            "semantic_fit": r[3],
            "created_at": r[4],
        }
        for r in rows
    ]


@app.get("/comparacoes/{comparacao_id}")
def get_comparacao(comparacao_id: int) -> dict[str, Any]:
    row = fetch_comparacao_by_id(comparacao_id)
    if not row:
        raise HTTPException(status_code=404, detail="Comparacao nao encontrada")
    return {
        "id": row[0],
        "analise_id": row[1],
        "vaga_titulo": row[2],
        "vaga_descricao": row[3],
        "compat": row[4],
        "semantic_fit": row[5],
        "presentes": load_json_field(row[6]),
        "ausentes": load_json_field(row[7]),
        "lacunas": load_json_field(row[8]),
        "recomendacoes": load_json_field(row[9]),
        "created_at": row[10],
    }


@app.get("/relatorios/{analise_id}")
def get_relatorio(analise_id: int) -> dict[str, Any]:
    row = fetch_analise_by_id(analise_id)
    if not row:
        raise HTTPException(status_code=404, detail="Analise nao encontrada")

    score = row[4]
    parsed = {}
    comparacao = {}
    texto = make_report_text(row, parsed, comparacao, score)

    return {
        "analise_id": analise_id,
        "score": score,
        "texto": texto,
    }
