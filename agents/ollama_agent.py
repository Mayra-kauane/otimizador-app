"""Simple tool-augmented agent for Ollama chat API."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

from tools.resume_tools import TOOL_REGISTRY, TOOL_SPECS

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
MAX_TEXT_CHARS = 8000
MAX_SKILLS = 60
MAX_TOOL_CALLS = 6


@dataclass
class OllamaConfig:
    model: str = "llama3.1:8b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.3
    top_p: float = 0.9
    num_predict: int = 700
    timeout_seconds: int = 120


def _read_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")


def _safe_json(raw: str) -> dict[str, Any]:
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return {}
        return {}


def _sanitize_text(value: str, max_chars: int = MAX_TEXT_CHARS) -> str:
    text = (value or "").strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text[:max_chars]


def _sanitize_skills(skills: list[str]) -> list[str]:
    clean: list[str] = []
    for item in skills or []:
        token = _sanitize_text(str(item), max_chars=60)
        if token:
            clean.append(token)

    dedup: list[str] = []
    seen = set()
    for token in clean:
        key = token.lower()
        if key not in seen:
            seen.add(key)
            dedup.append(token)
    return dedup[:MAX_SKILLS]


def _ollama_chat(config: OllamaConfig, messages: list[dict[str, str]]) -> str:
    payload = {
        "model": config.model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": config.temperature,
            "top_p": config.top_p,
            "num_predict": config.num_predict,
        },
    }

    req = request.Request(
        url=f"{config.base_url}/api/chat",
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with request.urlopen(req, timeout=config.timeout_seconds) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("message", {}).get("content", "")
    except error.URLError as exc:
        raise RuntimeError(
            "Falha ao conectar no Ollama. Verifique se o servidor está rodando em http://localhost:11434."
        ) from exc


def _tool_descriptions() -> str:
    return "\n".join(
        f"- {t.name}: {t.description}. Inputs: {json.dumps(t.input_schema, ensure_ascii=False)}" for t in TOOL_SPECS
    )


def _execute_tool_calls(tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for call in tool_calls[:MAX_TOOL_CALLS]:
        name = call.get("name")
        args = call.get("arguments", {})
        fn = TOOL_REGISTRY.get(name)
        if not fn:
            results.append({"tool": name, "error": "tool_not_found"})
            continue
        try:
            output = fn(**args)
            results.append({"tool": name, "arguments": args, "output": output})
        except Exception as exc:
            results.append({"tool": name, "arguments": args, "error": str(exc)})
    return results


def _get_tool_output(tool_results: list[dict[str, Any]], tool_name: str) -> dict[str, Any] | None:
    for item in tool_results:
        if item.get("tool") == tool_name and isinstance(item.get("output"), dict):
            return item["output"]
    return None


def _ensure_required_tool_results(
    tool_results: list[dict[str, Any]],
    *,
    job_description: str,
    resume_skills: list[str],
    section_metrics: dict[str, list[tuple]],
) -> list[dict[str, Any]]:
    keywords_output = _get_tool_output(tool_results, "extract_keywords")
    if not keywords_output:
        tool_results.append(
            {
                "tool": "extract_keywords",
                "arguments": {"job_description": job_description, "max_keywords": 20},
                "output": TOOL_REGISTRY["extract_keywords"](job_description=job_description, max_keywords=20),
            }
        )
        keywords_output = _get_tool_output(tool_results, "extract_keywords")

    job_keywords = (keywords_output or {}).get("keywords", [])

    gap_output = _get_tool_output(tool_results, "keyword_gap_analysis")
    if not gap_output:
        tool_results.append(
            {
                "tool": "keyword_gap_analysis",
                "arguments": {"resume_skills": resume_skills, "job_keywords": job_keywords},
                "output": TOOL_REGISTRY["keyword_gap_analysis"](
                    resume_skills=resume_skills,
                    job_keywords=job_keywords,
                ),
            }
        )
        gap_output = _get_tool_output(tool_results, "keyword_gap_analysis")

    score_output = _get_tool_output(tool_results, "section_score_summary")
    if not score_output:
        tool_results.append(
            {
                "tool": "section_score_summary",
                "arguments": {"section_metrics": section_metrics},
                "output": TOOL_REGISTRY["section_score_summary"](section_metrics=section_metrics),
            }
        )
        score_output = _get_tool_output(tool_results, "section_score_summary")

    if not _get_tool_output(tool_results, "prioritize_actions"):
        missing = (gap_output or {}).get("missing", [])
        section_scores = (score_output or {}).get("section_scores", {})
        tool_results.append(
            {
                "tool": "prioritize_actions",
                "arguments": {"missing_keywords": missing, "section_scores": section_scores},
                "output": TOOL_REGISTRY["prioritize_actions"](
                    missing_keywords=missing,
                    section_scores=section_scores,
                ),
            }
        )

    return tool_results


def _normalize_final_output(final_json: dict[str, Any], tool_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(final_json, dict):
        final_json = {}

    actions_output = _get_tool_output(tool_results, "prioritize_actions") or {}
    fallback_actions = actions_output.get("actions", [])

    summary = str(final_json.get("summary") or "Não foi possível gerar resumo confiável com o modelo.")
    ats_risk = str(final_json.get("ats_risk") or "medio").lower()
    if ats_risk not in {"baixo", "medio", "alto"}:
        ats_risk = "medio"

    def _to_list(value: Any, fallback: list[str]) -> list[str]:
        if isinstance(value, list):
            out = [str(v).strip() for v in value if str(v).strip()]
            return out[:6] if out else fallback
        return fallback

    strengths = _to_list(final_json.get("strengths"), ["Currículo possui base aproveitável."])
    weaknesses = _to_list(final_json.get("weaknesses"), ["Há oportunidades de melhoria em aderência à vaga."])
    next_actions = _to_list(final_json.get("next_actions"), fallback_actions or ["Revisar currículo com foco em ATS."])

    rewrites = final_json.get("section_rewrites")
    if not isinstance(rewrites, dict):
        rewrites = {}

    return {
        "summary": summary,
        "ats_risk": ats_risk,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "section_rewrites": {
            "estrutura": str(rewrites.get("estrutura") or "Aprimorar resumo profissional com objetivo e palavras-chave."),
            "experiencia": str(rewrites.get("experiencia") or "Reescrever experiências com verbos de ação e resultados mensuráveis."),
            "habilidades": str(rewrites.get("habilidades") or "Priorizar habilidades aderentes à vaga e remover redundâncias."),
        },
        "next_actions": next_actions,
    }


def run_resume_agent(
    *,
    candidate_name: str,
    area: str,
    resume_skills: list[str],
    section_metrics: dict[str, list[tuple]],
    job_title: str,
    job_description: str,
    config: OllamaConfig,
) -> dict[str, Any]:
    system_prompt = _read_prompt("system_prompt.txt")
    tool_selection_prompt = _read_prompt("tool_selection_prompt.txt")
    final_response_prompt = _read_prompt("final_response_prompt.txt")

    safe_context = {
        "candidate_name": _sanitize_text(candidate_name, 120),
        "area": _sanitize_text(area, 120),
        "resume_skills": _sanitize_skills(resume_skills),
        "section_metrics": section_metrics,
        "job_title": _sanitize_text(job_title, 180),
        "job_description": _sanitize_text(job_description, MAX_TEXT_CHARS),
    }

    planning_messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Tools disponíveis:\n{_tool_descriptions()}\n\n"
                f"Contexto:\n{json.dumps(safe_context, ensure_ascii=False)}\n\n"
                f"{tool_selection_prompt}"
            ),
        },
    ]

    planning_raw = _ollama_chat(config, planning_messages)
    planning_json = _safe_json(planning_raw)
    tool_calls = planning_json.get("tool_calls", []) if isinstance(planning_json, dict) else []

    if not isinstance(tool_calls, list):
        tool_calls = []

    tool_results = _execute_tool_calls(tool_calls)
    tool_results = _ensure_required_tool_results(
        tool_results,
        job_description=safe_context["job_description"],
        resume_skills=safe_context["resume_skills"],
        section_metrics=safe_context["section_metrics"],
    )

    final_messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Contexto base:\n{json.dumps(safe_context, ensure_ascii=False)}\n\n"
                f"Resultados de tools:\n{json.dumps(tool_results, ensure_ascii=False)}\n\n"
                f"{final_response_prompt}"
            ),
        },
    ]

    final_raw = _ollama_chat(config, final_messages)
    final_json = _safe_json(final_raw)
    final_json = _normalize_final_output(final_json, tool_results)

    return {
        "model": config.model,
        "parameters": {
            "temperature": config.temperature,
            "top_p": config.top_p,
            "num_predict": config.num_predict,
        },
        "planning": planning_json,
        "tool_results": tool_results,
        "final": final_json,
    }
