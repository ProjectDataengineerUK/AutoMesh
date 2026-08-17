# Snowflake MCP Integration Patterns

## Conexão Claude Code ↔ Snowflake MCP

```json
{
  "mcpServers": {
    "snowflake": {
      "command": "npx",
      "args": ["-y", "@snowflake/snowflake-mcp-server"],
      "env": {
        "SNOWFLAKE_ACCOUNT": "my_account",
        "SNOWFLAKE_USER": "mcp_user",
        "SNOWFLAKE_PRIVATE_KEY_FILE": "/path/to/key.p8",
        "SNOWFLAKE_DATABASE": "ANALYTICS",
        "SNOWFLAKE_SCHEMA": "GOLD",
        "SNOWFLAKE_WAREHOUSE": "CORTEX_WH",
        "SNOWFLAKE_ROLE": "MCP_ANALYST_ROLE"
      }
    }
  }
}
```

## Role Mínima para MCP

```sql
-- Role least-privilege para MCP — nunca usar ACCOUNTADMIN
CREATE ROLE IF NOT EXISTS MCP_ANALYST_ROLE;
GRANT ROLE MCP_ANALYST_ROLE TO ROLE SYSADMIN;

GRANT USAGE ON WAREHOUSE CORTEX_WH TO ROLE MCP_ANALYST_ROLE;
GRANT USAGE ON DATABASE ANALYTICS TO ROLE MCP_ANALYST_ROLE;
GRANT USAGE ON SCHEMA ANALYTICS.GOLD TO ROLE MCP_ANALYST_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA ANALYTICS.GOLD TO ROLE MCP_ANALYST_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA ANALYTICS.GOLD TO ROLE MCP_ANALYST_ROLE;
-- Sem WRITE, sem DDL, sem ACCOUNTADMIN
```

## Ferramentas MCP Disponíveis

| Ferramenta           | Uso                                           |
|----------------------|-----------------------------------------------|
| `cortex_analyst`     | NL→SQL via Semantic Model                     |
| `cortex_search`      | Busca semântica em dados não estruturados     |
| `snowflake_execute_sql` | Execução direta de SQL (SELECT only)       |

## Validação SQL Antes de Executar

```python
BLOCKED_PATTERNS = [
    r'\bDROP\b', r'\bDELETE\b', r'\bTRUNCATE\b',
    r'\bINSERT\b', r'\bUPDATE\b', r'\bCREATE\b',
    r'\bALTER\b', r'\bGRANT\b', r'\bREVOKE\b',
    r'\bACCOUNTADMIN\b', r'\bSYSADMIN\b'
]

def validate_mcp_sql(sql: str) -> bool:
    import re
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, sql, re.IGNORECASE):
            raise ValueError(f"Blocked SQL pattern: {pattern}")
    return True
```

## Flow Multi-Agente

```
Claude Code
    │
    ├── snowflake-cortex-expert   (Cortex Analyst / Search)
    │       │
    │       └── MCP: cortex_analyst → gera SQL → Snowflake executa
    │
    ├── snowflake-sql-expert      (queries diretas, otimização)
    │       │
    │       └── MCP: snowflake_execute_sql → resultado → agente formata
    │
    └── snowflake-cost-optimizer  (análise account_usage)
            │
            └── MCP: snowflake_execute_sql → credit queries
```

## Guardrails

- NUNCA expor token ou private key em logs
- SEMPRE validar SQL com `validate_mcp_sql()` antes de executar
- Role MCP → somente SELECT, sem DDL, sem DML
- Trust Score < 0.7 → não executar, pedir refinamento
- PII em resultado → aplicar `AI_REDACT` antes de retornar
