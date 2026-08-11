import sqlite3

from config import DATABASE, ensure_dirs

SCHEMA = """
CREATE TABLE IF NOT EXISTS orcamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mes TEXT NOT NULL,
    tipo TEXT NOT NULL,
    categoria TEXT NOT NULL,
    valor_planejado REAL NOT NULL,
    UNIQUE(mes, tipo, categoria)
);

CREATE TABLE IF NOT EXISTS receitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    categoria TEXT NOT NULL,
    descricao TEXT DEFAULT '',
    valor REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS despesas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    categoria TEXT NOT NULL,
    descricao TEXT DEFAULT '',
    valor REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_receitas_data ON receitas(data);
CREATE INDEX IF NOT EXISTS idx_despesas_data ON despesas(data);
CREATE INDEX IF NOT EXISTS idx_orcamento_mes ON orcamento(mes);
"""


def get_connection() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
