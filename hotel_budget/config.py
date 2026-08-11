from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_IMG_DIR = BASE_DIR / "static" / "img"
DATABASE = DATA_DIR / "hotel.db"

HOTEL_NOME = "Ibis Styles Curitiba Centro Cívico"
SISTEMA_NOME = "Hotel Budget Manager"
VERSAO = "1.0"

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

TIPOS = ["receita", "despesa"]

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_IMG_DIR.mkdir(parents=True, exist_ok=True)


def mes_nome(mes: str) -> str:
    try:
        ano, num = mes.split("-")
        return f"{MESES_PT[int(num) - 1]}/{ano}"
    except (ValueError, IndexError):
        return mes
