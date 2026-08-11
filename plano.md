# Product Requirements Document (PRD)

# Hotel Budget Manager
## Sistema de Planejamento Orçamentário do Ibis Styles Curitiba Centro Cívico

**Versão:** 1.0  
**Disciplina:** Python Básico  
**Equipe:** Nome dos integrantes

---

# 1. Visão Geral

O **Hotel Budget Manager** é um sistema desenvolvido em Python com o objetivo de auxiliar o gerente financeiro do Hotel Ibis Styles Curitiba Centro Cívico no planejamento e controle do orçamento mensal.

A aplicação permitirá cadastrar receitas e despesas, organizar os dados financeiros, realizar análises simples e apresentar gráficos que auxiliem na tomada de decisões.

---

# 2. Problema

O controle financeiro realizado manualmente pode dificultar a organização das informações e tornar a análise dos resultados mais demorada.

O sistema busca centralizar os dados financeiros em um único ambiente, permitindo uma visualização clara das receitas, despesas e do resultado financeiro do hotel.

---

# 3. Objetivo

Desenvolver uma aplicação em Python que permita:

- Cadastrar receitas;
- Cadastrar despesas;
- Organizar os dados financeiros;
- Realizar análises utilizando Pandas;
- Gerar gráficos para facilitar a visualização das informações.

---

# 4. Público-Alvo

O sistema será utilizado por:

- Gerente Financeiro;
- Administração do Hotel.

---

# 5. Tecnologias

O projeto será desenvolvido utilizando as seguintes tecnologias:

- **Python** – Desenvolvimento da aplicação.
- **Pandas** – Manipulação e análise dos dados.
- **Streamlit** – Interface interativa da aplicação.
- **Arquivos CSV** – Armazenamento das informações.

---

# 6. Funcionalidades

## Cadastro de Receitas

O sistema permitirá cadastrar receitas provenientes de:

- Hospedagem
- Café da manhã
- Restaurante
- Bar
- Estacionamento
- Lavanderia
- Eventos
- Pet Fee

Todas as informações serão armazenadas em um arquivo CSV.

---

## Cadastro de Despesas

O sistema permitirá cadastrar despesas como:

- Folha de pagamento
- Energia elétrica
- Água
- Internet
- Produtos de limpeza
- Amenities
- Rouparia
- Lavanderia
- Manutenção
- Marketing
- Impostos
- Seguros

As informações também serão armazenadas em arquivos CSV.

---

## Consulta dos Dados

O usuário poderá visualizar:

- Todas as receitas;
- Todas as despesas;
- Total de receitas;
- Total de despesas.

---

## Controle Orçamentário

O sistema realizará automaticamente os seguintes cálculos:

- Receita Total;
- Despesa Total;
- Lucro;
- Diferença entre receitas e despesas.

---

# 7. Processo ETL

Antes da geração dos gráficos, será realizado um processo simples de ETL.

## Extração

Leitura dos arquivos CSV utilizando Pandas.

## Transformação

- Remoção de linhas vazias;
- Remoção de registros duplicados;
- Conversão de valores para formato numérico;
- Organização das categorias.

## Carga

Os dados tratados serão utilizados para gerar análises e gráficos.

---

# 8. Dashboard

A interface será desenvolvida utilizando **Streamlit**, permitindo uma visualização simples e intuitiva dos dados.

O Dashboard apresentará gráficos como:

- Receita por categoria;
- Despesas por categoria;
- Receita x Despesa;
- Lucro Total.

---

# 9. Estrutura do Projeto

```text
hotel_budget/

app.py

cadastro.py

analise.py

etl.py

graficos.py

utils.py

data/
    receitas.csv
    despesas.csv

requirements.txt
README.md
```

---

# 10. Fluxo da Aplicação

```text
Início

↓

Tela Inicial (Streamlit)

↓

Cadastrar Receita

↓

Cadastrar Despesa

↓

Ler arquivos CSV

↓

Processo ETL

↓

Análise com Pandas

↓

Dashboard

↓

Visualização dos Gráficos
```

---

# 11. Recursos do Curso Aplicados

Durante o desenvolvimento serão utilizados os seguintes conceitos aprendidos na disciplina:

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

# 12. Gráficos

O sistema apresentará os seguintes gráficos:

- Receita por categoria;
- Despesas por categoria;
- Comparação entre receitas e despesas;
- Lucro total.

---

# 13. Critérios de Sucesso

O projeto será considerado concluído quando for possível:

- Cadastrar receitas;
- Cadastrar despesas;
- Armazenar os dados em arquivos CSV;
- Ler os dados utilizando Pandas;
- Aplicar um processo simples de ETL;
- Gerar gráficos utilizando os dados cadastrados;
- Demonstrar o funcionamento da aplicação durante a apresentação.

---

# 14. Objetivo da Apresentação

Demonstrar como a linguagem Python pode ser utilizada para organizar informações financeiras de um hotel e transformá-las em análises e gráficos que auxiliam na tomada de decisões.

---

# 15. Considerações Finais

O **Hotel Budget Manager** foi desenvolvido como uma aplicação prática para demonstrar os conhecimentos adquiridos na disciplina de Python.

O projeto reúne conceitos de manipulação de arquivos CSV, análise de dados com Pandas, processo ETL, visualização de dados e desenvolvimento de interfaces simples com Streamlit, oferecendo uma solução organizada para o controle financeiro de um hotel.