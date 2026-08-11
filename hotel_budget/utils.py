import re
from datetime import date, datetime

from config import RECEITA_CATEGORIAS, DESPESA_CATEGORIAS


def validar_data(valor: str) -> date:
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Data inválida. Use o formato AAAA-MM-DD.")


def validar_valor(valor) -> float:
    try:
        v = float(str(valor).replace(",", ".").strip())
    except ValueError:
        raise ValueError("Valor inválido.")
    if v < 0:
        raise ValueError("O valor não pode ser negativo.")
    return v


def validar_categoria(tipo: str, categoria: str) -> str:
    if not categoria.strip():
        raise ValueError("Informe uma categoria.")
    categorias = RECEITA_CATEGORIAS if tipo == "receita" else DESPESA_CATEGORIAS
    if categoria not in categorias:
        raise ValueError(f"Categoria '{categoria}' inválida para {tipo}.")
    return categoria


def validar_tipo(tipo: str) -> str:
    if tipo not in ("receita", "despesa"):
        raise ValueError("Tipo inválido. Use 'receita' ou 'despesa'.")
    return tipo


def validar_mes(mes: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}", mes):
        raise ValueError("Mês inválido. Use o formato AAAA-MM.")
    ano, num = mes.split("-")
    if not 1 <= int(num) <= 12:
        raise ValueError("Mês inválido. Deve ser entre 01 e 12.")
    return mes


def moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
