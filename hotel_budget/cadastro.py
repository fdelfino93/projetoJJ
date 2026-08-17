"""Cadastro — inclusão, alteração e exclusão de registros nos arquivos CSV.

É a única camada que escreve nos CSV. A leitura é sempre feita pelo `etl`,
garantindo que nada entre no sistema sem passar pelas validações do `utils`.
"""

import csv
from typing import Optional

import pandas as pd

from config import (
    ARQ_ORCAMENTO,
    COLUNAS_MOVIMENTACAO,
    COLUNAS_ORCAMENTO,
    arquivo_de,
    categorias_de,
    ensure_dirs,
)
from etl import ENCODING, carregar, carregar_orcamento, extrair
from utils import (
    validar_categoria,
    validar_data,
    validar_descricao,
    validar_mes,
    validar_tipo,
    validar_valor,
)


def _gravar(caminho, df: pd.DataFrame, colunas: list[str]) -> None:
    """Escreve o DataFrame no CSV preservando o cabeçalho oficial."""
    ensure_dirs()
    df.to_csv(
        caminho,
        index=False,
        columns=colunas,
        encoding=ENCODING,
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )


def _proximo_id(caminho) -> int:
    """Calcula o próximo id lendo o arquivo bruto (inclui linhas descartadas
    pelo ETL, para nunca reaproveitar um id existente)."""
    bruto = extrair(caminho, COLUNAS_MOVIMENTACAO)
    if bruto.empty:
        return 1
    ids = pd.to_numeric(bruto["id"], errors="coerce")
    return int(ids.max()) + 1 if ids.notna().any() else 1


# ------------------------------------------------------------ Movimentações


def adicionar_movimentacao(tipo: str, data, categoria: str, descricao: str, valor) -> int:
    """Valida e grava um lançamento. Devolve o id gerado."""
    tipo = validar_tipo(tipo)
    data = validar_data(data)
    categoria = validar_categoria(tipo, categoria)
    descricao = validar_descricao(descricao)
    valor = validar_valor(valor)

    caminho = arquivo_de(tipo)
    novo_id = _proximo_id(caminho)

    ensure_dirs()
    existe = caminho.exists() and caminho.stat().st_size > 0
    with open(caminho, "a", encoding=ENCODING, newline="") as arq:
        writer = csv.writer(arq, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        if not existe:
            writer.writerow(COLUNAS_MOVIMENTACAO)
        writer.writerow([novo_id, data.isoformat(), categoria, descricao, f"{valor:.2f}"])
    return novo_id


def excluir_movimentacao(tipo: str, mov_id: int) -> bool:
    """Remove um lançamento pelo id. Devolve True se algo foi removido."""
    tipo = validar_tipo(tipo)
    caminho = arquivo_de(tipo)
    bruto = extrair(caminho, COLUNAS_MOVIMENTACAO)
    if bruto.empty:
        return False
    manter = pd.to_numeric(bruto["id"], errors="coerce") != int(mov_id)
    if manter.all():
        return False
    _gravar(caminho, bruto[manter], COLUNAS_MOVIMENTACAO)
    return True


def atualizar_movimentacao(tipo: str, mov_id: int, data, categoria: str, descricao: str, valor) -> bool:
    """Altera um lançamento existente. Devolve True se algo foi alterado."""
    tipo = validar_tipo(tipo)
    data = validar_data(data)
    categoria = validar_categoria(tipo, categoria)
    descricao = validar_descricao(descricao)
    valor = validar_valor(valor)

    caminho = arquivo_de(tipo)
    bruto = extrair(caminho, COLUNAS_MOVIMENTACAO)
    alvo = pd.to_numeric(bruto["id"], errors="coerce") == int(mov_id)
    if not alvo.any():
        return False
    bruto.loc[alvo, ["data", "categoria", "descricao", "valor"]] = [
        data.isoformat(),
        categoria,
        descricao,
        f"{valor:.2f}",
    ]
    _gravar(caminho, bruto, COLUNAS_MOVIMENTACAO)
    return True


def listar_movimentacoes(tipo: str, mes: Optional[str] = None) -> pd.DataFrame:
    """Lançamentos já tratados pelo ETL, opcionalmente filtrados por mês."""
    df, _ = carregar(validar_tipo(tipo))
    if mes:
        df = df[df["mes"] == validar_mes(mes)]
    return df.sort_values(["data", "id"], ascending=[False, False]).reset_index(drop=True)


# ----------------------------------------------------------------- Orçamento


def salvar_orcamento(mes: str, tipo: str, categoria: str, valor_planejado) -> None:
    """Insere ou atualiza o valor planejado de uma categoria no mês."""
    mes = validar_mes(mes)
    tipo = validar_tipo(tipo)
    categoria = validar_categoria(tipo, categoria)
    valor = float(valor_planejado)
    if valor < 0:
        raise ValueError("O valor planejado não pode ser negativo.")

    df = extrair(ARQ_ORCAMENTO, COLUNAS_ORCAMENTO)
    chave = (
        (df["mes"].astype(str).str.strip() == mes)
        & (df["tipo"].astype(str).str.strip().str.lower() == tipo)
        & (df["categoria"].astype(str).str.strip() == categoria)
    )
    if chave.any():
        df.loc[chave, "valor_planejado"] = f"{valor:.2f}"
    else:
        nova = pd.DataFrame(
            [{"mes": mes, "tipo": tipo, "categoria": categoria, "valor_planejado": f"{valor:.2f}"}]
        )
        df = pd.concat([df, nova], ignore_index=True)
    _gravar(ARQ_ORCAMENTO, df, COLUNAS_ORCAMENTO)


def salvar_orcamento_mes(mes: str, valores: dict[str, dict[str, float]]) -> int:
    """Grava o orçamento inteiro de um mês de uma só vez.

    `valores` tem o formato {"receita": {categoria: valor}, "despesa": {...}}.
    Reescreve o arquivo uma única vez, em vez de uma vez por categoria.
    """
    mes = validar_mes(mes)
    df = extrair(ARQ_ORCAMENTO, COLUNAS_ORCAMENTO)

    outros_meses = df[df["mes"].astype(str).str.strip() != mes]
    linhas = []
    for tipo, categorias in valores.items():
        tipo = validar_tipo(tipo)
        for categoria, valor in categorias.items():
            categoria = validar_categoria(tipo, categoria)
            linhas.append(
                {
                    "mes": mes,
                    "tipo": tipo,
                    "categoria": categoria,
                    "valor_planejado": f"{max(float(valor), 0.0):.2f}",
                }
            )

    atualizado = pd.concat([outros_meses, pd.DataFrame(linhas, columns=COLUNAS_ORCAMENTO)], ignore_index=True)
    atualizado = atualizado.sort_values(["mes", "tipo", "categoria"])
    _gravar(ARQ_ORCAMENTO, atualizado, COLUNAS_ORCAMENTO)
    return len(linhas)


def excluir_orcamento_mes(mes: str) -> int:
    """Remove todo o orçamento de um mês. Devolve quantas linhas saíram."""
    mes = validar_mes(mes)
    df = extrair(ARQ_ORCAMENTO, COLUNAS_ORCAMENTO)
    manter = df["mes"].astype(str).str.strip() != mes
    removidas = int((~manter).sum())
    if removidas:
        _gravar(ARQ_ORCAMENTO, df[manter], COLUNAS_ORCAMENTO)
    return removidas


def copiar_orcamento(mes_origem: str, mes_destino: str, reajuste: float = 0.0) -> int:
    """Duplica o orçamento de um mês para outro, com reajuste percentual.

    Atalho de planejamento: o gerente monta janeiro e replica para o ano.
    """
    mes_origem = validar_mes(mes_origem)
    mes_destino = validar_mes(mes_destino)
    if mes_origem == mes_destino:
        raise ValueError("O mês de origem e o de destino devem ser diferentes.")

    orcamento, _ = carregar_orcamento()
    origem = orcamento[orcamento["mes"] == mes_origem]
    if origem.empty:
        raise ValueError(f"Não há orçamento cadastrado em {mes_origem}.")

    fator = 1 + (float(reajuste) / 100)
    valores: dict[str, dict[str, float]] = {"receita": {}, "despesa": {}}
    for linha in origem.itertuples():
        valores[linha.tipo][linha.categoria] = round(linha.valor_planejado * fator, 2)
    return salvar_orcamento_mes(mes_destino, valores)


def listar_orcamento(mes: Optional[str] = None) -> pd.DataFrame:
    """Orçamento já tratado pelo ETL, opcionalmente filtrado por mês."""
    df, _ = carregar_orcamento()
    if mes:
        df = df[df["mes"] == validar_mes(mes)]
    return df.reset_index(drop=True)


def orcamento_do_mes(mes: str, tipo: str) -> dict[str, float]:
    """Mapa {categoria: valor planejado} para preencher o formulário."""
    df = listar_orcamento(mes)
    df = df[df["tipo"] == validar_tipo(tipo)]
    planejado = dict(zip(df["categoria"], df["valor_planejado"]))
    return {cat: float(planejado.get(cat, 0.0)) for cat in categorias_de(tipo)}
