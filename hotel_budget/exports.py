import io
from typing import Optional

import models
import reports
from budget import resumo_mes
from config import HOTEL_NOME, SISTEMA_NOME, VERSAO, mes_nome
from utils import moeda

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:  # pragma: no cover
    pass


_CORES = {
    "verde": colors.HexColor("#2e7d32"),
    "vermelho": colors.HexColor("#c62828"),
    "roxo": colors.HexColor("#6a1b9a"),
    "cinza": colors.HexColor("#eeeeee"),
}


def _estilos_pdf():
    base = getSampleStyleSheet()
    titulo = ParagraphStyle("Titulo", parent=base["Title"], fontSize=18, textColor=_CORES["roxo"])
    subtitulo = ParagraphStyle("Subtitulo", parent=base["Normal"], fontSize=11, textColor=colors.grey, alignment=TA_CENTER)
    cabecario = ParagraphStyle("Cabecario", parent=base["Normal"], fontSize=9, textColor=colors.white)
    celula = ParagraphStyle("Celula", parent=base["Normal"], fontSize=9)
    celula_dir = ParagraphStyle("CelulaDir", parent=celula, alignment=TA_RIGHT)
    return base, titulo, subtitulo, cabecario, celula, celula_dir


def _tabela_pdf(dados, largura_cel: Optional[float] = None) -> Table:
    _, _, _, cabecario, celula, celula_dir = _estilos_pdf()
    linhas = [[Paragraph(str(c), cabecario) for c in cab] for cab in dados[0]]
    for linha in dados[1:]:
        linhas.append([Paragraph(str(c), celula) for c in linha])
    tabela = Table(linhas)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _CORES["roxo"]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _CORES["cinza"]]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tabela


def gerar_pdf_movimentacoes(tipo: str, mes: Optional[str] = None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=f"{SISTEMA_NOME} — {tipo}")
    _, titulo, subtitulo, _, celula, celula_dir = _estilos_pdf()
    titulo_tipo = "Receitas" if tipo == "receita" else "Despesas"
    elementos = [
        Paragraph(titulo_tipo, titulo),
        Paragraph(f"{HOTEL_NOME} — {mes_nome(mes) if mes else 'Todos os meses'}", subtitulo),
        Spacer(1, 6 * mm),
    ]
    movs = models.listar_movimentacoes(tipo, mes)
    dados = [["Data", "Categoria", "Descrição", "Valor"]]
    total = 0.0
    for m in movs:
        dados.append([m["data"], m["categoria"], m["descricao"] or "—", moeda(m["valor"])])
        total += m["valor"]
    if not movs:
        elementos.append(Paragraph("Nenhum lançamento encontrado.", celula))
    else:
        dados.append(["", "", "Total", moeda(total)])
        elementos.append(_tabela_pdf(dados))
    doc.build(elementos)
    return buf.getvalue()


def _tabelas_relatorio_pdf(r: dict):
    receitas = [["Categoria", "Planejado", "Realizado", "Variação", "%"]]
    despesas = [["Categoria", "Planejado", "Realizado", "Variação", "%"]]
    for c in r["receitas"]:
        receitas.append([c["categoria"], moeda(c["planejado"]), moeda(c["realizado"]), moeda(c["variacao"]), f"{c['percentual']:.1f}%"])
    for c in r["despesas"]:
        despesas.append([c["categoria"], moeda(c["planejado"]), moeda(c["realizado"]), moeda(c["variacao"]), f"{c['percentual']:.1f}%"])
    return _tabela_pdf(receitas), _tabela_pdf(despesas)


def gerar_pdf_relatorio(mes: str) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=f"{SISTEMA_NOME} — Relatório Mensal")
    base, titulo, subtitulo, _, celula, celula_dir = _estilos_pdf()
    r = reports.relatorio_mensal(mes)
    resumo = r["resumo"]
    saldo_cor = _CORES["verde"] if resumo["saldo_realizado"] >= 0 else _CORES["vermelho"]

    def linha_resumo(rotulo: str, valor: str, cor=colors.black):
        return Table(
            [[Paragraph(rotulo, celula), Paragraph(valor, ParagraphStyle("v", parent=celula_dir, textColor=cor))]],
            colWidths=[90 * mm, 60 * mm],
        )

    elementos = [
        Paragraph(f"Relatório Mensal — {r['mes_nome']}", titulo),
        Paragraph(f"{HOTEL_NOME} — {SISTEMA_NOME} v{VERSAO}", subtitulo),
        Spacer(1, 6 * mm),
        linha_resumo("Receitas (realizado)", moeda(resumo["receita_realizada"]), _CORES["verde"]),
        Spacer(1, 2 * mm),
        linha_resumo("Despesas (realizado)", moeda(resumo["despesa_realizada"]), _CORES["vermelho"]),
        Spacer(1, 2 * mm),
        linha_resumo("Saldo realizado", moeda(resumo["saldo_realizado"]), saldo_cor),
        Spacer(1, 2 * mm),
        linha_resumo("Adimplência receitas", f"{resumo['adimplencia_receita']:.1f}%"),
        Spacer(1, 2 * mm),
        linha_resumo("Adimplência despesas", f"{resumo['adimplencia_despesa']:.1f}%"),
        Spacer(1, 8 * mm),
        Paragraph("Planejado x Realizado — Receitas", base["Heading2"]),
        Spacer(1, 3 * mm),
    ]
    tab_receitas, tab_despesas = _tabelas_relatorio_pdf(r)
    elementos.append(tab_receitas)
    elementos.append(Spacer(1, 8 * mm))
    elementos.append(Paragraph("Planejado x Realizado — Despesas", base["Heading2"]))
    elementos.append(Spacer(1, 3 * mm))
    elementos.append(tab_despesas)
    doc.build(elementos)
    return buf.getvalue()


def gerar_csv_relatorio(mes: str) -> str:
    r = reports.relatorio_mensal(mes)
    resumo = r["resumo"]
    linhas = [
        "RELATÓRIO MENSAL",
        f"Hotel: {HOTEL_NOME}",
        f"Mês: {r['mes_nome']}",
        "",
        "RESUMO",
        f"Receitas realizadas;{resumo['receita_realizada']:.2f}",
        f"Receitas planejadas;{resumo['receita_planejada']:.2f}",
        f"Despesas realizadas;{resumo['despesa_realizada']:.2f}",
        f"Despesas planejadas;{resumo['despesa_planejada']:.2f}",
        f"Saldo realizado;{resumo['saldo_realizado']:.2f}",
        f"Saldo planejado;{resumo['saldo_planejado']:.2f}",
        f"Adimplência receitas;{resumo['adimplencia_receita']:.2f}%",
        f"Adimplência despesas;{resumo['adimplencia_despesa']:.2f}%",
        "",
        "CATEGORIA;PLANEJADO;REALIZADO;VARIACAO;PERCENTUAL;TIPO",
    ]
    for c in r["receitas"]:
        linhas.append(f"{c['categoria']};{c['planejado']:.2f};{c['realizado']:.2f};{c['variacao']:.2f};{c['percentual']:.2f}%;receita")
    for c in r["despesas"]:
        linhas.append(f"{c['categoria']};{c['planejado']:.2f};{c['realizado']:.2f};{c['variacao']:.2f};{c['percentual']:.2f}%;despesa")
    return "\n".join(linhas)


def _mes_anterior(mes: str) -> str:
    ano, num = mes.split("-")
    num = int(num)
    if num == 1:
        return f"{int(ano) - 1:04d}-12"
    return f"{ano}-{num - 1:02d}"


def _pptx_base():
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def _slide_capa(prs, titulo, subtitulo, rodape=HOTEL_NOME):
    from pptx.util import Inches, Pt

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _texto_caixa(
        slide, 1, 2.0, 11.3, 3.5,
        [(f"{SISTEMA_NOME} v{VERSAO}", 40), (titulo, 30), (subtitulo, 18), (rodape, 14)],
        cor=(0x6A, 0x1B, 0x9A), negrito=True, centralizado=True,
    )
    return slide


def _slide_titulo(prs, titulo):
    from pptx.util import Inches

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _texto_caixa(slide, 0.8, 0.4, 11.7, 0.8, [(titulo, 30)], cor=(0x6A, 0x1B, 0x9A), negrito=True)
    return slide


def _texto_caixa(slide, x, y, w, h, linhas, tam=28, cor=(0, 0, 0), negrito=False, centralizado=False):
    from pptx.util import Inches, Pt

    caixa = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = caixa.text_frame
    tf.word_wrap = True
    for i, (texto, t) in enumerate(linhas):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = texto
        p.font.size = Pt(t)
        p.font.bold = negrito
        p.font.color.rgb = _rgb(cor)
        if centralizado:
            p.alignment = 1
    return caixa


def _rgb(cor):
    from pptx.dml.color import RGBColor

    return RGBColor(*cor)


def _slide_grafico(prs, titulo, fig):
    from pptx.util import Inches

    slide = _slide_titulo(prs, titulo)
    if fig:
        import matplotlib.pyplot as plt

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        plt.close(fig)
        buf.seek(0)
        slide.shapes.add_picture(buf, Inches(1.5), Inches(1.5), width=Inches(10.3))
    return slide


def _slide_resumo(prs, titulo, itens):
    _slide_titulo(prs, titulo)
    _texto_caixa(
        prs.slides[-1], 0.8, 1.4, 11.7, 6,
        [(f"{rotulo}: {valor}", 22) for rotulo, valor in itens],
        cor=(0, 0, 0), negrito=False,
    )


def gerar_pptx_relatorio(mes: str) -> bytes:
    import dashboard

    r = reports.relatorio_mensal(mes)
    resumo = r["resumo"]
    prs = _pptx_base()
    _slide_capa(prs, f"Relatório Mensal — {r['mes_nome']}", HOTEL_NOME)
    _slide_resumo(
        prs,
        "Resumo do mês",
        [
            ("Receitas (realizado)", moeda(resumo["receita_realizada"])),
            ("Despesas (realizado)", moeda(resumo["despesa_realizada"])),
            ("Saldo realizado", moeda(resumo["saldo_realizado"])),
            ("Receitas planejadas", moeda(resumo["receita_planejada"])),
            ("Despesas planejadas", moeda(resumo["despesa_planejada"])),
            ("Adimplência receitas", f"{resumo['adimplencia_receita']:.1f}%"),
            ("Adimplência despesas", f"{resumo['adimplencia_despesa']:.1f}%"),
        ],
    )
    _slide_grafico(prs, "Receitas — Planejado x Realizado", dashboard.fig_planejado_x_realizado("receita", mes))
    _slide_grafico(prs, "Despesas — Planejado x Realizado", dashboard.fig_planejado_x_realizado("despesa", mes))

    slide = _slide_titulo(prs, "Distribuição de Receitas e Despesas")
    fig_rec = dashboard.fig_distribuicao("receita", mes)
    fig_des = dashboard.fig_distribuicao("despesa", mes)
    if fig_rec or fig_des:
        import matplotlib.pyplot as plt
        from pptx.util import Inches

        for i, fig in enumerate((fig_rec, fig_des)):
            if not fig:
                continue
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
            plt.close(fig)
            buf.seek(0)
            slide.shapes.add_picture(buf, Inches(0.6 + i * 6.4), Inches(1.5), width=Inches(6.1))

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


def gerar_pptx_executivo(mes: str) -> bytes:
    import dashboard

    r = reports.relatorio_mensal(mes)
    resumo = r["resumo"]
    prs = _pptx_base()
    _slide_capa(prs, f"Relatório Executivo — {r['mes_nome']}", HOTEL_NOME)
    _slide_grafico(prs, "Evolução Mensal — Receitas x Despesas", dashboard.fig_serie_mensal())
    _slide_resumo(
        prs,
        "Resumo do mês",
        [
            ("Receitas (realizado)", moeda(resumo["receita_realizada"])),
            ("Despesas (realizado)", moeda(resumo["despesa_realizada"])),
            ("Saldo realizado", moeda(resumo["saldo_realizado"])),
            ("Adimplência receitas", f"{resumo['adimplencia_receita']:.1f}%"),
            ("Adimplência despesas", f"{resumo['adimplencia_despesa']:.1f}%"),
        ],
    )
    _slide_grafico(prs, "Receitas — Planejado x Realizado", dashboard.fig_planejado_x_realizado("receita", mes))
    _slide_grafico(prs, "Despesas — Planejado x Realizado", dashboard.fig_planejado_x_realizado("despesa", mes))

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


def gerar_pptx_comparativo(mes: str) -> bytes:
    import dashboard

    anterior = _mes_anterior(mes)
    r = reports.relatorio_mensal(mes)
    resumo = r["resumo"]
    ant = reports.relatorio_mensal(anterior)["resumo"]

    def variacao(atual, passado):
        if not passado:
            return "—"
        pct = ((atual - passado) / passado) * 100
        return f"{pct:+.1f}%"

    prs = _pptx_base()
    _slide_capa(prs, f"Comparativo — {r['mes_nome']} vs {mes_nome(anterior)}", HOTEL_NOME)
    _slide_resumo(
        prs,
        "Comparativo de resultados",
        [
            ("Receitas realizadas", f"{moeda(resumo['receita_realizada'])}  ({variacao(resumo['receita_realizada'], ant['receita_realizada'])})"),
            ("Despesas realizadas", f"{moeda(resumo['despesa_realizada'])}  ({variacao(resumo['despesa_realizada'], ant['despesa_realizada'])})"),
            ("Saldo realizado", f"{moeda(resumo['saldo_realizado'])}  ({variacao(resumo['saldo_realizado'], ant['saldo_realizado'])})"),
            ("Receitas planejadas", moeda(resumo["receita_planejada"])),
            ("Despesas planejadas", moeda(resumo["despesa_planejada"])),
            (f"Adimplência receitas ({mes_nome(anterior)})", f"{resumo['adimplencia_receita']:.1f}%  (ant: {ant['adimplencia_receita']:.1f}%)"),
            (f"Adimplência despesas ({mes_nome(anterior)})", f"{resumo['adimplencia_despesa']:.1f}%  (ant: {ant['adimplencia_despesa']:.1f}%)"),
        ],
    )
    _slide_grafico(prs, f"Receitas — Planejado x Realizado ({r['mes_nome']})", dashboard.fig_planejado_x_realizado("receita", mes))
    _slide_grafico(prs, f"Despesas — Planejado x Realizado ({r['mes_nome']})", dashboard.fig_planejado_x_realizado("despesa", mes))

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
