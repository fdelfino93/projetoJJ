import csv
import io
from typing import Optional

import budget
import models
from config import mes_nome


def _linhas_csv(tipo: str, mes: Optional[str]) -> list[dict]:
    linhas = []
    for r in models.listar_movimentacoes(tipo, mes):
        linhas.append(
            {
                "id": r["id"],
                "data": r["data"],
                "categoria": r["categoria"],
                "descricao": r["descricao"],
                "valor": r["valor"],
            }
        )
    return linhas


def gerar_csv_movimentacoes(tipo: str, mes: Optional[str] = None) -> io.StringIO:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "data", "categoria", "descricao", "valor"])
    for linha in _linhas_csv(tipo, mes):
        writer.writerow(
            [linha["id"], linha["data"], linha["categoria"], linha["descricao"], f"{linha['valor']:.2f}"]
        )
    return buf


def gerar_csv_orcamento(mes: Optional[str] = None) -> io.StringIO:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["mes", "tipo", "categoria", "valor_planejado"])
    for r in models.listar_orcamento(mes):
        writer.writerow([r["mes"], r["tipo"], r["categoria"], f"{r['valor_planejado']:.2f}"])
    return buf


def relatorio_mensal(mes: str) -> dict:
    resumo = budget.resumo_mes(mes)
    return {
        "mes": mes,
        "mes_nome": mes_nome(mes),
        "resumo": resumo,
        "receitas": budget.comparativo_categorias("receita", mes),
        "despesas": budget.comparativo_categorias("despesa", mes),
        "lista_receitas": models.listar_movimentacoes("receita", mes),
        "lista_despesas": models.listar_movimentacoes("despesa", mes),
    }
