import argparse
import random
import sys
from datetime import date
from pathlib import Path

from flask import Flask, redirect, render_template, request, Response, url_for

import budget
import dashboard
import models
import reports
from config import (
    DESPESA_CATEGORIAS,
    HOTEL_NOME,
    RECEITA_CATEGORIAS,
    SISTEMA_NOME,
    VERSAO,
    mes_nome,
)
from database import init_db
from utils import moeda, validar_categoria, validar_data, validar_mes, validar_tipo, validar_valor

app = Flask(__name__)
app.config["SECRET_KEY"] = "hotel-budget-manager"


def _mes_selecionado():
    mes = request.args.get("mes", "")
    if mes:
        validar_mes(mes)
        return mes
    return None


@app.template_filter("moeda")
def _moeda_filter(v):
    return moeda(v)


@app.template_filter("mes_nome")
def _mes_nome_filter(v):
    return mes_nome(v)


@app.context_processor
def inject_globals():
    return {
        "hotel_nome": HOTEL_NOME,
        "sistema_nome": SISTEMA_NOME,
        "versao": VERSAO,
        "meses_disponiveis": budget.meses_disponiveis(),
        "receita_categorias": RECEITA_CATEGORIAS,
        "despesa_categorias": DESPESA_CATEGORIAS,
    }


@app.route("/")
def pagina_dashboard():
    mes = _mes_selecionado()
    resumo = budget.resumo_mes(mes) if mes else None
    return render_template(
        "dashboard.html",
        mes=mes,
        resumo=resumo,
        grafico_serie=dashboard.serie_mensal(),
        grafico_receitas=dashboard.grafico_planejado_x_realizado("receita", mes),
        grafico_despesas=dashboard.grafico_planejado_x_realizado("despesa", mes),
        distrib_receitas=dashboard.grafico_distribuicao("receita", mes),
        distrib_despesas=dashboard.grafico_distribuicao("despesa", mes),
    )


@app.route("/orcamento", methods=["GET", "POST"])
def pagina_orcamento():
    if request.method == "POST":
        mes = validar_mes(request.form["mes"])
        for tipo in ("receita", "despesa"):
            categorias = RECEITA_CATEGORIAS if tipo == "receita" else DESPESA_CATEGORIAS
            for cat in categorias:
                campo = f"{tipo}_{cat}"
                raw = request.form.get(campo, "").strip()
                if raw:
                    models.upsert_orcamento(mes, tipo, cat, validar_valor(raw))
        return redirect(url_for("pagina_orcamento", mes=mes))
    mes = _mes_selecionado()
    orcamento = models.listar_orcamento(mes)
    planejado = {(o["tipo"], o["categoria"]): o["valor_planejado"] for o in orcamento}
    return render_template("orcamento.html", mes=mes, planejado=planejado)


@app.route("/movimentacoes/<tipo>")
def pagina_movimentacoes(tipo):
    tipo = validar_tipo(tipo)
    mes = _mes_selecionado()
    movs = models.listar_movimentacoes(tipo, mes)
    return render_template("movimentacoes.html", tipo=tipo, mes=mes, movimentacoes=movs)


@app.route("/movimentacoes/<tipo>/nova", methods=["GET", "POST"])
def nova_movimentacao(tipo):
    tipo = validar_tipo(tipo)
    erro = None
    if request.method == "POST":
        try:
            data = validar_data(request.form["data"])
            categoria = validar_categoria(tipo, request.form["categoria"])
            descricao = request.form.get("descricao", "").strip()
            valor = validar_valor(request.form["valor"])
            models.adicionar_movimentacao(tipo, data.isoformat(), categoria, descricao, valor)
            return redirect(url_for("pagina_movimentacoes", tipo=tipo, mes=data.isoformat()[:7]))
        except ValueError as e:
            erro = str(e)
    return render_template("nova_movimentacao.html", tipo=tipo, erro=erro)


@app.route("/movimentacoes/<tipo>/<int:mov_id>/excluir", methods=["POST"])
def excluir_movimentacao(tipo, mov_id):
    tipo = validar_tipo(tipo)
    models.excluir_movimentacao(tipo, mov_id)
    return redirect(request.referrer or url_for("pagina_movimentacoes", tipo=tipo))


@app.route("/relatorio")
def pagina_relatorio():
    mes = request.args.get("mes", "")
    if not mes:
        return redirect(url_for("pagina_dashboard"))
    validar_mes(mes)
    return render_template("relatorio.html", relatorio=reports.relatorio_mensal(mes))


@app.route("/csv/<tipo>")
def download_csv(tipo):
    tipo = validar_tipo(tipo)
    mes = _mes_selecionado()
    buf = reports.gerar_csv_movimentacoes(tipo, mes)
    nome = f"{tipo}_{mes or 'todos'}.csv"
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nome}"},
    )


def seed_dados():
    if models.listar_movimentacoes("receita"):
        print("Banco já possui dados. Seed ignorado.")
        return
    rnd = random.Random(42)
    for ano, mes_num in [(2026, m) for m in range(1, 9)]:
        mes = f"{ano}-{mes_num:02d}"
        for cat in RECEITA_CATEGORIAS:
            planejado = {
                "Diárias de Apartamentos": 520000,
                "Restaurante e Bar": 90000,
                "Eventos": 40000,
                "Estacionamento": 15000,
                "Outras Receitas": 5000,
            }.get(cat, 10000)
            models.upsert_orcamento(mes, "receita", cat, planejado)
        for cat in DESPESA_CATEGORIAS:
            planejado = {
                "Folha de Pagamento": 180000,
                "Energia Elétrica": 45000,
                "Água e Esgoto": 20000,
                "Gás": 12000,
                "Manutenção e Reparos": 30000,
                "Marketing e Vendas": 25000,
                "Impostos e Taxas": 60000,
                "Alimentação e Bebidas": 35000,
                "Limpeza e Higiene": 15000,
                "Outras Despesas": 10000,
            }.get(cat, 15000)
            models.upsert_orcamento(mes, "despesa", cat, planejado)
        for cat in RECEITA_CATEGORIAS:
            for _ in range(rnd.randint(3, 8)):
                dia = rnd.randint(1, 28)
                valor = round(rnd.uniform(1500, 9000) * (1.0 if cat == "Diárias de Apartamentos" else 0.5), 2)
                models.adicionar_movimentacao(
                    "receita", f"{mes}-{dia:02d}", cat, "Lançamento de teste", valor
                )
        for cat in DESPESA_CATEGORIAS:
            for _ in range(rnd.randint(1, 5)):
                dia = rnd.randint(1, 28)
                valor = round(rnd.uniform(800, 6000), 2)
                models.adicionar_movimentacao(
                    "despesa", f"{mes}-{dia:02d}", cat, "Lançamento de teste", valor
                )
    print("Dados de exemplo inseridos para jan/2026 a ago/2026.")


def main():
    parser = argparse.ArgumentParser(description=SISTEMA_NOME)
    parser.add_argument("--seed", action="store_true", help="Insere dados de exemplo")
    parser.add_argument("--port", type=int, default=5000, help="Porta do servidor")
    parser.add_argument("--host", default="127.0.0.1", help="Host do servidor")
    args = parser.parse_args()

    init_db()
    if args.seed:
        seed_dados()

    print(f"[+] {SISTEMA_NOME} v{VERSAO} - {HOTEL_NOME}")
    print(f"    Banco: {Path(reports.__file__).parent / 'data' / 'hotel.db'}")
    print(f"    Acesse: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
