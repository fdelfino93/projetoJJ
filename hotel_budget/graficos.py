"""Visualização de dados.

Dois destinos, duas bibliotecas:
    Plotly     -> gráficos interativos exibidos no Streamlit
    Matplotlib -> imagens estáticas embutidas no PDF e no PowerPoint

Os gráficos de tela recebem o tema em uso (`claro` ou `escuro`) e trocam de
paleta junto com a interface. Os gráficos dos arquivos exportados ficam sempre
no tema claro: documento impresso não acompanha a preferência da tela.

As paletas dos dois temas foram validadas para daltonismo — ver `config.PALETAS`.
"""

import io
from typing import Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import plotly.graph_objects as go

import analise
from config import (
    COR_CRITICO,
    COR_DESPESA,
    COR_GRADE,
    COR_PLANEJADO,
    COR_RECEITA,
    COR_TEXTO,
    COR_TEXTO_SUAVE,
    mes_nome,
    paleta,
)
from utils import moeda

FONTE = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def cor_do_tipo(tipo: str, cores: dict) -> str:
    """Cor categórica da série no tema em uso."""
    return cores["receita"] if tipo == "receita" else cores["despesa"]


def cor_da_situacao(situacao: str, cores: dict) -> str:
    """Cor de status da situação orçamentária."""
    return {
        "ok": cores["ok"],
        "atencao": cores["atencao"],
        "critico": cores["critico"],
        "sem_orcamento": cores["texto_suave"],
    }[situacao]


def _rotulo(tipo: str) -> str:
    return "Receitas" if tipo == "receita" else "Despesas"


# --------------------------------------------------------- Plotly (interface)


def _layout(fig: go.Figure, cores: dict, titulo: str = "", altura: int = 360,
            legenda: bool = True) -> go.Figure:
    """Aplica o padrão visual comum a todos os gráficos da tela."""
    if titulo:
        fig.update_layout(
            title=dict(text=titulo, font=dict(size=15, color=cores["texto"]), x=0, xanchor="left")
        )
    fig.update_layout(
        height=altura,
        # Padrão brasileiro: vírgula decimal, ponto para milhar.
        separators=",.",
        margin=dict(l=8, r=8, t=44 if titulo else 16, b=8),
        # Fundo transparente: o gráfico herda a superfície do tema do Streamlit.
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONTE, size=12, color=cores["texto_suave"]),
        hoverlabel=dict(
            font=dict(family=FONTE, size=12, color=cores["texto"]),
            bgcolor=cores["superficie"],
            bordercolor=cores["borda"],
        ),
        showlegend=legenda,
        # title_text="" e não None: com None o Plotly desenha a string "undefined".
        legend=dict(
            orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
            title_text="", traceorder="normal", font=dict(color=cores["texto_suave"]),
        ),
        bargap=0.28,
        bargroupgap=0.08,
    )
    # Grade em fio de cabelo e sempre sólida — tracejado sugere projeção.
    # `automargin` é obrigatório: como passamos `theme=None` ao Streamlit, as
    # margens acima valem ao pé da letra e cortariam os rótulos dos eixos.
    fig.update_xaxes(
        showgrid=False, zeroline=False, linecolor=cores["grade"], automargin=True,
        ticks="outside", tickcolor=cores["grade"], tickfont=dict(color=cores["texto_suave"]),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=cores["grade"], gridwidth=1, zeroline=False,
        linecolor="rgba(0,0,0,0)", automargin=True, tickfont=dict(color=cores["texto_suave"]),
    )
    return fig


def _eixo_reais(fig: go.Figure, eixo: str = "y") -> go.Figure:
    """Formata o eixo em reais, sem casas decimais para não poluir."""
    atualizar = fig.update_yaxes if eixo == "y" else fig.update_xaxes
    atualizar(tickprefix="R$ ", tickformat=",.0f", separatethousands=True)
    return fig


def grafico_evolucao_mensal(tema: str = "light") -> Optional[go.Figure]:
    """Linha do tempo de receitas x despesas, com a área do resultado."""
    serie = analise.serie_mensal()
    if serie.empty:
        return None
    cores = paleta(tema)

    rotulos = [mes_nome(m) for m in serie["mes"]]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=rotulos, y=serie["receita"], name="Receitas",
            mode="lines+markers", line=dict(color=cores["receita"], width=2),
            # O anel na cor da superfície separa marcadores sobrepostos.
            marker=dict(size=8, line=dict(width=2, color=cores["superficie"])),
            hovertemplate="<b>%{x}</b><br>Receitas: R$ %{y:,.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=rotulos, y=serie["despesa"], name="Despesas",
            mode="lines+markers", line=dict(color=cores["despesa"], width=2),
            marker=dict(size=8, line=dict(width=2, color=cores["superficie"])),
            # Área entre as curvas: mostra visualmente o resultado do mês.
            fill="tonexty",
            # Bem translúcido: a área situa o resultado sem virar bloco saturado.
            fillcolor="rgba(217,89,38,0.10)" if tema == "dark" else "rgba(235,104,52,0.08)",
            hovertemplate="<b>%{x}</b><br>Despesas: R$ %{y:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(hovermode="x unified")
    return _eixo_reais(_layout(fig, cores, altura=380))


def grafico_saldo_mensal(tema: str = "light") -> Optional[go.Figure]:
    """Resultado de cada mês. Azul para saldo positivo, vermelho para negativo."""
    serie = analise.serie_mensal()
    if serie.empty:
        return None
    cores = paleta(tema)

    barras = [cores["receita"] if v >= 0 else cores["critico"] for v in serie["saldo"]]
    fig = go.Figure(
        go.Bar(
            x=[mes_nome(m) for m in serie["mes"]],
            y=serie["saldo"],
            marker=dict(color=barras, line=dict(width=2, color=cores["superficie"])),
            hovertemplate="<b>%{x}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>",
            showlegend=False,
        )
    )
    fig.add_hline(y=0, line_width=1, line_color=cores["texto_suave"])
    return _eixo_reais(_layout(fig, cores, altura=300, legenda=False))


def grafico_planejado_realizado(tipo: str, mes: Optional[str] = None,
                                tema: str = "light") -> Optional[go.Figure]:
    """Barras horizontais comparando o previsto e o efetivado por categoria."""
    comparativo = analise.comparativo_categorias(tipo, mes)
    comparativo = comparativo[(comparativo["planejado"] > 0) | (comparativo["realizado"] > 0)]
    if comparativo.empty:
        return None
    cores = paleta(tema)

    comparativo = comparativo.sort_values("realizado")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=comparativo["categoria"], x=comparativo["planejado"], name="Planejado",
            orientation="h",
            marker=dict(color=cores["planejado"], line=dict(width=2, color=cores["superficie"])),
            hovertemplate="<b>%{y}</b><br>Planejado: R$ %{x:,.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            y=comparativo["categoria"], x=comparativo["realizado"], name="Realizado",
            orientation="h",
            marker=dict(color=cor_do_tipo(tipo, cores), line=dict(width=2, color=cores["superficie"])),
            hovertemplate="<b>%{y}</b><br>Realizado: R$ %{x:,.2f}<extra></extra>",
        )
    )
    altura = max(300, 46 * len(comparativo) + 90)
    fig = _layout(fig, cores, altura=altura)
    fig.update_yaxes(showgrid=False)
    fig.update_xaxes(showgrid=True, gridcolor=cores["grade"])
    return _eixo_reais(fig, eixo="x")


def grafico_distribuicao(tipo: str, mes: Optional[str] = None,
                         tema: str = "light") -> Optional[go.Figure]:
    """Ranking das categorias por valor realizado, com a participação no total.

    Barras ordenadas em vez de pizza: dez fatias de despesa seriam ilegíveis e
    comparar ângulos próximos é sabidamente pior do que comparar comprimentos.
    """
    comparativo = analise.comparativo_categorias(tipo, mes)
    comparativo = comparativo[comparativo["realizado"] > 0].sort_values("realizado")
    if comparativo.empty:
        return None
    cores = paleta(tema)

    fig = go.Figure(
        go.Bar(
            y=comparativo["categoria"], x=comparativo["realizado"],
            orientation="h",
            marker=dict(color=cor_do_tipo(tipo, cores), line=dict(width=2, color=cores["superficie"])),
            text=[f"{p:.1f}%" for p in comparativo["participacao"]],
            textposition="outside",
            textfont=dict(family=FONTE, size=11, color=cores["texto_suave"]),
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Realizado: R$ %{x:,.2f}<extra></extra>",
            showlegend=False,
        )
    )
    altura = max(280, 40 * len(comparativo) + 70)
    fig = _layout(fig, cores, altura=altura, legenda=False)
    fig.update_yaxes(showgrid=False)
    fig.update_xaxes(
        showgrid=True, gridcolor=cores["grade"],
        range=[0, comparativo["realizado"].max() * 1.18],
    )
    return _eixo_reais(fig, eixo="x")


def grafico_execucao_orcamentaria(tipo: str, mes: str, tema: str = "light") -> Optional[go.Figure]:
    """Percentual executado por categoria, colorido pela situação orçamentária.

    Aqui a cor é status (dentro/fora do orçamento), não identidade de série —
    por isso vem da paleta de status e acompanha o percentual escrito na barra.
    """
    comparativo = analise.comparativo_categorias(tipo, mes)
    comparativo = comparativo[comparativo["planejado"] > 0].sort_values("execucao")
    if comparativo.empty:
        return None
    cores = paleta(tema)

    fig = go.Figure(
        go.Bar(
            y=comparativo["categoria"], x=comparativo["execucao"], orientation="h",
            marker=dict(
                color=[cor_da_situacao(s, cores) for s in comparativo["situacao"]],
                line=dict(width=2, color=cores["superficie"]),
            ),
            text=[f"{e:.0f}%" for e in comparativo["execucao"]],
            textposition="outside",
            textfont=dict(family=FONTE, size=11, color=cores["texto_suave"]),
            cliponaxis=False,
            customdata=comparativo[["planejado", "realizado"]].values,
            hovertemplate=(
                "<b>%{y}</b><br>Planejado: R$ %{customdata[0]:,.2f}"
                "<br>Realizado: R$ %{customdata[1]:,.2f}"
                "<br>Execução: %{x:.1f}%<extra></extra>"
            ),
            showlegend=False,
        )
    )
    fig.add_vline(x=100, line_width=1, line_color=cores["texto_suave"])
    altura = max(280, 40 * len(comparativo) + 70)
    fig = _layout(fig, cores, altura=altura, legenda=False)
    fig.update_yaxes(showgrid=False)
    fig.update_xaxes(
        showgrid=True, gridcolor=cores["grade"], ticksuffix="%",
        range=[0, max(comparativo["execucao"].max() * 1.18, 110)],
    )
    return fig


def grafico_evolucao_categoria(tipo: str, categoria: str, tema: str = "light") -> Optional[go.Figure]:
    """Histórico mensal de uma categoria escolhida pelo usuário."""
    serie = analise.evolucao_categoria(tipo, categoria)
    if serie.empty:
        return None
    cores = paleta(tema)
    fig = go.Figure(
        go.Scatter(
            x=[mes_nome(m) for m in serie["mes"]], y=serie["valor"],
            mode="lines+markers", name=categoria,
            line=dict(color=cor_do_tipo(tipo, cores), width=2),
            marker=dict(size=8, line=dict(width=2, color=cores["superficie"])),
            hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>",
        )
    )
    return _eixo_reais(_layout(fig, cores, titulo=categoria, altura=320, legenda=False))


# ------------------------------------------------- Matplotlib (PDF e PowerPoint)

plt.rcParams["font.family"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def _png(fig) -> bytes:
    """Serializa e fecha a figura — sem o close a memória do processo cresce."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150, facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def _estilo_eixo(ax) -> None:
    """Grade discreta e moldura removida, como nos gráficos da tela."""
    ax.set_facecolor("white")
    ax.grid(axis="x", color=COR_GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right", "left", "bottom"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(colors=COR_TEXTO_SUAVE, labelsize=9, length=0)


def _cor_export(tipo: str) -> str:
    """Cor da série nos arquivos exportados (sempre o tema claro)."""
    return COR_RECEITA if tipo == "receita" else COR_DESPESA


def png_planejado_realizado(tipo: str, mes: Optional[str] = None) -> Optional[bytes]:
    """Versão estática do comparativo, para os arquivos exportados."""
    comparativo = analise.comparativo_categorias(tipo, mes)
    comparativo = comparativo[(comparativo["planejado"] > 0) | (comparativo["realizado"] > 0)]
    if comparativo.empty:
        return None
    comparativo = comparativo.sort_values("realizado")

    posicoes = range(len(comparativo))
    altura_barra = 0.38
    fig, ax = plt.subplots(figsize=(9, max(3.2, 0.52 * len(comparativo) + 1.2)))
    ax.barh([p + altura_barra / 2 for p in posicoes], comparativo["planejado"],
            altura_barra, label="Planejado", color=COR_PLANEJADO)
    ax.barh([p - altura_barra / 2 for p in posicoes], comparativo["realizado"],
            altura_barra, label="Realizado", color=_cor_export(tipo))
    ax.set_yticks(list(posicoes))
    ax.set_yticklabels(comparativo["categoria"])
    ax.set_title(f"{_rotulo(tipo)} — Planejado x Realizado", color=COR_TEXTO, fontsize=12, loc="left")
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    ax.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "."))
    )
    _estilo_eixo(ax)
    fig.tight_layout()
    return _png(fig)


def png_evolucao_mensal() -> Optional[bytes]:
    """Versão estática da evolução mensal."""
    serie = analise.serie_mensal()
    if serie.empty:
        return None
    fig, ax = plt.subplots(figsize=(9, 4))
    x = range(len(serie))
    ax.plot(x, serie["receita"], marker="o", markersize=5, linewidth=2,
            label="Receitas", color=COR_RECEITA)
    ax.plot(x, serie["despesa"], marker="o", markersize=5, linewidth=2,
            label="Despesas", color=COR_DESPESA)
    ax.fill_between(x, serie["receita"], serie["despesa"], alpha=0.10, color=COR_DESPESA)
    ax.set_xticks(list(x))
    ax.set_xticklabels([mes_nome(m) for m in serie["mes"]], rotation=30, ha="right")
    ax.set_title("Evolução Mensal — Receitas x Despesas", color=COR_TEXTO, fontsize=12, loc="left")
    ax.legend(frameon=False, fontsize=9)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "."))
    )
    _estilo_eixo(ax)
    ax.grid(axis="y", color=COR_GRADE, linewidth=0.8)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    return _png(fig)


def png_distribuicao(tipo: str, mes: Optional[str] = None) -> Optional[bytes]:
    """Versão estática do ranking de categorias."""
    comparativo = analise.comparativo_categorias(tipo, mes)
    comparativo = comparativo[comparativo["realizado"] > 0].sort_values("realizado")
    if comparativo.empty:
        return None
    fig, ax = plt.subplots(figsize=(9, max(3.0, 0.46 * len(comparativo) + 1.0)))
    ax.barh(comparativo["categoria"], comparativo["realizado"], color=_cor_export(tipo), height=0.62)
    for y, (valor, parte) in enumerate(zip(comparativo["realizado"], comparativo["participacao"])):
        ax.text(valor, y, f"  {parte:.1f}%", va="center", fontsize=8, color=COR_TEXTO_SUAVE)
    ax.set_xlim(0, comparativo["realizado"].max() * 1.18)
    ax.set_title(
        f"{_rotulo(tipo)} por Categoria — {mes_nome(mes) if mes else 'Período completo'}",
        color=COR_TEXTO, fontsize=12, loc="left",
    )
    ax.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "."))
    )
    _estilo_eixo(ax)
    fig.tight_layout()
    return _png(fig)


def png_resultado_mes(mes: str) -> Optional[bytes]:
    """Cartão visual com receita, despesa e saldo do mês, usado no slide."""
    resumo = analise.resumo_mes(mes)
    valores = [resumo["receita_realizada"], resumo["despesa_realizada"], resumo["saldo_realizado"]]
    if not any(valores):
        return None
    cores = [COR_RECEITA, COR_DESPESA, COR_RECEITA if valores[2] >= 0 else COR_CRITICO]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    barras = ax.bar(["Receitas", "Despesas", "Saldo"], valores, color=cores, width=0.5)
    for barra, valor in zip(barras, valores):
        deslocamento = max(abs(v) for v in valores) * 0.03
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            valor + (deslocamento if valor >= 0 else -deslocamento),
            moeda(valor), ha="center", va="bottom" if valor >= 0 else "top",
            fontsize=9, color=COR_TEXTO,
        )
    ax.axhline(0, color=COR_TEXTO_SUAVE, linewidth=1)
    ax.set_title(f"Resultado de {mes_nome(mes)}", color=COR_TEXTO, fontsize=12, loc="left")
    ax.set_yticks([])
    _estilo_eixo(ax)
    ax.grid(visible=False)
    fig.tight_layout()
    return _png(fig)
