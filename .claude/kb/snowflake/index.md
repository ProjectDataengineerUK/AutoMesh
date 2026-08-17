---
mcp_validated: "2026-05-08"
---

# KB: Snowflake — Índice

**Domínio:** Ecossistema Snowflake para sistemas multiagentes — MCP Server, Cortex AI, Snowpark, governança e custo.
**Agentes:** snowflake-sql-expert, snowflake-cortex-expert, snowflake-data-engineer, snowflake-governance-expert, snowflake-cost-optimizer

---

## Conteúdo Disponível

### Conceitos (`concepts/`)

| Arquivo | Conteúdo |
|---------|---------|
| `concepts/mcp-server.md` | Snowflake-managed MCP Server — Cortex Analyst, Cortex Search, Cortex Agents, execução SQL via MCP |
| `concepts/cortex-ai.md` | Cortex AI Functions (AI_COMPLETE, AI_EMBED, AI_CLASSIFY, AI_FILTER, AI_TRANSCRIBE), Cortex Agents, Snowflake Intelligence |
| `concepts/cortex-analyst.md` | Cortex Analyst — NL→SQL, semantic model YAML, Trust Score, API |
| `concepts/cortex-search.md` | Cortex Search — CORTEX SEARCH SERVICE, hybrid search, chunking, reranking |
| `concepts/data-engineering.md` | Dynamic Tables, Streams, Tasks, Snowpipe, Snowpipe Streaming, Iceberg |
| `concepts/governance.md` | RBAC Snowflake, data classification, masking policies, row access policies, Trust Center |
| `concepts/snowpark.md` | Snowpark Python — DataFrames, UDFs, stored procedures, Snowpark ML |
| `concepts/multiagent-architecture.md` | Arquitetura de agentes especializados sobre Snowflake |

### Padrões (`patterns/`)

| Arquivo | Conteúdo |
|---------|---------|
| `patterns/mcp-integration.md` | Como conectar agentes ao Snowflake MCP Server, tool definitions, segurança |
| `patterns/cortex-analyst-patterns.md` | Semantic model YAML, perguntas de negócio, fallback SQL, confiança |
| `patterns/cortex-search-patterns.md` | Criação de SEARCH SERVICE, chunking, RAG com Cortex Search |
| `patterns/dynamic-table-patterns.md` | Medallion com Dynamic Tables, TARGET_LAG, chains |
| `patterns/cost-optimization.md` | Warehouse sizing, auto-suspend, credit alerting, Query Profile |

---

## Mapa KB por Tipo de Tarefa

| Tipo de Tarefa | KB a Ler Primeiro | Agente |
|----------------|-------------------|--------|
| Conectar agente via MCP | `concepts/mcp-server.md` | `@snowflake-cortex-expert` |
| NL→SQL / Cortex Analyst | `concepts/cortex-analyst.md` | `@snowflake-cortex-expert` |
| Busca semântica / RAG | `concepts/cortex-search.md` | `@snowflake-cortex-expert` |
| SQL / query optimization | `concepts/data-engineering.md` + `cloud-platforms/patterns/snowflake-patterns.md` | `@snowflake-sql-expert` |
| Dynamic Tables / Streams | `concepts/data-engineering.md` | `@snowflake-data-engineer` |
| RBAC / masking / RLS | `concepts/governance.md` | `@snowflake-governance-expert` |
| Créditos / warehouse sizing | `patterns/cost-optimization.md` | `@snowflake-cost-optimizer` |
| Snowpark Python / ML | `concepts/snowpark.md` | `@snowflake-data-engineer` |
