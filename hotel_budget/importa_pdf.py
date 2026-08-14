"""Importação diária do relatório OPERA (NA02 - Manager Report Gross).

O hotel exporta esse PDF uma vez por dia e ele precisa entrar no banco de dados
de forma padronizada. Este módulo:

  1. Extrai do PDF as métricas e os valores do dia, do mês e do ano acumulados,
     tanto do ano atual quanto do ano anterior;
  2. Traduz o nome das métricas para o português do Brasil usando o catálogo de
     `config.INDICADORES_OPERACAO`;
  3. Grava em `data/operacao.csv`, no formato "uma linha por métrica por dia".

O arquivo é idempotente: se o mesmo dia for importado de novo, os registros
antigos daquele dia são substituídos pelos novos — nunca duplica.

Uso:
    python importa_pdf.py              # importa o manrepTT.PDF do diretório atual
    python importa_pdf.py caminho.pdf  # importa um arquivo específico
"""

import argparse
import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import pdfplumber

from config import (
    ARQ_OPERACAO,
    COLUNAS_OPERACAO,
    INDICADORES_OPERACAO,
    ensure_dirs,
)
from etl import ENCODING

# Um token de valor é um número: inteiro, decimal ou com separador de milhar
# (formato americano do relatório: 19,774.58) e sinal negativo.
_VALOR = re.compile(r"^-?\d[\d,]*\.?\d*$")
_DATA = re.compile(r"^\d{2}-\d{2}-\d{2}$")

# Linhas de cabeçalho/rodapé que aparecem entre as métricas e não devem entrar
# no banco (a "Page X of Y" é a única com números e por isso precisa de filtro).
_RODAPE = (
    "page", "manager_report", "calendar/month", "filter",
    "last year", "room class all", "gross",
)


def _normalizar(texto) -> str:
    """Chave canônica: caixa baixa, espaços simples e sem vírgulas.

    Aceita uma lista de tokens (como sai do `pdfplumber`) ou uma string.
    """
    partes = texto if isinstance(texto, list) else str(texto).split()
    return re.sub(r"\s+", " ", " ".join(partes).lower()).replace(",", "")


# Catálogo com as chaves já normalizadas, para a busca não depender da caixa,
# da pontuação ou da quantidade de espaços do nome extraído do PDF.
_CHAVES = {_normalizar(k): v for k, v in INDICADORES_OPERACAO.items()}


def _eh_valor(token: str) -> bool:
    return bool(_VALOR.match(token))


def _eh_rodape(chave: str) -> bool:
    return chave.startswith(_RODAPE) or chave in _RODAPE


def _converter(token: str):
    """Devolve int para contagens e float arredondado para valores monetários."""
    numero = float(token.replace(",", ""))
    return int(numero) if numero.is_integer() else round(numero, 2)


def _texto(valor) -> str:
    """Formato canônico do CSV: inteiro sem casas, decimal com duas casas."""
    if not isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, int):
        return str(valor)
    return f"{valor:.2f}"


def _linhas(pagina):
    """Agrupa as palavras do PDF por linha, preservando a ordem da esquerda."""
    grupos = defaultdict(list)
    for palavra in pagina.extract_words(use_text_flow=False, keep_blank_chars=False):
        grupos[round(palavra["top"], 1)].append((palavra["x0"], palavra["text"]))
    for topo in sorted(grupos):
        yield [texto for _, texto in sorted(grupos[topo], key=lambda p: p[0])]


def _data_do_pdf(primeiras_linhas: list[list[str]]) -> Optional[str]:
    """Procura a data no formato DD-MM-AA nas primeiras linhas do PDF."""
    for linha in primeiras_linhas:
        for token in linha:
            if _DATA.match(token):
                try:
                    return datetime.strptime(token, "%d-%m-%y").date().isoformat()
                except ValueError:
                    continue
    return None


def extrair(caminho_pdf) -> tuple[list[dict], dict]:
    """Lê o PDF e devolve (registros padronizados, resumo da extração).

    Cada registro é um dict com as colunas de `COLUNAS_OPERACAO`, já com o nome
    da métrica traduzido para o português do Brasil.
    """
    resumo = {
        "data": None,
        "ano_atual": None,
        "ano_anterior": None,
        "reconhecidos": 0,
        "linhas_com_metrica": 0,
        "desconhecidos": [],
    }
    registros: list[dict] = []

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            linhas = list(_linhas(pagina))
            if resumo["data"] is None:
                resumo["data"] = _data_do_pdf(linhas)

            iniciado = False
            anos: list[str] = []
            pendente: list[str] = []

            def processar(nome: list[str], valores: list[str]) -> None:
                chave = _normalizar(nome)
                if _eh_rodape(chave) or chave not in _CHAVES:
                    if not _eh_rodape(chave):
                        resumo["desconhecidos"].append(chave)
                    return
                resumo["linhas_com_metrica"] += 1

                convertidos = [_converter(v) for v in valores]
                if len(valores) == 6:
                    hoje, mtd, ytd = convertidos[0:3]
                    hoje_ant, mtd_ant, ytd_ant = convertidos[3:6]
                elif len(valores) == 2:
                    hoje, mtd, ytd = convertidos[0], "", ""
                    hoje_ant, mtd_ant, ytd_ant = convertidos[1], "", ""
                else:
                    return  # quantidade inesperada de colunas; ignora a linha

                registros.append(
                    {
                        "data": resumo["data"],
                        "indicador": _CHAVES[chave],
                        "hoje": hoje,
                        "mtd": mtd,
                        "ytd": ytd,
                        "hoje_ant": hoje_ant,
                        "mtd_ant": mtd_ant,
                        "ytd_ant": ytd_ant,
                    }
                )
                resumo["reconhecidos"] += 1

            for linha in linhas:
                if resumo["ano_atual"] is None and len(linha) == 6 and all(re.fullmatch(r"\d{4}", t) for t in linha):
                    anos = linha
                    continue
                if not iniciado and linha == ["DAY", "MONTH", "YEAR", "DAY", "MONTH", "YEAR"]:
                    if anos:
                        resumo["ano_atual"] = anos[0]
                        resumo["ano_anterior"] = anos[3]
                    iniciado = True
                    continue
                if not iniciado:
                    continue

                # Os valores são o sufixo numérico da linha. Isso mantém no nome
                # números que fazem parte da métrica, como o "7" de "Next 7 Days".
                fim = len(linha)
                while fim > 0 and _eh_valor(linha[fim - 1]):
                    fim -= 1
                nome, valores = linha[:fim], linha[fim:]

                if nome and valores:
                    if pendente:
                        nome = pendente + nome
                        pendente = []
                    processar(nome, valores)
                elif nome:
                    chave = _normalizar(nome)
                    if _eh_rodape(chave):
                        pendente = []
                    elif len(pendente) < 2:
                        pendente = pendente + nome
                elif valores and pendente:
                    processar(pendente, valores)
                    pendente = []

    resumo["desconhecidos"] = sorted(set(resumo["desconhecidos"]))
    return registros, resumo


def gravar(registros: list[dict], caminho=ARQ_OPERACAO) -> tuple[int, int]:
    """Substitui os registros do mesmo dia e concatena. Devolve (novos, substituídos).

    A substituição por data torna a importação idempotente: rodar o importador
    duas vezes para o mesmo arquivo não duplica linhas no CSV.
    """
    ensure_dirs()
    colunas = COLUNAS_OPERACAO
    novo = pd.DataFrame([{k: _texto(v) for k, v in reg.items()} for reg in registros], columns=colunas)

    antigo = pd.DataFrame(columns=colunas)
    if caminho.exists() and caminho.stat().st_size > 0:
        try:
            antigo = pd.read_csv(caminho, encoding=ENCODING, dtype=str, keep_default_na=False)
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            antigo = pd.DataFrame(columns=colunas)

    datas_novas = set(novo["data"])
    substituidos = int(antigo["data"].isin(datas_novas).sum())
    manter = antigo[~antigo["data"].isin(datas_novas)]

    for coluna in colunas:
        if coluna not in manter.columns:
            manter[coluna] = ""

    juntos = pd.concat([manter, novo], ignore_index=True)
    juntos = juntos.drop_duplicates(subset=["data", "indicador"], keep="last")
    juntos = juntos.sort_values(["data", "indicador"]).reset_index(drop=True)
    juntos.to_csv(caminho, index=False, encoding=ENCODING, lineterminator="\n")
    return len(novo), substituidos


def importar(caminho_pdf) -> tuple[list[dict], dict]:
    """Extrai, traduz e grava o relatório. Devolve (registros, resumo)."""
    registros, resumo = extrair(caminho_pdf)
    if not registros:
        raise ValueError(f"Nenhuma métrica reconhecida no arquivo {caminho_pdf}.")
    novos, substituidos = gravar(registros)
    resumo["gravados"] = novos
    resumo["substituidos"] = substituidos
    return registros, resumo


def main() -> None:
    """Ponto de entrada da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Importa o relatório diário do OPERA (NA02) para o banco de dados."
    )
    parser.add_argument("pdf", nargs="?", default="manrepTT.PDF", help="caminho do PDF (padrão: manrepTT.PDF)")
    parser.add_argument("--csv", default=str(ARQ_OPERACAO), help="arquivo CSV de destino")
    args = parser.parse_args()

    if not Path(args.pdf).exists():
        parser.error(f"Arquivo não encontrado: {args.pdf}")

    registros, resumo = importar(args.pdf)

    print(f"Arquivo .................. {args.pdf}")
    print(f"Data do relatório ........ {resumo['data']}")
    if resumo["ano_atual"]:
        print(f"Comparação ............... {resumo['ano_atual']} vs {resumo['ano_anterior']}")
    print(f"Métricas reconhecidas .... {resumo['reconhecidos']} de {resumo['linhas_com_metrica']}")
    print(f"Registros gravados ....... {resumo['gravados']} em {args.csv}")
    print(f"Substituídos (mesma data)  {resumo['substituidos']}")
    for desconhecido in resumo["desconhecidos"]:
        print(f"  ! métrica sem tradução: {desconhecido}")
    print(f"\nConferir com: python -m etl  ou  streamlit run app.py")


if __name__ == "__main__":
    main()
