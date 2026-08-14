# Gerente de Orçamento de Hotel

Sistema de planejamento orçamentário do **Hotel Ibis Styles Curitiba Centro Cívico**.

Cadastra receitas e despesas, guarda tudo em arquivos CSV, aplica um processo
ETL de limpeza, analisa os dados com Pandas e apresenta o resultado em um
dashboard interativo feito em Streamlit.

O código da aplicação fica na pasta `hotel_budget/`.

---

## Como executar

```bash
cd hotel_budget
pip install -r requirements.txt
python seed.py            # opcional: gera 12 meses de dados de exemplo
streamlit run app.py
```

A aplicação abre em <http://localhost:8501>.

---

## Importação diária do relatório do OPERA

O hotel exporta do PMS (Opera) o relatório **NA02 - Manager Report Gross** uma
vez por dia (`manrepTT.PDF`). Ele entra no banco de dados de forma padronizada:

```bash
cd hotel_budget
python importa_pdf.py manrepTT.PDF
```

O comando extrai as métricas do PDF, traduz o nome de cada uma para o português
do Brasil e grava em `data/operacao.csv`, no formato **uma linha por métrica por
dia**. Para cada métrica são guardados o valor do dia, do mês acumulado e do ano
acumulado, tanto do ano atual quanto do ano anterior.

A importação é **idempotente**: rodar de novo o mesmo arquivo substitui os
registros daquele dia em vez de duplicá-los — pode ser executada diariamente sem
cuidado. Métricas novas (que o relatório passe a exibir e ainda não tenham
tradução no catálogo `config.INDICADORES_OPERACAO`) são listadas como aviso no
fim da execução.

Para agendar a importação automática diária no Windows, basta criar uma tarefa
no Agendador de Tarefas que rode `python importa_pdf.py` na pasta do projeto.

---

## Estrutura

```text
README.md
hotel_budget/
    app.py            interface Streamlit (5 páginas)
    cadastro.py       inclusão, alteração e exclusão nos CSV
    etl.py            extração, transformação e carga
    analise.py        análises com Pandas (totais, comparativos, projeção)
    graficos.py       Plotly (tela) e Matplotlib (PDF/PPTX)
    exports.py        geração de CSV, PDF e PowerPoint
    utils.py          validações e formatação
    config.py         categorias, cores, caminhos e traduções das métricas
    seed.py           gerador de dados de exemplo
    importa_pdf.py    importador diário do relatório do OPERA (NA02)
    data/
        receitas.csv
        despesas.csv
        orcamento.csv
        operacao.csv   indicadores diários importados do OPERA
    requirements.txt
```

O fluxo de dependências é de mão única, sem importações circulares:

```text
config / utils  →  etl  →  cadastro
                    ↓
                 analise  →  graficos  →  exports  →  app
```

---

## Páginas

| Página | O que faz |
|---|---|
| **Painel** | Indicadores do período, evolução mensal, resultado por mês, ranking de categorias e comparativo planejado x realizado |
| **Movimentações** | Tabela editável de receitas e despesas, com exportação em PDF |
| **Orçamento** | Definição do valor previsto por categoria, com cópia entre meses e reajuste percentual |
| **Relatório Mensal** | Comparativo detalhado, pontos de atenção, projeção de fechamento e exportação em CSV, PDF e PowerPoint |
| **Qualidade de Dados** | Registro das correções que o ETL aplicou na última leitura dos CSV |

### Editando lançamentos

A página de Movimentações é uma grade editável. O `Nº` é gerado pelo sistema e
fica bloqueado; Data, Categoria (lista fechada), Descrição e Valor são
editáveis. A linha em branco no fim inclui um novo lançamento e a tecla Delete
remove a linha selecionada.

Nada é gravado antes de o usuário clicar em **Salvar alterações**, e cada linha
passa pelas validações do `utils` na gravação — uma linha inválida é recusada
com aviso, sem impedir que as demais sejam salvas.

### Tema claro e escuro

O usuário escolhe em **⋮ › Settings › Appearance**, entre Light, Dark e a
preferência do sistema. As duas paletas estão em `config.PALETAS` e os gráficos
trocam de cor junto com a interface, lendo `st.context.theme`.

Os tons escuros não são os claros invertidos: são os mesmos matizes
reposicionados para a faixa de luminosidade do fundo escuro, de modo que ambos
mantenham no mínimo 3:1 de contraste contra a própria superfície. Os dois
conjuntos passam nos mesmos testes de daltonismo (ΔE 33,6 claro e 31,8 escuro em
visão normal; 24,7 e 26,8 em protanopia).

---

## O processo ETL

Nenhum módulo lê os CSV diretamente — toda leitura passa por `etl.py`, de modo
que os dados analisados são sempre os dados tratados.

**Extração.** Leitura dos três CSV com Pandas. Arquivo ausente ou vazio devolve
um DataFrame com as colunas esperadas, em vez de quebrar a aplicação.

**Transformação.**

1. Remoção de linhas vazias — sem data, categoria ou valor.
2. Conversão dos valores para numérico, aceitando o formato brasileiro
   (`R$ 1.234,56`) e descartando o que não for número positivo.
3. Conversão e validação das datas no formato `AAAA-MM-DD`.
4. Organização das categorias: o mapa de sinônimos em `config.py` consolida os
   nomes usados no dia a dia do hotel nas categorias contábeis oficiais
   (`Hospedagem` → `Diárias de Apartamentos`, `Amenities` → `Limpeza e Higiene`),
   e corrige diferenças de acento e de caixa.
5. Remoção de duplicados — mesma data, categoria, descrição e valor.
6. Criação das colunas derivadas `mes` e `tipo`, usadas nas análises.

**Carga.** Os DataFrames tratados alimentam análises, gráficos e exportações. O
resultado fica em cache, chaveado pela data de modificação dos arquivos: o ETL
só roda de novo quando algum CSV muda.

A página **Qualidade dos Dados** mostra o relatório de cada execução — quantas
linhas entraram, quantas foram descartadas e por qual critério.

Os indicadores diários do OPERA (`operacao.csv`) passam pelo mesmo processo pela
função `etl.carregar_operacao()` — a tradução das métricas acontece na
importação, e a leitura do CSV continua sempre tratada pelo ETL.

---

## Decisões de projeto

**Por que barras em vez de pizza.** Comparar comprimentos é mais preciso do que
comparar ângulos, e dez fatias de despesa seriam ilegíveis. O ranking horizontal
mostra o valor e a participação percentual ao mesmo tempo.

**Por que azul e laranja, e não verde e vermelho.** A cor identifica a série
(receita ou despesa) e não julga o valor. As paletas foram validadas para
daltonismo contra um piso de ΔE 15 em visão normal e 8 sob simulação. O
julgamento "dentro ou fora do orçamento" usa cores de status separadas, sempre
acompanhadas de rótulo escrito — a cor nunca é o único canal de informação.

**Por que duas bibliotecas de gráficos.** Plotly dá interatividade na tela
(tooltip, zoom, legenda clicável); Matplotlib gera as imagens estáticas
embutidas no PDF e no PowerPoint. As duas leem os mesmos dados de `analise.py`.

**Por que a exportação tem dois cliques.** O `st.download_button` do Streamlit
exige os bytes prontos no momento em que é desenhado, o que remontaria o arquivo
a cada interação da página. Gerar sob demanda e só então oferecer o download
mantém a navegação instantânea.

---

## Conceitos da disciplina aplicados

Variáveis, condicionais, laços `for`, funções, listas, dicionários, manipulação
de arquivos CSV, Pandas, processo ETL, visualização de dados e modularização.
