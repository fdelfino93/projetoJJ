"""Análise dos dados financeiros com Pandas.

Consome exclusivamente os DataFrames tratados pelo ETL e devolve os números
usados pelo dashboard, pelos gráficos e pelos relatórios exportados.
"""

import calendar
from datetime import date
from functools import lru_cache
from typing import Optional

import pandas as pd

from config import (
    ARQ_ORCAMENTO,
    LIMITE_DESVIO,
    ARQ_DESPESAS,
    ARQ_RECEITAS,
    categorias_de,
)
from etl import carregar_tudo
from utils import percentual


def _assinatura() -> tuple:
    """Impressão digital dos arquivos CSV (caminho, data de alteração, tamanho).

    Serve de chave do cache: qualquer gravação feita pelo `cadastro` muda a
    assinatura e o ETL roda de novo automaticamente.
    """
    marcas = []
    for caminho in (ARQ_RECEITAS, ARQ_DESPESAS, ARQ_ORCAMENTO):
        if caminho.exists():
            info = caminho.stat()
            marcas.append((caminho.name, info.st_mtime_ns, info.st_size))
        else:
            marcas.append((caminho.name, 0, 0))
    return tuple(marcas)


@lru_cache(maxsize=4)
def _etl_cacheado(assinatura: tuple):
    """Executa o ETL uma única vez por versão dos arquivos."""
    return carregar_tudo()


def dados() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Movimentações e orçamento tratados (a partir do cache do ETL)."""
    movimentacoes, orcamento, _ = _etl_cacheado(_assinatura())
    return movimentacoes, orcamento


def meses_disponiveis() -> list[str]:
    """Meses com movimentação ou orçamento, do mais recente para o mais antigo."""
    movimentacoes, orcamento = dados()
    meses = set(movimentacoes["mes"].dropna()) | set(orcamento["mes"].dropna())
    return sorted(meses, reverse=True)


def _filtrar(df: pd.DataFrame, tipo: Optional[str] = None, mes: Optional[str] = None) -> pd.DataFrame:
    """Aplica os filtros de tipo e mês quando informados."""
    if tipo:
        df = df[df["tipo"] == tipo]
    if mes:
        df = df[df["mes"] == mes]
    return df


def total_realizado(tipo: str, mes: Optional[str] = None) -> float:
    """Soma dos lançamentos efetivamente registrados."""
    movimentacoes, _ = dados()
    return float(_filtrar(movimentacoes, tipo, mes)["valor"].sum())


def total_planejado(tipo: str, mes: Optional[str] = None) -> float:
    """Soma do que estava previsto no orçamento."""
    _, orcamento = dados()
    return float(_filtrar(orcamento, tipo, mes)["valor_planejado"].sum())


def comparativo_categorias(tipo: str, mes: Optional[str] = None) -> pd.DataFrame:
    """Planejado x realizado por categoria, com desvio e situação.

    Colunas: categoria, planejado, realizado, variacao, execucao, participacao,
    situacao. Todas as categorias do tipo aparecem, mesmo sem lançamento.
    """
    movimentacoes, orcamento = dados()
    realizado = _filtrar(movimentacoes, tipo, mes).groupby("categoria")["valor"].sum()
    planejado = _filtrar(orcamento, tipo, mes).groupby("categoria")["valor_planejado"].sum()

    linhas = []
    total_real = float(realizado.sum())
    for categoria in categorias_de(tipo):
        r = float(realizado.get(categoria, 0.0))
        p = float(planejado.get(categoria, 0.0))
        execucao = percentual(r, p)
        linhas.append(
            {
                "categoria": categoria,
                "planejado": p,
                "realizado": r,
                "variacao": r - p,
                "execucao": execucao,
                "participacao": percentual(r, total_real),
                "situacao": _situacao(tipo, execucao, p),
            }
        )
    return pd.DataFrame(linhas)


def _situacao(tipo: str, execucao: float, planejado: float) -> str:
    """Classifica a categoria em 'ok', 'atencao' ou 'critico'.

    A leitura é invertida entre receita e despesa: receita abaixo do planejado
    é um problema; despesa abaixo do planejado é economia.
    """
    if not planejado:
        return "sem_orcamento"
    desvio = execucao - 100
    if tipo == "receita":
        desvio = -desvio  # receita a menos vira desvio positivo (ruim)
    if desvio <= 0:
        return "ok"
    return "atencao" if desvio <= LIMITE_DESVIO else "critico"


def resumo_mes(mes: Optional[str] = None) -> dict:
    """Indicadores consolidados do mês (ou de todo o período, se mes=None)."""
    receita_planejada = total_planejado("receita", mes)
    receita_realizada = total_realizado("receita", mes)
    despesa_planejada = total_planejado("despesa", mes)
    despesa_realizada = total_realizado("despesa", mes)
    saldo_realizado = receita_realizada - despesa_realizada
    return {
        "mes": mes,
        "receita_planejada": receita_planejada,
        "receita_realizada": receita_realizada,
        "despesa_planejada": despesa_planejada,
        "despesa_realizada": despesa_realizada,
        "saldo_planejado": receita_planejada - despesa_planejada,
        "saldo_realizado": saldo_realizado,
        "execucao_receita": percentual(receita_realizada, receita_planejada),
        "execucao_despesa": percentual(despesa_realizada, despesa_planejada),
        "margem": percentual(saldo_realizado, receita_realizada),
        "qtd_receitas": len(_filtrar(dados()[0], "receita", mes)),
        "qtd_despesas": len(_filtrar(dados()[0], "despesa", mes)),
    }


def serie_mensal() -> pd.DataFrame:
    """Receitas, despesas e saldo por mês, em ordem cronológica."""
    movimentacoes, _ = dados()
    if movimentacoes.empty:
        return pd.DataFrame(columns=["mes", "receita", "despesa", "saldo"])
    tabela = (
        movimentacoes.pivot_table(index="mes", columns="tipo", values="valor", aggfunc="sum")
        .fillna(0.0)
        .reset_index()
    )
    for coluna in ("receita", "despesa"):
        if coluna not in tabela.columns:
            tabela[coluna] = 0.0
    tabela["saldo"] = tabela["receita"] - tabela["despesa"]
    return tabela.sort_values("mes").reset_index(drop=True)[["mes", "receita", "despesa", "saldo"]]


def evolucao_categoria(tipo: str, categoria: str) -> pd.DataFrame:
    """Histórico mensal de uma única categoria."""
    movimentacoes, _ = dados()
    df = movimentacoes[(movimentacoes["tipo"] == tipo) & (movimentacoes["categoria"] == categoria)]
    if df.empty:
        return pd.DataFrame(columns=["mes", "valor"])
    return df.groupby("mes", as_index=False)["valor"].sum().sort_values("mes")


def ticket_medio(tipo: str, mes: Optional[str] = None) -> float:
    """Valor médio por lançamento."""
    movimentacoes, _ = dados()
    df = _filtrar(movimentacoes, tipo, mes)
    return float(df["valor"].mean()) if len(df) else 0.0


def projecao_fechamento(mes: str) -> dict:
    """Projeta o fechamento do mês pelo ritmo diário observado até aqui.

    Só faz sentido para o mês corrente; para meses passados a projeção
    coincide com o realizado.
    """
    movimentacoes, _ = dados()
    do_mes = movimentacoes[movimentacoes["mes"] == mes]
    ano, num = int(mes[:4]), int(mes[5:7])
    dias_no_mes = calendar.monthrange(ano, num)[1]

    hoje = date.today()
    if (hoje.year, hoje.month) == (ano, num):
        dias_corridos = hoje.day
    elif do_mes.empty:
        dias_corridos = dias_no_mes
    else:
        dias_corridos = int(pd.to_datetime(do_mes["data"]).dt.day.max())
    dias_corridos = max(dias_corridos, 1)

    projecao = {"mes": mes, "dias_corridos": dias_corridos, "dias_no_mes": dias_no_mes}
    for tipo in ("receita", "despesa"):
        realizado = float(do_mes[do_mes["tipo"] == tipo]["valor"].sum())
        projecao[f"{tipo}_realizada"] = realizado
        projecao[f"{tipo}_projetada"] = (realizado / dias_corridos) * dias_no_mes
    projecao["saldo_projetado"] = projecao["receita_projetada"] - projecao["despesa_projetada"]
    return projecao


def alertas(mes: str) -> list[dict]:
    """Categorias fora do limite de desvio, da mais grave para a menos grave."""
    encontrados = []
    for tipo in ("receita", "despesa"):
        comparativo = comparativo_categorias(tipo, mes)
        fora = comparativo[comparativo["situacao"].isin(["atencao", "critico"])]
        for linha in fora.itertuples():
            if tipo == "receita":
                texto = f"Receita de {linha.categoria} {abs(linha.execucao - 100):.1f}% abaixo do planejado"
            else:
                texto = f"Despesa de {linha.categoria} {linha.execucao - 100:.1f}% acima do planejado"
            encontrados.append(
                {
                    "tipo": tipo,
                    "categoria": linha.categoria,
                    "situacao": linha.situacao,
                    "mensagem": texto,
                    "variacao": linha.variacao,
                    "execucao": linha.execucao,
                }
            )
    ordem = {"critico": 0, "atencao": 1}
    return sorted(encontrados, key=lambda a: (ordem[a["situacao"]], -abs(a["variacao"])))


def relatorio_mensal(mes: str) -> dict:
    """Pacote completo usado pela tela de relatório e pelas exportações."""
    movimentacoes, _ = dados()
    return {
        "mes": mes,
        "resumo": resumo_mes(mes),
        "receitas": comparativo_categorias("receita", mes),
        "despesas": comparativo_categorias("despesa", mes),
        "lancamentos": _filtrar(movimentacoes, mes=mes).sort_values("data"),
        "alertas": alertas(mes),
        "projecao": projecao_fechamento(mes),
    }


def qualidade_dados() -> dict:
    """Números da última execução do ETL, exibidos na tela de dados."""
    _, _, relatorio = _etl_cacheado(_assinatura())
    return {
        "lidas": relatorio.lidas,
        "carregadas": relatorio.carregadas,
        "descartadas": relatorio.descartadas,
        "vazias": relatorio.vazias,
        "duplicadas": relatorio.duplicadas,
        "valor_invalido": relatorio.valor_invalido,
        "data_invalida": relatorio.data_invalida,
        "categoria_ajustada": relatorio.categoria_ajustada,
        "categoria_invalida": relatorio.categoria_invalida,
        "detalhes": relatorio.detalhes,
    }
