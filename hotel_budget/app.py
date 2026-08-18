"""Gerente de Orçamento de Hotel — interface Streamlit.

Ponto de entrada da aplicação. Execute com:

    streamlit run app.py

Esta camada só cuida da tela: toda regra de negócio vive em `cadastro`,
`etl`, `analise`, `graficos` e `exports`.
"""

from datetime import date

import streamlit as st

import analise
import cadastro
import exports
import graficos
from config import (
    HOTEL_NOME,
    LIMITE_DESVIO,
    SISTEMA_NOME,
    VERSAO,
    categorias_de,
    mes_nome,
    paleta,
)
from utils import moeda

st.set_page_config(
    page_title=f"{SISTEMA_NOME} — {HOTEL_NOME}",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

TODOS_OS_MESES = "Todo o período"
ROTULO = {"receita": "Receitas", "despesa": "Despesas"}
NOME_SITUACAO = {
    "ok": "Dentro do previsto",
    "atencao": "Atenção",
    "critico": "Crítico",
    "sem_orcamento": "Sem orçamento",
}


def tema_atual() -> str:
    """Tema escolhido pelo usuário em Menu (⋮) > Settings > Appearance.

    Os gráficos leem daqui para trocar de paleta junto com a interface.
    """
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except (AttributeError, RuntimeError):
        return "light"


def brl(valor) -> str:
    """Valor em reais pronto para markdown.

    O Streamlit interpreta `$` como delimitador de LaTeX, então "R$ 1.000,00"
    sairia renderizado como fórmula. A barra invertida desliga esse parser.
    Dentro de HTML (`unsafe_allow_html`) o escape não é necessário — lá vale
    o `moeda()` puro.
    """
    return moeda(valor).replace("$", r"\$")


# ------------------------------------------------------------------ Auxiliares


def selectbox_mes(rotulo: str, chave: str, meses: list[str], incluir_todos: bool = False) -> str | None:
    """Selectbox de mês sem `format_func`, que no Streamlit 1.61 mostra um
    mês diferente do clicado quando o campo fecha. As opções já são os
    rótulos ("Março/2026"); o valor original ("2026-03") é recuperado pelo
    mapa reverso de `mes_nome`.
    """
    itens = ([TODOS_OS_MESES] + meses) if incluir_todos else meses
    rotulo_para_mes = {mes_nome(m): m for m in itens}
    escolha = st.selectbox(rotulo, list(rotulo_para_mes), key=chave)
    return rotulo_para_mes[escolha]


def seletor_de_mes(chave: str, incluir_todos: bool = True, rotulo: str = "Período"):
    """Selectbox de mês compartilhado pelas páginas. Devolve None para 'todos'."""
    meses = analise.meses_disponiveis()
    if not meses:
        return None
    escolha = selectbox_mes(rotulo, chave, meses, incluir_todos)
    return None if escolha == TODOS_OS_MESES else escolha


def grafico(fig, vazio: str = "Sem dados para o período selecionado.") -> None:
    """Exibe um gráfico Plotly ou uma mensagem quando não há dados.

    `theme=None` impede o Streamlit de sobrepor o próprio tema ao nosso — as
    cores já vêm da paleta validada correspondente ao tema em uso.
    """
    if fig is None:
        st.info(vazio)
    else:
        st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


def indicador(coluna, rotulo: str, valor: str, apoio: str = "", cor: str = "") -> None:
    """Cartão de indicador com valor grande e uma linha de apoio."""
    with coluna:
        st.caption(rotulo)
        estilo = f"color:{cor};" if cor else ""
        # Dentro do HTML o cifrão não dispara o parser de LaTeX, então vai cru.
        st.markdown(
            f"<div style='{estilo}font-size:1.75rem;font-weight:600;line-height:1.2'>{valor}</div>",
            unsafe_allow_html=True,
        )
        if apoio:
            st.caption(apoio.replace("$", r"\$"))


def tabela_comparativa(df) -> None:
    """Tabela planejado x realizado com barra de execução e situação."""
    if df.empty:
        st.info("Sem dados.")
        return
    visao = df.copy()
    visao["situacao"] = visao["situacao"].map(NOME_SITUACAO)
    st.dataframe(
        visao[["categoria", "planejado", "realizado", "variacao", "execucao", "participacao", "situacao"]],
        width="stretch",
        hide_index=True,
        column_config={
            "categoria": st.column_config.TextColumn("Categoria"),
            "planejado": st.column_config.NumberColumn("Planejado (R$)", format="localized"),
            "realizado": st.column_config.NumberColumn("Realizado (R$)", format="localized"),
            "variacao": st.column_config.NumberColumn("Variação (R$)", format="localized"),
            "execucao": st.column_config.ProgressColumn(
                "Execução", format="%.0f%%", min_value=0,
                max_value=float(max(visao["execucao"].max(), 100)),
            ),
            "participacao": st.column_config.NumberColumn("Part. %", format="%.1f%%"),
            "situacao": st.column_config.TextColumn("Situação"),
        },
    )


def mostrar_alertas(mes: str, limite: int = 6) -> None:
    """Lista as categorias fora do limite de desvio orçamentário."""
    cores = paleta(tema_atual())
    encontrados = analise.alertas(mes)
    if not encontrados:
        st.success(f"Nenhuma categoria com desvio acima de {LIMITE_DESVIO:.0f}% em {mes_nome(mes)}.")
        return
    criticos = sum(1 for a in encontrados if a["situacao"] == "critico")
    st.markdown(f"**{len(encontrados)} categorias fora do previsto** — {criticos} em situação crítica.")
    for alerta in encontrados[:limite]:
        cor = graficos.cor_da_situacao(alerta["situacao"], cores)
        st.markdown(
            f"<div style='border-left:3px solid {cor};padding:.35rem .7rem;margin-bottom:.35rem'>"
            f"{alerta['mensagem']}<br>"
            f"<span style='color:{cores['texto_suave']};font-size:.85rem'>"
            f"diferença de {moeda(abs(alerta['variacao']))}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    if len(encontrados) > limite:
        st.caption(f"e mais {len(encontrados) - limite} categoria(s).")


def botao_exportar(rotulo: str, chave: str, gerador, nome_arquivo: str, mime: str) -> None:
    """Exportação em duas etapas: gera sob demanda, depois oferece o download.

    Evita que o arquivo seja remontado a cada interação da página — o
    `st.download_button` exige os bytes prontos no momento em que é desenhado.
    """
    pronto = st.session_state.get(chave)
    if pronto and pronto.get("arquivo") == nome_arquivo:
        st.download_button(
            f"⬇ Baixar {rotulo}", data=pronto["dados"], file_name=nome_arquivo,
            mime=mime, key=f"dl_{chave}", width="stretch",
        )
        return
    if st.button(f"Gerar {rotulo}", key=f"gen_{chave}", width="stretch"):
        with st.spinner(f"Gerando {rotulo}..."):
            st.session_state[chave] = {"arquivo": nome_arquivo, "dados": gerador()}
        st.rerun()


# --------------------------------------------------------------------- Páginas


def pagina_dashboard() -> None:
    """Visão geral: indicadores, evolução, comparativos e alertas."""
    tema = tema_atual()
    cores = paleta(tema)
    st.title("Painel")
    mes = seletor_de_mes("dash_mes")
    resumo = analise.resumo_mes(mes)

    c1, c2, c3, c4 = st.columns(4)
    indicador(
        c1, "Receitas", moeda(resumo["receita_realizada"]),
        f"{resumo['execucao_receita']:.1f}% de {moeda(resumo['receita_planejada'])} previstos",
        cores["receita"],
    )
    indicador(
        c2, "Despesas", moeda(resumo["despesa_realizada"]),
        f"{resumo['execucao_despesa']:.1f}% de {moeda(resumo['despesa_planejada'])} previstos",
        cores["despesa"],
    )
    indicador(
        c3, "Saldo", moeda(resumo["saldo_realizado"]),
        f"previsto: {moeda(resumo['saldo_planejado'])}",
        cores["ok"] if resumo["saldo_realizado"] >= 0 else cores["critico"],
    )
    indicador(
        c4, "Margem", f"{resumo['margem']:.1f}%",
        f"{resumo['qtd_receitas'] + resumo['qtd_despesas']} lançamentos",
    )

    st.divider()

    st.subheader("Evolução mensal")
    grafico(graficos.grafico_evolucao_mensal(tema))

    st.subheader("Resultado por mês")
    grafico(graficos.grafico_saldo_mensal(tema))

    st.divider()
    periodo = f" — {mes_nome(mes)}" if mes else ""
    esquerda, direita = st.columns(2)
    with esquerda:
        st.subheader(f"Receitas por categoria{periodo}")
        grafico(graficos.grafico_distribuicao("receita", mes, tema))
    with direita:
        st.subheader(f"Despesas por categoria{periodo}")
        grafico(graficos.grafico_distribuicao("despesa", mes, tema))

    esquerda, direita = st.columns(2)
    with esquerda:
        st.subheader("Receitas — Planejado x Realizado")
        grafico(graficos.grafico_planejado_realizado("receita", mes, tema))
    with direita:
        st.subheader("Despesas — Planejado x Realizado")
        grafico(graficos.grafico_planejado_realizado("despesa", mes, tema))

    if mes:
        st.divider()
        st.subheader("Pontos de atenção")
        mostrar_alertas(mes)


def pagina_movimentacoes() -> None:
    """Cadastro, edição, exclusão e exportação dos lançamentos."""
    st.title("Movimentações")
    abas = st.tabs([ROTULO["receita"], ROTULO["despesa"]])
    for aba, tipo in zip(abas, ("receita", "despesa")):
        with aba:
            _aba_movimentacoes(tipo)


def _aba_movimentacoes(tipo: str) -> None:
    """Conteúdo de uma aba de movimentações."""
    with st.expander("Importar CSV"):
        _uploader_csv(tipo)

    filtro, _ = st.columns([1, 2])
    with filtro:
        mes = seletor_de_mes(f"mov_mes_{tipo}", rotulo="Período")

    df = cadastro.listar_movimentacoes(tipo, mes)
    _editor_lancamentos(tipo, mes, df)

    if df.empty:
        return

    total = float(df["valor"].sum())
    resumo, medio, exportar = st.columns([2, 2, 1])
    resumo.markdown(f"**Total do período:** {brl(total)}  ·  {len(df)} lançamentos")
    medio.markdown(f"**Ticket médio:** {brl(total / len(df))}")
    with exportar:
        sufixo = mes or "todos"
        botao_exportar(
            "PDF", f"exp_pdf_{tipo}_{sufixo}",
            lambda: exports.gerar_pdf_movimentacoes(tipo, mes),
            f"{tipo}s_{sufixo}.pdf", "application/pdf",
        )


def _uploader_csv(tipo: str) -> None:
    """Área de upload de CSV com pré-visualização e confirmação."""
    import pandas as pd
    from config import categorias_de

    st.caption(
        f"Envie um CSV com as colunas: **data, categoria, descricao, valor** "
        f"(coluna `id` é gerada automaticamente)."
    )
    arquivo = st.file_uploader(
        f"Arquivo CSV de {ROTULO[tipo]}",
        type=["csv"],
        key=f"upload_{tipo}",
        label_visibility="collapsed",
    )
    if arquivo is None:
        return

    try:
        df_upload = pd.read_csv(arquivo)
    except Exception:
        st.error("Não foi possível ler o arquivo. Verifique se é um CSV válido.")
        return

    colunas_esperadas = {"data", "categoria", "descricao", "valor"}
    colunas_faltando = colunas_esperadas - set(df_upload.columns)
    if colunas_faltando:
        st.error(f"Colunas faltando: {', '.join(sorted(colunas_faltando))}")
        return

    if df_upload.empty:
        st.warning("O arquivo está vazio.")
        return

    st.caption(f"{len(df_upload)} registro(s) encontrado(s). Pré-visualização:")
    st.dataframe(df_upload, width="stretch", hide_index=True)

    categorias_validas = categorias_de(tipo)
    categorias_invalidas = set(df_upload["categoria"].dropna().unique()) - set(categorias_validas)
    if categorias_invalidas:
        st.warning(
            f"Categorias não reconhecidas (serão ignoradas): "
            f"{', '.join(sorted(categorias_invalidas))}"
        )

    if st.button(f"Importar {len(df_upload)} registro(s)", key=f"btn_importar_{tipo}", type="primary"):
        incluidos = 0
        erros = []
        for idx, linha in df_upload.iterrows():
            try:
                cadastro.adicionar_movimentacao(
                    tipo,
                    linha.get("data"),
                    linha.get("categoria"),
                    linha.get("descricao", ""),
                    linha.get("valor"),
                )
                incluidos += 1
            except (ValueError, TypeError) as erro:
                erros.append(f"Linha {idx + 2}: {erro}")

        if incluidos:
            st.success(f"{incluidos} registro(s) importado(s) com sucesso.")
        for erro in erros:
            st.error(erro)
        if incluidos:
            st.rerun()


def _editor_lancamentos(tipo: str, mes, df) -> None:
    """Tabela editável: inclui, altera e exclui lançamentos na própria grade.

    O `Nº` é gerado pelo sistema e fica bloqueado. Data, Categoria, Descrição e
    Valor são editáveis, e a última linha em branco serve para incluir um novo
    registro. Nada é gravado antes de o usuário confirmar.
    """
    # A chave carrega uma versão: ao incrementá-la, o editor renasce limpo e as
    # alterações já aplicadas não voltam a ser processadas.
    versao = st.session_state.get(f"versao_editor_{tipo}", 0)
    chave = f"editor_{tipo}_{mes}_{versao}"

    st.caption(
        "Edite direto na tabela. A linha em branco no fim inclui um novo lançamento; "
        "para excluir, selecione a linha pela caixa à esquerda e tecle Delete. "
        "As mudanças só valem depois de salvar."
    )
    st.data_editor(
        df[["id", "data", "categoria", "descricao", "valor"]],
        key=chave,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn(
                "Nº", format="%d", disabled=True, help="Gerado automaticamente pelo sistema.",
            ),
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", required=True),
            "categoria": st.column_config.SelectboxColumn(
                "Categoria", options=categorias_de(tipo), required=True,
            ),
            "descricao": st.column_config.TextColumn("Descrição", max_chars=120),
            # "localized" usa o separador de milhar do navegador (1.234,56 em
            # pt-BR); o printf "R$ %.2f" sairia sem separador nenhum.
            "valor": st.column_config.NumberColumn(
                "Valor (R$)", format="localized", min_value=0.01, step=100.0, required=True,
            ),
        },
    )

    mudancas = st.session_state.get(chave, {})
    pendentes = (
        len(mudancas.get("added_rows", []))
        + len(mudancas.get("edited_rows", {}))
        + len(mudancas.get("deleted_rows", []))
    )

    coluna, _ = st.columns([1, 3])
    with coluna:
        salvar = st.button(
            f"Salvar {pendentes} alteração(ões)" if pendentes else "Salvar alterações",
            key=f"salvar_{tipo}_{mes}", type="primary",
            disabled=not pendentes, width="stretch",
        )
    if salvar:
        _aplicar_edicoes(tipo, df, mudancas)
        st.session_state[f"versao_editor_{tipo}"] = versao + 1
        st.rerun()


def _aplicar_edicoes(tipo: str, df, mudancas: dict) -> None:
    """Grava no CSV o que foi mexido na grade, validando registro a registro."""
    incluidos = alterados = excluidos = 0
    erros: list[str] = []

    # Exclusões primeiro: as posições se referem ao DataFrame original.
    for posicao in mudancas.get("deleted_rows", []):
        try:
            if cadastro.excluir_movimentacao(tipo, int(df.iloc[posicao]["id"])):
                excluidos += 1
        except (IndexError, ValueError) as erro:
            erros.append(f"Exclusão: {erro}")

    for posicao, campos in mudancas.get("edited_rows", {}).items():
        try:
            linha = df.iloc[int(posicao)]
            valores = {
                "data": campos.get("data", linha["data"]),
                "categoria": campos.get("categoria", linha["categoria"]),
                "descricao": campos.get("descricao", linha["descricao"]),
                "valor": campos.get("valor", linha["valor"]),
            }
            cadastro.atualizar_movimentacao(
                tipo, int(linha["id"]), valores["data"], valores["categoria"],
                valores["descricao"], valores["valor"],
            )
            alterados += 1
        except (IndexError, ValueError, TypeError) as erro:
            erros.append(f"Nº {df.iloc[int(posicao)]['id']}: {erro}")

    for nova in mudancas.get("added_rows", []):
        if not nova:
            continue
        try:
            cadastro.adicionar_movimentacao(
                tipo, nova.get("data"), nova.get("categoria"),
                nova.get("descricao", ""), nova.get("valor"),
            )
            incluidos += 1
        except (ValueError, TypeError) as erro:
            erros.append(f"Nova linha: {erro}")

    partes = []
    if incluidos:
        partes.append(f"{incluidos} incluído(s)")
    if alterados:
        partes.append(f"{alterados} alterado(s)")
    if excluidos:
        partes.append(f"{excluidos} excluído(s)")
    if partes:
        st.toast(" · ".join(partes), icon="✅")
    for erro in erros:
        st.toast(erro, icon="⚠️")


def pagina_orcamento() -> None:
    """Planejamento: define o valor previsto de cada categoria no mês."""
    cores = paleta(tema_atual())
    st.title("Orçamento")
    meses = analise.meses_disponiveis()
    proximo = date.today().strftime("%Y-%m")
    opcoes = sorted(set(meses) | {proximo}, reverse=True)
    rotulos_orc = {mes_nome(m): m for m in opcoes}

    c1, _ = st.columns([1, 2])
    with c1:
        mes = rotulos_orc[st.selectbox("Mês do orçamento", list(rotulos_orc), key="orc_mes")]

    with st.expander("Copiar de outro mês"):
        _copiar_orcamento(mes, [m for m in meses if m != mes])

    st.caption("Informe o valor previsto para cada categoria do mês selecionado.")

    with st.form(f"form_orcamento_{mes}"):
        receitas_atuais = cadastro.orcamento_do_mes(mes, "receita")
        despesas_atuais = cadastro.orcamento_do_mes(mes, "despesa")

        col_receita, col_despesa = st.columns(2)
        with col_receita:
            st.subheader(ROTULO["receita"])
            receitas = _campos_orcamento(mes, "receita", receitas_atuais)
            st.markdown(f"**Total previsto:** {brl(sum(receitas.values()))}")
        with col_despesa:
            st.subheader(ROTULO["despesa"])
            despesas = _campos_orcamento(mes, "despesa", despesas_atuais)
            st.markdown(f"**Total previsto:** {brl(sum(despesas.values()))}")

        salvo = st.form_submit_button("Salvar orçamento", type="primary", width="stretch")

    if salvo:
        try:
            gravadas = cadastro.salvar_orcamento_mes(mes, {"receita": receitas, "despesa": despesas})
            st.success(f"Orçamento de {mes_nome(mes)} salvo — {gravadas} categorias.")
            st.rerun()
        except ValueError as erro:
            st.error(str(erro))

    resultado = sum(receitas.values()) - sum(despesas.values())
    st.divider()
    indicador(
        st.container(), "Resultado previsto para o mês", moeda(resultado),
        cor=cores["ok"] if resultado >= 0 else cores["critico"],
    )


def _campos_orcamento(mes: str, tipo: str, atuais: dict) -> dict:
    """Campos numéricos do formulário. A chave inclui o mês — sem isso o
    Streamlit reaproveitaria o valor digitado no mês anterior."""
    valores = {}
    for categoria in categorias_de(tipo):
        valores[categoria] = st.number_input(
            categoria,
            min_value=0.0,
            step=1000.0,
            value=float(atuais.get(categoria, 0.0)),
            format="%.2f",
            key=f"orc_{mes}_{tipo}_{categoria}",
        )
    return valores


def _copiar_orcamento(destino: str, origens: list[str]) -> None:
    """Replica o orçamento de um mês para outro, com reajuste percentual."""
    if not origens:
        st.caption("Nenhum outro mês com orçamento cadastrado.")
        return
    c1, c2, c3 = st.columns([2, 1, 1])
    rotulos_origem = {mes_nome(m): m for m in origens}
    origem = rotulos_origem[c1.selectbox("Copiar de", list(rotulos_origem), key="orc_origem")]
    reajuste = c2.number_input("Reajuste (%)", value=0.0, step=1.0, format="%.1f", key="orc_reajuste")
    c3.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
    if c3.button("Copiar", key="orc_copiar", width="stretch"):
        try:
            total = cadastro.copiar_orcamento(origem, destino, reajuste)
            st.success(f"{total} categorias copiadas de {mes_nome(origem)} para {mes_nome(destino)}.")
            st.rerun()
        except ValueError as erro:
            st.error(str(erro))


def pagina_relatorio() -> None:
    """Relatório mensal detalhado, com projeção e exportações."""
    tema = tema_atual()
    cores = paleta(tema)
    st.title("Relatório Mensal")
    meses = analise.meses_disponiveis()
    if not meses:
        st.info("Nenhum mês disponível. Cadastre lançamentos ou gere os dados de exemplo com `python seed.py`.")
        return

    c1, _ = st.columns([1, 2])
    with c1:
        mes = selectbox_mes("Mês", "rel_mes", meses)

    resumo = analise.resumo_mes(mes)
    projecao = analise.projecao_fechamento(mes)

    c1, c2, c3, c4 = st.columns(4)
    indicador(c1, "Receitas", moeda(resumo["receita_realizada"]),
              f"{resumo['execucao_receita']:.1f}% do previsto", cores["receita"])
    indicador(c2, "Despesas", moeda(resumo["despesa_realizada"]),
              f"{resumo['execucao_despesa']:.1f}% do previsto", cores["despesa"])
    indicador(c3, "Saldo", moeda(resumo["saldo_realizado"]),
              f"previsto: {moeda(resumo['saldo_planejado'])}",
              cores["ok"] if resumo["saldo_realizado"] >= 0 else cores["critico"])
    indicador(c4, "Saldo projetado", moeda(projecao["saldo_projetado"]),
              f"ritmo de {projecao['dias_corridos']} de {projecao['dias_no_mes']} dias")

    st.divider()
    st.subheader("Pontos de atenção")
    mostrar_alertas(mes, limite=10)

    st.divider()
    for tipo in ("receita", "despesa"):
        st.subheader(f"{ROTULO[tipo]} — Planejado x Realizado")
        tabela_comparativa(analise.comparativo_categorias(tipo, mes))
        grafico(graficos.grafico_execucao_orcamentaria(tipo, mes, tema),
                "Cadastre o orçamento do mês para ver a execução.")

    st.divider()
    st.subheader("Exportar")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        botao_exportar("Excel", f"rel_xlsx_{mes}", lambda: exports.gerar_xlsx_relatorio(mes),
                       f"relatorio_{mes}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        botao_exportar("PDF", f"rel_pdf_{mes}", lambda: exports.gerar_pdf_relatorio(mes),
                       f"relatorio_{mes}.pdf", "application/pdf")
    with c3:
        botao_exportar("PowerPoint", f"rel_pptx_{mes}", lambda: exports.gerar_pptx_relatorio(mes),
                       f"relatorio_{mes}.pptx",
                       "application/vnd.openxmlformats-officedocument.presentationml.presentation")
    with c4:
        botao_exportar("Apresentação Executiva", f"rel_pptx_exec_{mes}",
                       lambda: exports.gerar_pptx_executivo(mes),
                       f"relatorio_executivo_{mes}.pptx",
                       "application/vnd.openxmlformats-officedocument.presentationml.presentation")


def pagina_qualidade() -> None:
    """Registro das correções feitas pelo ETL na última leitura dos CSV."""
    cores = paleta(tema_atual())
    st.title("Qualidade dos Dados")
    st.caption(
        "Registro das correções aplicadas na leitura dos arquivos CSV. Todo dado "
        "exibido no sistema passa por Extração, Transformação e Carga antes de ser analisado."
    )

    qualidade = analise.qualidade_dados()
    c1, c2, c3 = st.columns(3)
    indicador(c1, "Linhas lidas", f"{qualidade['lidas']}", "nos três arquivos CSV")
    indicador(c2, "Linhas carregadas", f"{qualidade['carregadas']}",
              "aprovadas na transformação", cores["ok"])
    indicador(c3, "Linhas descartadas", f"{qualidade['descartadas']}", "fora do padrão",
              cores["critico"] if qualidade["descartadas"] else "")

    st.subheader("Correções aplicadas")
    correcoes = [
        ("Linhas vazias removidas", qualidade["vazias"], "sem data, categoria ou valor"),
        ("Registros duplicados removidos", qualidade["duplicadas"], "mesma data, categoria, descrição e valor"),
        ("Valores inválidos descartados", qualidade["valor_invalido"], "não numéricos ou menores ou iguais a zero"),
        ("Datas inválidas descartadas", qualidade["data_invalida"], "fora do formato AAAA-MM-DD"),
        ("Categorias padronizadas", qualidade["categoria_ajustada"], "sinônimos e acentos convertidos"),
        ("Categorias não reconhecidas", qualidade["categoria_invalida"], "fora da lista oficial"),
    ]
    st.dataframe(
        [{"Correção": nome, "Ocorrências": qtd, "Critério": criterio} for nome, qtd, criterio in correcoes],
        width="stretch",
        hide_index=True,
        column_config={
            "Correção": st.column_config.TextColumn(width="medium"),
            "Ocorrências": st.column_config.NumberColumn(format="%d", width="small"),
            "Critério": st.column_config.TextColumn(width="large"),
        },
    )

    if not qualidade["descartadas"] and not qualidade["categoria_ajustada"]:
        st.success("Nenhuma correção foi necessária: os arquivos estão íntegros.")
    for detalhe in qualidade["detalhes"]:
        st.warning(detalhe)


# ----------------------------------------------------------------- Navegação

# Páginas da aplicação. O menu é desenhado na barra lateral com o rádio do
# Streamlit, estilizado para parecer um menu moderno (ver `ESTILO_MENU`). Os
# ícones vêm em formato emoji para aparecerem dentro do próprio rádio.
PAGINAS = {
    "Painel": pagina_dashboard,
    "Movimentações": pagina_movimentacoes,
    "Orçamento": pagina_orcamento,
    "Relatório Mensal": pagina_relatorio,
    "Qualidade de Dados": pagina_qualidade,
}

ICONES_MENU = {
    "Painel": "📊",
    "Movimentações": "💳",
    "Orçamento": "🎯",
    "Relatório Mensal": "📄",
    "Qualidade de Dados": "✅",
}

# Estilo do menu lateral: transforma o rádio em itens de menu com cantos
# arredondados e destaque no item ativo. A cor primária é a mesma do tema
# (config.toml), injetada por tema para funcionar mesmo no modo escuro.
PRIMARIA_POR_TEMA = {"light": "#2a78d6", "dark": "#3987e5"}


def _rgba(hex_cor: str, alfa: float) -> str:
    """Converte "#rrggbb" em "rgba(r, g, b, alfa)"."""
    cor = hex_cor.lstrip("#")
    r, g, b = (int(cor[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alfa})"


def estilo_menu(tema: str) -> str:
    """CSS do menu lateral na cor primária do tema escolhido."""
    primaria = PRIMARIA_POR_TEMA[tema]
    hover = _rgba(primaria, 0.12)
    return f"""
<style>
[data-testid="stSidebar"] div[role="radiogroup"] {{
    gap: 0.2rem;
}}
[data-testid="stSidebar"] div[role="radiogroup"] label {{
    display: flex;
    align-items: center;
    gap: 0.55rem;
    width: 100%;
    padding: 0.5rem 0.7rem;
    border-radius: 0.6rem;
    cursor: pointer;
    transition: background-color 0.15s ease, color 0.15s ease;
}}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
    background-color: {hover};
}}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
    background-color: {primaria};
    color: #ffffff;
    font-weight: 600;
}}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {{
    color: #ffffff;
}}
</style>
"""


def main() -> None:
    """Monta a barra lateral (título em primeiro lugar) e despacha a página."""
    tema = tema_atual()
    cores = paleta(tema)
    with st.sidebar:
        st.markdown(estilo_menu(tema), unsafe_allow_html=True)
        st.markdown(
            f"<div style='font-size:1.25rem;font-weight:700;line-height:1.25;"
            f"color:{cores['texto']}'>🏨 {SISTEMA_NOME}</div>"
            f"<div style='font-size:.85rem;color:{cores['texto_suave']}'>"
            f"{HOTEL_NOME}</div>",
            unsafe_allow_html=True,
        )
        st.divider()
        escolhida = st.radio(
            "Navegação",
            list(PAGINAS),
            label_visibility="collapsed",
            format_func=lambda nome: f"{ICONES_MENU[nome]}  {nome}",
        )
        st.divider()
        resumo = analise.resumo_mes()
        st.caption("Acumulado do período")
        st.markdown(
            f"Receitas: **{brl(resumo['receita_realizada'])}**  \n"
            f"Despesas: **{brl(resumo['despesa_realizada'])}**  \n"
            f"Saldo: **{brl(resumo['saldo_realizado'])}**"
        )
        st.divider()
        atual = "escuro" if tema == "dark" else "claro"
        st.caption(f"Tema {atual} · troque em ⋮ › Settings › Appearance")
        st.caption(f"versão {VERSAO}")

    PAGINAS[escolhida]()


# O Streamlit executa este arquivo como "__main__"; a guarda permite importar o
# módulo em testes sem disparar a montagem da interface.
if __name__ == "__main__":
    main()
