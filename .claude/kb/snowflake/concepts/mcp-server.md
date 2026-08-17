# Snowflake-Managed MCP Server

> **Fonte principal para o sistema multiagentes Snowflake.**
> O Snowflake MCP Server expõe Cortex Analyst, Cortex Search, Cortex Agents,
> ferramentas customizadas e execução SQL via interface MCP padrão.

---

## O que é

O **Snowflake-managed MCP Server** é um servidor MCP hospedado pelo Snowflake que permite
que clientes MCP (Claude Code, Cursor, Codex, agentes customizados) descubram e invoquem
capacidades do Snowflake sem gerenciar infraestrutura.

```
Cliente MCP (Claude / agente)
        │
        │ MCP protocol (JSON-RPC)
        ▼
Snowflake MCP Server
        │
        ├── Cortex Analyst  (NL→SQL sobre dados estruturados)
        ├── Cortex Search   (busca semântica em dados não estruturados)
        ├── Cortex Agents   (orquestração multi-tool nativa)
        ├── SQL Execution   (queries diretas com controle de acesso)
        └── Custom Tools    (funções Snowflake expostas como tools MCP)
```

---

## Ferramentas Expostas via MCP

### Cortex Analyst Tool

```json
{
  "name": "cortex_analyst",
  "description": "Answer business questions using natural language over structured Snowflake data",
  "inputSchema": {
    "type": "object",
    "properties": {
      "question": { "type": "string" },
      "semantic_model": { "type": "string", "description": "YAML semantic model name or path" }
    },
    "required": ["question"]
  }
}
```

### Cortex Search Tool

```json
{
  "name": "cortex_search",
  "description": "Semantic search over unstructured data indexed in a Cortex Search Service",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": { "type": "string" },
      "service": { "type": "string", "description": "CORTEX SEARCH SERVICE name" },
      "limit": { "type": "integer", "default": 5 }
    },
    "required": ["query", "service"]
  }
}
```

### SQL Execution Tool

```json
{
  "name": "snowflake_execute_sql",
  "description": "Execute SQL on Snowflake with role and warehouse context",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sql": { "type": "string" },
      "role": { "type": "string" },
      "warehouse": { "type": "string" },
      "database": { "type": "string" },
      "schema": { "type": "string" }
    },
    "required": ["sql"]
  }
}
```

---

## Configuração de Conexão

```python
# snowflake_mcp_config.py
MCP_SERVER_CONFIG = {
    "account": "YOUR_ACCOUNT.snowflakecomputing.com",
    "authenticator": "externalbrowser",  # ou "oauth", "private_key"
    "role": "DATA_ENGINEER_ROLE",        # least-privilege role
    "warehouse": "ANALYST_WH_XS",
    "database": "ANALYTICS",
    "schema": "CORTEX",
    # Snowflake MCP endpoint:
    "mcp_endpoint": "https://{account}.snowflakecomputing.com/api/v2/mcp"
}
```

---

## Guardrails de Segurança (Crítico)

> MCP tem vulnerabilidade conhecida de RCE quando inputs não são validados.
> Implementar SEMPRE antes de expor em produção.

```python
# Validação obrigatória antes de passar SQL para o MCP
import re

BLOCKED_PATTERNS = [
    r'\bDROP\b', r'\bTRUNCATE\b', r'\bDELETE\b(?!\s+FROM\s+\w+\s+WHERE)',
    r'\bGRANT\b', r'\bREVOKE\b', r'\bALTER\s+ACCOUNT\b',
    r'--\s*\w',          # SQL injection comment
    r';\s*\w',           # multi-statement injection
    r'\bSYSTEM\$\w+\b',  # system functions
]

def validate_mcp_sql(sql: str) -> bool:
    sql_upper = sql.upper()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, sql_upper, re.IGNORECASE):
            raise ValueError(f"SQL blocked by MCP security policy: pattern '{pattern}'")
    return True
```

### Configuração de Role Least-Privilege

```sql
-- Role dedicada para o MCP Server (NUNCA usar ACCOUNTADMIN)
CREATE ROLE IF NOT EXISTS MCP_ANALYST_ROLE;

-- Grants mínimos necessários
GRANT USAGE ON WAREHOUSE ANALYST_WH TO ROLE MCP_ANALYST_ROLE;
GRANT USAGE ON DATABASE ANALYTICS TO ROLE MCP_ANALYST_ROLE;
GRANT USAGE ON SCHEMA ANALYTICS.GOLD TO ROLE MCP_ANALYST_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA ANALYTICS.GOLD TO ROLE MCP_ANALYST_ROLE;

-- Para Cortex Analyst
GRANT SNOWFLAKE.CORTEX_USER ON ACCOUNT TO ROLE MCP_ANALYST_ROLE;

-- Sem permissões de escrita, DDL ou admin
-- NUNCA: GRANT ACCOUNTADMIN, SYSADMIN, CREATE TABLE ao MCP role
```

---

## Integração com Claude Code (este plugin)

```json
// .claude/mcp-configs/snowflake.json (exemplo)
{
  "mcpServers": {
    "snowflake": {
      "command": "snowflake-mcp",
      "args": ["--account", "${SNOWFLAKE_ACCOUNT}", "--role", "MCP_ANALYST_ROLE"],
      "env": {
        "SNOWFLAKE_ACCOUNT": "${SNOWFLAKE_ACCOUNT}",
        "SNOWFLAKE_PRIVATE_KEY_PATH": "${SNOWFLAKE_KEY_PATH}"
      }
    }
  }
}
```

---

## Fluxo Típico — Agente Multiagente sobre Snowflake

```
1. Usuário: "Qual foi a receita por região no Q1?"
       ↓
2. @snowflake-cortex-expert recebe a pergunta
       ↓
3. Lê kb/snowflake/concepts/cortex-analyst.md
       ↓
4. Invoca MCP tool: cortex_analyst(question=..., semantic_model="financeiro")
       ↓
5. Snowflake MCP → Cortex Analyst → gera SQL → executa → retorna resultado
       ↓
6. Agente valida Trust Score ≥ 0.7 antes de apresentar
       ↓
7. Resultado estruturado ao usuário com proveniência
```
