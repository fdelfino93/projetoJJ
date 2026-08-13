"""Gera dados de exemplo para demonstração do sistema.

Uso:
    python seed.py            # cria os CSV se ainda não existirem
    python seed.py --forcar   # recria os CSV do zero

Os valores são sorteados em torno do orçamento planejado, com sazonalidade
mensal, para que a demonstração mostre desvios plausíveis de um hotel real —
alguns meses acima do previsto, outros abaixo.
"""

import argparse
import calendar
import csv
import random

from config import (
    ARQ_ORCAMENTO,
    COLUNAS_MOVIMENTACAO,
    COLUNAS_ORCAMENTO,
    DESPESA_CATEGORIAS,
    RECEITA_CATEGORIAS,
    arquivo_de,
    ensure_dirs,
)
from etl import ENCODING

# Orçamento mensal do hotel, em reais.
PLANEJADO_RECEITA = {
    "Diárias de Apartamentos": 520_000,
    "Restaurante e Bar": 90_000,
    "Eventos": 40_000,
    "Estacionamento": 15_000,
    "Outras Receitas": 5_000,
}

PLANEJADO_DESPESA = {
    "Folha de Pagamento": 180_000,
    "Energia Elétrica": 45_000,
    "Água e Esgoto": 20_000,
    "Gás": 12_000,
    "Manutenção e Reparos": 30_000,
    "Marketing e Vendas": 25_000,
    "Impostos e Taxas": 60_000,
    "Alimentação e Bebidas": 35_000,
    "Limpeza e Higiene": 15_000,
    "Outras Despesas": 10_000,
}

# Sazonalidade de Curitiba: janeiro e julho fracos (férias), março a maio e
# setembro a novembro fortes (feiras, eventos e viagens corporativas).
SAZONALIDADE = {
    1: 0.82, 2: 0.90, 3: 1.08, 4: 1.12, 5: 1.06, 6: 0.95,
    7: 0.88, 8: 1.02, 9: 1.10, 10: 1.14, 11: 1.05, 12: 0.86,
}

DESCRICOES = {
    "Diárias de Apartamentos": ["Diárias balcão", "Reserva corporativa", "Reserva OTA", "Grupo/convênio"],
    "Restaurante e Bar": ["Café da manhã", "Almoço executivo", "Consumo do bar", "Room service"],
    "Eventos": ["Sala de reunião", "Coffee break", "Evento corporativo", "Locação de auditório"],
    "Estacionamento": ["Diária de garagem", "Mensalista", "Rotativo"],
    "Outras Receitas": ["Lavanderia de hóspede", "Pet fee", "Late check-out", "Frigobar"],
    "Folha de Pagamento": ["Salários", "Encargos sociais", "Horas extras", "Vale-transporte"],
    "Energia Elétrica": ["Fatura Copel", "Demanda contratada"],
    "Água e Esgoto": ["Fatura Sanepar"],
    "Gás": ["Recarga de GLP", "Gás da cozinha"],
    "Manutenção e Reparos": ["Manutenção de elevador", "Ar-condicionado", "Hidráulica", "Pintura"],
    "Marketing e Vendas": ["Comissão de OTA", "Mídia paga", "Material promocional"],
    "Impostos e Taxas": ["ISS", "PIS/COFINS", "IPTU", "Taxa de bombeiros"],
    "Alimentação e Bebidas": ["Hortifrúti", "Carnes e frios", "Bebidas", "Panificação"],
    "Limpeza e Higiene": ["Produtos de limpeza", "Amenities", "Enxoval e rouparia"],
    "Outras Despesas": ["Internet e telefonia", "Seguro predial", "Material de escritório"],
}


def _lancamentos(rnd, ano, mes, categoria, planejado, fator):
    """Distribui o total do mês em lançamentos diários plausíveis."""
    # Desvio de -18% a +12% sobre o planejado, já com a sazonalidade aplicada.
    total = planejado * fator * rnd.uniform(0.82, 1.12)
    quantidade = rnd.randint(6, 14)
    dias_no_mes = calendar.monthrange(ano, mes)[1]

    pesos = [rnd.uniform(0.5, 1.5) for _ in range(quantidade)]
    soma = sum(pesos)
    for peso in pesos:
        dia = rnd.randint(1, dias_no_mes)
        yield (
            f"{ano}-{mes:02d}-{dia:02d}",
            categoria,
            rnd.choice(DESCRICOES[categoria]),
            round(total * peso / soma, 2),
        )


def gerar(ano_inicial: int, meses: int, semente: int = 42):
    """Constrói as três tabelas de exemplo em memória."""
    rnd = random.Random(semente)
    receitas, despesas, orcamento = [], [], []
    proximo_id = {"receita": 1, "despesa": 1}

    for deslocamento in range(meses):
        ano = ano_inicial + (deslocamento // 12)
        mes = (deslocamento % 12) + 1
        fator = SAZONALIDADE[mes]

        for tipo, categorias, planejamento, destino in (
            ("receita", RECEITA_CATEGORIAS, PLANEJADO_RECEITA, receitas),
            ("despesa", DESPESA_CATEGORIAS, PLANEJADO_DESPESA, despesas),
        ):
            for categoria in categorias:
                planejado = planejamento[categoria]
                orcamento.append([f"{ano}-{mes:02d}", tipo, categoria, f"{planejado:.2f}"])
                # Despesa fixa (folha, impostos) varia pouco com a ocupação.
                fator_categoria = 1.0 if categoria in ("Folha de Pagamento", "Impostos e Taxas") else fator
                for data, cat, descricao, valor in _lancamentos(rnd, ano, mes, categoria, planejado, fator_categoria):
                    destino.append([proximo_id[tipo], data, cat, descricao, f"{valor:.2f}"])
                    proximo_id[tipo] += 1

    return receitas, despesas, orcamento


def _gravar(caminho, cabecalho, linhas):
    """Escreve uma tabela em CSV."""
    with open(caminho, "w", encoding=ENCODING, newline="") as arquivo:
        escritor = csv.writer(arquivo, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        escritor.writerow(cabecalho)
        escritor.writerows(linhas)


def main() -> None:
    """Grava os arquivos de exemplo em data/."""
    parser = argparse.ArgumentParser(description="Gera dados de exemplo do Hotel Budget Manager")
    parser.add_argument("--forcar", action="store_true", help="sobrescreve os arquivos existentes")
    parser.add_argument("--ano", type=int, default=2026, help="ano inicial (padrão: 2026)")
    parser.add_argument("--meses", type=int, default=12, help="quantidade de meses (padrão: 12)")
    args = parser.parse_args()

    ensure_dirs()
    existentes = [c for c in (arquivo_de("receita"), arquivo_de("despesa"), ARQ_ORCAMENTO) if c.exists()]
    if existentes and not args.forcar:
        print("Os arquivos abaixo já existem. Use --forcar para sobrescrever:")
        for caminho in existentes:
            print(f"  {caminho}")
        return

    receitas, despesas, orcamento = gerar(args.ano, args.meses)
    _gravar(arquivo_de("receita"), COLUNAS_MOVIMENTACAO, receitas)
    _gravar(arquivo_de("despesa"), COLUNAS_MOVIMENTACAO, despesas)
    _gravar(ARQ_ORCAMENTO, COLUNAS_ORCAMENTO, orcamento)

    print(f"Receitas geradas ..... {len(receitas)}")
    print(f"Despesas geradas ..... {len(despesas)}")
    print(f"Orçamento gerado ..... {len(orcamento)} linhas")
    print(f"Período .............. {args.meses} meses a partir de {args.ano}-01")


if __name__ == "__main__":
    main()
