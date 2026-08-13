"""Funções auxiliares: validação de entrada e formatação de saída."""

import re
import unicodedata
from datetime import date, datetime

from config import categorias_de


def sem_acento(texto: str) -> str:
    """Remove acentos e normaliza para minúsculas ('Gás' -> 'gas')."""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.strip().lower()


def validar_data(valor) -> date:
    """Aceita date ou string AAAA-MM-DD e devolve um objeto date."""
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    if isinstance(valor, datetime):
        return valor.date()
    try:
        return datetime.strptime(str(valor).strip()[:10], "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Data inválida. Use o formato AAAA-MM-DD.") from exc


def validar_valor(valor) -> float:
    """Aceita '1.234,56', '1234.56' ou float e devolve float positivo."""
    if isinstance(valor, (int, float)):
        v = float(valor)
    else:
        bruto = str(valor).strip().replace("R$", "").replace(" ", "")
        # Formato brasileiro: ponto separa milhar, vírgula separa decimal.
        if "," in bruto:
            bruto = bruto.replace(".", "").replace(",", ".")
        try:
            v = float(bruto)
        except ValueError as exc:
            raise ValueError(f"Valor inválido: {valor!r}") from exc
    if v <= 0:
        raise ValueError("O valor deve ser maior que zero.")
    return round(v, 2)


def validar_tipo(tipo: str) -> str:
    """Garante que o tipo é 'receita' ou 'despesa'."""
    tipo = str(tipo).strip().lower()
    if tipo not in ("receita", "despesa"):
        raise ValueError("Tipo inválido. Use 'receita' ou 'despesa'.")
    return tipo


def validar_categoria(tipo: str, categoria: str) -> str:
    """Garante que a categoria pertence ao tipo informado."""
    categoria = str(categoria).strip()
    if not categoria:
        raise ValueError("Informe uma categoria.")
    validas = categorias_de(validar_tipo(tipo))
    if categoria not in validas:
        raise ValueError(f"Categoria '{categoria}' não é válida para {tipo}.")
    return categoria


def validar_mes(mes: str) -> str:
    """Garante o formato AAAA-MM com mês entre 01 e 12."""
    mes = str(mes).strip()
    if not re.fullmatch(r"\d{4}-\d{2}", mes):
        raise ValueError("Mês inválido. Use o formato AAAA-MM.")
    if not 1 <= int(mes.split("-")[1]) <= 12:
        raise ValueError("Mês inválido. Deve estar entre 01 e 12.")
    return mes


def validar_descricao(descricao: str, limite: int = 120) -> str:
    """Limpa a descrição e limita o tamanho."""
    return " ".join(str(descricao or "").split())[:limite]


def moeda(valor: float) -> str:
    """Formata no padrão brasileiro: R$ 1.234,56."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "R$ 0,00"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def percentual(parte: float, total: float) -> float:
    """Percentual protegido contra divisão por zero."""
    if not total:
        return 0.0
    return (float(parte) / float(total)) * 100
