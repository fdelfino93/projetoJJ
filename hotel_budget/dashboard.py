import base64
import io
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import budget
import models
from config import STATIC_IMG_DIR, mes_nome

plt.rcParams["font.family"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

CORES = {"receita": "#2e7d32", "despesa": "#c62828", "planejado": "#6a1b9a"}


def _img_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def fig_planejado_x_realizado(tipo: str, mes: Optional[str] = None):
    categorias = budget.comparativo_categorias(tipo, mes)
    nomes = [c["categoria"] for c in categorias if c["planejado"] or c["realizado"]]
    planejado = [c["planejado"] for c in categorias if c["planejado"] or c["realizado"]]
    realizado = [c["realizado"] for c in categorias if c["planejado"] or c["realizado"]]
    if not nomes:
        return None
    x = range(len(nomes))
    largura = 0.38
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar([i - largura / 2 for i in x], planejado, largura, label="Planejado", color=CORES["planejado"])
    ax.bar([i + largura / 2 for i in x], realizado, largura, label="Realizado", color=CORES[tipo])
    ax.set_xticks(list(x))
    ax.set_xticklabels(nomes, rotation=30, ha="right")
    ax.set_title(f"{'Receitas' if tipo == 'receita' else 'Despesas'} — Planejado x Realizado")
    ax.legend()
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    fig.tight_layout()
    return fig


def grafico_planejado_x_realizado(tipo: str, mes: Optional[str] = None) -> str:
    fig = fig_planejado_x_realizado(tipo, mes)
    return _img_b64(fig) if fig else ""


def fig_distribuicao(tipo: str, mes: Optional[str] = None):
    categorias = budget.comparativo_categorias(tipo, mes)
    dados = [(c["categoria"], c["realizado"]) for c in categorias if c["realizado"] > 0]
    if not dados:
        return None
    nomes, valores = zip(*dados)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(
        valores,
        labels=nomes,
        autopct="%.1f%%",
        startangle=90,
        colors=plt.cm.Paired.colors[: len(nomes)],
    )
    ax.set_title(f"Distribuição de {'Receitas' if tipo == 'receita' else 'Despesas'} — {mes_nome(mes) if mes else 'Tudo'}")
    fig.tight_layout()
    return fig


def grafico_distribuicao(tipo: str, mes: Optional[str] = None) -> str:
    fig = fig_distribuicao(tipo, mes)
    return _img_b64(fig) if fig else ""


def fig_serie_mensal(ultimos_meses: int = 12):
    conn = models.get_connection()
    try:
        receitas = pd.read_sql_query(
            "SELECT substr(data, 1, 7) AS mes, SUM(valor) AS total FROM receitas GROUP BY mes",
            conn,
        )
        despesas = pd.read_sql_query(
            "SELECT substr(data, 1, 7) AS mes, SUM(valor) AS total FROM despesas GROUP BY mes",
            conn,
        )
    finally:
        conn.close()
    if receitas.empty and despesas.empty:
        return None
    dados = pd.concat(
        [
            receitas.assign(tipo="receita"),
            despesas.assign(tipo="despesa"),
        ]
    )
    dados = dados.sort_values("mes").tail(ultimos_meses)
    piv = dados.pivot(index="mes", columns="tipo", values="total").fillna(0)
    if "receita" not in piv.columns:
        piv["receita"] = 0
    if "despesa" not in piv.columns:
        piv["despesa"] = 0
    fig, ax = plt.subplots(figsize=(11, 6))
    x = range(len(piv))
    ax.plot(x, piv["receita"], marker="o", label="Receitas", color=CORES["receita"])
    ax.plot(x, piv["despesa"], marker="o", label="Despesas", color=CORES["despesa"])
    ax.fill_between(x, piv["receita"], piv["despesa"], alpha=0.15, color="#6a1b9a")
    ax.set_xticks(list(x))
    ax.set_xticklabels([mes_nome(m) for m in piv.index], rotation=30, ha="right")
    ax.set_title("Evolução Mensal — Receitas x Despesas")
    ax.legend()
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    fig.tight_layout()
    return fig


def serie_mensal(ultimos_meses: int = 12) -> str:
    fig = fig_serie_mensal(ultimos_meses)
    return _img_b64(fig) if fig else ""
