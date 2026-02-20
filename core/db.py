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
            created_at TEXT NOT NULL
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
    conn.commit()
    conn.close()


def insert_analise(candidato: str, area: str, status: str, score: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO analises (candidato, area, status, score, created_at) VALUES (?, ?, ?, ?, ?)",
        (candidato, area, status, score, datetime.now().strftime("%Y-%m-%d %H:%M")),
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


def delete_analise(analise_id: int):
    conn = get_conn()
    cur = conn.cursor()
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
