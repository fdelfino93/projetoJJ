from collections import defaultdict
from typing import Optional

import models
from config import RECEITA_CATEGORIAS, DESPESA_CATEGORIAS


def _total(tabela: str, mes: Optional[str] = None) -> float:
    conn = models.get_connection()
    try:
        sql = f"SELECT COALESCE(SUM(valor), 0) AS total FROM {tabela}"
        params: list = []
        if mes:
            sql += " WHERE substr(data, 1, 7) = ?"
            params.append(mes)
        return conn.execute(sql, params).fetchone()["total"]
    finally:
        conn.close()


def total_realizado(tipo: str, mes: Optional[str] = None) -> float:
    tabela = "receitas" if tipo == "receita" else "despesas"
    return _total(tabela, mes)


def total_planejado(tipo: str, mes: Optional[str] = None) -> float:
    conn = models.get_connection()
    try:
        sql = "SELECT COALESCE(SUM(valor_planejado), 0) AS total FROM orcamento WHERE tipo = ?"
        params: list = [tipo]
        if mes:
            sql += " AND mes = ?"
            params.append(mes)
        return conn.execute(sql, params).fetchone()["total"]
    finally:
        conn.close()


def _realizado_por_categoria(tabela: str, mes: Optional[str]) -> dict:
    conn = models.get_connection()
    try:
        sql = f"SELECT categoria, COALESCE(SUM(valor), 0) AS total FROM {tabela}"
        params: list = []
        if mes:
            sql += " WHERE substr(data, 1, 7) = ?"
            params.append(mes)
        sql += " GROUP BY categoria"
        rows = conn.execute(sql, params).fetchall()
        return {r["categoria"]: r["total"] for r in rows}
    finally:
        conn.close()


def _planejado_por_categoria(tipo: str, mes: Optional[str]) -> dict:
    conn = models.get_connection()
    try:
        sql = "SELECT categoria, valor_planejado FROM orcamento WHERE tipo = ?"
        params: list = [tipo]
        if mes:
            sql += " AND mes = ?"
            params.append(mes)
        rows = conn.execute(sql, params).fetchall()
        return {r["categoria"]: r["valor_planejado"] for r in rows}
    finally:
        conn.close()


def comparativo_categorias(tipo: str, mes: Optional[str] = None) -> list[dict]:
    categorias = RECEITA_CATEGORIAS if tipo == "receita" else DESPESA_CATEGORIAS
    tabela = "receitas" if tipo == "receita" else "despesas"
    realizado = _realizado_por_categoria(tabela, mes)
    planejado = _planejado_por_categoria(tipo, mes)
    comparativo = []
    for cat in categorias:
        r = realizado.get(cat, 0.0)
        p = planejado.get(cat, 0.0)
        variacao = (r - p) if p else r
        pct = ((r / p) * 100) if p else (100.0 if r else 0.0)
        comparativo.append(
            {
                "categoria": cat,
                "planejado": p,
                "realizado": r,
                "variacao": variacao,
                "percentual": pct,
            }
        )
    return comparativo


def resumo_mes(mes: str) -> dict:
    receita_planejada = total_planejado("receita", mes)
    receita_realizada = total_realizado("receita", mes)
    despesa_planejada = total_planejado("despesa", mes)
    despesa_realizada = total_realizado("despesa", mes)
    return {
        "mes": mes,
        "receita_planejada": receita_planejada,
        "receita_realizada": receita_realizada,
        "despesa_planejada": despesa_planejada,
        "despesa_realizada": despesa_realizada,
        "saldo_planejado": receita_planejada - despesa_planejada,
        "saldo_realizado": receita_realizada - despesa_realizada,
        "adimplencia_receita": _pct(receita_realizada, receita_planejada),
        "adimplencia_despesa": _pct(despesa_realizada, despesa_planejada),
    }


def _pct(realizado: float, planejado: float) -> float:
    if not planejado:
        return 0.0
    return (realizado / planejado) * 100


def meses_disponiveis() -> list:
    conn = models.get_connection()
    try:
        sql = """
            SELECT DISTINCT mes FROM orcamento
            UNION
            SELECT DISTINCT substr(data, 1, 7) FROM receitas
            UNION
            SELECT DISTINCT substr(data, 1, 7) FROM despesas
            ORDER BY mes DESC
        """
        return [r["mes"] for r in conn.execute(sql).fetchall()]
    finally:
        conn.close()


def quantidade_movimentacoes(tipo: str, mes: Optional[str] = None) -> int:
    return len(models.listar_movimentacoes(tipo, mes))
