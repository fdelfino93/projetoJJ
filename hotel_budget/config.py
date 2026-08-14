"""Constantes e configurações do Hotel Budget Manager."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ARQ_RECEITAS = DATA_DIR / "receitas.csv"
ARQ_DESPESAS = DATA_DIR / "despesas.csv"
ARQ_ORCAMENTO = DATA_DIR / "orcamento.csv"
ARQ_OPERACAO = DATA_DIR / "operacao.csv"

HOTEL_NOME = "Ibis Styles Curitiba Centro Cívico"
SISTEMA_NOME = "Gerente de Orçamento de Hotel"
VERSAO = "2.0"

TIPOS = ["receita", "despesa"]

COLUNAS_MOVIMENTACAO = ["id", "data", "categoria", "descricao", "valor"]
COLUNAS_ORCAMENTO = ["mes", "tipo", "categoria", "valor_planejado"]
# Relatório diário do OPERA (NA02 - Manager Report Gross): uma linha por
# métrica por dia. "hoje/mtd/ytd" são o valor do dia, do mês e do ano
# acumulados; o sufixo "_ant" é o mesmo período do ano anterior.
COLUNAS_OPERACAO = ["data", "indicador", "hoje", "mtd", "ytd", "hoje_ant", "mtd_ant", "ytd_ant"]

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

# Tradução das métricas do relatório diário do OPERA (NA02 - Manager Report
# Gross) para o português do Brasil. As chaves são os nomes originais do
# relatório em inglês; o `importa_pdf` as normaliza (caixa baixa, espaços
# simples e sem vírgulas) antes de consultar este catálogo.
INDICADORES_OPERACAO = {
    "Total Rooms in Hotel": "Total de quartos do hotel",
    "Rooms Occupied": "Quartos ocupados",
    "Total Rooms in Hotel minus OOO Rooms": "Total de quartos menos fora de ordem (OOO)",
    "Available Rooms": "Quartos disponíveis",
    "Available Rooms minus OOO Rooms": "Quartos disponíveis menos OOO",
    "Complimentary Rooms": "Quartos de cortesia",
    "House Use Rooms": "Quartos de uso interno",
    "Rooms Occupied minus Comp and House Use": "Quartos ocupados menos cortesia e uso interno",
    "Rooms Occupied minus House Use": "Quartos ocupados menos uso interno",
    "Rooms Occupied minus Comp": "Quartos ocupados menos cortesia",
    "Day Use Rooms": "Quartos de day use",
    "Out of Order Rooms": "Quartos fora de ordem (OOO)",
    "Out of Service Rooms": "Quartos fora de serviço (OOS)",
    "In-House Adults": "Adultos no hotel",
    "In-House Children": "Crianças no hotel",
    "Total In-House Persons": "Total de pessoas no hotel",
    "Individual Persons In-House": "Pessoas avulsas no hotel",
    "Block Persons In-House": "Pessoas de blocos no hotel",
    "Member Persons In-House": "Pessoas de membros no hotel",
    "VIP Persons In-House": "Pessoas VIP no hotel",
    "Individual Rooms In-House": "Quartos avulsos no hotel",
    "Block Rooms In-House": "Quartos de blocos no hotel",
    "Source Rooms In-House": "Quartos por fonte no hotel",
    "Company Rooms In-House": "Quartos corporativos no hotel",
    "Travel Agent Rooms In-House": "Quartos de agência no hotel",
    "Group Rooms In-House": "Quartos de grupos no hotel",
    "Blocks In-House": "Blocos no hotel",
    "Birthdays In-House": "Aniversariantes no hotel",
    "% Rooms Occupied": "Taxa de ocupação",
    "% Rooms Occupied minus Comp and House": "Ocupação menos cortesia e uso interno",
    "% Rooms Occupied minus Comp, House and OOO": "Ocupação menos cortesia, uso interno e OOO",
    "% Rooms Occupied minus Comp": "Ocupação menos cortesia",
    "% Rooms Occupied minus House": "Ocupação menos uso interno",
    "% Rooms Occupied minus Comp and OOO": "Ocupação menos cortesia e OOO",
    "% Rooms Occupied minus House and OOO": "Ocupação menos uso interno e OOO",
    "% Rooms Occupied minus OOO": "Ocupação menos OOO",
    "Arrival Rooms": "Quartos em chegada",
    "Arrival Persons": "Pessoas em chegada",
    "Deducted Arrivals": "Chegadas deduzidas",
    "Non-Deducted Arrivals": "Chegadas não deduzidas",
    "Walk-in Rooms": "Quartos walk-in",
    "Walk-in Persons": "Pessoas walk-in",
    "Extended Departure Rooms": "Quartos com saída estendida",
    "Extended Departure Persons": "Pessoas com saída estendida",
    "Departure Rooms": "Quartos em saída",
    "Departure Persons": "Pessoas em saída",
    "Early Departure Rooms": "Quartos com saída antecipada",
    "Early Departure Persons": "Pessoas com saída antecipada",
    "Individual Departure Rooms": "Quartos avulsos em saída",
    "Individual Departure Persons": "Pessoas avulsas em saída",
    "Individual Member Departure Rooms": "Quartos de membro avulso em saída",
    "Individual Member Departure Persons": "Pessoas de membro avulso em saída",
    "% Individual Member Departures": "Saídas de membros avulsos (%)",
    "Member Departure Rooms": "Quartos de membros em saída",
    "Member Departure Persons": "Pessoas de membros em saída",
    "% Member Departures": "Saídas de membros (%)",
    "No Show Rooms": "Quartos no-show",
    "No Show Persons": "Pessoas no-show",
    "Cancelled Reservations for Today": "Reservas canceladas hoje",
    "Late Reservation Cancellations for Today": "Cancelamentos tardios de reserva hoje",
    "Reservations Made Today": "Reservas feitas hoje",
    "Reservation Cancellations made Today": "Cancelamentos de reservas feitos hoje",
    "Room Nights Reserved Today": "Diárias reservadas hoje",
    "Today's Demand": "Demanda de hoje",
    "Clean Rooms": "Quartos limpos",
    "Dirty Rooms": "Quartos sujos",
    "Doubles As Singles": "Duplos vendidos como single",
    "% Beds Occupied": "Taxa de camas ocupadas",
    "ADR": "Diária média (ADR)",
    "ADR minus Comp": "Diária média menos cortesia",
    "ADR minus House": "Diária média menos uso interno",
    "ADR minus Comp and House": "Diária média menos cortesia e uso interno",
    "Average Person Rate": "Tarifa média por pessoa",
    "Average Persons per Block Rooms": "Média de pessoas por bloco",
    "Average Revenue per Block Rooms": "Receita média por bloco",
    "Average Room Revenue per Block Rooms": "Receita média de diárias por bloco",
    "Room Revenue": "Receita de diárias",
    "Food And Beverage Revenue": "Receita de alimentação e bebidas",
    "Other Revenue": "Outras receitas",
    "Total Revenue": "Receita total",
    "Block Revenue": "Receita de blocos",
    "Block Room Revenue": "Receita de diárias de blocos",
    "Individual Revenue": "Receita de avulsos",
    "Individual Room Revenue": "Receita de diárias de avulsos",
    "Member Revenue": "Receita de membros",
    "Member Room Revenue": "Receita de diárias de membros",
    "Total Revenue per Person": "Receita total por pessoa",
    "Payment": "Recebimentos",
    "Maximum Revenue": "Receita máxima",
    "Maximum Revenue for Rooms Occupied": "Receita máxima por quarto ocupado",
    "Maximum Revenue %": "Receita máxima (%)",
    "Maximum Revenue % per Rooms Occupied": "Receita máxima por quarto ocupado (%)",
    "Arrival Rooms for Tomorrow": "Quartos em chegada amanhã",
    "Arrival Persons for Tomorrow": "Pessoas em chegada amanhã",
    "Departure Rooms for Tomorrow": "Quartos em saída amanhã",
    "Departure Persons for Tomorrow": "Pessoas em saída amanhã",
    "% Rooms Occupied for Tomorrow": "Ocupação prevista para amanhã",
    "% Multiple Occupancy": "Ocupação múltipla (%)",
    "% Rooms Occupied for the Next 7 Days": "Ocupação prevista para os próximos 7 dias",
    "REVPAR": "Receita por quarto disponível (RevPAR)",
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
