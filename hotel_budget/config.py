"""Constantes e configurações do Hotel Budget Manager."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ARQ_RECEITAS = DATA_DIR / "receitas.csv"
ARQ_DESPESAS = DATA_DIR / "despesas.csv"
ARQ_ORCAMENTO = DATA_DIR / "orcamento.csv"

HOTEL_NOME = "Ibis Styles Curitiba Centro Cívico"
SISTEMA_NOME = "Hotel Budget Manager"
VERSAO = "2.0"

TIPOS = ["receita", "despesa"]

COLUNAS_MOVIMENTACAO = ["id", "data", "categoria", "descricao", "valor"]
COLUNAS_ORCAMENTO = ["mes", "tipo", "categoria", "valor_planejado"]

RECEITA_CATEGORIAS = [
    "Diárias de Apartamentos",
    "Restaurante e Bar",
    "Eventos",
    "Estacionamento",
    "Outras Receitas",
]

DESPESA_CATEGORIAS = [
    "Folha de Pagamento",
    "Energia Elétrica",
    "Água e Esgoto",
    "Gás",
    "Manutenção e Reparos",
    "Marketing e Vendas",
    "Impostos e Taxas",
    "Alimentação e Bebidas",
    "Limpeza e Higiene",
    "Outras Despesas",
]

# Usado na etapa de Transformação do ETL: consolida os nomes operacionais que o
# hotel usa no dia a dia nas categorias contábeis oficiais do orçamento.
SINONIMOS_RECEITA = {
    "hospedagem": "Diárias de Apartamentos",
    "diarias": "Diárias de Apartamentos",
    "apartamentos": "Diárias de Apartamentos",
    "cafe da manha": "Restaurante e Bar",
    "restaurante": "Restaurante e Bar",
    "bar": "Restaurante e Bar",
    "a&b": "Restaurante e Bar",
    "eventos": "Eventos",
    "salas de reuniao": "Eventos",
    "estacionamento": "Estacionamento",
    "garagem": "Estacionamento",
    "lavanderia": "Outras Receitas",
    "pet fee": "Outras Receitas",
    "outras": "Outras Receitas",
}

SINONIMOS_DESPESA = {
    "folha de pagamento": "Folha de Pagamento",
    "salarios": "Folha de Pagamento",
    "energia eletrica": "Energia Elétrica",
    "energia": "Energia Elétrica",
    "luz": "Energia Elétrica",
    "agua": "Água e Esgoto",
    "agua e esgoto": "Água e Esgoto",
    "gas": "Gás",
    "manutencao": "Manutenção e Reparos",
    "manutencao e reparos": "Manutenção e Reparos",
    "marketing": "Marketing e Vendas",
    "marketing e vendas": "Marketing e Vendas",
    "impostos": "Impostos e Taxas",
    "impostos e taxas": "Impostos e Taxas",
    "seguros": "Outras Despesas",
    "internet": "Outras Despesas",
    "rouparia": "Outras Despesas",
    "alimentacao e bebidas": "Alimentação e Bebidas",
    "produtos de limpeza": "Limpeza e Higiene",
    "amenities": "Limpeza e Higiene",
    "limpeza": "Limpeza e Higiene",
    "limpeza e higiene": "Limpeza e Higiene",
    "outras": "Outras Despesas",
}

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

# Paleta validada para daltonismo nos dois temas. A cor identifica a série
# (receita/despesa) e nunca julga o valor — o juízo "dentro/fora do orçamento"
# usa as cores de status, que vêm sempre acompanhadas de rótulo escrito.
#
# Claro:  ΔE 33.6 em visão normal, 24.7 em protanopia (pisos: 15 e 8)
# Escuro: ΔE 31.8 em visão normal, 26.8 em protanopia
#
# Os tons escuros não são os claros "invertidos": são os mesmos matizes
# reposicionados para a faixa de luminosidade do fundo escuro, de modo que
# ambos mantenham no mínimo 3:1 de contraste contra a própria superfície.
PALETAS = {
    "light": {
        "receita": "#2a78d6",     # azul
        "despesa": "#eb6834",     # laranja
        "planejado": "#c3c2b7",   # referência neutra
        "texto": "#0b0b0b",
        "texto_suave": "#52514e",
        "grade": "#e1e0d9",
        "superficie": "#ffffff",
        "borda": "#e1e0d9",
        "ok": "#0ca30c",
        "atencao": "#b07a00",
        "critico": "#d03b3b",
    },
    "dark": {
        "receita": "#3987e5",
        "despesa": "#d95926",
        "planejado": "#6b6a65",   # cinza a 3.4:1 do fundo: visível sem competir
        "texto": "#ffffff",
        "texto_suave": "#c3c2b7",
        "grade": "#2c2c2a",
        "superficie": "#1a1a19",
        "borda": "#383835",
        "ok": "#0ca30c",
        "atencao": "#fab219",
        "critico": "#e66767",
    },
}


def paleta(tema: str = "light") -> dict:
    """Cores do tema informado. Qualquer valor desconhecido cai no claro."""
    return PALETAS.get(tema, PALETAS["light"])


# Atalhos do tema claro, usados pelo PDF e pelo PowerPoint — documento impresso
# não acompanha o tema da tela.
COR_RECEITA = PALETAS["light"]["receita"]
COR_DESPESA = PALETAS["light"]["despesa"]
COR_PLANEJADO = PALETAS["light"]["planejado"]
COR_TEXTO = PALETAS["light"]["texto"]
COR_TEXTO_SUAVE = PALETAS["light"]["texto_suave"]
COR_GRADE = PALETAS["light"]["grade"]
COR_SUPERFICIE = PALETAS["light"]["superficie"]
COR_OK = PALETAS["light"]["ok"]
COR_ATENCAO = PALETAS["light"]["atencao"]
COR_CRITICO = PALETAS["light"]["critico"]

# Desvio percentual a partir do qual a categoria é sinalizada no dashboard.
LIMITE_DESVIO = 10.0


def ensure_dirs() -> None:
    """Garante que a pasta de dados existe."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def mes_nome(mes: str) -> str:
    """Converte '2026-03' em 'Março/2026'."""
    try:
        ano, num = mes.split("-")
        return f"{MESES_PT[int(num) - 1]}/{ano}"
    except (ValueError, IndexError, AttributeError):
        return str(mes)


def categorias_de(tipo: str) -> list[str]:
    """Lista de categorias válidas para o tipo informado."""
    return RECEITA_CATEGORIAS if tipo == "receita" else DESPESA_CATEGORIAS


def arquivo_de(tipo: str) -> Path:
    """Arquivo CSV correspondente ao tipo de movimentação."""
    return ARQ_RECEITAS if tipo == "receita" else ARQ_DESPESAS


def sinonimos_de(tipo: str) -> dict[str, str]:
    """Mapa de normalização de categorias usado no ETL."""
    return SINONIMOS_RECEITA if tipo == "receita" else SINONIMOS_DESPESA
