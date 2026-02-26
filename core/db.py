import json
import os
import sqlite3
from datetime import datetime

from core.constants import DB_PATH, STATUS_CONCLUIDA, STATUS_EM_ANALISE, STATUS_REVISAO


def _get_db_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base_dir, DB_PATH)


def get_conn():
    return sqlite3.connect(_get_db_path())


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidato TEXT NOT NULL,
            area TEXT NOT NULL,
            status TEXT NOT NULL,
            score INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            parsed_json TEXT,
            metrics_json TEXT,
            ai_sections_json TEXT,
            ai_comparison_json TEXT,
            ai_report_json TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS comparacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analise_id INTEGER NOT NULL,
            vaga_titulo TEXT NOT NULL,
            vaga_descricao TEXT NOT NULL,
            compat INTEGER NOT NULL,
            semantic_fit INTEGER NOT NULL,
            presentes TEXT NOT NULL,
            ausentes TEXT NOT NULL,
            lacunas TEXT NOT NULL,
            recomendacoes TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    # Migração leve para bases já existentes sem as colunas novas.
    cur.execute("PRAGMA table_info(analises)")
    cols = {row[1] for row in cur.fetchall()}
    if "parsed_json" not in cols:
        cur.execute("ALTER TABLE analises ADD COLUMN parsed_json TEXT")
    if "metrics_json" not in cols:
        cur.execute("ALTER TABLE analises ADD COLUMN metrics_json TEXT")
    if "ai_sections_json" not in cols:
        cur.execute("ALTER TABLE analises ADD COLUMN ai_sections_json TEXT")
    if "ai_comparison_json" not in cols:
        cur.execute("ALTER TABLE analises ADD COLUMN ai_comparison_json TEXT")
    if "ai_report_json" not in cols:
        cur.execute("ALTER TABLE analises ADD COLUMN ai_report_json TEXT")
    conn.commit()
    conn.close()


def insert_analise(
    candidato: str,
    area: str,
    status: str,
    score: int,
    parsed_data: dict | None = None,
    metrics_data: dict | None = None,
) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO analises (candidato, area, status, score, created_at, parsed_json, metrics_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            candidato,
            area,
            status,
            score,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            json.dumps(parsed_data, ensure_ascii=False) if parsed_data else None,
            json.dumps(metrics_data, ensure_ascii=False) if metrics_data else None,
        ),
    )
    analise_id = cur.lastrowid
    conn.commit()
    conn.close()
    return analise_id


def update_analise(analise_id: int, status: str, score: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE analises SET status = ?, score = ? WHERE id = ?", (status, score, analise_id))
    conn.commit()
    conn.close()


def update_analise_artifacts(
    analise_id: int,
    parsed_data: dict,
    metrics_data: dict,
    candidato: str | None = None,
    area: str | None = None,
    score: int | None = None,
):
    conn = get_conn()
    cur = conn.cursor()
    if candidato is not None and area is not None and score is not None:
        cur.execute(
            """
            UPDATE analises
            SET candidato = ?, area = ?, score = ?, parsed_json = ?, metrics_json = ?
            WHERE id = ?
            """,
            (
                candidato,
                area,
                score,
                json.dumps(parsed_data, ensure_ascii=False),
                json.dumps(metrics_data, ensure_ascii=False),
                analise_id,
            ),
        )
    else:
        cur.execute(
            """
            UPDATE analises
            SET parsed_json = ?, metrics_json = ?
            WHERE id = ?
            """,
            (
                json.dumps(parsed_data, ensure_ascii=False),
                json.dumps(metrics_data, ensure_ascii=False),
                analise_id,
            ),
        )
    conn.commit()
    conn.close()


def delete_analise(analise_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM comparacoes WHERE analise_id = ?", (analise_id,))
    cur.execute("DELETE FROM analises WHERE id = ?", (analise_id,))
    conn.commit()
    conn.close()


def fetch_analises():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, candidato, area, status, score, created_at FROM analises ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_analise_by_id(analise_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, candidato, area, status, score, created_at FROM analises WHERE id = ?",
        (analise_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def fetch_analise_artifacts(analise_id: int) -> tuple[dict, dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT parsed_json, metrics_json FROM analises WHERE id = ?", (analise_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {}, {}

    parsed_data = {}
    metrics_data = {}
    try:
        parsed_data = json.loads(row[0]) if row[0] else {}
    except Exception:
        parsed_data = {}
    try:
        metrics_data = json.loads(row[1]) if row[1] else {}
    except Exception:
        metrics_data = {}
    return parsed_data, metrics_data


def fetch_analise_ai_sections(analise_id: int) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT ai_sections_json FROM analises WHERE id = ?", (analise_id,))
    row = cur.fetchone()
    conn.close()
    if not row or not row[0]:
        return {}
    try:
        data = json.loads(row[0])
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def update_analise_ai_section(
    analise_id: int,
    section_key: str,
    llm_result: dict,
    job_description: str,
):
    current = fetch_analise_ai_sections(analise_id)
    current[section_key] = {
        "job_description": job_description,
        "result": llm_result,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE analises SET ai_sections_json = ? WHERE id = ?",
        (json.dumps(current, ensure_ascii=False), analise_id),
    )
    conn.commit()
    conn.close()


def fetch_analise_ai_payload(analise_id: int, payload_type: str) -> dict:
    col_map = {
        "comparison": "ai_comparison_json",
        "report": "ai_report_json",
    }
    col = col_map.get(payload_type)
    if not col:
        return {}

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT {col} FROM analises WHERE id = ?", (analise_id,))
    row = cur.fetchone()
    conn.close()
    if not row or not row[0]:
        return {}
    try:
        data = json.loads(row[0])
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def update_analise_ai_payload(analise_id: int, payload_type: str, payload: dict):
    col_map = {
        "comparison": "ai_comparison_json",
        "report": "ai_report_json",
    }
    col = col_map.get(payload_type)
    if not col:
        return

    to_save = dict(payload or {})
    to_save["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE analises SET {col} = ? WHERE id = ?",
        (json.dumps(to_save, ensure_ascii=False), analise_id),
    )
    conn.commit()
    conn.close()


def insert_comparacao(
    analise_id: int,
    vaga_titulo: str,
    vaga_descricao: str,
    compat: int,
    semantic_fit: int,
    presentes: list[str],
    ausentes: list[str],
    lacunas: list[str],
    recomendacoes: list[str],
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO comparacoes
        (analise_id, vaga_titulo, vaga_descricao, compat, semantic_fit, presentes, ausentes, lacunas, recomendacoes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            analise_id,
            vaga_titulo,
            vaga_descricao,
            compat,
            semantic_fit,
            json.dumps(presentes, ensure_ascii=False),
            json.dumps(ausentes, ensure_ascii=False),
            json.dumps(lacunas, ensure_ascii=False),
            json.dumps(recomendacoes, ensure_ascii=False),
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ),
    )
    conn.commit()
    conn.close()


def fetch_comparacoes_by_analise(analise_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, vaga_titulo, compat, semantic_fit, created_at
        FROM comparacoes
        WHERE analise_id = ?
        ORDER BY id DESC
        """,
        (analise_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def load_json_field(raw: str) -> list[str]:
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def fetch_comparacao_by_id(comparacao_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, analise_id, vaga_titulo, vaga_descricao, compat, semantic_fit, presentes, ausentes, lacunas, recomendacoes, created_at
        FROM comparacoes
        WHERE id = ?
        """,
        (comparacao_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def seed_if_empty():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM app_meta WHERE key = 'demo_seed_done'")
    meta = cur.fetchone()
    conn.close()
    if meta and meta[0] == "1":
        return

    if fetch_analises():
        return
    samples = [
        ("Camila Ribeiro", "Marketing", STATUS_CONCLUIDA, 82),
        ("Joao Alves", "Dados", STATUS_EM_ANALISE, 67),
        ("Fernanda Lima", "Vendas", STATUS_REVISAO, 59),
        ("Lucas Martins", "Dados", STATUS_CONCLUIDA, 88),
        ("Patricia Souza", "Marketing", STATUS_EM_ANALISE, 73),
        ("Rafael Nunes", "Vendas", STATUS_CONCLUIDA, 79),
        ("Bruna Castro", "Dados", STATUS_REVISAO, 61),
        ("Thiago Melo", "Vendas", STATUS_EM_ANALISE, 70),
        ("Marina Rocha", "Marketing", STATUS_REVISAO, 64),
        ("Caio Fernandes", "Dados", STATUS_CONCLUIDA, 91),
        ("Aline Costa", "Vendas", STATUS_CONCLUIDA, 84),
        ("Diego Pereira", "Marketing", STATUS_EM_ANALISE, 68),
    ]
    for candidato, area, status, score in samples:
        insert_analise(candidato, area, status, score)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO app_meta (key, value) VALUES ('demo_seed_done', '1')"
    )
    conn.commit()
    conn.close()
