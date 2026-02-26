import html
import re

import streamlit as st


def _pick_first(data: dict, keys: list[str], default: str = "") -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default


def _clean_text(text: str) -> str:
    value = (text or "").strip()
    value = value.replace("\n", " ").replace("\r", " ")
    value = re.sub(r"\s+", " ", value)
    value = value.strip("[]{}\"'")
    value = re.sub(r"\s*,\s*", ", ", value)
    return value.strip()


def _normalize_priority(raw: str) -> str:
    value = (raw or "").strip().lower()
    return {
        "high": "alta",
        "medium": "média",
        "low": "baixa",
        "alta": "alta",
        "media": "média",
        "média": "média",
        "baixa": "baixa",
    }.get(value, "média")


def _extract_action_priority_from_text(text: str) -> tuple[str, str]:
    raw = _clean_text(text)
    action_match = re.search(
        r"(acao|ação|action|recomendacao|recomendação|recommendation)\s*[:=]\s*['\"]?([^'\";]+)['\"]?",
        raw,
        flags=re.IGNORECASE,
    )
    prio_match = re.search(
        r"(prioridade|priority)\s*[:=]\s*['\"]?(alta|media|média|baixa|high|medium|low)['\"]?",
        raw,
        flags=re.IGNORECASE,
    )
    action = _clean_text(action_match.group(2)) if action_match else raw
    prioridade = _normalize_priority(prio_match.group(2) if prio_match else "média")
    return action, prioridade


def _strip_json_like_artifacts(text: str) -> str:
    value = _clean_text(text)
    value = re.sub(
        r"(^|\s)(acao|ação|action|prioridade|priority)\s*:\s*",
        " ",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"['\"]", "", value)
    value = re.sub(r"\s+", " ", value).strip(" ;,.")
    return value.strip()


def _clean_action_sentence(text: str) -> str:
    value = _strip_json_like_artifacts(text)
    if "Adicionar palavras-chave faltantes" in value or "Adicionar palavras-chave" in value:
        head, _, tail = value.partition(":")
        if tail:
            tokens = [t.strip() for t in tail.split(",")]
            tokens = [t for t in tokens if len(t) >= 4 and not re.fullmatch(r"[a-z]{1,2}", t.lower())]
            if tokens:
                value = f"{head}: {', '.join(tokens[:8])}"
            else:
                value = "Adicionar palavras-chave da vaga de forma natural no currículo"
    if value and not value.endswith("."):
        value += "."
    return value


def stringify_value(value) -> str:
    if isinstance(value, dict):
        main = _pick_first(
            value,
            ["recomendacao", "recomendação", "acao", "ação", "action", "texto", "sugestao", "sugestão", "summary"],
            default="",
        )
        just = _pick_first(value, ["justificativa", "justification"], default="")
        parts = []
        if main:
            parts.append(_clean_action_sentence(main))
        if just:
            parts.append(f"Justificativa: {_clean_action_sentence(just)}")
        return " ".join(parts).strip()

    if isinstance(value, list):
        items = [item for item in (stringify_value(v).strip() for v in value) if item]
        return " ".join(items)

    return _clean_action_sentence(str(value))


def _normalize_rewrite_items(raw_value, section_key: str):
    items: list[str] = []
    source = raw_value if raw_value is not None else ""

    if isinstance(source, list):
        for item in source:
            text = stringify_value(item) if isinstance(item, (dict, list)) else _clean_action_sentence(str(item))
            if text:
                items.extend([_clean_action_sentence(p) for p in re.split(r"\s*[;|]\s*", text) if p.strip()])
    elif isinstance(source, dict):
        text = stringify_value(source)
        if text:
            items.extend([_clean_action_sentence(p) for p in re.split(r"\s*[;|]\s*", text) if p.strip()])
    else:
        text = _clean_action_sentence(str(source))
        if text:
            items.extend([_clean_action_sentence(p) for p in re.split(r"\s*[;|]\s*", text) if p.strip()])

    items = [i for i in items if i and i.lower() != "n/a."]

    if section_key == "estrutura" and len(items) < 2:
        items.append("Abra com um resumo de 3 linhas alinhado à vaga, destacando objetivo, domínio técnico e diferencial.")
        items.append("Organize as seções por relevância: resumo, experiência, habilidades e formação.")
    elif section_key == "experiencia" and len(items) < 2:
        items.append("Reescreva cada experiência com verbo de ação, contexto, resultado e métrica.")
        items.append("Use bullets no formato: Ação + Ferramenta + Impacto (ex.: aumentei X% em Y meses).")
    elif section_key == "habilidades" and len(items) < 2:
        items.append("Priorize habilidades exigidas na vaga e agrupe em hard skills e soft skills.")
        items.append("Remova itens genéricos e mantenha apenas competências demonstráveis no currículo.")

    return items[:4]


def render_rewrites(rewrites, label_key_pairs):
    for label, key in label_key_pairs:
        items = _normalize_rewrite_items((rewrites or {}).get(key), key)
        if not items:
            items = ["Sem sugestão disponível para esta seção."]

        list_html = "".join(f"<li style='margin-bottom:6px;'>{html.escape(item)}</li>" for item in items)
        st.markdown(
            f"""
            <div style="
                border:1px solid #1e3a5f;
                border-radius:10px;
                background:#0f2744;
                padding:12px;
                margin-bottom:8px;
            ">
                <div style="font-size:12px;color:#93c5fd;margin-bottom:8px;">{html.escape(label)}</div>
                <ul style="margin:0;padding-left:18px;color:#e2e8f0;font-size:14px;line-height:1.55;">
                    {list_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
