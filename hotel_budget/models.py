from typing import Optional

from database import get_connection


def listar_movimentacoes(tipo: str, mes: Optional[str] = None):
    tabela = "receitas" if tipo == "receita" else "despesas"
    conn = get_connection()
    try:
        sql = f"SELECT * FROM {tabela}"
        params: list = []
        if mes:
            sql += " WHERE substr(data, 1, 7) = ?"
            params.append(mes)
        sql += " ORDER BY data DESC, id DESC"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def adicionar_movimentacao(tipo: str, data: str, categoria: str, descricao: str, valor: float) -> int:
    tabela = "receitas" if tipo == "receita" else "despesas"
    conn = get_connection()
    try:
        cur = conn.execute(
            f"INSERT INTO {tabela} (data, categoria, descricao, valor) VALUES (?, ?, ?, ?)",
            (data, categoria, descricao, valor),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def excluir_movimentacao(tipo: str, mov_id: int) -> bool:
    tabela = "receitas" if tipo == "receita" else "despesas"
    conn = get_connection()
    try:
        cur = conn.execute(f"DELETE FROM {tabela} WHERE id = ?", (mov_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_movimentacao(tipo: str, mov_id: int):
    tabela = "receitas" if tipo == "receita" else "despesas"
    conn = get_connection()
    try:
        return conn.execute(f"SELECT * FROM {tabela} WHERE id = ?", (mov_id,)).fetchone()
    finally:
        conn.close()


def listar_orcamento(mes: Optional[str] = None):
    conn = get_connection()
    try:
        sql = "SELECT * FROM orcamento"
        params: list = []
        if mes:
            sql += " WHERE mes = ?"
            params.append(mes)
        sql += " ORDER BY tipo, categoria"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def upsert_orcamento(mes: str, tipo: str, categoria: str, valor_planejado: float) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO orcamento (mes, tipo, categoria, valor_planejado)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(mes, tipo, categoria)
            DO UPDATE SET valor_planejado = excluded.valor_planejado
            """,
            (mes, tipo, categoria, valor_planejado),
        )
        conn.commit()
    finally:
        conn.close()


def excluir_orcamento(mes: str, tipo: str, categoria: str) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM orcamento WHERE mes = ? AND tipo = ? AND categoria = ?",
            (mes, tipo, categoria),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
