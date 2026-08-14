"""Processo ETL — Extração, Transformação e Carga dos arquivos CSV.

Fluxo:
    Extração      -> lê os arquivos CSV com Pandas
    Transformação -> limpa, converte tipos e organiza as categorias
    Carga         -> entrega DataFrames prontos para análise e gráficos

Toda leitura de dados do sistema passa por aqui. Nenhum outro módulo lê CSV
diretamente, de modo que os dados analisados são sempre os dados tratados.
"""

from dataclasses import dataclass, field

import pandas as pd

from config import (
    ARQ_OPERACAO,
    ARQ_ORCAMENTO,
    COLUNAS_MOVIMENTACAO,
    COLUNAS_OPERACAO,
    COLUNAS_ORCAMENTO,
    TIPOS,
    arquivo_de,
    categorias_de,
    ensure_dirs,
    sinonimos_de,
)
from utils import sem_acento

ENCODING = "utf-8-sig"


@dataclass
class RelatorioETL:
    """Registra o que foi descartado em cada etapa da transformação."""

    lidas: int = 0
    vazias: int = 0
    duplicadas: int = 0
    valor_invalido: int = 0
    data_invalida: int = 0
    categoria_ajustada: int = 0
    categoria_invalida: int = 0
    detalhes: list[str] = field(default_factory=list)

    @property
    def carregadas(self) -> int:
        """Linhas que sobreviveram à transformação."""
        return self.lidas - self.descartadas

    @property
    def descartadas(self) -> int:
        """Total de linhas removidas pelo processo."""
        return self.vazias + self.duplicadas + self.valor_invalido + self.data_invalida + self.categoria_invalida

    def somar(self, outro: "RelatorioETL") -> None:
        """Agrega o relatório de outro arquivo neste."""
        self.lidas += outro.lidas
        self.vazias += outro.vazias
        self.duplicadas += outro.duplicadas
        self.valor_invalido += outro.valor_invalido
        self.data_invalida += outro.data_invalida
        self.categoria_ajustada += outro.categoria_ajustada
        self.categoria_invalida += outro.categoria_invalida
        self.detalhes.extend(outro.detalhes)


# ---------------------------------------------------------------- Extração


def extrair(caminho, colunas: list[str]) -> pd.DataFrame:
    """Lê um CSV do disco. Devolve DataFrame vazio se o arquivo não existir."""
    ensure_dirs()
    if not caminho.exists():
        return pd.DataFrame(columns=colunas)
    try:
        df = pd.read_csv(caminho, encoding=ENCODING, dtype=str, keep_default_na=False)
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return pd.DataFrame(columns=colunas)
    for coluna in colunas:
        if coluna not in df.columns:
            df[coluna] = ""
    return df[colunas]


# ----------------------------------------------------------- Transformação


def _normalizar_categoria(valor: str, tipo: str) -> str:
    """Aplica o mapa de sinônimos e corrige diferenças de acento/caixa."""
    validas = categorias_de(tipo)
    bruto = str(valor).strip()
    if bruto in validas:
        return bruto
    chave = sem_acento(bruto)
    # Nome oficial escrito com caixa ou acentuação diferente.
    for oficial in validas:
        if sem_acento(oficial) == chave:
            return oficial
    return sinonimos_de(tipo).get(chave, "")


def transformar_movimentacoes(df: pd.DataFrame, tipo: str) -> tuple[pd.DataFrame, RelatorioETL]:
    """Limpa e padroniza receitas ou despesas."""
    rel = RelatorioETL(lidas=len(df))
    if df.empty:
        return pd.DataFrame(columns=COLUNAS_MOVIMENTACAO + ["mes", "tipo"]), rel

    df = df.copy()

    # 1. Remoção de linhas vazias (sem data, sem categoria ou sem valor).
    essenciais = df[["data", "categoria", "valor"]].apply(lambda c: c.astype(str).str.strip())
    vazias = (essenciais == "").any(axis=1) | (essenciais.isin(["nan", "None"])).any(axis=1)
    rel.vazias = int(vazias.sum())
    df = df[~vazias]

    # 2. Conversão de valores para formato numérico.
    valores = (
        df["valor"].astype(str)
        .str.replace(r"[R$\s]", "", regex=True)
        .str.replace(r"\.(?=\d{3}(\D|$))", "", regex=True)  # separador de milhar
        .str.replace(",", ".", regex=False)
    )
    df["valor"] = pd.to_numeric(valores, errors="coerce")
    invalidos = df["valor"].isna() | (df["valor"] <= 0)
    rel.valor_invalido = int(invalidos.sum())
    df = df[~invalidos]

    # 3. Conversão e validação de datas.
    df["data"] = pd.to_datetime(df["data"], format="%Y-%m-%d", errors="coerce")
    sem_data = df["data"].isna()
    rel.data_invalida = int(sem_data.sum())
    df = df[~sem_data]

    # 4. Organização das categorias (sinônimos, acentos e caixa).
    original = df["categoria"].astype(str).str.strip()
    df["categoria"] = original.map(lambda c: _normalizar_categoria(c, tipo))
    desconhecidas = df["categoria"] == ""
    rel.categoria_invalida = int(desconhecidas.sum())
    if rel.categoria_invalida:
        nomes = sorted(set(original[desconhecidas]))
        rel.detalhes.append(f"{tipo}: categorias não reconhecidas {nomes}")
    rel.categoria_ajustada = int(((~desconhecidas) & (original != df["categoria"])).sum())
    df = df[~desconhecidas]

    # 5. Remoção de registros duplicados (mesma data, categoria, descrição e valor).
    df["descricao"] = df["descricao"].astype(str).str.strip().replace({"nan": ""})
    antes = len(df)
    df = df.drop_duplicates(subset=["data", "categoria", "descricao", "valor"], keep="first")
    rel.duplicadas = antes - len(df)

    # 6. Colunas derivadas usadas nas análises.
    df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    df["mes"] = df["data"].dt.strftime("%Y-%m")
    df["tipo"] = tipo

    df = df.sort_values(["data", "id"]).reset_index(drop=True)
    return df[COLUNAS_MOVIMENTACAO + ["mes", "tipo"]], rel


def transformar_operacao(df: pd.DataFrame) -> tuple[pd.DataFrame, RelatorioETL]:
    """Limpa e padroniza os indicadores diários importados do relatório OPERA.

    Algumas métricas do relatório só trazem o valor do dia (não acumulam mês ou
    ano) — nesses casos as colunas `mtd`, `ytd`, `mtd_ant` e `ytd_ant` ficam
    vazias e continuam válidas.
    """
    rel = RelatorioETL(lidas=len(df))
    if df.empty:
        return pd.DataFrame(columns=COLUNAS_OPERACAO), rel

    df = df.copy()

    vazias = df[["data", "indicador"]].apply(lambda c: c.astype(str).str.strip() == "").any(axis=1)
    rel.vazias = int(vazias.sum())
    df = df[~vazias]

    df["data"] = pd.to_datetime(df["data"], format="%Y-%m-%d", errors="coerce")
    sem_data = df["data"].isna()
    rel.data_invalida = int(sem_data.sum())
    df = df[~sem_data]

    for coluna in ("hoje", "mtd", "ytd", "hoje_ant", "mtd_ant", "ytd_ant"):
        df[coluna] = pd.to_numeric(df[coluna].astype(str).str.replace(",", ""), errors="coerce")
    invalidos = df["hoje"].isna()
    rel.valor_invalido = int(invalidos.sum())
    df = df[~invalidos]

    antes = len(df)
    df = df.drop_duplicates(subset=["data", "indicador"], keep="last")
    rel.duplicadas = antes - len(df)

    df["data"] = df["data"].dt.strftime("%Y-%m-%d")
    df = df.sort_values(["data", "indicador"]).reset_index(drop=True)
    return df[COLUNAS_OPERACAO], rel


def transformar_orcamento(df: pd.DataFrame) -> tuple[pd.DataFrame, RelatorioETL]:
    """Limpa e padroniza o orçamento planejado."""
    rel = RelatorioETL(lidas=len(df))
    if df.empty:
        return pd.DataFrame(columns=COLUNAS_ORCAMENTO), rel

    df = df.copy()

    vazias = df[COLUNAS_ORCAMENTO].apply(lambda c: c.astype(str).str.strip() == "").any(axis=1)
    rel.vazias = int(vazias.sum())
    df = df[~vazias]

    df["tipo"] = df["tipo"].astype(str).str.strip().str.lower()
    df = df[df["tipo"].isin(TIPOS)]

    df["mes"] = df["mes"].astype(str).str.strip()
    mes_ok = df["mes"].str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])")
    rel.data_invalida = int((~mes_ok).sum())
    df = df[mes_ok]

    valores = df["valor_planejado"].astype(str).str.replace(",", ".", regex=False)
    df["valor_planejado"] = pd.to_numeric(valores, errors="coerce")
    invalidos = df["valor_planejado"].isna() | (df["valor_planejado"] < 0)
    rel.valor_invalido = int(invalidos.sum())
    df = df[~invalidos]

    original = df["categoria"].astype(str).str.strip()
    df["categoria"] = [_normalizar_categoria(c, t) for c, t in zip(original, df["tipo"])]
    desconhecidas = df["categoria"] == ""
    rel.categoria_invalida = int(desconhecidas.sum())
    rel.categoria_ajustada = int(((~desconhecidas) & (original != df["categoria"])).sum())
    df = df[~desconhecidas]

    antes = len(df)
    df = df.drop_duplicates(subset=["mes", "tipo", "categoria"], keep="last")
    rel.duplicadas = antes - len(df)

    df = df.sort_values(["mes", "tipo", "categoria"]).reset_index(drop=True)
    return df[COLUNAS_ORCAMENTO], rel


# -------------------------------------------------------------------- Carga


def carregar(tipo: str) -> tuple[pd.DataFrame, RelatorioETL]:
    """Executa o ETL completo de receitas ou despesas."""
    bruto = extrair(arquivo_de(tipo), COLUNAS_MOVIMENTACAO)
    return transformar_movimentacoes(bruto, tipo)


def carregar_orcamento() -> tuple[pd.DataFrame, RelatorioETL]:
    """Executa o ETL completo do orçamento."""
    bruto = extrair(ARQ_ORCAMENTO, COLUNAS_ORCAMENTO)
    return transformar_orcamento(bruto)


def carregar_operacao() -> tuple[pd.DataFrame, RelatorioETL]:
    """Executa o ETL completo dos indicadores diários do relatório OPERA."""
    bruto = extrair(ARQ_OPERACAO, COLUNAS_OPERACAO)
    return transformar_operacao(bruto)


def carregar_tudo() -> tuple[pd.DataFrame, pd.DataFrame, RelatorioETL]:
    """Executa o ETL de todos os arquivos e devolve um relatório consolidado.

    Retorna (movimentações, orçamento, relatório). As movimentações vêm em um
    único DataFrame com a coluna 'tipo' distinguindo receita de despesa.
    """
    receitas, rel_r = carregar("receita")
    despesas, rel_d = carregar("despesa")
    orcamento, rel_o = carregar_orcamento()

    consolidado = RelatorioETL()
    for parcial in (rel_r, rel_d, rel_o):
        consolidado.somar(parcial)

    movimentacoes = pd.concat([receitas, despesas], ignore_index=True)
    return movimentacoes, orcamento, consolidado


if __name__ == "__main__":
    movs, orc, relatorio = carregar_tudo()
    print(f"Linhas lidas .............. {relatorio.lidas}")
    print(f"Linhas vazias removidas ... {relatorio.vazias}")
    print(f"Duplicadas removidas ...... {relatorio.duplicadas}")
    print(f"Valores inválidos ......... {relatorio.valor_invalido}")
    print(f"Datas/meses inválidos ..... {relatorio.data_invalida}")
    print(f"Categorias normalizadas ... {relatorio.categoria_ajustada}")
    print(f"Categorias descartadas .... {relatorio.categoria_invalida}")
    print(f"Linhas carregadas ......... {relatorio.carregadas}")
    print(f"\nMovimentações: {len(movs)} | Orçamento: {len(orc)}")
    for detalhe in relatorio.detalhes:
        print(f"  ! {detalhe}")
