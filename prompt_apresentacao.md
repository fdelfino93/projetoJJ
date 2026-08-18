# Prompt para Apresentação - Hotel Budget Manager

## Estrutura da Apresentação (10 Slides)

### Slide 1: Capa
- **Título:** Hotel Budget Manager - Sistema de Planejamento Orçamentário
- **Subtítulo:** Hotel Ibis Styles Curitiba Centro Cívico
- **Elementos visuais:** Logo do hotel, cores azul e laranja (paleta do projeto)
- **Informações:** Data, autor, disciplina

### Slide 2: Introdução e Objetivos
- **Problema:** Gestão orçamentária manual e fragmentada em planilhas
- **Objetivo:** Sistema integrado para cadastro, análise e acompanhamento financeiro
- **Público-alvo:** Equipe administrativa e gerência do hotel
- **Diferencial:** Dashboard interativo com importação automática de dados do PMS Opera

### Slide 3: Arquitetura do Sistema
- **Diagrama de blocos:** Frontend (Streamlit) → Backend (Python) → Dados (CSV)
- **Fluxo de dados:** Cadastro → ETL → Análise → Visualização → Exportação
- **Tecnologias:** Python, Pandas, Streamlit, Plotly, Matplotlib
- **Estrutura modular:** Separação clara de responsabilidades entre arquivos

### Slide 4: Módulo de Cadastro e ETL
- **Entrada de dados:** Formulário web para receitas e despesas
- **Validação:** Regras de negócio em `utils.py`
- **Processo ETL:**
  - Extração: Leitura dos CSV
  - Transformação: Limpeza, padronização, tradução de categorias
  - Carga: Dados tratados para análise
- **Qualidade:** Relatório de linhas processadas e descartadas

### Slide 5: Importação do Relatório OPERA
- **Fonte:** PMS Opera - Relatório NA02 Manager Report Gross
- **Formato:** PDF diário (`manrepTT.PDF`)
- **Processo:** Extração automática de métricas e tradução para português
- **Idempotência:** Substituição segura de dados duplicados
- **Agendamento:** Tarefa automática no Agendador de Tarefas Windows

### Slide 6: Análise de Dados com Pandas
- **Métricas calculadas:** Totais, médias, comparativos mensais
- **Indicadores:** Receita, despesa, resultado, participação percentual
- **Projeções:** Estimativa de fechamento mensal
- **Comparativos:** Planejado vs. realizado, mês atual vs. mês anterior
- **Categorização:** Hierarquia de categorias contábeis do hotel

### Slide 7: Dashboard Interativo (Streamlit)
- **Páginas do sistema:**
  - Painel: Indicadores gerais e evolução mensal
  - Movimentações: Tabela editável de lançamentos
  - Orçamento: Definição de valores previstos
  - Relatório Mensal: Análise detalhada com exportação
  - Qualidade de Dados: Log de correções do ETL
- **Recursos:** Tema claro/escuro, gráficos interativos, filtros por período

### Slide 8: Visualização de Dados
- **Bibliotecas:** Plotly (interativo) e Matplotlib (estático)
- **Tipos de gráficos:**
  - Barras horizontais: Ranking de categorias (melhor que pizza para 10+ categorias)
  - Linhas: Evolução mensal de receitas e despesas
  - Colunas: Comparativo planejado vs. realizado
- **Acessibilidade:** Cores validadas para daltonismo (ΔE > 15 normal, > 8 simulação)
- **Paleta:** Azul (receitas) e laranja (despesas) - sem julgamento de valor

### Slide 9: Exportação e Relatórios
- **Formatos suportados:** Excel, PDF, PowerPoint, CSV
- **Relatório mensal:** Comparativo detalhado com pontos de atenção
- **Gráficos estáticos:** Matplotlib para documentos impressos
- **PowerPoint:** Apresentação automática com gráficos embutidos
- **Performance:** Geração sob demanda para manter navegação instantânea

### Slide 10: Resultados e Conclusões
- **Benefícios alcançados:**
  - Redução do tempo de consolidação orçamentária
  - Eliminação de erros manuais de digitação
  - Visão integrada de receitas e despesas
  - Tomada de decisão baseada em dados
- **Métricas de sucesso:** 12 meses de dados processados, 5 páginas funcionais
- **Próximos passos:** Integração com API do Opera, alertas automáticos
- **Conceitos aplicados:** Variáveis, condicionais, laços, funções, ETL, visualização