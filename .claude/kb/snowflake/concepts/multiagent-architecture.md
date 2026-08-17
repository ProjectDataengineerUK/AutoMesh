# Arquitetura Multiagentes sobre Snowflake

> **Propósito:** Design de sistema com agentes especialistas usando Snowflake como
> plataforma central — MCP como interface, Cortex como motor AI, RBAC como guardrail.

---

## Visão Geral

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code / Cliente MCP             │
│   @snowflake-cortex-expert  @snowflake-sql-expert        │
│   @snowflake-data-engineer  @snowflake-governance-expert │
└───────────────────────┬─────────────────────────────────┘
                        │ MCP Protocol
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Snowflake MCP Server                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Cortex Analyst│  │Cortex Search │  │ SQL Execution│  │
│  │  (NL→SQL)    │  │  (RAG/Search)│  │  (Direct)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────────────────────────┐ │
│  │Cortex Agents │  │  Custom Tools (Snowflake UDFs)   │ │
│  │(orchestration│  │  exposed as MCP tools            │ │
│  └──────────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                   Snowflake Platform                     │
│   Dynamic Tables   Streams/Tasks   Snowpipe             │
│   Iceberg Tables   Snowpark        RBAC/Governance       │
│   Cost Controls    System Views    Trust Center          │
└─────────────────────────────────────────────────────────┘
```

---

## Roteamento de Tarefas — Qual Agente Usar

| Tarefa | Agente | Via MCP |
|--------|--------|---------|
| "Qual foi a receita do Q1?" | `@snowflake-cortex-expert` | `cortex_analyst` tool |
| "Buscar documentos sobre regulatório" | `@snowflake-cortex-expert` | `cortex_search` tool |
| "Otimizar esta query lenta" | `@snowflake-sql-expert` | `snowflake_execute_sql` + EXPLAIN |
| "Criar pipeline de ingestão" | `@snowflake-data-engineer` | SQL DDL via `snowflake_execute_sql` |
| "Configurar masking policy em PII" | `@snowflake-governance-expert` | DDL via `snowflake_execute_sql` |
| "Nosso warehouse XL está caro" | `@snowflake-cost-optimizer` | `system$query_history` via SQL |

---

## Protocolo Multiagente (DOMA adaptado para Snowflake)

### Guardrails do sistema

```
1. Toda query SQL passa por validate_mcp_sql() antes de execução
2. Role MCP_ANALYST_ROLE: somente SELECT em tabelas Gold
3. DDL (CREATE, ALTER, DROP): role separada com aprovação explícita
4. Trust Score < 0.7 em Cortex Analyst: não apresentar → escalar
5. PII detection: se AI_CLASSIFY detectar PII, mascarar antes de retornar
```

### Fluxo de perguntas estruturadas (Cortex Analyst path)

```
1. Receber pergunta de negócio
2. Verificar se Semantic Model cobre o domínio
   ├── Sim → cortex_analyst tool → validar Trust Score → retornar
   └── Não → escalar para @snowflake-sql-expert (SQL direto)
3. Se Trust Score < 0.7: apresentar SQL para revisão humana antes de executar
```

### Fluxo de busca (Cortex Search path)

```
1. Receber query de busca
2. Identificar qual CORTEX SEARCH SERVICE serve o domínio
3. cortex_search tool → top-k chunks
4. AI_COMPLETE (dentro do Snowflake) → gerar resposta
5. Citar fontes (doc_id, score) na resposta
```

### Fluxo de pipeline/infra (Data Engineer path)

```
1. Receber spec do pipeline
2. Ler kb/snowflake/concepts/data-engineering.md
3. Gerar DDL (Dynamic Tables preferred over Tasks/Streams)
4. Revisar com @snowflake-governance-expert antes de aplicar em PROD
5. Aplicar via snowflake_execute_sql com role DATA_ENGINEER_ROLE
```

---

## Grupos de Fontes (5 grupos do sistema)

### Grupo 1 — Snowflake MCP Server
- `snowflake_execute_sql` — queries e DDL controlados
- `cortex_analyst` — NL→SQL para perguntas de negócio
- `cortex_search` — busca semântica sobre docs
- `cortex_agents` — orquestração multi-tool nativa

### Grupo 2 — MCP Servers Externos Integrados
- Salesforce MCP — dados de CRM para enriquecer análises
- GitHub MCP — rastreamento de código que gera os dados
- Slack/Teams — notificação de alerts via Sentinel

### Grupo 3 — KBs para RAG (CORTEX SEARCH SERVICES)
- `kb_snowflake_docs` — documentação técnica indexada
- `kb_business_rules` — regras de negócio em linguagem natural
- `kb_query_patterns` — histórico de queries validadas
- `kb_incidents` — runbooks e padrões de falha

### Grupo 4 — Docs Oficiais Snowflake
- SQL Reference (dialect, functions)
- Cortex Functions Reference (AI_*)
- Snowpark Developer Guide
- Dynamic Tables Reference
- Trust Center / Security Guide

### Grupo 5 — Agentes Especialistas (este plugin)
- `@snowflake-sql-expert` — SQL, queries, Snowpark
- `@snowflake-cortex-expert` — Cortex Analyst, Search, Agents, MCP
- `@snowflake-data-engineer` — Dynamic Tables, Streams, Snowpipe, Iceberg
- `@snowflake-governance-expert` — RBAC, masking, row access, Trust Center
- `@snowflake-cost-optimizer` — warehouse sizing, credits, Query Profile

---

## Deployment Model

```yaml
# Recomendado: um warehouse por tipo de carga
warehouses:
  LOAD_WH_S:
    size: Small
    auto_suspend: 60s
    use_for: [ingestion, snowpipe_streaming]
  
  TRANSFORM_WH_M:
    size: Medium
    auto_suspend: 120s
    use_for: [dynamic_tables, dbt, snowpark]
  
  ANALYTICS_WH_XS:
    size: X-Small
    auto_suspend: 30s
    use_for: [cortex_analyst, cortex_search, ad_hoc_queries]
  
  CORTEX_WH_S:
    size: Small
    auto_suspend: 60s
    use_for: [cortex_search_indexing, ai_functions]
```
