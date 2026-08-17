# Product Requirements Document (PRD)

# Hotel Budget Manager
## Sistema de Planejamento Orçamentário do Ibis Styles Curitiba Centro Cívico

**Versão:** 2.0  
**Disciplina:** Python Básico  
**Equipe:** Nome dos integrantes

---

# 1. Visão Geral

O **Hotel Budget Manager** é um sistema desenvolvido em Python com o objetivo de auxiliar o gerente financeiro do Hotel Ibis Styles Curitiba Centro Cívico no planejamento e controle do orçamento mensal.

A aplicação cadastra receitas e despesas, organiza os dados financeiros em arquivos CSV, realiza análises com Pandas, importa indicadores operacionais do PMS (Opera) e apresenta gráficos interativos em um dashboard Streamlit com suporte a exportação em Excel, PDF e PowerPoint.

---

# 2. Problema

O controle financeiro realizado manualmente pode dificultar a organização das informações e tornar a análise dos resultados mais demorada.

O sistema centraliza os dados financeiros em um único ambiente, permitindo uma visualização clara das receitas, despesas, do resultado financeiro e dos indicadores operacionais do hotel.

---

# 3. Objetivo

Desenvolver uma aplicação em Python que permita:

- Cadastrar receitas e despesas com validação completa;
- Armazenar os dados em arquivos CSV com codificação UTF-8;
- Importar automaticamente o relatório diário do OPERA (PDF);
- Aplicar um processo ETL completo com relatório de qualidade;
- Analisar os dados com Pandas (totais, comparativos, projeções);
- Gerar gráficos interativos (Plotly) e estáticos (Matplotlib);
- Exportar relatórios em Excel, PDF e PowerPoint;
- Suportar temas claro e escuro com paletas validadas para daltonismo.

---

# 4. Público-Alvo

- Gerente Financeiro do hotel;
- Administração do Hotel Ibis Styles Curitiba Centro Cívico.

---

# 5. Tecnologias

| Tecnologia | Uso |
|---|---|
| **Python** | Desenvolvimento da aplicação |
| **Pandas** | Manipulação e análise dos dados |
| **Streamlit** | Interface interativa (dashboard) |
| **Plotly** | Gráficos interativos na tela |
| **Matplotlib** | Gráficos estáticos para exportação |
| **ReportLab** | Geração de PDF |
| **python-pptx** | Geração de PowerPoint |
| **xlsxwriter** | Geração de Excel |
| **pdfplumber** | Extração de dados do PDF do OPERA |
| **Arquivos CSV** | Armazenamento das informações |

---

# 6. Funcionalidades

## 6.1 Cadastro de Receitas

Categorias oficiais:
- Diárias de Apartamentos
- Restaurante e Bar
- Eventos
- Estacionamento
- Outras Receitas

O sistema aceita sinônimos operacionais (ex: "Hospedagem" → "Diárias de Apartamentos", "Café da manhã" → "Restaurante e Bar") e normaliza automaticamente via ETL.

## 6.2 Cadastro de Despesas

Categorias oficiais:
- Folha de Pagamento
- Energia Elétrica
- Água e Esgoto
- Gás
- Manutenção e Reparos
- Marketing e Vendas
- Impostos e Taxas
- Alimentação e Bebidas
- Limpeza e Higiene
- Outras Despesas

## 6.3 Controle Orçamentário

- Definição do valor previsto por categoria em cada mês;
- Cópia de orçamento entre meses com reajuste percentual;
- Comparativo planejado x realizado com indicadores de situação (ok, atenção, crítico).

## 6.4 Importação do OPERA

- Importação diária do relatório NA02 (Manager Report Gross) em PDF;
- Tradução automática de ~100 métricas do inglês para o português;
- Formato: uma linha por métrica por dia, com valores do dia, mês acumulado e ano acumulado;
- Importação idempotente (nunca duplica registros).

## 6.5 Dashboard Interativo (Streamlit)

| Página | O que faz |
|---|---|
| **Painel** | Indicadores do período, evolução mensal, resultado por mês, ranking de categorias e comparativo planejado x realizado |
| **Movimentações** | Tabela editável de receitas e despesas, com exportação em PDF |
| **Orçamento** | Definição do valor previsto por categoria, com cópia entre meses e reajuste percentual |
| **Relatório Mensal** | Comparativo detalhado, pontos de atenção, projeção de fechamento e exportação em CSV, Excel, PDF e PowerPoint |
| **Qualidade de Dados** | Registro das correções que o ETL aplicou na última leitura dos CSV |

## 6.6 Exportações

- **Excel** (.xlsx): relatório mensal com abas Resumo, Receitas, Despesas e Lançamentos;
- **PDF**: relatório mensal com resumo, alertas, tabelas e gráficos estáticos;
- **PowerPoint**: apresentação do fechamento mensal (relatório completo e versão executiva);
- **CSV**: movimentações e relatório mensal em formato separado por ponto e vírgula.

## 6.7 Tema Claro e Escuro

- Escolha via ⋮ › Settings › Appearance no Streamlit;
- Paletas validadas para daltonismo (ΔE > 15 em visão normal, > 8 em protanopia);
- Contraste mínimo de 3:1 contra a superfície;
- Gráficos Plotly acompanham o tema automaticamente.

---

# 7. Processo ETL

## Extração

Leitura dos arquivos CSV utilizando Pandas. Arquivo ausente ou vazio devolve um DataFrame vazio com as colunas esperadas.

## Transformação

1. Remoção de linhas vazias (sem data, categoria ou valor);
2. Conversão de valores para formato numérico (aceita formato brasileiro `R$ 1.234,56`);
3. Conversão e validação de datas no formato `AAAA-MM-DD`;
4. Normalização de categorias via mapa de sinônimos e correção de acentos;
5. Remoção de registros duplicados;
6. Criação de colunas derivadas (`mes`, `tipo`).

## Carga

Os dados tratados são alimentados em cache (chaveado por data de modificação dos arquivos) e consumidos por análises, gráficos e exportações.

## Relatório de Qualidade

A página "Qualidade dos Dados" exibe:
- Total de linhas lidas, carregadas e descartadas;
- Detalhamento por critério (vazias, duplicadas, valores inválidos, datas inválidas, categorias não reconhecidas).

---

# 8. Estrutura do Projeto

```text
hotel_budget/
├── app.py              Interface Streamlit (5 páginas)
├── cadastro.py         Inclusão, alteração e exclusão nos CSV
├── etl.py              Extração, Transformação e Carga
├── analise.py          Análises com Pandas
├── graficos.py         Plotly (tela) e Matplotlib (PDF/PPTX)
├── exports.py          Geração de Excel, PDF e PowerPoint
├── utils.py            Validações e formatação
├── config.py           Categorias, cores, caminhos e traduções
├── seed.py             Gerador de dados de exemplo
├── importa_pdf.py      Importador do relatório OPERA
├── data/
│   ├── receitas.csv
│   ├── despesas.csv
│   ├── orcamento.csv
│   └── operacao.csv
├── .streamlit/
│   └── config.toml
├── requirements.txt
└── README.md
```

---

# 9. Fluxo de Dependências

```text
config / utils  →  etl  →  cadastro
                    ↓
                 analise  →  graficos  →  exports  →  app
```

Fluxo de mão única, sem importações circulares.

---

# 10. Recursos do Curso Aplicados

- Variáveis;
- Estruturas condicionais (`if`);
- Estruturas de repetição (`for` e `while`);
- Funções;
- Listas;
- Dicionários;
- Manipulação de arquivos CSV;
- Pandas;
- ETL;
- Visualização de Dados;
- Modularização do código.

---

# 11. Critérios de Sucesso

O projeto é considerado concluído quando for possível:

- [x] Cadastrar receitas e despesas com validação;
- [x] Armazenar os dados em arquivos CSV;
- [x] Ler os dados utilizando Pandas;
- [x] Aplicar um processo completo de ETL com relatório de qualidade;
- [x] Importar o relatório diário do OPERA (PDF);
- [x] Gerar gráficos interativos e estáticos;
- [x] Exportar relatórios em Excel, PDF e PowerPoint;
- [x] Suportar temas claro e escuro;
- [x] Demonstrar o funcionamento da aplicação durante a apresentação.

---

# 12. Considerações Finais

O **Hotel Budget Manager** foi desenvolvido como uma aplicação prática para demonstrar os conhecimentos adquiridos na disciplina de Python.

O projeto reúne conceitos de manipulação de arquivos CSV, análise de dados com Pandas, processo ETL, visualização de dados, importação de PDFs e desenvolvimento de interfaces com Streamlit, oferecendo uma solução completa e organizada para o controle financeiro de um hotel.
