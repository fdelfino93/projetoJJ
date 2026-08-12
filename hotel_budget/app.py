from datetime import date

import streamlit as st

import budget
import dashboard
import exports
import models
import reports
from config import (
    DESPESA_CATEGORIAS,
    HOTEL_NOME,
    RECEITA_CATEGORIAS,
    SISTEMA_NOME,
    VERSAO,
    mes_nome,
)
from database import init_db
from utils import moeda, validar_data, validar_valor

st.set_page_config(
    page_title=f"{SISTEMA_NOME} — {HOTEL_NOME}",
    page_icon="hotel",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

PAGINAS = ["Dashboard", "Orçamento", "Movimentações", "Relatório Mensal"]
TIPO_NOME = {"receita": "Receitas", "despesa": "Despesas"}


def _mes_options(obrigatorio=False):
    meses = budget.meses_disponiveis()
    if not meses:
        return []
    return meses if obrigatorio else (["Todos os meses"] + meses)


def _mes_para_filtro(valor):
    return None if valor in (None, "", "Todos os meses") else valor


def pagina_dashboard():
    st.title("Dashboard")
    meses = budget.meses_disponiveis()
    opcoes = _mes_options()
    selecao = st.selectbox("Período", opcoes, index=0) if opcoes else None
    mes = _mes_para_filtro(selecao)

    if mes:
        resumo = budget.resumo_mes(mes)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Receitas (realizado)",
            moeda(resumo["receita_realizada"]),
            f"planejado: {moeda(resumo['receita_planejada'])}",
        )
        c2.metric(
            "Despesas (realizado)",
            moeda(resumo["despesa_realizada"]),
            f"planejado: {moeda(resumo['despesa_planejada'])}",
        )
        c3.metric(
            "Saldo realizado",
            moeda(resumo["saldo_realizado"]),
            f"planejado: {moeda(resumo['saldo_planejado'])}",
        )
        c4.metric("Adimplência receitas", f"{resumo['adimplencia_receita']:.1f}%", "sobre o planejado")

    st.subheader("Evolução mensal — Receitas x Despesas")
    fig = dashboard.fig_serie_mensal()
    if fig:
        st.pyplot(fig)
    else:
        st.info("Sem dados para exibir.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Receitas — Planejado x Realizado {f'({mes_nome(mes)})' if mes else ''}")
        fig = dashboard.fig_planejado_x_realizado("receita", mes)
        st.pyplot(fig) if fig else st.info("Sem dados para exibir.")
    with col2:
        st.subheader(f"Despesas — Planejado x Realizado {f'({mes_nome(mes)})' if mes else ''}")
        fig = dashboard.fig_planejado_x_realizado("despesa", mes)
        st.pyplot(fig) if fig else st.info("Sem dados para exibir.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribuição de Receitas")
        fig = dashboard.fig_distribuicao("receita", mes)
        st.pyplot(fig) if fig else st.info("Sem dados para exibir.")
    with col2:
        st.subheader("Distribuição de Despesas")
        fig = dashboard.fig_distribuicao("despesa", mes)
        st.pyplot(fig) if fig else st.info("Sem dados para exibir.")


def _campos_orcamento(mes, tipo, categorias):
    atuais = {o["categoria"]: o["valor_planejado"] for o in models.listar_orcamento(mes) if o["tipo"] == tipo}
    valores = {}
    for cat in categorias:
        valores[cat] = st.number_input(
            cat,
            min_value=0.0,
            step=100.0,
            value=float(atuais.get(cat, 0.0)),
            format="%.2f",
            key=f"{tipo}_{cat}",
        )
    return valores


def pagina_orcamento():
    st.title("Orçamento")
    meses = budget.meses_disponiveis()
    if not meses:
        st.info("Não há meses disponíveis. Cadastre movimentações ou rode o seed.")
        return
    mes = st.selectbox("Mês", meses, index=0, key="orc_mes")

    with st.form("form_orcamento"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Receitas")
            receitas = _campos_orcamento(mes, "receita", RECEITA_CATEGORIAS)
        with col2:
            st.subheader("Despesas")
            despesas = _campos_orcamento(mes, "despesa", DESPESA_CATEGORIAS)
        salvar = st.form_submit_button("Salvar orçamento", type="primary", width="stretch")

    if salvar:
        for cat, valor in receitas.items():
            models.upsert_orcamento(mes, "receita", cat, valor)
        for cat, valor in despesas.items():
            models.upsert_orcamento(mes, "despesa", cat, valor)
        st.success(f"Orçamento de {mes_nome(mes)} salvo com sucesso.")


def _tabela_movimentacoes(tipo, mes):
    movs = models.listar_movimentacoes(tipo, mes)
    if not movs:
        st.info("Nenhum lançamento encontrado.")
        return
    dados = [
        {
            "id": m["id"],
            "data": m["data"],
            "categoria": m["categoria"],
            "descricao": m["descricao"] or "—",
            "valor": m["valor"],
        }
        for m in movs
    ]
    st.dataframe(
        dados,
        width="stretch",
        hide_index=True,
        column_config={
            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
        },
    )
    total = sum(m["valor"] for m in movs)
    st.markdown(f"**Total:** {moeda(total)}")


def _form_nova_movimentacao(tipo):
    categorias = RECEITA_CATEGORIAS if tipo == "receita" else DESPESA_CATEGORIAS
    with st.expander(f"+ Novo lançamento de {TIPO_NOME[tipo].lower()}", expanded=False):
        with st.form(f"form_novo_{tipo}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            data = c1.date_input("Data", value=date.today())
            categoria = c2.selectbox("Categoria", categorias, key=f"cat_{tipo}")
            descricao = st.text_input("Descrição", placeholder="Opcional")
            valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f", key=f"val_{tipo}")
            enviar = st.form_submit_button("Salvar", type="primary")
        if enviar:
            models.adicionar_movimentacao(tipo, data.isoformat(), categoria, descricao.strip(), valor)
            st.success("Lançamento adicionado.")
            st.rerun()


def _excluir_movimentacao(tipo, mes):
    movs = models.listar_movimentacoes(tipo, mes)
    if not movs:
        return
    opcoes = [f"#{m['id']} — {m['data']} — {m['categoria']} — {moeda(m['valor'])}" for m in movs]
    rotulo = st.selectbox("Lançamento para excluir", opcoes, key=f"del_{tipo}_{mes}")
    indice = opcoes.index(rotulo)
    if st.button("Excluir lançamento", type="secondary", key=f"btn_del_{tipo}_{mes}"):
        models.excluir_movimentacao(tipo, movs[indice]["id"])
        st.success("Lançamento excluído.")
        st.rerun()


def pagina_movimentacoes():
    st.title("Movimentações")
    abas = st.tabs(["Receitas", "Despesas"])
    for aba, tipo in zip(abas, ("receita", "despesa")):
        with aba:
            meses = budget.meses_disponiveis()
            opcoes = _mes_options()
            selecao = st.selectbox("Mês", opcoes, index=0, key=f"mes_{tipo}") if opcoes else None
            mes = _mes_para_filtro(selecao)
            c1, c2, c3 = st.columns([2, 2, 3])
            with c3:
                _form_nova_movimentacao(tipo)
            with c1:
                buf = reports.gerar_csv_movimentacoes(tipo, mes)
                st.download_button(
                    "Exportar CSV",
                    data=buf.getvalue(),
                    file_name=f"{tipo}_{mes or 'todos'}.csv",
                    mime="text/csv",
                    key=f"csv_{tipo}_{mes}",
                )
            with c2:
                pdf = exports.gerar_pdf_movimentacoes(tipo, mes)
                st.download_button(
                    "Exportar PDF",
                    data=pdf,
                    file_name=f"{tipo}_{mes or 'todos'}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{tipo}_{mes}",
                )
            _tabela_movimentacoes(tipo, mes)
            _excluir_movimentacao(tipo, mes)


def _tabela_comparativo(titulo, linhas, cor):
    st.subheader(titulo)
    if not linhas:
        st.info("Sem dados.")
        return
    for linha in linhas:
        c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 2, 1, 3])
        c1.markdown(linha["categoria"])
        c2.markdown(moeda(linha["planejado"]))
        c3.markdown(f"**{moeda(linha['realizado'])}**")
        c4.markdown(moeda(linha["variacao"]))
        c5.markdown(f"{linha['percentual']:.1f}%")
        if linha["planejado"]:
            pct = min(linha["percentual"], 100.0) / 100.0
            cor_bar = cor if linha["percentual"] < 100 else "#d32f2f"
            c6.progress(pct)
        else:
            c6.markdown("—")


def pagina_relatorio():
    st.title("Relatório Mensal")
    meses = budget.meses_disponiveis()
    if not meses:
        st.info("Não há meses disponíveis.")
        return
    mes = st.selectbox("Mês", meses, index=0, key="rel_mes")
    relatorio = reports.relatorio_mensal(mes)
    resumo = relatorio["resumo"]

    c1, c2, c3, c4 = st.columns(4)
    c1.download_button(
        "Exportar CSV",
        data=exports.gerar_csv_relatorio(mes),
        file_name=f"relatorio_{mes}.csv",
        mime="text/csv",
        key="csv_rel",
    )
    c2.download_button(
        "Exportar PDF",
        data=exports.gerar_pdf_relatorio(mes),
        file_name=f"relatorio_{mes}.pdf",
        mime="application/pdf",
        key="pdf_rel",
    )
    c3.download_button(
        "Exportar Slide",
        data=exports.gerar_pptx_relatorio(mes),
        file_name=f"relatorio_{mes}.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        key="pptx_rel",
    )

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Receitas",
        moeda(resumo["receita_realizada"]),
        f"planejado: {moeda(resumo['receita_planejada'])} ({resumo['adimplencia_receita']:.1f}%)",
    )
    c2.metric(
        "Despesas",
        moeda(resumo["despesa_realizada"]),
        f"planejado: {moeda(resumo['despesa_planejada'])} ({resumo['adimplencia_despesa']:.1f}%)",
    )
    c3.metric(
        "Saldo realizado",
        moeda(resumo["saldo_realizado"]),
        f"planejado: {moeda(resumo['saldo_planejado'])}",
    )

    _tabela_comparativo("Planejado x Realizado — Receitas", relatorio["receitas"], cor="#2e7d32")
    _tabela_comparativo("Planejado x Realizado — Despesas", relatorio["despesas"], cor="#c62828")


def main():
    with st.sidebar:
        st.title("Hotel Budget Manager")
        st.caption(HOTEL_NOME)
        st.markdown(f"**{SISTEMA_NOME} v{VERSAO}**")
        pagina = st.radio("Navegação", PAGINAS)

    paginas = {
        "Dashboard": pagina_dashboard,
        "Orçamento": pagina_orcamento,
        "Movimentações": pagina_movimentacoes,
        "Relatório Mensal": pagina_relatorio,
    }
    paginas[pagina]()


main()
